import numpy as np
import pytest

from pfev2.core.exceptions import InstrumentError
from pfev2.instruments.vanilla import VanillaOption


class TestVanillaOption:
    """Tests for unified VanillaOption (call and put via option_type)."""

    def test_call_itm(self):
        opt = VanillaOption(trade_id="C1", maturity=1.0, notional=1.0,
                            asset_indices=(0,), strike=100.0, option_type="call")
        spots = np.array([[120.0], [80.0], [100.0]])
        payoffs = opt.payoff(spots)
        np.testing.assert_allclose(payoffs, [20.0, 0.0, 0.0])

    def test_call_otm(self):
        opt = VanillaOption(trade_id="C2", maturity=1.0, notional=1.0,
                            asset_indices=(0,), strike=200.0, option_type="call")
        spots = np.array([[100.0], [150.0]])
        payoffs = opt.payoff(spots)
        np.testing.assert_allclose(payoffs, [0.0, 0.0])

    def test_put_itm(self):
        opt = VanillaOption(trade_id="P1", maturity=1.0, notional=1.0,
                            asset_indices=(0,), strike=100.0, option_type="put")
        spots = np.array([[80.0], [120.0], [100.0]])
        payoffs = opt.payoff(spots)
        np.testing.assert_allclose(payoffs, [20.0, 0.0, 0.0])

    def test_put_otm(self):
        opt = VanillaOption(trade_id="P2", maturity=1.0, notional=1.0,
                            asset_indices=(0,), strike=50.0, option_type="put")
        spots = np.array([[100.0], [150.0]])
        payoffs = opt.payoff(spots)
        np.testing.assert_allclose(payoffs, [0.0, 0.0])

    def test_requires_full_path_false(self):
        opt = VanillaOption(trade_id="V1", maturity=1.0, notional=1.0,
                            asset_indices=(0,), strike=100.0, option_type="call")
        assert opt.requires_full_path is False

    def test_negative_strike_rejected(self):
        with pytest.raises(InstrumentError):
            VanillaOption(trade_id="V1", maturity=1.0, notional=1.0,
                          asset_indices=(0,), strike=-10.0, option_type="call")

    def test_zero_strike_rejected(self):
        with pytest.raises(InstrumentError):
            VanillaOption(trade_id="V1", maturity=1.0, notional=1.0,
                          asset_indices=(0,), strike=0.0, option_type="put")

    def test_invalid_option_type_rejected(self):
        with pytest.raises(InstrumentError):
            VanillaOption(trade_id="V1", maturity=1.0, notional=1.0,
                          asset_indices=(0,), strike=100.0, option_type="straddle")

    def test_is_alive_boundary(self):
        opt = VanillaOption(trade_id="V1", maturity=1.0, notional=1.0,
                            asset_indices=(0,), strike=100.0, option_type="call")
        assert opt.is_alive(0.5) is True
        assert opt.is_alive(1.0) is False
        assert opt.is_alive(1.5) is False

    def test_vectorized_multi_path(self):
        """Test payoff computation across many paths for both call and put."""
        rng = np.random.default_rng(42)
        spots = rng.uniform(80.0, 120.0, size=(10_000, 1))

        call = VanillaOption(trade_id="VC", maturity=1.0, notional=1.0,
                             asset_indices=(0,), strike=100.0, option_type="call")
        put = VanillaOption(trade_id="VP", maturity=1.0, notional=1.0,
                            asset_indices=(0,), strike=100.0, option_type="put")

        call_payoffs = call.payoff(spots)
        put_payoffs = put.payoff(spots)

        # All payoffs non-negative
        assert np.all(call_payoffs >= 0.0)
        assert np.all(put_payoffs >= 0.0)

        # Put-call parity: call - put = S - K
        np.testing.assert_allclose(
            call_payoffs - put_payoffs,
            spots[:, 0] - 100.0,
            atol=1e-10,
        )
