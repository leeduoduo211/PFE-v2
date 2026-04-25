import numpy as np
import pytest

from pfev2.core.exceptions import InstrumentError
from pfev2.instruments.range_accrual import RangeAccrual


def make_instrument(**kwargs):
    defaults = dict(
        trade_id="RA1",
        maturity=1.0,
        notional=1.0,
        asset_indices=(0,),
        lower=90.0,
        upper=110.0,
        coupon_rate=0.05,
        schedule=[0.25, 0.50, 0.75, 1.00],
    )
    defaults.update(kwargs)
    return RangeAccrual(**defaults)


def build_path(prices, maturity=1.0):
    """Build path_history of shape (1, n_steps, 1) and matching t_grid."""
    n_steps = len(prices)
    arr = np.array(prices, dtype=float).reshape(1, n_steps, 1)
    t_grid = np.linspace(0.0, maturity, n_steps)
    return arr, t_grid


def test_all_in_range():
    ra = make_instrument()
    # 4 steps at t=0.25,0.5,0.75,1.0 — all within [90, 110]
    prices = [100.0, 100.0, 100.0, 100.0]
    path, t_grid = build_path(prices)
    payoffs = ra.payoff(spots=path[:, -1, :], path_history=path, t_grid=t_grid)
    np.testing.assert_allclose(payoffs, [0.05])  # 4/4 * 0.05


def test_none_in_range():
    ra = make_instrument()
    prices = [120.0, 120.0, 120.0, 120.0]
    path, t_grid = build_path(prices)
    payoffs = ra.payoff(spots=path[:, -1, :], path_history=path, t_grid=t_grid)
    np.testing.assert_allclose(payoffs, [0.0])  # 0/4 * 0.05


def test_partial_in_range():
    ra = make_instrument()
    # Obs at indices corresponding to schedule [0.25, 0.5, 0.75, 1.0]
    # With linspace(0,1,5): t=[0, 0.25, 0.5, 0.75, 1.0]
    # searchsorted gives indices [1, 2, 3, 4] → prices [100, 100, 120, 120]
    prices = [95.0, 100.0, 100.0, 120.0, 120.0]
    path, t_grid = build_path(prices)
    payoffs = ra.payoff(spots=path[:, -1, :], path_history=path, t_grid=t_grid)
    # 2 in range (100, 100), 2 out (120, 120) → 2/4 * 0.05 = 0.025
    np.testing.assert_allclose(payoffs, [0.025])


def test_invalid_range_equal():
    with pytest.raises(InstrumentError, match="lower"):
        make_instrument(lower=100.0, upper=100.0)


def test_invalid_range_lower_gt_upper():
    with pytest.raises(InstrumentError, match="lower"):
        make_instrument(lower=110.0, upper=90.0)


def test_requires_full_path():
    ra = make_instrument()
    assert ra.requires_full_path is True
