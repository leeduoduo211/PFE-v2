import numpy as np

from pfev2.instruments.vanilla import VanillaOption
from pfev2.modifiers.leverage import LeverageModifier


def test_leverage_above_threshold():
    base = VanillaOption(trade_id="C1", maturity=1.0, notional=1.0,
                         asset_indices=(0,), strike=100.0, option_type="call")
    lev = LeverageModifier(base, threshold=10.0, leverage=2.0)
    spots = np.array([[120.0], [105.0]])
    payoffs = lev.payoff(spots, None)
    np.testing.assert_allclose(payoffs, [40.0, 5.0])
