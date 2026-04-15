import numpy as np
import pytest
from pfev2.instruments.autocallable import Autocallable


def make_autocallable(**kwargs):
    defaults = dict(
        trade_id="AC1",
        maturity=1.0,
        notional=1.0,
        asset_indices=(0,),
        autocall_trigger=1.0,
        coupon_rate=0.05,
        put_strike=0.8,
        schedule=np.array([0.5, 1.0]),
    )
    defaults.update(kwargs)
    return Autocallable(**defaults)


def test_early_redemption():
    """S always above trigger → called at first observation, pays one coupon."""
    # path: [100, 110, 120, 130, 140], 5 steps over maturity=1.0
    # linspace(0,1,5) = [0, 0.25, 0.5, 0.75, 1.0]
    # schedule=[0.5] → searchsorted side='right' gives index 3 → clipped to idx=2
    # perf at idx=2: 120/100=1.2 >= trigger=1.0 → called at obs 1
    # payoff = coupon_rate * 1 = 0.05
    path = np.array([[[100.0], [110.0], [120.0], [130.0], [140.0]]])
    ac = Autocallable(
        trade_id="AC1", maturity=1.0, notional=1.0,
        asset_indices=(0,), autocall_trigger=1.0, coupon_rate=0.05,
        put_strike=0.8, schedule=np.array([0.5]),
    )
    payoffs = ac.payoff(spots=path[:, -1, :], path_history=path)
    np.testing.assert_allclose(payoffs[0], 0.05, atol=1e-10)


def test_no_call_put_loss():
    """S always below trigger, terminal perf < put_strike → negative payoff."""
    # path: [100, 70, 60], 3 steps over maturity=1.0
    # linspace(0,1,3) = [0, 0.5, 1.0]
    # schedule=[0.5] → idx=1, perf=0.7 < trigger=1.0 → not called
    # terminal: perf=60/100=0.6 < put_strike=0.8 → payoff=0.6-1.0=-0.4
    path = np.array([[[100.0], [70.0], [60.0]]])
    ac = Autocallable(
        trade_id="AC2", maturity=1.0, notional=1.0,
        asset_indices=(0,), autocall_trigger=1.0, coupon_rate=0.05,
        put_strike=0.8, schedule=np.array([0.5]),
    )
    payoffs = ac.payoff(spots=path[:, -1, :], path_history=path)
    np.testing.assert_allclose(payoffs[0], -0.4, atol=1e-10)


def test_no_call_above_put_strike():
    """Never called but terminal perf > put_strike → payoff = 0."""
    # path: [100, 95, 90], trigger=1.2, put_strike=0.8
    # obs perf=95/100=0.95 < 1.2 → not called
    # terminal perf=90/100=0.9 >= 0.8 → payoff=0.0
    path = np.array([[[100.0], [95.0], [90.0]]])
    ac = Autocallable(
        trade_id="AC3", maturity=1.0, notional=1.0,
        asset_indices=(0,), autocall_trigger=1.2, coupon_rate=0.05,
        put_strike=0.8, schedule=np.array([0.5]),
    )
    payoffs = ac.payoff(spots=path[:, -1, :], path_history=path)
    np.testing.assert_allclose(payoffs[0], 0.0, atol=1e-10)


def test_multi_asset_worst_of():
    """2 assets: worst performer determines trigger and loss."""
    # asset0: [100, 110, 120], asset1: [50, 40, 35]
    # path shape: (1, 3, 2)
    # linspace(0,1,3) = [0, 0.5, 1.0], schedule=[0.5] → idx=1
    # obs: asset0 perf=1.1, asset1 perf=40/50=0.8 → worst=0.8 < trigger=1.2 → not called
    # terminal: asset0 perf=1.2, asset1 perf=35/50=0.7 → worst=0.7 < put_strike=0.8
    # payoff = 0.7 - 1.0 = -0.3
    path = np.array([[[100.0, 50.0], [110.0, 40.0], [120.0, 35.0]]])
    ac = Autocallable(
        trade_id="AC4", maturity=1.0, notional=1.0,
        asset_indices=(0, 1), autocall_trigger=1.2, coupon_rate=0.05,
        put_strike=0.8, schedule=np.array([0.5]),
    )
    payoffs = ac.payoff(spots=path[:, -1, :], path_history=path)
    np.testing.assert_allclose(payoffs[0], -0.3, atol=1e-10)


def test_requires_full_path():
    ac = make_autocallable()
    assert ac.requires_full_path is True


def test_observation_dates_returned():
    schedule = np.array([0.25, 0.5, 0.75, 1.0])
    ac = make_autocallable(schedule=schedule)
    np.testing.assert_array_equal(ac.observation_dates(), schedule)
