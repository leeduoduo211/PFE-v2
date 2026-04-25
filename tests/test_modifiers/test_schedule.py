import numpy as np

from pfev2.instruments.vanilla import VanillaOption
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
