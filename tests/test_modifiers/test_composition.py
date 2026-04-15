import numpy as np
from pfev2.instruments.vanilla import VanillaOption
from pfev2.modifiers.knock_out import KnockOut
from pfev2.modifiers.cap_floor import PayoffCap


def test_ko_plus_cap():
    base = VanillaOption(trade_id="C1", maturity=1.0, notional=1.0,
                         asset_indices=(0,), strike=100.0, option_type="call")
    capped = PayoffCap(base, cap=15.0)
    ko = KnockOut(capped, barrier=140.0, direction="up")

    paths1 = np.array([[[100.0], [110.0], [130.0]]])
    p1 = ko.payoff(paths1[:, -1, :], paths1)
    np.testing.assert_allclose(p1, [15.0])

    paths2 = np.array([[[100.0], [145.0], [130.0]]])
    p2 = ko.payoff(paths2[:, -1, :], paths2)
    np.testing.assert_allclose(p2, [0.0])
