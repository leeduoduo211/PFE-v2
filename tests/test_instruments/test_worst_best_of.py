import numpy as np
import pytest
from pfev2.instruments.worst_best_of import WorstOfOption, BestOfOption
from pfev2.core.exceptions import InstrumentError


class TestWorstOfOptionCall:
    def test_basic(self):
        """Two assets, worst performer above strike -> positive payoff."""
        wc = WorstOfOption(
            trade_id="WC1", maturity=1.0, notional=1.0,
            asset_indices=(0, 1), strikes=[100.0, 50.0], option_type="call",
        )
        # perfs: 120/100=1.2, 60/50=1.2 -> worst=1.2 -> payoff=0.2
        spots = np.array([[120.0, 60.0]])
        np.testing.assert_allclose(wc.payoff(spots, None), [0.2], atol=1e-10)

    def test_all_above(self):
        """All assets above strike, worst performer determines payoff."""
        wc = WorstOfOption(
            trade_id="WC2", maturity=1.0, notional=1.0,
            asset_indices=(0, 1), strikes=[100.0, 50.0], option_type="call",
        )
        # perfs: 130/100=1.3, 55/50=1.1 -> worst=1.1 -> payoff=0.1
        spots = np.array([[130.0, 55.0]])
        np.testing.assert_allclose(wc.payoff(spots, None), [0.1], atol=1e-10)

    def test_one_below_strike(self):
        """One asset below strike -> worst perf < 1 -> payoff is zero."""
        wc = WorstOfOption(
            trade_id="WC3", maturity=1.0, notional=1.0,
            asset_indices=(0, 1), strikes=[100.0, 50.0], option_type="call",
        )
        spots = np.array([[120.0, 40.0]])
        np.testing.assert_allclose(wc.payoff(spots, None), [0.0])


class TestWorstOfOptionPut:
    def test_two_assets(self):
        """Two assets, worst performer below strike -> positive put payoff."""
        wp = WorstOfOption(
            trade_id="WP1", maturity=1.0, notional=1.0,
            asset_indices=(0, 1), strikes=[100.0, 50.0], option_type="put",
        )
        # perfs: 90/100=0.9, 40/50=0.8 -> worst=0.8 -> payoff=1-0.8=0.2
        spots = np.array([[90.0, 40.0]])
        np.testing.assert_allclose(wp.payoff(spots, None), [0.2], atol=1e-10)

    def test_both_above_strike(self):
        """Both assets above strike -> worst perf > 1 -> put payoff is zero."""
        wp = WorstOfOption(
            trade_id="WP2", maturity=1.0, notional=1.0,
            asset_indices=(0, 1), strikes=[100.0, 50.0], option_type="put",
        )
        spots = np.array([[110.0, 60.0]])
        np.testing.assert_allclose(wp.payoff(spots, None), [0.0])

    def test_five_assets(self):
        """Five assets, all at 90% of strike -> put payoff = 0.1."""
        wp = WorstOfOption(
            trade_id="WP3", maturity=1.0, notional=1.0,
            asset_indices=(0, 1, 2, 3, 4),
            strikes=[100.0, 100.0, 100.0, 100.0, 100.0], option_type="put",
        )
        spots = np.array([[90.0, 90.0, 90.0, 90.0, 90.0]])
        np.testing.assert_allclose(wp.payoff(spots, None), [0.1], atol=1e-10)


class TestBestOfOptionCall:
    def test_basic(self):
        """Best performer drives call payoff."""
        bc = BestOfOption(
            trade_id="BC1", maturity=1.0, notional=1.0,
            asset_indices=(0, 1), strikes=[100.0, 50.0], option_type="call",
        )
        # perfs: 80/100=0.8, 60/50=1.2 -> best=1.2 -> payoff=0.2
        spots = np.array([[80.0, 60.0]])
        np.testing.assert_allclose(bc.payoff(spots, None), [0.2], atol=1e-10)

    def test_all_below_strike(self):
        """All assets below strike -> best perf < 1 -> call payoff is zero."""
        bc = BestOfOption(
            trade_id="BC2", maturity=1.0, notional=1.0,
            asset_indices=(0, 1), strikes=[100.0, 50.0], option_type="call",
        )
        spots = np.array([[80.0, 40.0]])
        np.testing.assert_allclose(bc.payoff(spots, None), [0.0])


class TestBestOfOptionPut:
    def test_basic_asymmetric(self):
        """Verify asymmetric put: individual puts evaluated FIRST, then max.

        This is NOT max(1 - max_i(perf), 0).
        It IS max_i(max(1 - S_i/K_i, 0)).
        """
        bp = BestOfOption(
            trade_id="BP1", maturity=1.0, notional=1.0,
            asset_indices=(0, 1), strikes=[100.0, 50.0], option_type="put",
        )
        # perfs: 110/100=1.1, 40/50=0.8
        # individual puts: max(1-1.1, 0)=0, max(1-0.8, 0)=0.2 -> max=0.2
        spots = np.array([[110.0, 40.0]])
        np.testing.assert_allclose(bp.payoff(spots, None), [0.2], atol=1e-10)

    def test_all_above_zero(self):
        """When all assets above their strikes, all individual puts are zero."""
        bp = BestOfOption(
            trade_id="BP2", maturity=1.0, notional=1.0,
            asset_indices=(0, 1), strikes=[100.0, 50.0], option_type="put",
        )
        spots = np.array([[120.0, 60.0]])
        np.testing.assert_allclose(bp.payoff(spots, None), [0.0])

    def test_all_below_strike(self):
        """When all assets below strike, payoff is the best individual put."""
        bp = BestOfOption(
            trade_id="BP3", maturity=1.0, notional=1.0,
            asset_indices=(0, 1), strikes=[100.0, 50.0], option_type="put",
        )
        # S1/K1=0.8, S2/K2=0.7 -> puts: 0.2, 0.3 -> best = 0.3
        spots = np.array([[80.0, 35.0]])
        np.testing.assert_allclose(bp.payoff(spots, None), [0.3], atol=1e-10)

    def test_asymmetry_vs_symmetric(self):
        """Demonstrate that BestOfPut is NOT max(1 - max(perf), 0).

        If best perf > 1 but another asset is below strike,
        symmetric formula would give 0, but asymmetric gives positive payoff.
        """
        bp = BestOfOption(
            trade_id="BP4", maturity=1.0, notional=1.0,
            asset_indices=(0, 1), strikes=[100.0, 100.0], option_type="put",
        )
        # perfs: 1.2, 0.7
        # symmetric: max(1 - max(1.2, 0.7), 0) = max(1 - 1.2, 0) = 0
        # asymmetric: max(max(1-1.2, 0), max(1-0.7, 0)) = max(0, 0.3) = 0.3
        spots = np.array([[120.0, 70.0]])
        symmetric_result = max(1.0 - max(1.2, 0.7), 0.0)
        assert symmetric_result == 0.0, "symmetric formula would give zero"
        np.testing.assert_allclose(bp.payoff(spots, None), [0.3], atol=1e-10)


class TestValidation:
    def test_invalid_option_type(self):
        with pytest.raises(InstrumentError, match="option_type must be 'call' or 'put'"):
            WorstOfOption(
                trade_id="V1", maturity=1.0, notional=1.0,
                asset_indices=(0, 1), strikes=[100.0, 50.0], option_type="straddle",
            )

    def test_invalid_option_type_best_of(self):
        with pytest.raises(InstrumentError, match="option_type must be 'call' or 'put'"):
            BestOfOption(
                trade_id="V2", maturity=1.0, notional=1.0,
                asset_indices=(0, 1), strikes=[100.0, 50.0], option_type="straddle",
            )

    def test_strikes_length_mismatch_worst_of(self):
        with pytest.raises(InstrumentError, match="strikes length must match asset_indices"):
            WorstOfOption(
                trade_id="V3", maturity=1.0, notional=1.0,
                asset_indices=(0, 1), strikes=[100.0], option_type="call",
            )

    def test_strikes_length_mismatch_best_of(self):
        with pytest.raises(InstrumentError, match="strikes length must match asset_indices"):
            BestOfOption(
                trade_id="V4", maturity=1.0, notional=1.0,
                asset_indices=(0, 1), strikes=[100.0, 50.0, 30.0], option_type="put",
            )

    def test_requires_full_path_false(self):
        wo = WorstOfOption(
            trade_id="V5", maturity=1.0, notional=1.0,
            asset_indices=(0, 1), strikes=[100.0, 50.0], option_type="call",
        )
        bo = BestOfOption(
            trade_id="V6", maturity=1.0, notional=1.0,
            asset_indices=(0, 1), strikes=[100.0, 50.0], option_type="put",
        )
        assert wo.requires_full_path is False
        assert bo.requires_full_path is False
