import numpy as np
from pfev2.instruments.digital import Digital, DualDigital, TripleDigital


class TestDigital:
    def test_call(self):
        d = Digital(trade_id="D1", maturity=1.0, notional=1.0,
                    asset_indices=(0,), strike=100.0, option_type="call")
        spots = np.array([[120.0], [80.0], [100.0]])
        np.testing.assert_allclose(d.payoff(spots, None), [1.0, 0.0, 0.0])

    def test_put(self):
        d = Digital(trade_id="D1", maturity=1.0, notional=1.0,
                    asset_indices=(0,), strike=100.0, option_type="put")
        spots = np.array([[120.0], [80.0], [100.0]])
        np.testing.assert_allclose(d.payoff(spots, None), [0.0, 1.0, 0.0])


class TestDualDigital:
    def test_both_conditions_met(self):
        dd = DualDigital(
            trade_id="DD1", maturity=1.0, notional=1.0,
            asset_indices=(0, 1),
            strikes=[100.0, 50.0],
            option_types=["call", "call"],
        )
        spots = np.array([[120.0, 60.0], [120.0, 40.0], [80.0, 60.0]])
        np.testing.assert_allclose(dd.payoff(spots, None), [1.0, 0.0, 0.0])

    def test_mixed_call_put(self):
        dd = DualDigital(
            trade_id="DD1", maturity=1.0, notional=1.0,
            asset_indices=(0, 1),
            strikes=[100.0, 50.0],
            option_types=["call", "put"],
        )
        spots = np.array([[120.0, 40.0], [120.0, 60.0]])
        np.testing.assert_allclose(dd.payoff(spots, None), [1.0, 0.0])


class TestTripleDigital:
    def test_all_conditions_met(self):
        td = TripleDigital(
            trade_id="TD1", maturity=1.0, notional=1.0,
            asset_indices=(0, 1, 2),
            strikes=[100.0, 50.0, 30.0],
            option_types=["call", "call", "call"],
        )
        spots = np.array([[120.0, 60.0, 40.0], [120.0, 60.0, 20.0]])
        np.testing.assert_allclose(td.payoff(spots, None), [1.0, 0.0])
