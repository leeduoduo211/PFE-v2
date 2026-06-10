"""Payment-time discounting for periodic instruments.

Autocallable / TARF / Accumulator cashflows settle at their own observation
dates, not at maturity. ``pv_payoff`` discounts each cashflow from its payment
date to the valuation node, and the pricer must use it (skipping the blanket
``exp(-r*tau)`` maturity discount) for trades with ``pays_before_maturity``.
"""

import numpy as np
import pytest

from pfev2.core.types import MarketData, PayoffTimeGrid, TimeGrid
from pfev2.engine.backends.numpy_backend import NumpyBackend
from pfev2.engine.gbm import MultivariateGBM
from pfev2.instruments.accumulator import Accumulator
from pfev2.instruments.autocallable import Autocallable
from pfev2.instruments.tarf import TARF
from pfev2.pricing.inner_mc import InnerMCPricer

RATE = 0.05
VALUATION = 0.25
# Absolute grid from inception; node sits at t=0.25, obs at 0.5 and 1.0.
GRID = PayoffTimeGrid(np.array([0.0, 0.25, 0.5, 0.75, 1.0]), valuation_time=VALUATION)


def _path(prices):
    """Single-asset path history of shape (1, n_steps, 1)."""
    return np.asarray(prices, dtype=float).reshape(1, -1, 1)


class TestAccumulatorPV:
    def _trade(self):
        return Accumulator(trade_id="ACC", maturity=1.0, notional=1.0,
                           asset_indices=(0,), strike=100.0, leverage=2.0,
                           side="buy", schedule=[0.5, 1.0])

    def test_pv_discounts_each_settlement(self):
        # Obs at 0.5: S=110 -> units 1, pnl +10. Obs at 1.0: S=90 -> units 2, pnl -20.
        path = _path([100, 100, 110, 105, 90])
        acc = self._trade()
        expected = (10.0 * np.exp(-RATE * (0.5 - VALUATION))
                    - 20.0 * np.exp(-RATE * (1.0 - VALUATION)))
        pv = acc.pv_payoff(path[:, -1, :], path, GRID, RATE)
        np.testing.assert_allclose(pv, [expected], rtol=1e-12)

    def test_raw_payoff_unchanged(self):
        path = _path([100, 100, 110, 105, 90])
        acc = self._trade()
        np.testing.assert_allclose(acc.payoff(path[:, -1, :], path, GRID), [-10.0])

    def test_zero_rate_matches_raw_payoff(self):
        path = _path([100, 100, 110, 105, 90])
        acc = self._trade()
        np.testing.assert_allclose(
            acc.pv_payoff(path[:, -1, :], path, GRID, 0.0),
            acc.payoff(path[:, -1, :], path, GRID),
        )


class TestTARFPV:
    def _trade(self, target=15.0):
        return TARF(trade_id="T1", maturity=1.0, notional=1.0,
                    asset_indices=(0,), strike=100.0, target=target,
                    leverage=2.0, side="buy", schedule=[0.5, 1.0])

    def test_pv_discounts_each_period(self):
        # No target hit: +10 at 0.5, -20 at 1.0.
        path = _path([100, 100, 110, 105, 90])
        tarf = self._trade()
        expected = (10.0 * np.exp(-RATE * (0.5 - VALUATION))
                    - 20.0 * np.exp(-RATE * (1.0 - VALUATION)))
        pv = tarf.pv_payoff(path[:, -1, :], path, GRID, RATE)
        np.testing.assert_allclose(pv, [expected], rtol=1e-12)

    def test_pv_discounts_residual_at_hit_date(self):
        # +10 at 0.5 (cum 10 < 15); +20 at 1.0 would breach -> residual 5 paid at 1.0.
        path = _path([100, 100, 110, 115, 120])
        tarf = self._trade(target=15.0)
        expected = (10.0 * np.exp(-RATE * (0.5 - VALUATION))
                    + 5.0 * np.exp(-RATE * (1.0 - VALUATION)))
        pv = tarf.pv_payoff(path[:, -1, :], path, GRID, RATE)
        np.testing.assert_allclose(pv, [expected], rtol=1e-12)

    def test_zero_rate_matches_raw_payoff(self):
        path = _path([100, 100, 110, 115, 120])
        tarf = self._trade()
        np.testing.assert_allclose(
            tarf.pv_payoff(path[:, -1, :], path, GRID, 0.0),
            tarf.payoff(path[:, -1, :], path, GRID),
        )


class TestAutocallablePV:
    def _trade(self):
        return Autocallable(trade_id="AC1", maturity=1.0, notional=1.0,
                            asset_indices=(0,), autocall_trigger=0.5,
                            coupon_rate=0.06, put_strike=0.7,
                            schedule=[0.5, 1.0])

    def test_coupon_discounted_from_call_date(self):
        # Perf at obs 0.5 is 1.1 >= 0.5 -> calls, coupon paid at 0.5.
        path = _path([100, 100, 110, 105, 90])
        ac = self._trade()
        expected = 0.06 * np.exp(-RATE * (0.5 - VALUATION))
        pv = ac.pv_payoff(path[:, -1, :], path, GRID, RATE)
        np.testing.assert_allclose(pv, [expected], rtol=1e-12)

    def test_put_loss_discounted_from_maturity(self):
        # Never calls (perf 0.4 then 0.45 < trigger); terminal 0.45 < put_strike.
        path = _path([100, 80, 40, 40, 45])
        ac = self._trade()
        expected = (0.45 - 1.0) * np.exp(-RATE * (1.0 - VALUATION))
        pv = ac.pv_payoff(path[:, -1, :], path, GRID, RATE)
        np.testing.assert_allclose(pv, [expected], rtol=1e-12)

    def test_zero_rate_matches_raw_payoff(self):
        for prices in ([100, 100, 110, 105, 90], [100, 80, 40, 40, 45]):
            path = _path(prices)
            ac = self._trade()
            np.testing.assert_allclose(
                ac.pv_payoff(path[:, -1, :], path, GRID, 0.0),
                ac.payoff(path[:, -1, :], path, GRID),
            )


class TestPricerUsesPaymentTimeDiscounting:
    """The pricer must not apply the full-tau maturity discount on top."""

    @pytest.fixture
    def market(self):
        return MarketData(
            spots=np.array([100.0]),
            vols=np.array([0.20]),
            rates=np.array([RATE]),
            domestic_rate=RATE,
            corr_matrix=np.array([[1.0]]),
            asset_names=["X"],
            asset_classes=["EQUITY"],
        )

    @pytest.fixture
    def pricer(self):
        return InnerMCPricer(engine=MultivariateGBM(backend=NumpyBackend()))

    def _always_calls(self):
        # Trigger near zero: every (positive) GBM path calls at the first
        # observation, so the MtM is deterministic regardless of randomness.
        return Autocallable(trade_id="AC1", maturity=1.0, notional=1.0,
                            asset_indices=(0,), autocall_trigger=1e-9,
                            coupon_rate=0.06, put_strike=0.7,
                            schedule=[0.5, 1.0])

    def test_batch_path_dependent_discounts_from_call_date(self, pricer, market):
        pricer.set_market(market)
        trade = self._always_calls()
        # Node at t=0.25; remaining relative grid hits obs 0.5 and maturity 1.0.
        remaining = TimeGrid(dates=np.array([0.0, 0.25, 0.75]),
                             dt=np.diff(np.array([0.0, 0.25, 0.75])))
        node_spots = np.array([[100.0], [120.0], [80.0]])
        realized = np.concatenate(
            [np.full((3, 1, 1), 100.0), node_spots[:, np.newaxis, :]], axis=1
        )
        mtms = pricer.batch_price_path_dependent(
            trade, market, node_spots, remaining, n_inner=64,
            seed_seq=np.random.SeedSequence(7),
            realized_paths=realized, realized_grid=np.array([0.0, 0.25]),
        )
        expected = 0.06 * np.exp(-RATE * 0.25)  # coupon paid 0.25y after node
        np.testing.assert_allclose(mtms, np.full(3, expected), rtol=1e-12)

    def test_price_trade_discounts_from_call_date(self, pricer, market):
        trade = self._always_calls()
        remaining = TimeGrid(dates=np.array([0.0, 0.25, 0.75]),
                             dt=np.diff(np.array([0.0, 0.25, 0.75])))
        mtm = pricer.price_trade(
            trade, market, node_spots=np.array([100.0]),
            remaining_grid=remaining, n_inner=64, seed=7,
        )
        expected = 0.06 * np.exp(-RATE * 0.25)
        np.testing.assert_allclose(mtm, expected, rtol=1e-12)
