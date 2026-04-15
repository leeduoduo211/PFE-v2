import numpy as np
import pytest
from pfev2.instruments.asian import AsianOption
from pfev2.core.exceptions import InstrumentError


def _make_path(prices_1d):
    """Wrap a 1-D price sequence into path_history shape (1, n_steps, 1)."""
    return np.array([[[p] for p in prices_1d]])


# ---------------------------------------------------------------------------
# Fixed-strike (average_type="price")
# ---------------------------------------------------------------------------

def test_fixed_strike_call_itm():
    # average = (110+120+130)/3 = 120 > strike=100  → payoff = 20
    schedule = np.array([0.25, 0.5, 0.75])
    opt = AsianOption(
        trade_id="A1", maturity=1.0, notional=1.0,
        asset_indices=(0,), strike=100.0,
        option_type="call", average_type="price", schedule=schedule,
    )
    # 5-step path; t_grid = [0, 0.25, 0.5, 0.75, 1.0]
    path = _make_path([100.0, 110.0, 120.0, 130.0, 140.0])
    t_grid = np.array([0.0, 0.25, 0.5, 0.75, 1.0])
    payoffs = opt.payoff(spots=path[:, -1, :], path_history=path, t_grid=t_grid)
    np.testing.assert_allclose(payoffs, [20.0])


def test_fixed_strike_call_otm():
    # average = (50+50+50)/3 = 50 < strike=200  → payoff = 0
    schedule = np.array([0.25, 0.5, 0.75])
    opt = AsianOption(
        trade_id="A2", maturity=1.0, notional=1.0,
        asset_indices=(0,), strike=200.0,
        option_type="call", average_type="price", schedule=schedule,
    )
    path = _make_path([50.0, 50.0, 50.0, 50.0, 50.0])
    t_grid = np.array([0.0, 0.25, 0.5, 0.75, 1.0])
    payoffs = opt.payoff(spots=path[:, -1, :], path_history=path, t_grid=t_grid)
    np.testing.assert_allclose(payoffs, [0.0])


def test_fixed_strike_put():
    # average = (80+85+90)/3 = 85 < strike=100 → payoff = 15
    schedule = np.array([0.25, 0.5, 0.75])
    opt = AsianOption(
        trade_id="A3", maturity=1.0, notional=1.0,
        asset_indices=(0,), strike=100.0,
        option_type="put", average_type="price", schedule=schedule,
    )
    path = _make_path([100.0, 80.0, 85.0, 90.0, 95.0])
    t_grid = np.array([0.0, 0.25, 0.5, 0.75, 1.0])
    payoffs = opt.payoff(spots=path[:, -1, :], path_history=path, t_grid=t_grid)
    np.testing.assert_allclose(payoffs, [15.0])


# ---------------------------------------------------------------------------
# Floating-strike (average_type="strike")
# ---------------------------------------------------------------------------

def test_floating_strike_call():
    # average = (100+110+120)/3 ≈ 110; S(T)=140 → payoff = 30
    schedule = np.array([0.25, 0.5, 0.75])
    opt = AsianOption(
        trade_id="A4", maturity=1.0, notional=1.0,
        asset_indices=(0,), strike=0.0,   # strike unused for floating
        option_type="call", average_type="strike", schedule=schedule,
    )
    path = _make_path([100.0, 100.0, 110.0, 120.0, 140.0])
    t_grid = np.array([0.0, 0.25, 0.5, 0.75, 1.0])
    payoffs = opt.payoff(spots=path[:, -1, :], path_history=path, t_grid=t_grid)
    np.testing.assert_allclose(payoffs, [30.0])


def test_floating_strike_put():
    # average = (120+110+100)/3 ≈ 110; S(T)=80 → payoff = 30
    schedule = np.array([0.25, 0.5, 0.75])
    opt = AsianOption(
        trade_id="A5", maturity=1.0, notional=1.0,
        asset_indices=(0,), strike=0.0,
        option_type="put", average_type="strike", schedule=schedule,
    )
    path = _make_path([100.0, 120.0, 110.0, 100.0, 80.0])
    t_grid = np.array([0.0, 0.25, 0.5, 0.75, 1.0])
    payoffs = opt.payoff(spots=path[:, -1, :], path_history=path, t_grid=t_grid)
    np.testing.assert_allclose(payoffs, [30.0])


# ---------------------------------------------------------------------------
# Properties
# ---------------------------------------------------------------------------

def test_requires_full_path():
    opt = AsianOption(
        trade_id="A6", maturity=1.0, notional=1.0,
        asset_indices=(0,), strike=100.0,
        option_type="call", average_type="price",
        schedule=np.array([0.5, 1.0]),
    )
    assert opt.requires_full_path is True


def test_observation_dates_returned():
    schedule = np.array([0.25, 0.5, 0.75, 1.0])
    opt = AsianOption(
        trade_id="A7", maturity=1.0, notional=1.0,
        asset_indices=(0,), strike=100.0,
        option_type="call", average_type="price", schedule=schedule,
    )
    np.testing.assert_array_equal(opt.observation_dates(), schedule)


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def test_invalid_option_type():
    with pytest.raises(InstrumentError, match="option_type"):
        AsianOption(
            trade_id="A8", maturity=1.0, notional=1.0,
            asset_indices=(0,), strike=100.0,
            option_type="straddle", average_type="price",
            schedule=np.array([0.5]),
        )


def test_invalid_average_type():
    with pytest.raises(InstrumentError, match="average_type"):
        AsianOption(
            trade_id="A9", maturity=1.0, notional=1.0,
            asset_indices=(0,), strike=100.0,
            option_type="call", average_type="geometric",
            schedule=np.array([0.5]),
        )
