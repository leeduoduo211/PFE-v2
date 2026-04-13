import numpy as np
import pytest
from pfev2.pricing.inner_mc import InnerMCPricer
from pfev2.instruments.vanilla import VanillaCall
from pfev2.engine.gbm import MultivariateGBM
from pfev2.engine.backends.numpy_backend import NumpyBackend
from pfev2.core.types import MarketData, TimeGrid


@pytest.fixture
def pricer():
    engine = MultivariateGBM(backend=NumpyBackend())
    return InnerMCPricer(engine=engine)


@pytest.fixture
def market():
    return MarketData(
        spots=np.array([100.0]),
        vols=np.array([0.20]),
        rates=np.array([0.05]),
        domestic_rate=0.05,
        corr_matrix=np.array([[1.0]]),
        asset_names=["X"],
        asset_classes=["EQUITY"],
    )


def test_vanilla_call_convergence(pricer, market):
    """MC price should converge to Black-Scholes for a vanilla call."""
    call = VanillaCall(trade_id="C1", maturity=1.0, notional=1.0,
                       asset_indices=(0,), strike=100.0)
    node_spots = np.array([100.0])
    remaining_grid = TimeGrid.from_maturity(1.0, frequency="weekly")

    mtm = pricer.price_trade(
        trade=call, market=market, node_spots=node_spots,
        remaining_grid=remaining_grid, n_inner=50000, seed=42,
    )

    from scipy.stats import norm
    S, K, r, sigma, T = 100.0, 100.0, 0.05, 0.20, 1.0
    d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    bs_price = S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)

    np.testing.assert_allclose(mtm, bs_price, rtol=0.03)


def test_portfolio_netting(pricer, market):
    """Long call + short call at same strike = ~zero."""
    call = VanillaCall(trade_id="C1", maturity=1.0, notional=1.0,
                       asset_indices=(0,), strike=100.0)
    put = VanillaCall(trade_id="C2", maturity=1.0, notional=-1.0,
                      asset_indices=(0,), strike=100.0)

    node_spots = np.array([100.0])
    remaining_grid = TimeGrid.from_maturity(1.0, frequency="weekly")
    portfolio = [call, put]

    net_mtm = pricer.price_portfolio(
        portfolio=portfolio, market=market, node_spots=node_spots,
        remaining_grid=remaining_grid, n_inner=10000, base_seed=42,
    )
    np.testing.assert_allclose(net_mtm, 0.0, atol=0.5)
