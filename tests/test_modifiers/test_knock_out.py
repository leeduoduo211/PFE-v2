import numpy as np
from pfev2.instruments.vanilla import VanillaCall
from pfev2.modifiers.knock_out import KnockOut


def test_no_breach_preserves_payoff():
    base = VanillaCall(trade_id="C1", maturity=1.0, notional=1.0,
                       asset_indices=(0,), strike=100.0)
    ko = KnockOut(base, barrier=120.0, direction="up")
    paths = np.array([[[100.0], [105.0], [110.0], [115.0]]])
    spots = paths[:, -1, :]
    raw = base.payoff(spots, None)
    modified = ko.payoff(spots, paths)
    np.testing.assert_allclose(modified, raw)


def test_breach_zeros_payoff():
    base = VanillaCall(trade_id="C1", maturity=1.0, notional=1.0,
                       asset_indices=(0,), strike=100.0)
    ko = KnockOut(base, barrier=120.0, direction="up")
    paths = np.array([[[100.0], [125.0], [110.0], [130.0]]])
    spots = paths[:, -1, :]
    payoffs = ko.payoff(spots, paths)
    np.testing.assert_allclose(payoffs, [0.0])


def test_down_and_out():
    base = VanillaCall(trade_id="C1", maturity=1.0, notional=1.0,
                       asset_indices=(0,), strike=100.0)
    ko = KnockOut(base, barrier=80.0, direction="down")
    paths = np.array([[[100.0], [75.0], [110.0]]])
    payoffs = ko.payoff(paths[:, -1, :], paths)
    np.testing.assert_allclose(payoffs, [0.0])


def test_inherits_trade_id():
    base = VanillaCall(trade_id="C1", maturity=1.0, notional=1.0,
                       asset_indices=(0,), strike=100.0)
    ko = KnockOut(base, barrier=120.0, direction="up")
    assert ko.trade_id == "C1"
    assert ko.maturity == 1.0
    assert ko.notional == 1.0
    assert ko.asset_indices == (0,)


def test_requires_full_path():
    base = VanillaCall(trade_id="C1", maturity=1.0, notional=1.0,
                       asset_indices=(0,), strike=100.0)
    ko = KnockOut(base, barrier=120.0, direction="up")
    assert ko.requires_full_path is True
