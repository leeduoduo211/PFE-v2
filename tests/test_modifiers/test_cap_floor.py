import numpy as np
from pfev2.instruments.vanilla import VanillaOption
from pfev2.modifiers.cap_floor import PayoffCap, PayoffFloor


def test_cap():
    base = VanillaOption(trade_id="C1", maturity=1.0, notional=1.0,
                         asset_indices=(0,), strike=100.0, option_type="call")
    capped = PayoffCap(base, cap=15.0)
    spots = np.array([[130.0], [110.0], [80.0]])
    payoffs = capped.payoff(spots, None)
    np.testing.assert_allclose(payoffs, [15.0, 10.0, 0.0])


def test_floor():
    base = VanillaOption(trade_id="C1", maturity=1.0, notional=1.0,
                         asset_indices=(0,), strike=100.0, option_type="call")
    floored = PayoffFloor(base, floor=5.0)
    spots = np.array([[130.0], [102.0], [80.0]])
    payoffs = floored.payoff(spots, None)
    np.testing.assert_allclose(payoffs, [30.0, 5.0, 5.0])
