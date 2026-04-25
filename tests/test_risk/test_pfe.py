import numpy as np
import pytest

from pfev2.core.types import MarketData, PFEConfig
from pfev2.instruments.accumulator import Accumulator
from pfev2.instruments.vanilla import VanillaOption
from pfev2.instruments.worst_best_of import WorstOfOption
from pfev2.risk.pfe import compute_pfe


@pytest.fixture
def market():
    return MarketData(
        spots=np.array([100.0]),
        vols=np.array([0.20]),
        rates=np.array([0.05]),
        domestic_rate=0.05,
        corr_matrix=np.array([[1.0]]),
        asset_names=["X"],
        asset_classes=["EQUITY"],
    )


@pytest.fixture
def portfolio():
    return [
        VanillaOption(trade_id="C1", maturity=1.0, notional=1_000_000,
                      asset_indices=(0,), strike=100.0, option_type="call"),
    ]


def test_basic_pfe(market, portfolio):
    config = PFEConfig(n_outer=100, n_inner=200, seed=42, grid_frequency="monthly")
    result = compute_pfe(portfolio, market, config)

    assert result.pfe_curve.shape[0] == result.time_points.shape[0]
    assert result.epe_curve.shape[0] == result.time_points.shape[0]
    assert result.peak_pfe >= 0
    assert result.eepe >= 0
    assert result.computation_time > 0


def test_pfe_greater_than_epe(market, portfolio):
    config = PFEConfig(n_outer=200, n_inner=200, seed=42, grid_frequency="monthly")
    result = compute_pfe(portfolio, market, config)
    assert np.all(result.pfe_curve >= result.epe_curve - 1e-6)


def test_peak_pfe_is_max(market, portfolio):
    config = PFEConfig(n_outer=100, n_inner=200, seed=42, grid_frequency="monthly")
    result = compute_pfe(portfolio, market, config)
    np.testing.assert_allclose(result.peak_pfe, np.max(result.pfe_curve))


def test_progress_callback(market, portfolio):
    progress_values = []
    config = PFEConfig(n_outer=50, n_inner=100, seed=42, grid_frequency="monthly")
    compute_pfe(portfolio, market, config, on_progress=lambda p: progress_values.append(p))
    assert len(progress_values) > 0
    assert progress_values[-1] == pytest.approx(1.0, abs=0.1)


def test_batch_european_multi_asset():
    """Batch pricing path for multi-asset European portfolio."""
    market = MarketData(
        spots=np.array([100.0, 80.0]),
        vols=np.array([0.25, 0.30]),
        rates=np.array([0.05, 0.05]),
        domestic_rate=0.05,
        corr_matrix=np.array([[1.0, 0.6], [0.6, 1.0]]),
        asset_names=["A", "B"],
        asset_classes=["EQ", "EQ"],
    )
    portfolio = [
        VanillaOption(trade_id="C1", maturity=1.0, notional=100_000,
                      asset_indices=(0,), strike=100.0, option_type="call"),
        WorstOfOption(trade_id="WOP", maturity=1.0, notional=100_000,
                      asset_indices=(0, 1), strikes=[100.0, 80.0], option_type="put"),
    ]
    config = PFEConfig(n_outer=100, n_inner=200, seed=42, grid_frequency="monthly")
    result = compute_pfe(portfolio, market, config, per_trade_detail=True)

    assert result.peak_pfe > 0
    assert result.per_trade_mtm.shape == (2, 100, len(result.time_points))
    # Per-trade should sum to total
    total_from_trades = np.sum(result.per_trade_mtm, axis=0)
    np.testing.assert_allclose(total_from_trades, result.mtm_matrix, atol=1e-6)


def test_mixed_european_and_path_dependent():
    """Mixed portfolio: European (batch) + path-dependent (per-path loop)."""
    market = MarketData(
        spots=np.array([100.0]),
        vols=np.array([0.20]),
        rates=np.array([0.05]),
        domestic_rate=0.05,
        corr_matrix=np.array([[1.0]]),
        asset_names=["X"],
        asset_classes=["EQ"],
    )
    call = VanillaOption(trade_id="C1", maturity=1.0, notional=100_000,
                         asset_indices=(0,), strike=100.0, option_type="call")
    acc = Accumulator(trade_id="ACC", maturity=1.0, notional=100_000,
                      asset_indices=(0,), strike=100.0, side="buy",
                      leverage=2.0, schedule=[0.25, 0.5, 0.75, 1.0])

    assert not call.requires_full_path
    assert acc.requires_full_path

    portfolio = [call, acc]
    config = PFEConfig(n_outer=50, n_inner=100, seed=42, grid_frequency="monthly")
    result = compute_pfe(portfolio, market, config, per_trade_detail=True)

    assert result.peak_pfe > 0
    assert result.per_trade_mtm.shape[0] == 2
    # Per-trade should sum to total
    total_from_trades = np.sum(result.per_trade_mtm, axis=0)
    np.testing.assert_allclose(total_from_trades, result.mtm_matrix, atol=1e-6)


def test_batch_reproducibility():
    """Batch pricing must be seed-reproducible."""
    market = MarketData(
        spots=np.array([100.0, 80.0]),
        vols=np.array([0.25, 0.30]),
        rates=np.array([0.05, 0.05]),
        domestic_rate=0.05,
        corr_matrix=np.array([[1.0, 0.6], [0.6, 1.0]]),
        asset_names=["A", "B"],
        asset_classes=["EQ", "EQ"],
    )
    portfolio = [
        VanillaOption(trade_id="C1", maturity=1.0, notional=100_000,
                      asset_indices=(0,), strike=100.0, option_type="call"),
    ]
    config = PFEConfig(n_outer=100, n_inner=200, seed=42, grid_frequency="monthly")

    r1 = compute_pfe(portfolio, market, config)
    r2 = compute_pfe(portfolio, market, config)
    np.testing.assert_array_equal(r1.mtm_matrix, r2.mtm_matrix)
