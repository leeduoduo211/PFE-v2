import numpy as np

from pfev2.core.types import MarketData, PFEConfig
from pfev2.instruments.vanilla import VanillaOption
from pfev2.risk.pfe import compute_pfe


def test_margined_less_than_unmargined():
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
        VanillaOption(trade_id="C1", maturity=1.0, notional=1_000_000,
                      asset_indices=(0,), strike=100.0, option_type="call"),
    ]
    config_unmargined = PFEConfig(n_outer=200, n_inner=200, seed=42,
                                   grid_frequency="monthly", margined=False)
    config_margined = PFEConfig(n_outer=200, n_inner=200, seed=42,
                                 grid_frequency="monthly", margined=True, mpor_days=10)

    r_un = compute_pfe(portfolio, market, config_unmargined)
    r_m = compute_pfe(portfolio, market, config_margined)

    assert r_m.peak_pfe <= r_un.peak_pfe


def test_unmargined_curves_populated():
    """Margined run must also populate unmargined curves."""
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
        VanillaOption(trade_id="C1", maturity=1.0, notional=1_000_000,
                      asset_indices=(0,), strike=100.0, option_type="call"),
    ]
    config = PFEConfig(n_outer=200, n_inner=200, seed=42,
                       grid_frequency="monthly", margined=True, mpor_days=10)
    result = compute_pfe(portfolio, market, config)

    assert result.unmargined_pfe_curve is not None
    assert result.unmargined_epe_curve is not None
    assert result.unmargined_pfe_curve.shape == result.pfe_curve.shape
    assert result.unmargined_epe_curve.shape == result.epe_curve.shape
    assert np.all(result.unmargined_pfe_curve >= result.pfe_curve - 1e-6)


def test_unmargined_only_curves_identical():
    """When margined=False, unmargined curves must equal primary curves."""
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
        VanillaOption(trade_id="C1", maturity=1.0, notional=1_000_000,
                      asset_indices=(0,), strike=100.0, option_type="call"),
    ]
    config = PFEConfig(n_outer=100, n_inner=200, seed=42,
                       grid_frequency="monthly", margined=False)
    result = compute_pfe(portfolio, market, config)

    np.testing.assert_array_equal(result.unmargined_pfe_curve, result.pfe_curve)
    np.testing.assert_array_equal(result.unmargined_epe_curve, result.epe_curve)
