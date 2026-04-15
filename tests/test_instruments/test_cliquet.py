import numpy as np
import pytest
from pfev2.instruments.cliquet import Cliquet


def make_cliquet(schedule, local_cap=0.05, local_floor=0.0, global_floor=0.0, maturity=1.0):
    return Cliquet(
        trade_id="CLQ1",
        maturity=maturity,
        notional=1.0,
        asset_indices=(0,),
        local_cap=local_cap,
        local_floor=local_floor,
        global_floor=global_floor,
        schedule=np.asarray(schedule),
    )


def test_positive_returns_capped():
    """Each period +10% return, capped at 5% => 4 * 5% = 20%."""
    schedule = np.array([0.25, 0.5, 0.75, 1.0])
    clq = make_cliquet(schedule, local_cap=0.05, local_floor=-1.0, global_floor=0.0)
    # 5-step path: S0=100, then each step +10%
    s = 100.0 * (1.1 ** np.arange(5))  # [100, 110, 121, 133.1, 146.41]
    path = s.reshape(1, 5, 1)  # shape (1 path, 5 steps, 1 asset)
    payoffs = clq.payoff(spots=path[:, -1, :], path_history=path)
    np.testing.assert_allclose(payoffs[0], 4 * 0.05, rtol=1e-10)


def test_negative_returns_floored():
    """Each period negative return, floored to 0 => total = 0 => payoff = global_floor = 0."""
    schedule = np.array([0.25, 0.5, 0.75, 1.0])
    clq = make_cliquet(schedule, local_cap=0.10, local_floor=0.0, global_floor=0.0)
    # 5-step path: S0=100, each step -10%
    s = 100.0 * (0.9 ** np.arange(5))
    path = s.reshape(1, 5, 1)
    payoffs = clq.payoff(spots=path[:, -1, :], path_history=path)
    np.testing.assert_allclose(payoffs[0], 0.0, atol=1e-12)


def test_global_floor_kicks_in():
    """Both periods negative, sum below global_floor => global_floor returned."""
    schedule = np.array([0.5, 1.0])
    global_floor = -0.03
    clq = make_cliquet(schedule, local_cap=0.10, local_floor=-0.20, global_floor=global_floor)
    # 3-step path: S0=100, drop 15% each period
    path = np.array([[[100.0], [85.0], [72.25]]])
    payoffs = clq.payoff(spots=path[:, -1, :], path_history=path)
    # local returns: -0.15 each, sum = -0.30 < global_floor=-0.03
    np.testing.assert_allclose(payoffs[0], global_floor, atol=1e-12)


def test_requires_full_path():
    schedule = np.array([0.5, 1.0])
    clq = make_cliquet(schedule)
    assert clq.requires_full_path is True


def test_observation_dates_returned():
    schedule = np.array([0.25, 0.5, 0.75, 1.0])
    clq = make_cliquet(schedule)
    np.testing.assert_array_equal(clq.observation_dates(), schedule)
