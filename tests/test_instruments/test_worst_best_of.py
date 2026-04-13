import numpy as np
from pfev2.instruments.worst_best_of import WorstOfCall, WorstOfPut, BestOfCall, BestOfPut


class TestWorstOfPut:
    def test_two_assets(self):
        wp = WorstOfPut(
            trade_id="WP1", maturity=1.0, notional=1.0,
            asset_indices=(0, 1), strikes=[100.0, 50.0],
        )
        spots = np.array([[90.0, 40.0]])
        np.testing.assert_allclose(wp.payoff(spots, None), [0.2], atol=1e-10)

    def test_both_above_strike(self):
        wp = WorstOfPut(
            trade_id="WP1", maturity=1.0, notional=1.0,
            asset_indices=(0, 1), strikes=[100.0, 50.0],
        )
        spots = np.array([[110.0, 60.0]])
        np.testing.assert_allclose(wp.payoff(spots, None), [0.0])

    def test_five_assets(self):
        wp = WorstOfPut(
            trade_id="WP1", maturity=1.0, notional=1.0,
            asset_indices=(0, 1, 2, 3, 4),
            strikes=[100.0, 100.0, 100.0, 100.0, 100.0],
        )
        spots = np.array([[90.0, 90.0, 90.0, 90.0, 90.0]])
        np.testing.assert_allclose(wp.payoff(spots, None), [0.1], atol=1e-10)


class TestWorstOfCall:
    def test_basic(self):
        wc = WorstOfCall(
            trade_id="WC1", maturity=1.0, notional=1.0,
            asset_indices=(0, 1), strikes=[100.0, 50.0],
        )
        spots = np.array([[120.0, 60.0]])
        np.testing.assert_allclose(wc.payoff(spots, None), [0.2], atol=1e-10)

    def test_one_below(self):
        wc = WorstOfCall(
            trade_id="WC1", maturity=1.0, notional=1.0,
            asset_indices=(0, 1), strikes=[100.0, 50.0],
        )
        spots = np.array([[120.0, 40.0]])
        np.testing.assert_allclose(wc.payoff(spots, None), [0.0])


class TestBestOfCall:
    def test_basic(self):
        bc = BestOfCall(
            trade_id="BC1", maturity=1.0, notional=1.0,
            asset_indices=(0, 1), strikes=[100.0, 50.0],
        )
        spots = np.array([[80.0, 60.0]])
        np.testing.assert_allclose(bc.payoff(spots, None), [0.2], atol=1e-10)


class TestBestOfPut:
    def test_basic(self):
        bp = BestOfPut(
            trade_id="BP1", maturity=1.0, notional=1.0,
            asset_indices=(0, 1), strikes=[100.0, 50.0],
        )
        spots = np.array([[110.0, 40.0]])
        np.testing.assert_allclose(bp.payoff(spots, None), [0.2], atol=1e-10)

    def test_all_above_strike_zero(self):
        """When all assets above their strikes, BestOfPut pays zero."""
        bp = BestOfPut(
            trade_id="BP1", maturity=1.0, notional=1.0,
            asset_indices=(0, 1), strikes=[100.0, 50.0],
        )
        spots = np.array([[120.0, 60.0]])
        np.testing.assert_allclose(bp.payoff(spots, None), [0.0])

    def test_all_below_strike(self):
        """When all assets below strike, payoff is the best put payoff."""
        bp = BestOfPut(
            trade_id="BP1", maturity=1.0, notional=1.0,
            asset_indices=(0, 1), strikes=[100.0, 50.0],
        )
        # S1/K1=0.8, S2/K2=0.7 → put payoffs: 0.2, 0.3 → best = 0.3
        spots = np.array([[80.0, 35.0]])
        np.testing.assert_allclose(bp.payoff(spots, None), [0.3], atol=1e-10)
