import numpy as np

from pfev2.instruments.vanilla import VanillaOption
from pfev2.modifiers.knock_out import KnockOut
from pfev2.modifiers.schedule import ObservationSchedule


def test_restricts_to_schedule_dates():
    base = VanillaOption(trade_id="C1", maturity=1.0, notional=1.0,
                         asset_indices=(0,), strike=100.0, option_type="call")
    obs = ObservationSchedule(base, dates=np.array([0.5, 1.0]))
    spots = np.array([[120.0]])
    payoffs = obs.payoff(spots, None)
    np.testing.assert_allclose(payoffs, [20.0])


def test_requires_full_path():
    base = VanillaOption(trade_id="C1", maturity=1.0, notional=1.0,
                         asset_indices=(0,), strike=100.0, option_type="call")
    obs = ObservationSchedule(base, dates=np.array([0.5, 1.0]))
    assert obs.requires_full_path is True


def test_observation_dates_returned():
    base = VanillaOption(trade_id="C1", maturity=1.0, notional=1.0,
                         asset_indices=(0,), strike=100.0, option_type="call")
    dates = np.array([0.25, 0.5, 0.75, 1.0])
    obs = ObservationSchedule(base, dates=dates)
    np.testing.assert_array_equal(obs.observation_dates(), dates)


def test_filters_wrapped_path_modifier_to_schedule():
    base = VanillaOption(trade_id="C1", maturity=1.0, notional=1.0,
                         asset_indices=(0,), strike=100.0, option_type="call")
    knock_out = KnockOut(base, barrier=110.0, direction="up")
    obs = ObservationSchedule(knock_out, dates=np.array([1.0]))

    path = np.array([[[100.0], [130.0], [105.0]]])
    t_grid = np.array([0.0, 0.5, 1.0])

    np.testing.assert_allclose(knock_out.payoff(path[:, -1, :], path, t_grid), [0.0])
    np.testing.assert_allclose(obs.payoff(path[:, -1, :], path, t_grid), [5.0])


def test_does_not_preserve_unscheduled_endpoints():
    base = VanillaOption(trade_id="C1", maturity=1.0, notional=1.0,
                         asset_indices=(0,), strike=100.0, option_type="call")
    knock_out = KnockOut(base, barrier=110.0, direction="up")
    obs = ObservationSchedule(knock_out, dates=np.array([0.5]))

    path = np.array([[[130.0], [105.0], [130.0]]])
    t_grid = np.array([0.0, 0.5, 1.0])

    np.testing.assert_allclose(knock_out.payoff(path[:, -1, :], path, t_grid), [0.0])
    np.testing.assert_allclose(obs.payoff(path[:, -1, :], path, t_grid), [30.0])
