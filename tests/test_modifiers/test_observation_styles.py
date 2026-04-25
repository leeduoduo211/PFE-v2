import numpy as np
import pytest

from pfev2.core.exceptions import ModifierError
from pfev2.instruments.vanilla import VanillaOption
from pfev2.modifiers.knock_in import KnockIn
from pfev2.modifiers.knock_out import KnockOut


class TestKnockOutObservationStyles:
    def _make_base(self):
        return VanillaOption(trade_id="C1", maturity=1.0, notional=1.0,
                             asset_indices=(0,), strike=100.0, option_type="call")

    def test_continuous_default_unchanged(self):
        base = self._make_base()
        ko = KnockOut(base, barrier=120.0, direction="up")
        assert ko.observation_style == "continuous"
        paths = np.array([[[100.0], [125.0], [110.0]]])
        payoffs = ko.payoff(paths[:, -1, :], paths)
        np.testing.assert_allclose(payoffs, [0.0])

    def test_discrete_no_breach_on_non_observation_date(self):
        base = self._make_base()
        t_grid = np.array([0.0, 0.25, 0.5, 0.75, 1.0])
        ko = KnockOut(base, barrier=120.0, direction="up",
                      observation_style="discrete",
                      observation_dates=[0.5, 1.0])
        paths = np.array([[[100.0], [125.0], [110.0], [105.0], [115.0]]])
        payoffs = ko.payoff(paths[:, -1, :], paths, t_grid=t_grid)
        np.testing.assert_allclose(payoffs, [15.0])

    def test_discrete_breach_on_observation_date(self):
        base = self._make_base()
        t_grid = np.array([0.0, 0.25, 0.5, 0.75, 1.0])
        ko = KnockOut(base, barrier=120.0, direction="up",
                      observation_style="discrete",
                      observation_dates=[0.5, 1.0])
        paths = np.array([[[100.0], [110.0], [125.0], [105.0], [115.0]]])
        payoffs = ko.payoff(paths[:, -1, :], paths, t_grid=t_grid)
        np.testing.assert_allclose(payoffs, [0.0])

    def test_window_breach_inside_window(self):
        base = self._make_base()
        t_grid = np.array([0.0, 0.25, 0.5, 0.75, 1.0])
        ko = KnockOut(base, barrier=120.0, direction="up",
                      observation_style="window",
                      window_start=0.25, window_end=0.75)
        paths = np.array([[[100.0], [110.0], [125.0], [105.0], [115.0]]])
        payoffs = ko.payoff(paths[:, -1, :], paths, t_grid=t_grid)
        np.testing.assert_allclose(payoffs, [0.0])

    def test_window_breach_outside_window(self):
        base = self._make_base()
        t_grid = np.array([0.0, 0.25, 0.5, 0.75, 1.0])
        ko = KnockOut(base, barrier=120.0, direction="up",
                      observation_style="window",
                      window_start=0.5, window_end=0.75)
        paths = np.array([[[100.0], [125.0], [110.0], [105.0], [115.0]]])
        payoffs = ko.payoff(paths[:, -1, :], paths, t_grid=t_grid)
        np.testing.assert_allclose(payoffs, [15.0])

    def test_invalid_observation_style_rejected(self):
        base = self._make_base()
        with pytest.raises(ModifierError):
            KnockOut(base, barrier=120.0, direction="up",
                     observation_style="invalid")

    def test_discrete_requires_observation_dates(self):
        base = self._make_base()
        with pytest.raises(ModifierError):
            KnockOut(base, barrier=120.0, direction="up",
                     observation_style="discrete")

    def test_window_requires_start_and_end(self):
        base = self._make_base()
        with pytest.raises(ModifierError):
            KnockOut(base, barrier=120.0, direction="up",
                     observation_style="window", window_start=0.25)


class TestKnockOutRebate:
    def _make_base(self):
        return VanillaOption(trade_id="C1", maturity=1.0, notional=1.0,
                             asset_indices=(0,), strike=100.0, option_type="call")

    def test_rebate_paid_on_knockout(self):
        base = self._make_base()
        ko = KnockOut(base, barrier=120.0, direction="up", rebate=5.0)
        paths = np.array([[[100.0], [125.0], [130.0]]])
        payoffs = ko.payoff(paths[:, -1, :], paths)
        np.testing.assert_allclose(payoffs, [5.0])

    def test_no_rebate_when_not_knocked_out(self):
        base = self._make_base()
        ko = KnockOut(base, barrier=120.0, direction="up", rebate=5.0)
        paths = np.array([[[100.0], [110.0], [115.0]]])
        payoffs = ko.payoff(paths[:, -1, :], paths)
        np.testing.assert_allclose(payoffs, [15.0])

    def test_default_rebate_is_zero(self):
        base = self._make_base()
        ko = KnockOut(base, barrier=120.0, direction="up")
        assert ko.rebate == 0.0


class TestKnockInObservationStyles:
    def _make_base(self):
        return VanillaOption(trade_id="C1", maturity=1.0, notional=1.0,
                             asset_indices=(0,), strike=100.0, option_type="call")

    def test_discrete_activation_on_observation_date(self):
        base = self._make_base()
        t_grid = np.array([0.0, 0.25, 0.5, 0.75, 1.0])
        ki = KnockIn(base, barrier=80.0, direction="down",
                     observation_style="discrete",
                     observation_dates=[0.5, 1.0])
        paths = np.array([[[100.0], [90.0], [75.0], [95.0], [110.0]]])
        payoffs = ki.payoff(paths[:, -1, :], paths, t_grid=t_grid)
        np.testing.assert_allclose(payoffs, [10.0])

    def test_discrete_no_activation_between_dates(self):
        base = self._make_base()
        t_grid = np.array([0.0, 0.25, 0.5, 0.75, 1.0])
        ki = KnockIn(base, barrier=80.0, direction="down",
                     observation_style="discrete",
                     observation_dates=[0.5, 1.0])
        paths = np.array([[[100.0], [75.0], [90.0], [95.0], [110.0]]])
        payoffs = ki.payoff(paths[:, -1, :], paths, t_grid=t_grid)
        np.testing.assert_allclose(payoffs, [0.0])
