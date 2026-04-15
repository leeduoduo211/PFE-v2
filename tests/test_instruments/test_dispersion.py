import numpy as np
import pytest
from pfev2.instruments.dispersion import Dispersion
from pfev2.core.exceptions import InstrumentError


class TestDispersionPayoff:
    """Payoff correctness tests."""

    def test_all_call_components_vs_call_basket(self):
        """All-call, 2 assets: hand-verified example.

        S=[120, 240], K=[100, 200], w=[0.5, 0.5], K_basket=150
        Components: 0.5*max(120-100,0) + 0.5*max(240-200,0) = 10 + 20 = 30
        Basket: max(0.5*120+0.5*240-150, 0) = max(180-150, 0) = 30
        Total: 30 - 30 = 0
        """
        d = Dispersion(
            trade_id="D1", maturity=1.0, notional=1.0,
            asset_indices=(0, 1),
            strikes=[100.0, 200.0],
            weights=[0.5, 0.5],
            basket_strike=150.0,
            component_types=["call", "call"],
            basket_type="call",
        )
        spots = np.array([[120.0, 240.0]])
        np.testing.assert_allclose(d.payoff(spots, None), [0.0], atol=1e-10)

    def test_dispersion_positive(self):
        """Components disperse, basket doesn't — positive payoff.

        S=[150, 50], K=[100, 100], w=[0.5, 0.5], K_basket=100
        Components: 0.5*max(150-100,0) + 0.5*max(50-100,0) = 25 + 0 = 25
        Basket: max(0.5*150+0.5*50-100, 0) = max(100-100, 0) = 0
        Total: 25 - 0 = 25
        """
        d = Dispersion(
            trade_id="D2", maturity=1.0, notional=1.0,
            asset_indices=(0, 1),
            strikes=[100.0, 100.0],
            weights=[0.5, 0.5],
            basket_strike=100.0,
            component_types=["call", "call"],
            basket_type="call",
        )
        spots = np.array([[150.0, 50.0]])
        np.testing.assert_allclose(d.payoff(spots, None), [25.0], atol=1e-10)

    def test_mixed_call_put_components(self):
        """First component call, second component put.

        S=[120, 80], K=[100, 100], w=[0.6, 0.4], K_basket=100, basket=call
        Components: 0.6*max(120-100,0) + 0.4*max(100-80,0) = 12 + 8 = 20
        Basket spot: 0.6*120 + 0.4*80 = 72 + 32 = 104
        Basket: max(104-100, 0) = 4
        Total: 20 - 4 = 16
        """
        d = Dispersion(
            trade_id="D3", maturity=1.0, notional=1.0,
            asset_indices=(0, 1),
            strikes=[100.0, 100.0],
            weights=[0.6, 0.4],
            basket_strike=100.0,
            component_types=["call", "put"],
            basket_type="call",
        )
        spots = np.array([[120.0, 80.0]])
        np.testing.assert_allclose(d.payoff(spots, None), [16.0], atol=1e-10)

    def test_basket_put_type(self):
        """Basket is a put option.

        S=[90, 110], K=[100, 100], w=[0.5, 0.5], K_basket=120, basket=put
        Components: 0.5*max(90-100,0) + 0.5*max(110-100,0) = 0 + 5 = 5
        Basket spot: 0.5*90 + 0.5*110 = 100
        Basket: max(120-100, 0) = 20
        Total: 5 - 20 = -15
        """
        d = Dispersion(
            trade_id="D4", maturity=1.0, notional=1.0,
            asset_indices=(0, 1),
            strikes=[100.0, 100.0],
            weights=[0.5, 0.5],
            basket_strike=120.0,
            component_types=["call", "call"],
            basket_type="put",
        )
        spots = np.array([[90.0, 110.0]])
        np.testing.assert_allclose(d.payoff(spots, None), [-15.0], atol=1e-10)

    def test_multiple_paths_vectorized(self):
        """Multiple paths processed in a single call.

        Path 1: S=[150, 50], same as dispersion_positive -> 25
        Path 2: S=[120, 240], same as all_call -> 0
        Path 3: S=[80, 80], all OTM calls, basket OTM too -> 0 - 0 = 0
        """
        d = Dispersion(
            trade_id="D5", maturity=1.0, notional=1.0,
            asset_indices=(0, 1),
            strikes=[100.0, 100.0],
            weights=[0.5, 0.5],
            basket_strike=100.0,
            component_types=["call", "call"],
            basket_type="call",
        )
        spots = np.array([
            [150.0, 50.0],   # 25
            [120.0, 240.0],  # 0.5*20 + 0.5*140 = 80; basket: 0.5*120+0.5*240-100=80 -> 0
            [80.0, 80.0],    # 0; basket: 80-100 -> 0 -> 0
        ])
        expected = [25.0, 0.0, 0.0]
        np.testing.assert_allclose(d.payoff(spots, None), expected, atol=1e-10)

    def test_requires_full_path_false(self):
        """Dispersion is European-style, no path required."""
        d = Dispersion(
            trade_id="D6", maturity=1.0, notional=1.0,
            asset_indices=(0, 1),
            strikes=[100.0, 100.0],
            weights=[0.5, 0.5],
            basket_strike=100.0,
            component_types=["call", "call"],
            basket_type="call",
        )
        assert d.requires_full_path is False


class TestDispersionValidation:
    """Input validation tests."""

    def test_weights_must_sum_to_one(self):
        with pytest.raises(InstrumentError, match="weights must sum to 1"):
            Dispersion(
                trade_id="V1", maturity=1.0, notional=1.0,
                asset_indices=(0, 1),
                strikes=[100.0, 100.0],
                weights=[0.3, 0.3],
                basket_strike=100.0,
                component_types=["call", "call"],
                basket_type="call",
            )

    def test_strikes_length_mismatch(self):
        with pytest.raises(InstrumentError, match="strikes length"):
            Dispersion(
                trade_id="V2", maturity=1.0, notional=1.0,
                asset_indices=(0, 1),
                strikes=[100.0],
                weights=[0.5, 0.5],
                basket_strike=100.0,
                component_types=["call", "call"],
                basket_type="call",
            )

    def test_negative_component_strike_rejected(self):
        with pytest.raises(InstrumentError, match="strikes must be positive"):
            Dispersion(
                trade_id="V3", maturity=1.0, notional=1.0,
                asset_indices=(0, 1),
                strikes=[-100.0, 100.0],
                weights=[0.5, 0.5],
                basket_strike=100.0,
                component_types=["call", "call"],
                basket_type="call",
            )

    def test_negative_basket_strike_rejected(self):
        with pytest.raises(InstrumentError, match="basket_strike must be positive"):
            Dispersion(
                trade_id="V4", maturity=1.0, notional=1.0,
                asset_indices=(0, 1),
                strikes=[100.0, 100.0],
                weights=[0.5, 0.5],
                basket_strike=-50.0,
                component_types=["call", "call"],
                basket_type="call",
            )

    def test_invalid_component_type_rejected(self):
        with pytest.raises(InstrumentError, match="component_types entries must be 'call' or 'put'"):
            Dispersion(
                trade_id="V5", maturity=1.0, notional=1.0,
                asset_indices=(0, 1),
                strikes=[100.0, 100.0],
                weights=[0.5, 0.5],
                basket_strike=100.0,
                component_types=["call", "straddle"],
                basket_type="call",
            )

    def test_invalid_basket_type_rejected(self):
        with pytest.raises(InstrumentError, match="basket_type must be 'call' or 'put'"):
            Dispersion(
                trade_id="V6", maturity=1.0, notional=1.0,
                asset_indices=(0, 1),
                strikes=[100.0, 100.0],
                weights=[0.5, 0.5],
                basket_strike=100.0,
                component_types=["call", "call"],
                basket_type="butterfly",
            )
