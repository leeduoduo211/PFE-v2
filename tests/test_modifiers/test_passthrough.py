import numpy as np
from pfev2.instruments.vanilla import VanillaCall
from pfev2.modifiers.cap_floor import PayoffCap


def test_high_cap_is_passthrough():
    base = VanillaCall(trade_id="C1", maturity=1.0, notional=1.0,
                       asset_indices=(0,), strike=100.0)
    capped = PayoffCap(base, cap=1e10)
    spots = np.array([[150.0], [80.0]])
    raw = base.payoff(spots, None)
    modified = capped.payoff(spots, None)
    np.testing.assert_allclose(modified, raw)
