import numpy as np
import pytest
from pfev2.engine.gbm import MultivariateGBM
from pfev2.engine.backends.numpy_backend import NumpyBackend
from pfev2.core.types import MarketData, TimeGrid


@pytest.fixture
def engine():
    return MultivariateGBM(backend=NumpyBackend())


@pytest.fixture
def market():
    return MarketData(
        spots=np.array([100.0, 50.0]),
        vols=np.array([0.20, 0.30]),
        rates=np.array([0.05, 0.05]),
        domestic_rate=0.05,
        corr_matrix=np.array([[1.0, 0.5], [0.5, 1.0]]),
        asset_names=["A", "B"],
        asset_classes=["EQUITY", "EQUITY"],
    )


@pytest.fixture
def grid():
    return TimeGrid.from_maturity(1.0, frequency="weekly")


def test_outer_paths_shape(engine, market, grid):
    paths = engine.simulate(market, grid, n_paths=100, seed=42)
    assert paths.shape == (100, len(grid.dates), 2)


def test_outer_paths_start_at_spots(engine, market, grid):
    paths = engine.simulate(market, grid, n_paths=100, seed=42)
    np.testing.assert_allclose(paths[:, 0, 0], 100.0)
    np.testing.assert_allclose(paths[:, 0, 1], 50.0)


def test_outer_paths_positive(engine, market, grid):
    paths = engine.simulate(market, grid, n_paths=1000, seed=42)
    assert np.all(paths > 0)


def test_mean_converges_to_drift(engine, grid):
    """E[S(T)] = S0 * exp(r*T) under GBM."""
    market = MarketData(
        spots=np.array([100.0]),
        vols=np.array([0.20]),
        rates=np.array([0.05]),
        domestic_rate=0.05,
        corr_matrix=np.array([[1.0]]),
        asset_names=["X"],
        asset_classes=["EQUITY"],
    )
    paths = engine.simulate(market, grid, n_paths=50000, seed=42)
    terminal = paths[:, -1, 0]
    expected = 100.0 * np.exp(0.05 * 1.0)
    np.testing.assert_allclose(terminal.mean(), expected, rtol=0.02)


def test_correlation_recovery(engine, market):
    grid = TimeGrid.from_maturity(1.0, frequency="monthly")
    paths = engine.simulate(market, grid, n_paths=50000, seed=42)
    log_returns = np.log(paths[:, -1, :] / paths[:, 0, :])
    empirical_corr = np.corrcoef(log_returns.T)[0, 1]
    np.testing.assert_allclose(empirical_corr, 0.5, atol=0.03)


def test_inner_paths_shape(engine, market, grid):
    node_spots = np.array([105.0, 52.0])
    remaining = grid.remaining_grid(10)
    inner = engine.generate_inner_paths(
        market, node_spots, remaining, n_paths=200, seed=99
    )
    assert inner.shape == (200, len(remaining.dates), 2)
    np.testing.assert_allclose(inner[:, 0, :], np.broadcast_to(node_spots, (200, 2)))
