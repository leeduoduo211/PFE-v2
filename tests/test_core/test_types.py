import numpy as np
import pytest
from pfev2.core.types import AssetClass, TimeGrid, MarketData, PFEConfig
from pfev2.core.exceptions import MarketDataError, CorrelationMatrixError, ConfigError


class TestAssetClass:
    def test_values(self):
        assert AssetClass.FX.value == "FX"
        assert AssetClass.EQUITY.value == "EQUITY"


class TestTimeGrid:
    def test_from_maturity_weekly(self):
        grid = TimeGrid.from_maturity(1.0, frequency="weekly")
        assert grid.dates[0] == 0.0
        assert abs(grid.dates[-1] - 1.0) < 0.02
        assert len(grid.dt) == len(grid.dates) - 1
        assert np.all(grid.dt > 0)

    def test_from_maturity_monthly(self):
        grid = TimeGrid.from_maturity(1.0, frequency="monthly")
        assert 10 <= len(grid.dates) <= 14

    def test_remaining_grid_re_zeroed(self):
        grid = TimeGrid.from_maturity(1.0, frequency="weekly")
        mid = len(grid.dates) // 2
        remaining = grid.remaining_grid(mid)
        assert remaining.dates[0] == 0.0
        assert remaining.dates[-1] < grid.dates[-1]
        assert len(remaining.dates) == len(grid.dates) - mid


class TestMarketData:
    def test_valid_construction(self, single_asset_market):
        md = MarketData(**single_asset_market)
        assert md.spots[0] == 100.0
        assert md.domestic_rate == 0.05

    def test_index_of(self, two_asset_market):
        md = MarketData(**two_asset_market)
        assert md.index_of("EURUSD") == 0
        assert md.index_of("AAPL") == 1

    def test_evolve(self, single_asset_market):
        md = MarketData(**single_asset_market)
        new = md.evolve(np.array([110.0]), t=0.5)
        assert new.spots[0] == 110.0
        assert new.vols[0] == md.vols[0]

    def test_rejects_nan_spots(self, single_asset_market):
        single_asset_market["spots"] = np.array([np.nan])
        with pytest.raises(MarketDataError, match="NaN"):
            MarketData(**single_asset_market)

    def test_rejects_negative_vol(self, single_asset_market):
        single_asset_market["vols"] = np.array([-0.1])
        with pytest.raises(MarketDataError, match="vol"):
            MarketData(**single_asset_market)

    def test_rejects_non_psd_corr(self, two_asset_market):
        two_asset_market["corr_matrix"] = np.array([[1.0, 1.5], [1.5, 1.0]])
        with pytest.raises(CorrelationMatrixError):
            MarketData(**two_asset_market)

    def test_rejects_shape_mismatch(self, single_asset_market):
        single_asset_market["vols"] = np.array([0.2, 0.3])
        with pytest.raises(MarketDataError, match="shape"):
            MarketData(**single_asset_market)


class TestPFEConfig:
    def test_defaults(self):
        cfg = PFEConfig()
        assert cfg.n_outer == 5000
        assert cfg.n_inner == 2000
        assert cfg.confidence_level == 0.95
        assert cfg.margined is False

    def test_rejects_bad_confidence(self):
        with pytest.raises(ConfigError):
            PFEConfig(confidence_level=1.5)

    def test_rejects_zero_paths(self):
        with pytest.raises(ConfigError):
            PFEConfig(n_outer=0)
