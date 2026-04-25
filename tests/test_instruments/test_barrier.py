import numpy as np

from pfev2.instruments.barrier import DoubleNoTouch


def test_no_touch_pays_out():
    dnt = DoubleNoTouch(
        trade_id="DNT1", maturity=1.0, notional=1.0,
        asset_indices=(0,), lower=80.0, upper=120.0,
    )
    path = np.array([[[100.0], [105.0], [95.0], [110.0]]])
    payoffs = dnt.payoff(spots=path[:, -1, :], path_history=path)
    np.testing.assert_allclose(payoffs, [1.0])


def test_touch_lower_zeros():
    dnt = DoubleNoTouch(
        trade_id="DNT1", maturity=1.0, notional=1.0,
        asset_indices=(0,), lower=80.0, upper=120.0,
    )
    path = np.array([[[100.0], [75.0], [95.0], [110.0]]])
    payoffs = dnt.payoff(spots=path[:, -1, :], path_history=path)
    np.testing.assert_allclose(payoffs, [0.0])


def test_touch_upper_zeros():
    dnt = DoubleNoTouch(
        trade_id="DNT1", maturity=1.0, notional=1.0,
        asset_indices=(0,), lower=80.0, upper=120.0,
    )
    path = np.array([[[100.0], [125.0], [95.0]]])
    payoffs = dnt.payoff(spots=path[:, -1, :], path_history=path)
    np.testing.assert_allclose(payoffs, [0.0])


def test_requires_full_path():
    dnt = DoubleNoTouch(
        trade_id="DNT1", maturity=1.0, notional=1.0,
        asset_indices=(0,), lower=80.0, upper=120.0,
    )
    assert dnt.requires_full_path is True


def test_batch():
    dnt = DoubleNoTouch(
        trade_id="DNT1", maturity=1.0, notional=1.0,
        asset_indices=(0,), lower=80.0, upper=120.0,
    )
    paths = np.array([
        [[100.0], [110.0], [90.0]],
        [[100.0], [75.0], [90.0]],
        [[100.0], [125.0], [90.0]],
    ])
    payoffs = dnt.payoff(spots=paths[:, -1, :], path_history=paths)
    np.testing.assert_allclose(payoffs, [1.0, 0.0, 0.0])
