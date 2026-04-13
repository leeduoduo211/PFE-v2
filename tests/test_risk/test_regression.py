import numpy as np
from pfev2 import MarketData, PFEConfig, compute_pfe
from pfev2.instruments import VanillaCall


def test_pinned_pfe_values():
    """Seed-locked run must produce identical results across runs."""
    market = MarketData(
        spots=np.array([100.0]),
        vols=np.array([0.20]),
        rates=np.array([0.05]),
        domestic_rate=0.05,
        corr_matrix=np.array([[1.0]]),
        asset_names=["X"],
        asset_classes=["EQUITY"],
    )
    portfolio = [
        VanillaCall(trade_id="C1", maturity=1.0, notional=100_000,
                    asset_indices=(0,), strike=100.0),
    ]
    config = PFEConfig(n_outer=100, n_inner=200, seed=42, grid_frequency="monthly")

    r1 = compute_pfe(portfolio, market, config)
    r2 = compute_pfe(portfolio, market, config)

    np.testing.assert_array_equal(r1.pfe_curve, r2.pfe_curve)
    np.testing.assert_array_equal(r1.epe_curve, r2.epe_curve)
    assert r1.peak_pfe == r2.peak_pfe
