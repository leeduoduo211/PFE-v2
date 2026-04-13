import numpy as np
import pytest


@pytest.fixture
def single_asset_market():
    """Single equity asset for simple tests."""
    return {
        "spots": np.array([100.0]),
        "vols": np.array([0.20]),
        "rates": np.array([0.05]),
        "domestic_rate": 0.05,
        "corr_matrix": np.array([[1.0]]),
        "asset_names": ["EQUITY1"],
        "asset_classes": ["EQUITY"],
    }


@pytest.fixture
def two_asset_market():
    """Two correlated assets (1 FX + 1 Equity)."""
    return {
        "spots": np.array([1.10, 100.0]),
        "vols": np.array([0.08, 0.25]),
        "rates": np.array([0.02, 0.05]),
        "domestic_rate": 0.03,
        "corr_matrix": np.array([[1.0, 0.3], [0.3, 1.0]]),
        "asset_names": ["EURUSD", "AAPL"],
        "asset_classes": ["FX", "EQUITY"],
    }


@pytest.fixture
def three_asset_market():
    """Three correlated assets."""
    return {
        "spots": np.array([1.085, 150.0, 45.0]),
        "vols": np.array([0.08, 0.25, 0.30]),
        "rates": np.array([0.02, 0.05, 0.05]),
        "domestic_rate": 0.03,
        "corr_matrix": np.array([
            [1.0, 0.3, 0.1],
            [0.3, 1.0, 0.5],
            [0.1, 0.5, 1.0],
        ]),
        "asset_names": ["EURUSD", "AAPL", "XYZ"],
        "asset_classes": ["FX", "EQUITY", "EQUITY"],
    }
