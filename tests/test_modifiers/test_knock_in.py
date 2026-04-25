import numpy as np

from pfev2.instruments.vanilla import VanillaOption
from pfev2.modifiers.knock_in import KnockIn


def test_breach_activates_payoff():
    base = VanillaOption(trade_id="C1", maturity=1.0, notional=1.0,
                         asset_indices=(0,), strike=100.0, option_type="call")
    ki = KnockIn(base, barrier=120.0, direction="up")
    paths = np.array([[[100.0], [125.0], [130.0]]])
    payoffs = ki.payoff(paths[:, -1, :], paths)
    assert payoffs[0] > 0


def test_no_breach_zeros_payoff():
    base = VanillaOption(trade_id="C1", maturity=1.0, notional=1.0,
                         asset_indices=(0,), strike=100.0, option_type="call")
    ki = KnockIn(base, barrier=120.0, direction="up")
    paths = np.array([[[100.0], [110.0], [115.0]]])
    payoffs = ki.payoff(paths[:, -1, :], paths)
    np.testing.assert_allclose(payoffs, [0.0])
