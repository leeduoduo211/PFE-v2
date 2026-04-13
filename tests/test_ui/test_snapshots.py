import json
import numpy as np
import pytest
from ui.utils.snapshots import serialize_snapshot, deserialize_snapshot, validate_snapshot


class TestSerialize:
    def test_roundtrip(self):
        state = {
            "asset_names": ["EURUSD", "AAPL"],
            "asset_classes": ["FX", "EQUITY"],
            "spots": [1.085, 150.0],
            "vols": [0.08, 0.25],
            "rates": [0.02, 0.05],
            "domestic_rate": 0.03,
            "corr_matrix": [[1.0, 0.3], [0.3, 1.0]],
        }
        json_str = serialize_snapshot(state, name="test_snapshot")
        parsed = json.loads(json_str)
        assert parsed["version"] == 1
        assert parsed["name"] == "test_snapshot"
        assert parsed["spots"] == [1.085, 150.0]

        restored = deserialize_snapshot(json_str)
        assert restored["asset_names"] == ["EURUSD", "AAPL"]
        assert restored["domestic_rate"] == 0.03

    def test_numpy_arrays_serialized(self):
        state = {
            "asset_names": ["A"],
            "asset_classes": ["EQUITY"],
            "spots": np.array([100.0]),
            "vols": np.array([0.2]),
            "rates": np.array([0.05]),
            "domestic_rate": 0.05,
            "corr_matrix": np.array([[1.0]]),
        }
        json_str = serialize_snapshot(state, name="np_test")
        parsed = json.loads(json_str)
        assert isinstance(parsed["spots"], list)


class TestValidate:
    def test_valid_snapshot_raw(self):
        data = {
            "version": 1,
            "name": "test",
            "asset_names": ["A"],
            "asset_classes": ["EQUITY"],
            "spots": [100.0],
            "vols": [0.2],
            "rates": [0.05],
            "domestic_rate": 0.05,
            "corr_matrix": [[1.0]],
        }
        errors = validate_snapshot(data)
        assert errors == []

    def test_valid_after_deserialize(self):
        state = {
            "asset_names": ["A"],
            "asset_classes": ["EQUITY"],
            "spots": [100.0],
            "vols": [0.2],
            "rates": [0.05],
            "domestic_rate": 0.05,
            "corr_matrix": [[1.0]],
        }
        json_str = serialize_snapshot(state, name="t")
        restored = deserialize_snapshot(json_str)
        errors = validate_snapshot(restored)
        assert errors == []

    def test_missing_field(self):
        data = {"version": 1, "name": "test"}
        errors = validate_snapshot(data)
        assert len(errors) > 0

    def test_length_mismatch(self):
        data = {
            "version": 1,
            "name": "test",
            "asset_names": ["A", "B"],
            "asset_classes": ["EQUITY"],
            "spots": [100.0],
            "vols": [0.2],
            "rates": [0.05],
            "domestic_rate": 0.05,
            "corr_matrix": [[1.0]],
        }
        errors = validate_snapshot(data)
        assert any("length" in e.lower() or "mismatch" in e.lower() for e in errors)
