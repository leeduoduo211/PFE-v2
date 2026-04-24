import numpy as np

from pfev2.instruments.vanilla import VanillaOption
from pfev2.modifiers.cap_floor import PayoffCap


def test_high_cap_is_passthrough():
    base = VanillaOption(trade_id="C1", maturity=1.0, notional=1.0,
                         asset_indices=(0,), strike=100.0, option_type="call")
    capped = PayoffCap(base, cap=1e10)
    spots = np.array([[150.0], [80.0]])
    raw = base.payoff(spots, None)
    modified = capped.payoff(spots, None)
    np.testing.assert_allclose(modified, raw)
