import numpy as np
import pytest

from pfev2.core.exceptions import InstrumentError
from pfev2.instruments.single_barrier import SingleBarrier


def make_barrier(**kwargs):
    defaults = dict(
        trade_id="SB1", maturity=1.0, notional=1.0,
        asset_indices=(0,), strike=100.0, barrier=110.0,
        option_type="call", barrier_direction="up", barrier_type="in",
    )
    defaults.update(kwargs)
    return SingleBarrier(**defaults)


class TestSingleBarrierUpInCall:
    def test_barrier_met_payoff(self):
        """Up-and-in call: S(T) > barrier → vanilla payoff."""
        inst = make_barrier(strike=100.0, barrier=110.0,
                            option_type="call", barrier_direction="up", barrier_type="in")
        spots = np.array([[120.0]])  # 120 > 110, payoff = 120 - 100 = 20
        np.testing.assert_allclose(inst.payoff(spots), [20.0])

    def test_barrier_not_met_zero(self):
        """Up-and-in call: S(T) <= barrier → zero payoff."""
        inst = make_barrier(strike=100.0, barrier=110.0,
                            option_type="call", barrier_direction="up", barrier_type="in")
        spots = np.array([[105.0]])  # 105 < 110, barrier not breached → 0
        np.testing.assert_allclose(inst.payoff(spots), [0.0])

    def test_exactly_at_barrier_not_met(self):
        """Up-and-in: strict inequality, S(T) == barrier counts as not met."""
        inst = make_barrier(strike=100.0, barrier=110.0,
                            option_type="call", barrier_direction="up", barrier_type="in")
        spots = np.array([[110.0]])
        np.testing.assert_allclose(inst.payoff(spots), [0.0])


class TestSingleBarrierDownOutPut:
    def test_barrier_breached_zero(self):
        """Down-and-out put: S(T) < barrier → knocked out → zero."""
        inst = make_barrier(strike=100.0, barrier=90.0,
                            option_type="put", barrier_direction="down", barrier_type="out")
        spots = np.array([[80.0]])  # 80 < 90, knocked out → 0
        np.testing.assert_allclose(inst.payoff(spots), [0.0])

    def test_no_breach_payoff(self):
        """Down-and-out put: S(T) >= barrier → survives → vanilla payoff."""
        inst = make_barrier(strike=100.0, barrier=90.0,
                            option_type="put", barrier_direction="down", barrier_type="out")
        spots = np.array([[85.0], [95.0], [110.0]])
        # 85 < 90 → knocked out (0), 95 >= 90 → 5, 110 >= 90 → 0 (OTM)
        np.testing.assert_allclose(inst.payoff(spots), [0.0, 5.0, 0.0])


class TestSingleBarrierRequiresFullPath:
    def test_requires_full_path_false(self):
        inst = make_barrier()
        assert inst.requires_full_path is False


class TestSingleBarrierBatch:
    def test_batch_multiple_paths(self):
        """Batch of paths: up-and-in call with mixed outcomes."""
        inst = make_barrier(strike=100.0, barrier=110.0,
                            option_type="call", barrier_direction="up", barrier_type="in")
        spots = np.array([
            [120.0],   # breached, ITM → 20
            [115.0],   # breached, ITM → 15
            [108.0],   # not breached → 0
            [90.0],    # not breached, OTM → 0
            [125.0],   # breached, ITM → 25
        ])
        result = inst.payoff(spots)
        np.testing.assert_allclose(result, [20.0, 15.0, 0.0, 0.0, 25.0])


class TestSingleBarrierValidation:
    def test_invalid_option_type(self):
        with pytest.raises(InstrumentError, match="option_type"):
            make_barrier(option_type="forward")

    def test_invalid_barrier_direction(self):
        with pytest.raises(InstrumentError, match="barrier_direction"):
            make_barrier(barrier_direction="sideways")

    def test_invalid_barrier_type(self):
        with pytest.raises(InstrumentError, match="barrier_type"):
            make_barrier(barrier_type="maybe")

    def test_negative_strike_rejected(self):
        with pytest.raises(InstrumentError):
            make_barrier(strike=-50.0)

    def test_zero_barrier_rejected(self):
        with pytest.raises(InstrumentError):
            make_barrier(barrier=0.0)

    def test_negative_barrier_rejected(self):
        with pytest.raises(InstrumentError):
            make_barrier(barrier=-10.0)
