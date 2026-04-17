import numpy as np
from pfev2.core.types import MarketData, TimeGrid
from pfev2.engine.gbm import MultivariateGBM
from pfev2.engine.cholesky import CholeskyDecomposer
from pfev2.utils.seeds import cantor_pair


class InnerMCPricer:
    def __init__(self, engine: MultivariateGBM, antithetic: bool = False, n_workers: int = 1):
        self._engine = engine
        self._antithetic = antithetic
        self._mem_budget = 200_000_000 // max(n_workers, 1)
        # Cholesky cache: keyed by id(corr_matrix). Since MarketData is frozen and the
        # same market object is reused across all time steps in compute_pfe, this avoids
        # recomputing the identical decomposition hundreds of times per run.
        self._chol_cache: dict = {}

    def price_trade(
        self,
        trade,
        market: MarketData,
        node_spots: np.ndarray,
        remaining_grid: TimeGrid,
        n_inner: int,
        seed: int,
    ) -> float:
        """Price a single trade at a node. Returns scalar MtM."""
        inner_paths = self._engine.generate_inner_paths(
            market, node_spots, remaining_grid, n_inner, seed
        )

        asset_pos = list(trade.asset_indices)
        trade_paths = inner_paths[:, :, asset_pos]

        terminal_spots = trade_paths[:, -1, :]
        if trade.requires_full_path:
            payoffs = trade.payoff(terminal_spots, trade_paths, remaining_grid.dates)
        else:
            payoffs = trade.payoff(terminal_spots, None)

        tau = remaining_grid.dates[-1]
        discount = np.exp(-market.domestic_rate * tau) if tau > 0 else 1.0
        mtm = trade.notional * discount * np.mean(payoffs)
        return float(mtm)

    def batch_price_european(
        self,
        trade,
        market: MarketData,
        all_node_spots: np.ndarray,
        remaining_grid: TimeGrid,
        n_inner: int,
        seed: int,
    ) -> np.ndarray:
        """Batch-price a European trade across ALL outer paths at once.

        For non-path-dependent trades only. Generates terminal spots for all
        outer nodes in one vectorized operation — eliminates the Python loop
        over outer paths.

        Parameters
        ----------
        all_node_spots : (n_outer, n_assets) array of spot prices at each node
        Returns : (n_outer,) array of MtM values
        """
        n_outer, n_assets = all_node_spots.shape
        tau = remaining_grid.dates[-1]
        if tau <= 0:
            return np.zeros(n_outer)

        asset_pos = list(trade.asset_indices)
        n_trade_assets = len(asset_pos)

        # Cholesky factor for correlated normals (cached for the lifetime of this pricer)
        corr_id = id(market.corr_matrix)
        if corr_id not in self._chol_cache:
            self._chol_cache[corr_id] = CholeskyDecomposer.decompose(market.corr_matrix)
        L = self._chol_cache[corr_id]

        # Memory budget: process in chunks to stay under ~200MB
        bytes_per_element = 8
        target_bytes = self._mem_budget
        elements_per_outer = n_inner * n_trade_assets
        chunk_size = max(1, target_bytes // (elements_per_outer * bytes_per_element))
        chunk_size = min(chunk_size, n_outer)

        mtm_all = np.empty(n_outer)

        drift = (market.rates - 0.5 * market.vols ** 2) * tau  # (n_assets,)
        diffusion = market.vols * np.sqrt(tau)                  # (n_assets,)
        discount = np.exp(-market.domestic_rate * tau)

        # Antithetic: generate n_inner/2 normals, mirror to -Z
        n_half = n_inner // 2 if self._antithetic else n_inner

        for start in range(0, n_outer, chunk_size):
            end = min(start + chunk_size, n_outer)
            chunk_n = end - start
            chunk_spots = all_node_spots[start:end]  # (chunk_n, n_assets)

            # Generate correlated normals
            rng = np.random.Generator(np.random.PCG64(seed + start))
            z = rng.standard_normal((chunk_n, n_half, n_assets))
            w = z @ L.T

            if self._antithetic:
                w = np.concatenate([w, -w], axis=1)  # (chunk_n, n_inner, n_assets)

            # GBM to terminal time: S_T = S_0 * exp((r - 0.5σ²)*τ + σ*√τ*W)
            log_returns = drift[np.newaxis, np.newaxis, :] + diffusion[np.newaxis, np.newaxis, :] * w
            terminal_spots = chunk_spots[:, np.newaxis, :] * np.exp(log_returns)

            # Select trade assets and compute payoffs
            trade_terminal = terminal_spots[:, :, asset_pos]
            n_eff = w.shape[1]  # n_inner (or n_half*2 for antithetic)
            flat_spots = trade_terminal.reshape(chunk_n * n_eff, n_trade_assets)
            payoffs = trade.payoff(flat_spots, None)

            payoffs_2d = payoffs.reshape(chunk_n, n_eff)
            mean_payoffs = np.mean(payoffs_2d, axis=1)

            mtm_all[start:end] = trade.notional * discount * mean_payoffs

        return mtm_all

    def batch_price_path_dependent(
        self,
        trade,
        market: MarketData,
        all_node_spots: np.ndarray,
        remaining_grid: TimeGrid,
        n_inner: int,
        seed: int,
    ) -> np.ndarray:
        """Batch-price a path-dependent trade across ALL outer paths at once.

        Generates full inner MC paths for every outer node in chunked batches,
        eliminating the Python loop over outer paths that makes per-path pricing
        so slow.

        Parameters
        ----------
        all_node_spots : (n_outer, n_assets) array of spot prices at each node
        Returns : (n_outer,) array of MtM values
        """
        n_outer, n_assets = all_node_spots.shape
        tau = remaining_grid.dates[-1]
        if tau <= 0:
            return np.zeros(n_outer)

        asset_pos = list(trade.asset_indices)
        n_trade_assets = len(asset_pos)
        n_steps_gen = len(remaining_grid.dt)  # number of GBM increments

        corr_id = id(market.corr_matrix)
        if corr_id not in self._chol_cache:
            self._chol_cache[corr_id] = CholeskyDecomposer.decompose(market.corr_matrix)
        L = self._chol_cache[corr_id]
        dt = remaining_grid.dt  # (n_steps_gen,)
        drift = (market.rates[asset_pos] - 0.5 * market.vols[asset_pos] ** 2)  # (n_trade_assets,)
        diffusion_scale = market.vols[asset_pos]  # (n_trade_assets,)
        discount = np.exp(-market.domestic_rate * tau)

        # Antithetic: generate n_inner/2 normals, mirror to -Z
        n_half = n_inner // 2 if self._antithetic else n_inner
        n_eff = n_half * 2 if self._antithetic else n_inner

        # Memory budget: paths array is (chunk_n * n_eff, n_steps_gen+1, n_trade_assets)
        bytes_per_element = 8
        target_bytes = self._mem_budget
        elements_per_outer = n_eff * n_steps_gen * n_trade_assets
        chunk_size = max(1, target_bytes // (elements_per_outer * bytes_per_element))
        chunk_size = min(chunk_size, n_outer)

        mtm_all = np.empty(n_outer)

        for start in range(0, n_outer, chunk_size):
            end = min(start + chunk_size, n_outer)
            chunk_n = end - start

            # Starting spots for trade assets, repeated n_eff times per outer path
            chunk_trade_spots = all_node_spots[start:end, asset_pos]
            s0 = np.repeat(chunk_trade_spots, n_eff, axis=0)

            # Correlated normals
            rng = np.random.Generator(np.random.PCG64(seed + start))
            z = rng.standard_normal((chunk_n * n_half, n_steps_gen, n_assets))
            w = z @ L.T

            if self._antithetic:
                w = np.concatenate([w, -w], axis=0)  # (chunk_n * n_eff, n_steps_gen, n_assets)

            # Select trade assets from correlated normals
            w_trade = w[:, :, asset_pos]

            # GBM log-increments
            dt_col = dt[:, np.newaxis]
            log_inc = (drift * dt_col +
                       diffusion_scale * np.sqrt(dt_col) * w_trade)

            # Full log paths via cumsum, then exponentiate
            log_paths = np.cumsum(log_inc, axis=1)
            log_s0 = np.log(s0)

            paths = np.empty((chunk_n * n_eff, n_steps_gen + 1, n_trade_assets))
            paths[:, 0, :] = s0
            paths[:, 1:, :] = np.exp(log_s0[:, np.newaxis, :] + log_paths)

            terminal_spots = paths[:, -1, :]
            payoffs = trade.payoff(terminal_spots, paths, remaining_grid.dates)

            payoffs_2d = payoffs.reshape(chunk_n, n_eff)
            mean_payoffs = np.mean(payoffs_2d, axis=1)
            mtm_all[start:end] = trade.notional * discount * mean_payoffs

        return mtm_all

    def price_portfolio(
        self,
        portfolio: list,
        market: MarketData,
        node_spots: np.ndarray,
        remaining_grid: TimeGrid,
        n_inner: int,
        base_seed: int,
    ) -> float:
        """Price all trades in portfolio at a node. Returns net MtM."""
        net_mtm = 0.0
        for i, trade in enumerate(portfolio):
            if not trade.is_alive(remaining_grid.dates[0]):
                continue
            seed = base_seed + cantor_pair(i, 0)
            net_mtm += self.price_trade(
                trade, market, node_spots, remaining_grid, n_inner, seed
            )
        return net_mtm
