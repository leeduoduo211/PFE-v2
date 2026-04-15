import numpy as np
from pfev2.pricing.inner_mc import InnerMCPricer
from pfev2.instruments.vanilla import VanillaOption
from pfev2.engine.gbm import MultivariateGBM
from pfev2.engine.backends.numpy_backend import NumpyBackend
from pfev2.core.types import MarketData, TimeGrid


def test_call_put_parity_netting():
    """Long call + long put at same strike = straddle (always positive)."""
    market = MarketData(
        spots=np.array([100.0]),
        vols=np.array([0.20]),
        rates=np.array([0.05]),
        domestic_rate=0.05,
        corr_matrix=np.array([[1.0]]),
        asset_names=["X"],
        asset_classes=["EQUITY"],
    )
    call = VanillaOption(trade_id="C1", maturity=1.0, notional=1.0,
                         asset_indices=(0,), strike=100.0, option_type="call")
    put = VanillaOption(trade_id="P1", maturity=1.0, notional=1.0,
                        asset_indices=(0,), strike=100.0, option_type="put")

    engine = MultivariateGBM(backend=NumpyBackend())
    pricer = InnerMCPricer(engine=engine)
    grid = TimeGrid.from_maturity(1.0, frequency="weekly")

    mtm = pricer.price_portfolio(
        portfolio=[call, put],
        market=market,
        node_spots=np.array([100.0]),
        remaining_grid=grid,
        n_inner=10000,
        base_seed=42,
    )
    assert mtm > 0  # straddle is always worth something
