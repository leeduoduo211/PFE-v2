import time
from concurrent.futures import ThreadPoolExecutor

import numpy as np

from pfev2.core.exceptions import ConfigError
from pfev2.core.types import MarketData, PFEConfig, TimeGrid
from pfev2.engine.backends.numpy_backend import NumpyBackend
from pfev2.engine.gbm import MultivariateGBM
from pfev2.pricing.inner_mc import InnerMCPricer
from pfev2.risk.result import PFEResult
from pfev2.utils.seeds import cantor_pair


def compute_pfe(
    portfolio: list,
    market: MarketData,
    config: PFEConfig,
    on_progress=None,
    per_trade_detail: bool = False,
) -> PFEResult:
    """Main entry point: compute PFE/EPE profiles for a portfolio."""
    start_time = time.time()

    use_parallel = config.n_workers > 1

    # Validate
    for trade in portfolio:
        for idx in trade.asset_indices:
            if idx < 0 or idx >= len(market.spots):
                raise ConfigError(
                    f"Trade {trade.trade_id} references asset index {idx}, "
                    f"but market has {len(market.spots)} assets"
                )

    if not portfolio:
        raise ConfigError("portfolio must contain at least one trade")

    # Build time grid from longest maturity
    max_maturity = max(t.maturity for t in portfolio)
    grid = TimeGrid.from_maturity(max_maturity, config.grid_frequency)

    # Select backend
    if config.backend == "numba":
        try:
            from pfev2.engine.backends.numba_backend import NumbaBackend
            backend = NumbaBackend()
        except ImportError:
            backend = NumpyBackend()
    else:
        backend = NumpyBackend()

    engine = MultivariateGBM(backend=backend)
    pricer = InnerMCPricer(
        engine=engine,
        antithetic=config.antithetic,
        n_workers=config.n_workers if use_parallel else 1,
    )

    # Generate outer paths
    outer_paths = engine.simulate(market, grid, config.n_outer, config.seed)

    # Initialize MtM matrix
    n_steps = len(grid.dates)
    mtm_matrix = np.zeros((config.n_outer, n_steps))

    # Per-trade detail
    n_trades = len(portfolio)
    per_trade_mtm = np.zeros((n_trades, config.n_outer, n_steps)) if per_trade_detail else None

    # Nested MC loop — starts at t=0 to compute initial MtM (premium baseline)
    # This is critical for margined PFE: exposure(t) = max(MtM(t) - MtM(t-MPoR), 0)
    # Without t=0 MtM, the early lookback clips to zero instead of the actual premium.

    def _remaining_grid_to_maturity(t_idx, maturity):
        """Return a relative grid from the valuation node to this trade's maturity."""
        abs_time = grid.dates[t_idx]
        future_dates = grid.dates[t_idx:][grid.dates[t_idx:] <= maturity + 1e-12]
        if future_dates[-1] < maturity - 1e-12:
            future_dates = np.append(future_dates, maturity)
        remaining_dates = future_dates - abs_time
        return TimeGrid(dates=remaining_dates, dt=np.diff(remaining_dates))

    def _price_one_step(t_idx):
        """Price all trades at one time step. Returns list of (trade_idx, mtm_array)."""
        abs_time = grid.dates[t_idx]
        all_node_spots = outer_paths[:, t_idx, :]
        results = []

        for trade_idx, trade in enumerate(portfolio):
            if not trade.is_alive(abs_time):
                continue
            remaining = _remaining_grid_to_maturity(t_idx, trade.maturity)
            if remaining.dates[-1] <= 0:
                continue
            batch_seed = backend.derive_seed(config.seed, 0, t_idx) + cantor_pair(trade_idx, 0)
            if trade.requires_full_path:
                trade_mtms = pricer.batch_price_path_dependent(
                    trade,
                    market,
                    all_node_spots,
                    remaining,
                    config.n_inner,
                    batch_seed,
                    realized_paths=outer_paths[:, : t_idx + 1, :],
                    realized_grid=grid.dates[: t_idx + 1],
                )
            else:
                trade_mtms = pricer.batch_price_european(
                    trade, market, all_node_spots, remaining, config.n_inner, batch_seed
                )
            results.append((trade_idx, trade_mtms))
        return results

    if use_parallel:
        # Parallel execution across time steps using threads (NumPy releases GIL)
        with ThreadPoolExecutor(max_workers=config.n_workers) as pool:
            futures = {t_idx: pool.submit(_price_one_step, t_idx) for t_idx in range(n_steps)}
            for t_idx in range(n_steps):
                step_results = futures[t_idx].result()
                for trade_idx, trade_mtms in step_results:
                    mtm_matrix[:, t_idx] += trade_mtms
                    if per_trade_detail:
                        per_trade_mtm[trade_idx, :, t_idx] = trade_mtms
                if on_progress:
                    on_progress(t_idx / max(n_steps - 1, 1))
    else:
        for t_idx in range(0, n_steps):
            step_results = _price_one_step(t_idx)
            for trade_idx, trade_mtms in step_results:
                mtm_matrix[:, t_idx] += trade_mtms
                if per_trade_detail:
                    per_trade_mtm[trade_idx, :, t_idx] = trade_mtms
            if on_progress:
                on_progress(t_idx / max(n_steps - 1, 1))

    # Exposure calculation
    # Always compute unmargined exposure
    unmargined_exposure = np.maximum(mtm_matrix, 0.0)
    unmargined_pfe_curve = np.quantile(unmargined_exposure, config.confidence_level, axis=0)
    unmargined_epe_curve = np.mean(unmargined_exposure, axis=0)

    if config.margined:
        freq_map = {"daily": 252, "weekly": 52, "monthly": 12}
        steps_per_year = freq_map.get(config.grid_frequency, 52)
        mpor_steps = max(1, int(round(config.mpor_days / 252 * steps_per_year)))
        exposure = np.zeros_like(mtm_matrix)
        for t in range(n_steps):
            lookback = max(t - mpor_steps, 0)
            exposure[:, t] = np.maximum(mtm_matrix[:, t] - mtm_matrix[:, lookback], 0.0)
    else:
        exposure = unmargined_exposure

    # Risk metrics
    pfe_curve = np.quantile(exposure, config.confidence_level, axis=0)
    epe_curve = np.mean(exposure, axis=0)
    peak_pfe = float(np.max(pfe_curve))

    # EEPE: Basel III — Effective EE is non-decreasing version of *unmargined* EPE.
    # Per Basel III SA-CCR / IMM, EEPE must be computed on unmargined exposure regardless
    # of whether the margined PFE profile is also requested.
    effective_ee = np.zeros_like(unmargined_epe_curve)
    effective_ee[0] = unmargined_epe_curve[0]
    for t in range(1, len(unmargined_epe_curve)):
        effective_ee[t] = max(effective_ee[t - 1], unmargined_epe_curve[t])
    if len(grid.dt) > 0:
        eepe = float(np.sum(effective_ee[1:] * grid.dt) / grid.dates[-1])
    else:
        eepe = 0.0

    elapsed = time.time() - start_time

    return PFEResult(
        time_points=grid.dates,
        pfe_curve=pfe_curve,
        epe_curve=epe_curve,
        peak_pfe=peak_pfe,
        eepe=eepe,
        mtm_matrix=mtm_matrix,
        config=config,
        computation_time=elapsed,
        per_trade_mtm=per_trade_mtm,
        unmargined_pfe_curve=unmargined_pfe_curve,
        unmargined_epe_curve=unmargined_epe_curve,
    )
