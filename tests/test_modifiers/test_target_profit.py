import numpy as np
from pfev2.instruments.accumulator import Accumulator
from pfev2.modifiers.target_profit import TargetProfit


class TestTargetProfit:
    def test_target_hit_with_partial_fill(self):
        schedule = np.array([0.25, 0.5, 0.75, 1.0])
        acc = Accumulator(trade_id="A1", maturity=1.0, notional=1.0,
                          asset_indices=(0,), strike=100.0, leverage=1.0,
                          side="buy", schedule=schedule)
        tp = TargetProfit(acc, target=15.0, partial_fill=True)
        path = np.array([[[100.0], [110.0], [120.0], [130.0], [140.0]]])
        payoffs = tp.payoff(spots=path[:, -1, :], path_history=path)
        np.testing.assert_allclose(payoffs, [15.0])

    def test_no_target_hit(self):
        schedule = np.array([0.5, 1.0])
        acc = Accumulator(trade_id="A1", maturity=1.0, notional=1.0,
                          asset_indices=(0,), strike=100.0, leverage=1.0,
                          side="buy", schedule=schedule)
        tp = TargetProfit(acc, target=1000.0)
        path = np.array([[[100.0], [105.0], [110.0]]])
        payoffs = tp.payoff(spots=path[:, -1, :], path_history=path)
        assert payoffs[0] > 0

    def test_partial_fill_false_allows_overshoot(self):
        schedule = np.array([0.5, 1.0])
        acc = Accumulator(trade_id="A1", maturity=1.0, notional=1.0,
                          asset_indices=(0,), strike=100.0, leverage=1.0,
                          side="buy", schedule=schedule)
        tp = TargetProfit(acc, target=5.0, partial_fill=False)
        path = np.array([[[100.0], [110.0], [120.0]]])
        payoffs = tp.payoff(spots=path[:, -1, :], path_history=path)
        assert payoffs[0] > 5.0  # overshoot allowed

    def test_inherits_properties(self):
        schedule = np.array([0.5, 1.0])
        acc = Accumulator(trade_id="A1", maturity=1.0, notional=1.0,
                          asset_indices=(0,), strike=100.0, leverage=1.0,
                          side="buy", schedule=schedule)
        tp = TargetProfit(acc, target=50.0)
        assert tp.trade_id == "A1"
        assert tp.maturity == 1.0
        assert tp.requires_full_path is True
