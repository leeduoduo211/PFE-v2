import numpy as np
import pytest
from pfev2.instruments.vanilla import VanillaCall
from pfev2.modifiers.realized_vol_knock import RealizedVolKnockOut, RealizedVolKnockIn
from pfev2.core.exceptions import ModifierError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _call(strike=100.0, asset_indices=(0,)):
    return VanillaCall(trade_id="C1", maturity=1.0, notional=1.0,
                       asset_indices=asset_indices, strike=strike)


def _flat_path(n_paths, n_steps, spot=100.0):
    """A flat price path with zero returns → realized vol = 0."""
    prices = np.full((n_paths, n_steps, 1), spot, dtype=float)
    return prices


def _volatile_path(n_paths, n_steps, annualization_factor=52.0, target_vol=0.40):
    """Paths with known realized vol close to target_vol (deterministic via sin wave)."""
    # Use a sine wave to produce predictable, non-zero returns
    t = np.linspace(0, 2 * np.pi, n_steps)
    prices = 100.0 * np.exp(0.05 * np.sin(t))  # (n_steps,)
    paths = np.tile(prices[np.newaxis, :, np.newaxis], (n_paths, 1, 1))
    return paths


# ---------------------------------------------------------------------------
# RealizedVolKnockOut
# ---------------------------------------------------------------------------

class TestRealizedVolKnockOut:
    def test_flat_path_below_barrier_preserves_payoff(self):
        """Zero realized vol is below any positive barrier → no knock-out."""
        base = _call()
        ko = RealizedVolKnockOut(base, vol_barrier=0.20, direction="above",
                                 annualization_factor=52.0)
        paths = _flat_path(n_paths=3, n_steps=10, spot=120.0)
        spots = paths[:, -1, :]
        raw = base.payoff(spots, None)
        modified = ko.payoff(spots, paths)
        np.testing.assert_allclose(modified, raw)

    def test_high_vol_path_zeroed(self):
        """High-vol path exceeds barrier → knocked out to zero."""
        base = _call()
        # Build a path with large log returns
        n_paths, n_steps = 2, 50
        prices = np.ones((n_paths, n_steps, 1)) * 100.0
        # Alternate +/-5% each step → large realized vol
        for i in range(1, n_steps):
            prices[:, i, 0] = prices[:, i - 1, 0] * (1.1 if i % 2 == 0 else 0.9)
        spots = prices[:, -1, :]

        ko = RealizedVolKnockOut(base, vol_barrier=0.05, direction="above",
                                 annualization_factor=52.0)
        payoffs = ko.payoff(spots, prices)
        np.testing.assert_allclose(payoffs, [0.0, 0.0])

    def test_direction_below_knocks_out_low_vol(self):
        """Flat path (rv=0) < barrier → knocked out when direction='below'."""
        base = _call()
        ko = RealizedVolKnockOut(base, vol_barrier=0.20, direction="below",
                                 annualization_factor=52.0)
        paths = _flat_path(n_paths=2, n_steps=10, spot=120.0)
        spots = paths[:, -1, :]
        payoffs = ko.payoff(spots, paths)
        np.testing.assert_allclose(payoffs, [0.0, 0.0])

    def test_single_step_path_no_crash(self):
        """path_history with only 1 step yields rv=0, no exception."""
        base = _call()
        ko = RealizedVolKnockOut(base, vol_barrier=0.20, direction="above",
                                 annualization_factor=52.0)
        paths = _flat_path(n_paths=2, n_steps=1, spot=110.0)
        spots = paths[:, -1, :]
        payoffs = ko.payoff(spots, paths)
        raw = base.payoff(spots, None)
        np.testing.assert_allclose(payoffs, raw)

    def test_inherits_trade_properties(self):
        base = _call()
        ko = RealizedVolKnockOut(base, vol_barrier=0.30, direction="above")
        assert ko.trade_id == "C1"
        assert ko.maturity == 1.0
        assert ko.notional == 1.0
        assert ko.asset_indices == (0,)
        assert ko.requires_full_path is True

    def test_invalid_direction_raises(self):
        with pytest.raises(ModifierError, match="direction"):
            RealizedVolKnockOut(_call(), vol_barrier=0.30, direction="up")

    def test_non_positive_barrier_raises(self):
        with pytest.raises(ModifierError):
            RealizedVolKnockOut(_call(), vol_barrier=0.0, direction="above")

    def test_non_positive_annualization_raises(self):
        with pytest.raises(ModifierError):
            RealizedVolKnockOut(_call(), vol_barrier=0.30, direction="above",
                                annualization_factor=0.0)

    def test_mixed_paths_partial_knockout(self):
        """Some paths high-vol (knocked out), some flat (preserved)."""
        base = _call()
        n_steps = 20
        # Path 0: flat (rv ≈ 0)
        path0 = np.full((n_steps, 1), 100.0)
        # Path 1: alternating ±20% (high rv)
        path1 = np.ones((n_steps, 1)) * 100.0
        for i in range(1, n_steps):
            path1[i, 0] = path1[i - 1, 0] * (1.2 if i % 2 == 0 else 0.8)

        paths = np.stack([path0, path1])[np.newaxis]  # wrong shape, fix:
        paths = np.array([path0, path1])  # (2, n_steps, 1)
        spots = paths[:, -1, :]

        ko = RealizedVolKnockOut(base, vol_barrier=0.10, direction="above",
                                 annualization_factor=52.0)
        payoffs = ko.payoff(spots, paths)
        raw = base.payoff(spots, None)

        # Path 0 (low vol): preserved
        assert payoffs[0] == pytest.approx(raw[0])
        # Path 1 (high vol): zeroed
        assert payoffs[1] == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# RealizedVolKnockIn
# ---------------------------------------------------------------------------

class TestRealizedVolKnockIn:
    def test_flat_path_not_activated(self):
        """rv=0 is not above barrier → knock-in not activated → payoff=0."""
        base = _call()
        ki = RealizedVolKnockIn(base, vol_barrier=0.20, direction="above",
                                annualization_factor=52.0)
        paths = _flat_path(n_paths=3, n_steps=10, spot=120.0)
        spots = paths[:, -1, :]
        payoffs = ki.payoff(spots, paths)
        np.testing.assert_allclose(payoffs, [0.0, 0.0, 0.0])

    def test_high_vol_path_activates(self):
        """High-vol path exceeds barrier → activated → full payoff."""
        base = _call()
        n_steps = 50
        prices = np.ones((2, n_steps, 1)) * 100.0
        for i in range(1, n_steps):
            prices[:, i, 0] = prices[:, i - 1, 0] * (1.1 if i % 2 == 0 else 0.9)
        spots = prices[:, -1, :]
        raw = base.payoff(spots, None)

        ki = RealizedVolKnockIn(base, vol_barrier=0.05, direction="above",
                                annualization_factor=52.0)
        payoffs = ki.payoff(spots, prices)
        np.testing.assert_allclose(payoffs, raw)

    def test_direction_below_activates_low_vol(self):
        """rv=0 < barrier → activated when direction='below'."""
        base = _call()
        ki = RealizedVolKnockIn(base, vol_barrier=0.20, direction="below",
                                annualization_factor=52.0)
        paths = _flat_path(n_paths=2, n_steps=10, spot=120.0)
        spots = paths[:, -1, :]
        raw = base.payoff(spots, None)
        payoffs = ki.payoff(spots, paths)
        np.testing.assert_allclose(payoffs, raw)

    def test_ko_ki_complement(self):
        """KO and KI on same path/barrier sum to the unmodified payoff."""
        base = _call()
        n_steps = 30
        prices = np.ones((4, n_steps, 1)) * 100.0
        # Paths 0,1: flat; paths 2,3: alternating
        for k in range(2, 4):
            for i in range(1, n_steps):
                prices[k, i, 0] = prices[k, i - 1, 0] * (1.15 if i % 2 == 0 else 0.85)
        spots = prices[:, -1, :]
        raw = base.payoff(spots, None)

        ko = RealizedVolKnockOut(base, vol_barrier=0.20, direction="above",
                                 annualization_factor=52.0)
        ki = RealizedVolKnockIn(base, vol_barrier=0.20, direction="above",
                                annualization_factor=52.0)
        payoff_ko = ko.payoff(spots, prices)
        payoff_ki = ki.payoff(spots, prices)
        np.testing.assert_allclose(payoff_ko + payoff_ki, raw, rtol=1e-10)

    def test_invalid_direction_raises(self):
        with pytest.raises(ModifierError, match="direction"):
            RealizedVolKnockIn(_call(), vol_barrier=0.30, direction="down")

    def test_multi_asset_monitor_pos(self):
        """asset_idx selects the correct column from path_history."""
        base = VanillaCall(trade_id="T1", maturity=1.0, notional=1.0,
                           asset_indices=(0, 1), strike=100.0)
        # Column 0: volatile; column 1: flat
        n_paths, n_steps = 2, 30
        prices = np.ones((n_paths, n_steps, 2)) * 100.0
        for i in range(1, n_steps):
            prices[:, i, 0] = prices[:, i - 1, 0] * (1.1 if i % 2 == 0 else 0.9)
        # Column 1 stays flat
        spots = prices[:, -1, :]

        # Monitor asset_idx=1 (flat) → rv ≈ 0 → not above 0.20 → no KO
        ko_flat = RealizedVolKnockOut(base, vol_barrier=0.20, direction="above",
                                     asset_idx=1, annualization_factor=52.0)
        raw = base.payoff(spots, None)
        np.testing.assert_allclose(ko_flat.payoff(spots, prices), raw)

        # Monitor asset_idx=0 (volatile) → rv >> 0.20 → KO
        ko_vol = RealizedVolKnockOut(base, vol_barrier=0.20, direction="above",
                                    asset_idx=0, annualization_factor=52.0)
        np.testing.assert_allclose(ko_vol.payoff(spots, prices), [0.0, 0.0])
