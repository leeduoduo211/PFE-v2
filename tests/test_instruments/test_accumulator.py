import numpy as np

from pfev2.core.types import PayoffTimeGrid
from pfev2.instruments.accumulator import Accumulator


def test_buy_accumulation_above_strike():
    schedule = np.array([0.25, 0.5, 0.75, 1.0])
    acc = Accumulator(
        trade_id="A1", maturity=1.0, notional=1.0,
        asset_indices=(0,), strike=100.0, leverage=2.0,
        side="buy", schedule=schedule,
    )
    path = np.array([[[100.0], [110.0], [115.0], [120.0], [130.0]]])
    payoffs = acc.payoff(spots=path[:, -1, :], path_history=path)
    assert payoffs[0] > 0


def test_buy_accumulation_below_strike():
    schedule = np.array([0.25, 0.5, 0.75, 1.0])
    acc = Accumulator(
        trade_id="A1", maturity=1.0, notional=1.0,
        asset_indices=(0,), strike=100.0, leverage=2.0,
        side="buy", schedule=schedule,
    )
    path = np.array([[[100.0], [90.0], [85.0], [80.0], [75.0]]])
    payoffs = acc.payoff(spots=path[:, -1, :], path_history=path)
    assert payoffs[0] < 0


def test_sell_direction():
    schedule = np.array([0.5, 1.0])
    acc = Accumulator(
        trade_id="A1", maturity=1.0, notional=1.0,
        asset_indices=(0,), strike=100.0, leverage=2.0,
        side="sell", schedule=schedule,
    )
    path = np.array([[[100.0], [110.0], [120.0]]])
    payoffs = acc.payoff(spots=path[:, -1, :], path_history=path)
    assert payoffs[0] < 0


def test_requires_full_path():
    schedule = np.array([0.5, 1.0])
    acc = Accumulator(
        trade_id="A1", maturity=1.0, notional=1.0,
        asset_indices=(0,), strike=100.0, leverage=2.0,
        side="buy", schedule=schedule,
    )
    assert acc.requires_full_path is True


def test_observation_dates_returned():
    schedule = np.array([0.25, 0.5, 0.75, 1.0])
    acc = Accumulator(
        trade_id="A1", maturity=1.0, notional=1.0,
        asset_indices=(0,), strike=100.0, leverage=2.0,
        side="buy", schedule=schedule,
    )
    np.testing.assert_array_equal(acc.observation_dates(), schedule)


def test_absolute_grid_prices_only_unsettled_fixings():
    schedule = np.array([0.25, 0.5, 0.75, 1.0])
    acc = Accumulator(
        trade_id="A1", maturity=1.0, notional=1.0,
        asset_indices=(0,), strike=100.0, leverage=2.0,
        side="buy", schedule=schedule,
    )
    path = np.array([[[100.0], [200.0], [200.0], [120.0], [130.0]]])
    t_grid = PayoffTimeGrid(np.array([0.0, 0.25, 0.5, 0.75, 1.0]), valuation_time=0.5)

    payoffs = acc.payoff(spots=path[:, -1, :], path_history=path, t_grid=t_grid)

    np.testing.assert_allclose(payoffs, [50.0])
