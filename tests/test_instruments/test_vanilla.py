import numpy as np
import pytest
from pfev2.instruments.vanilla import VanillaCall, VanillaPut
from pfev2.core.exceptions import InstrumentError


class TestVanillaCall:
    def test_itm(self):
        c = VanillaCall(trade_id="C1", maturity=1.0, notional=1.0,
                        asset_indices=(0,), strike=100.0)
        spots = np.array([[120.0], [80.0], [100.0]])
        payoffs = c.payoff(spots, None)
        np.testing.assert_allclose(payoffs, [20.0, 0.0, 0.0])

    def test_all_otm(self):
        c = VanillaCall(trade_id="C1", maturity=1.0, notional=1.0,
                        asset_indices=(0,), strike=200.0)
        spots = np.array([[100.0], [150.0]])
        payoffs = c.payoff(spots, None)
        np.testing.assert_allclose(payoffs, [0.0, 0.0])

    def test_requires_full_path_false(self):
        c = VanillaCall(trade_id="C1", maturity=1.0, notional=1.0,
                        asset_indices=(0,), strike=100.0)
        assert c.requires_full_path is False

    def test_negative_strike_rejected(self):
        with pytest.raises(InstrumentError):
            VanillaCall(trade_id="C1", maturity=1.0, notional=1.0,
                        asset_indices=(0,), strike=-10.0)

    def test_is_alive(self):
        c = VanillaCall(trade_id="C1", maturity=1.0, notional=1.0,
                        asset_indices=(0,), strike=100.0)
        assert c.is_alive(0.5) is True
        assert c.is_alive(1.0) is False


class TestVanillaPut:
    def test_itm(self):
        p = VanillaPut(trade_id="P1", maturity=1.0, notional=1.0,
                       asset_indices=(0,), strike=100.0)
        spots = np.array([[80.0], [120.0], [100.0]])
        payoffs = p.payoff(spots, None)
        np.testing.assert_allclose(payoffs, [20.0, 0.0, 0.0])
