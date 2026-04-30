import numpy as np

from pfev2.core.types import PayoffTimeGrid
from pfev2.instruments.restrike import RestrikeOption


def test_call_restrike():
    rs = RestrikeOption(
        trade_id="RS1", maturity=1.0, notional=1.0,
        asset_indices=(0,), reset_time=0.5, option_type="call",
    )
    paths = np.array([
        [[100.0], [90.0], [95.0], [80.0], [110.0]],
        [[100.0], [110.0], [105.0], [100.0], [95.0]],
    ])
    payoffs = rs.payoff(spots=paths[:, -1, :], path_history=paths)
    assert payoffs[0] > 0
    assert payoffs[1] == 0.0


def test_put_restrike():
    rs = RestrikeOption(
        trade_id="RS1", maturity=1.0, notional=1.0,
        asset_indices=(0,), reset_time=0.5, option_type="put",
    )
    paths = np.array([
        [[100.0], [110.0], [105.0], [100.0], [95.0]],
    ])
    payoffs = rs.payoff(spots=paths[:, -1, :], path_history=paths)
    assert payoffs[0] > 0


def test_requires_full_path():
    rs = RestrikeOption(
        trade_id="RS1", maturity=1.0, notional=1.0,
        asset_indices=(0,), reset_time=0.5, option_type="call",
    )
    assert rs.requires_full_path is True


def test_absolute_grid_uses_realized_reset_fixing():
    rs = RestrikeOption(
        trade_id="RS1", maturity=1.0, notional=1.0,
        asset_indices=(0,), reset_time=0.25, option_type="call",
    )
    paths = np.array([[[100.0], [110.0], [120.0], [140.0], [165.0]]])
    t_grid = PayoffTimeGrid(np.array([0.0, 0.25, 0.5, 0.75, 1.0]), valuation_time=0.75)

    payoffs = rs.payoff(spots=paths[:, -1, :], path_history=paths, t_grid=t_grid)

    np.testing.assert_allclose(payoffs, [55.0])
