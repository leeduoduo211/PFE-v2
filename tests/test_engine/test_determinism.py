import numpy as np

from pfev2.core.types import MarketData, TimeGrid
from pfev2.engine.backends.numpy_backend import NumpyBackend
from pfev2.engine.gbm import MultivariateGBM


def test_same_seed_same_paths():
    engine = MultivariateGBM(backend=NumpyBackend())
    market = MarketData(
        spots=np.array([100.0]),
        vols=np.array([0.20]),
        rates=np.array([0.05]),
        domestic_rate=0.05,
        corr_matrix=np.array([[1.0]]),
        asset_names=["X"],
        asset_classes=["EQUITY"],
    )
    grid = TimeGrid.from_maturity(0.5, frequency="weekly")
    p1 = engine.simulate(market, grid, n_paths=50, seed=42)
    p2 = engine.simulate(market, grid, n_paths=50, seed=42)
    np.testing.assert_array_equal(p1, p2)


def test_different_seed_different_paths():
    engine = MultivariateGBM(backend=NumpyBackend())
    market = MarketData(
        spots=np.array([100.0]),
        vols=np.array([0.20]),
        rates=np.array([0.05]),
        domestic_rate=0.05,
        corr_matrix=np.array([[1.0]]),
        asset_names=["X"],
        asset_classes=["EQUITY"],
    )
    grid = TimeGrid.from_maturity(0.5, frequency="weekly")
    p1 = engine.simulate(market, grid, n_paths=50, seed=1)
    p2 = engine.simulate(market, grid, n_paths=50, seed=2)
    assert not np.allclose(p1, p2)
