import numpy as np
import pytest

from pfev2.core.exceptions import InstrumentError
from pfev2.instruments.tarf import TARF


def make_tarf(**kwargs):
    defaults = dict(
        trade_id="T1", maturity=1.0, notional=1.0,
        asset_indices=(0,), strike=100.0, target=15.0,
        leverage=2.0, side="buy",
        schedule=np.array([0.25, 0.5, 0.75, 1.0]),
    )
    defaults.update(kwargs)
    return TARF(**defaults)


def make_path(*prices):
    """Build path_history array of shape (1, len(prices), 1)."""
    return np.array([[[p] for p in prices]])


# ── payoff tests ────────────────────────────────────────────────────────────

def test_target_hit_partial_fill():
    """S always above strike; cumulative exceeds target → capped at target.

    schedule=[0.25,0.5,0.75,1.0], path=[100,110,120,130,140]
    obs at indices matching schedule times:
      obs1 (t≈0.25): S=110, units=1 → pnl=10, cumulative=10
      obs2 (t≈0.5):  S=120, units=1 → pnl=20, new_cum=30 ≥ 15 → cap at 15
    """
    tarf = make_tarf(strike=100.0, target=15.0, leverage=2.0, side="buy")
    path = make_path(100.0, 110.0, 120.0, 130.0, 140.0)
    payoffs = tarf.payoff(spots=path[:, -1, :], path_history=path)
    assert payoffs[0] == pytest.approx(15.0)


def test_no_target_hit():
    """Target very high → returns full cumulative without capping.

    schedule=[0.25,0.5,0.75,1.0], path=[100,105,110,115,120], target=1000
    obs prices: 105, 110, 115, 120 (all above 100)
    pnls: 5, 10, 15, 20 → cumulative=50, far below 1000
    """
    tarf = make_tarf(
        strike=100.0, target=1000.0, leverage=2.0, side="buy",
        schedule=np.array([0.25, 0.5, 0.75, 1.0]),
    )
    path = make_path(100.0, 105.0, 110.0, 115.0, 120.0)
    payoffs = tarf.payoff(spots=path[:, -1, :], path_history=path)
    assert payoffs[0] == pytest.approx(50.0)


def test_leverage_below_strike():
    """S below strike → leveraged negative P&L accumulated.

    schedule=[0.25,0.5], path has 5 steps (t_grid=[0,0.25,0.5,0.75,1.0]):
    obs1 (t=0.25, idx=1): S=90 < 100 → units=2, pnl=2*(90-100)=-20
    obs2 (t=0.5,  idx=2): S=110 > 100 → units=1, pnl=1*(110-100)=+10
    cumulative = -10
    """
    tarf = make_tarf(
        strike=100.0, target=1000.0, leverage=2.0, side="buy",
        schedule=np.array([0.25, 0.5]),
    )
    # 5-step path so t_grid_full=[0.0,0.25,0.5,0.75,1.0] maps schedule exactly
    path = make_path(100.0, 90.0, 110.0, 105.0, 100.0)
    payoffs = tarf.payoff(spots=path[:, -1, :], path_history=path)
    assert payoffs[0] == pytest.approx(-10.0)


def test_sell_side():
    """Sell direction with S declining.

    schedule=[0.25,0.5], path has 5 steps (t_grid=[0,0.25,0.5,0.75,1.0]):
    sign=-1
    obs1 (t=0.25, idx=1): S=90 ≤ 100 → units=1, pnl=1*(90-100)*(-1)=+10
    obs2 (t=0.5,  idx=2): S=80 ≤ 100 → units=1, pnl=1*(80-100)*(-1)=+20
    cumulative=+30
    """
    tarf = make_tarf(
        strike=100.0, target=1000.0, leverage=2.0, side="sell",
        schedule=np.array([0.25, 0.5]),
    )
    # 5-step path so t_grid_full=[0.0,0.25,0.5,0.75,1.0] maps schedule exactly
    path = make_path(100.0, 90.0, 80.0, 75.0, 70.0)
    payoffs = tarf.payoff(spots=path[:, -1, :], path_history=path)
    assert payoffs[0] == pytest.approx(30.0)


# ── property / metadata tests ────────────────────────────────────────────────

def test_requires_full_path():
    tarf = make_tarf()
    assert tarf.requires_full_path is True


def test_observation_dates_returned():
    schedule = np.array([0.25, 0.5, 0.75, 1.0])
    tarf = make_tarf(schedule=schedule)
    np.testing.assert_array_equal(tarf.observation_dates(), schedule)


# ── validation tests ─────────────────────────────────────────────────────────

def test_invalid_side_rejected():
    with pytest.raises(InstrumentError, match="side must be"):
        make_tarf(side="long")


def test_invalid_strike_rejected():
    with pytest.raises(InstrumentError, match="strike must be positive"):
        make_tarf(strike=-5.0)


def test_invalid_target_rejected():
    with pytest.raises(InstrumentError, match="target must be positive"):
        make_tarf(target=0.0)


def test_invalid_leverage_rejected():
    with pytest.raises(InstrumentError, match="leverage must be positive"):
        make_tarf(leverage=-1.0)
