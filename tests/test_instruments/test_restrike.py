import numpy as np
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
