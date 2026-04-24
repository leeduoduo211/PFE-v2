import numpy as np

from pfev2.instruments.contingent import ContingentOption


def test_trigger_met_call():
    co = ContingentOption(
        trade_id="CO1", maturity=1.0, notional=1.0,
        asset_indices=(0, 1),
        trigger_asset_idx=0, trigger_barrier=110.0, trigger_direction="up",
        target_asset_idx=1, target_strike=50.0, target_type="call",
    )
    spots = np.array([[120.0, 60.0], [90.0, 60.0]])
    payoffs = co.payoff(spots, None)
    np.testing.assert_allclose(payoffs, [10.0, 0.0])


def test_trigger_not_met():
    co = ContingentOption(
        trade_id="CO1", maturity=1.0, notional=1.0,
        asset_indices=(0, 1),
        trigger_asset_idx=0, trigger_barrier=110.0, trigger_direction="up",
        target_asset_idx=1, target_strike=50.0, target_type="call",
    )
    spots = np.array([[100.0, 80.0]])
    np.testing.assert_allclose(co.payoff(spots, None), [0.0])


def test_down_trigger():
    co = ContingentOption(
        trade_id="CO1", maturity=1.0, notional=1.0,
        asset_indices=(0, 1),
        trigger_asset_idx=0, trigger_barrier=90.0, trigger_direction="down",
        target_asset_idx=1, target_strike=50.0, target_type="put",
    )
    spots = np.array([[80.0, 40.0]])
    np.testing.assert_allclose(co.payoff(spots, None), [10.0])
