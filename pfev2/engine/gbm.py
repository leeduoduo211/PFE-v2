import numpy as np

from pfev2.core.protocols import SimulationBackend
from pfev2.core.types import MarketData, TimeGrid
from pfev2.engine.cholesky import CholeskyDecomposer


class MultivariateGBM:
    def __init__(self, backend: SimulationBackend):
        self._backend = backend

    def simulate(
        self, market: MarketData, grid: TimeGrid, n_paths: int, seed: int
    ) -> np.ndarray:
        """Generate outer paths. Returns (n_paths, T_steps, N_assets)."""
        n_assets = len(market.spots)
        n_steps = len(grid.dates) - 1
        L = CholeskyDecomposer.decompose(market.corr_matrix)

        # Correlated normals: (n_paths, n_steps, n_assets)
        z = self._backend.randn((n_paths, n_steps, n_assets), seed=seed)
        w = self._backend.matmul(z, L.T)

        # GBM log-increments
        dt = grid.dt  # (n_steps,)
        drift = (market.rates - 0.5 * market.vols ** 2) * dt[:, np.newaxis]  # (n_steps, n_assets)
        diffusion = market.vols * np.sqrt(dt[:, np.newaxis]) * w  # (n_paths, n_steps, n_assets)
        log_increments = drift[np.newaxis, :, :] + diffusion  # (n_paths, n_steps, n_assets)

        # Cumulative sum → prices
        log_paths = np.cumsum(log_increments, axis=1)  # (n_paths, n_steps, n_assets)
        log_s0 = np.log(market.spots)  # (n_assets,)

        # Prepend t=0: spots
        paths = np.zeros((n_paths, n_steps + 1, n_assets))
        paths[:, 0, :] = market.spots
        paths[:, 1:, :] = self._backend.exp(log_s0 + log_paths)

        return paths

    def generate_inner_paths(
        self,
        market: MarketData,
        node_spots: np.ndarray,
        remaining_grid: TimeGrid,
        n_paths: int,
        seed: int,
    ) -> np.ndarray:
        """Generate inner paths from a node. Returns (n_paths, T_remaining, N_assets)."""
        inner_market = market.evolve(node_spots, t=0.0)
        return self.simulate(inner_market, remaining_grid, n_paths, seed)
