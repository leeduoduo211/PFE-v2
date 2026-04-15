import numpy as np
import pytest
from ui.utils.converters import build_market_data, build_instrument, build_portfolio, build_config


class TestBuildMarketData:
    def test_basic_two_asset(self):
        state = {
            "asset_names": ["EURUSD", "AAPL"],
            "asset_classes": ["FX", "EQUITY"],
            "spots": [1.085, 150.0],
            "vols": [0.08, 0.25],
            "rates": [0.02, 0.05],
            "domestic_rate": 0.03,
            "corr_matrix": [[1.0, 0.3], [0.3, 1.0]],
        }
        md = build_market_data(state)
        assert len(md.spots) == 2
        np.testing.assert_allclose(md.spots, [1.085, 150.0])
        assert md.domestic_rate == 0.03
        assert md.asset_names == ["EURUSD", "AAPL"]

    def test_single_asset(self):
        state = {
            "asset_names": ["AAPL"],
            "asset_classes": ["EQUITY"],
            "spots": [150.0],
            "vols": [0.25],
            "rates": [0.05],
            "domestic_rate": 0.05,
            "corr_matrix": [[1.0]],
        }
        md = build_market_data(state)
        assert len(md.spots) == 1


class TestBuildInstrument:
    def test_vanilla_call(self):
        spec = {
            "trade_id": "C1",
            "instrument_type": "VanillaOption",
            "params": {
                "maturity": 1.0,
                "notional": 100_000,
                "asset_indices": [0],
                "strike": 100.0,
                "option_type": "call",
            },
            "modifiers": [],
        }
        name_to_idx = {"AAPL": 0}
        inst = build_instrument(spec, name_to_idx)
        assert inst.trade_id == "C1"
        assert inst.strike == 100.0

    def test_assets_name_to_indices(self):
        """UI trade builder passes 'assets' (names), converter must map to asset_indices."""
        spec = {
            "trade_id": "C1",
            "instrument_type": "VanillaOption",
            "params": {
                "maturity": 1.0,
                "notional": 100_000,
                "assets": ["TSLA"],
                "strike": 100.0,
                "option_type": "call",
            },
            "modifiers": [],
        }
        name_to_idx = {"AAPL": 0, "TSLA": 1}
        inst = build_instrument(spec, name_to_idx)
        assert inst.asset_indices == (1,)

    def test_with_knock_out_modifier(self):
        spec = {
            "trade_id": "C2",
            "instrument_type": "VanillaOption",
            "params": {
                "maturity": 1.0,
                "notional": 100_000,
                "asset_indices": [0],
                "strike": 100.0,
                "option_type": "call",
            },
            "modifiers": [
                {"type": "KnockOut", "params": {"barrier": 120.0, "direction": "up"}},
            ],
        }
        name_to_idx = {"AAPL": 0}
        inst = build_instrument(spec, name_to_idx)
        assert inst.trade_id == "C2"
        assert hasattr(inst, "barrier")
        assert inst.barrier == 120.0

    def test_accumulator(self):
        spec = {
            "trade_id": "ACC1",
            "instrument_type": "AccumulatorDecumulator",
            "params": {
                "maturity": 1.0,
                "notional": 500_000,
                "asset_indices": [0],
                "strike": 1.10,
                "leverage": 2.0,
                "side": "buy",
                "schedule": [0.0833, 0.1667, 0.25],
            },
            "modifiers": [],
        }
        name_to_idx = {"EURUSD": 0}
        inst = build_instrument(spec, name_to_idx)
        assert inst.trade_id == "ACC1"
        assert inst.leverage == 2.0

    def test_worst_of_put(self):
        spec = {
            "trade_id": "WP1",
            "instrument_type": "WorstOfOption",
            "params": {
                "maturity": 1.0,
                "notional": 100_000,
                "asset_indices": [0, 1],
                "strikes": [100.0, 50.0],
                "option_type": "put",
            },
            "modifiers": [],
        }
        name_to_idx = {"AAPL": 0, "XYZ": 1}
        inst = build_instrument(spec, name_to_idx)
        assert inst.trade_id == "WP1"

    def test_stacked_modifiers(self):
        spec = {
            "trade_id": "C3",
            "instrument_type": "VanillaOption",
            "params": {
                "maturity": 1.0,
                "notional": 100_000,
                "asset_indices": [0],
                "strike": 100.0,
                "option_type": "call",
            },
            "modifiers": [
                {"type": "KnockOut", "params": {"barrier": 120.0, "direction": "up"}},
                {"type": "PayoffCap", "params": {"cap": 0.5}},
            ],
        }
        name_to_idx = {"AAPL": 0}
        inst = build_instrument(spec, name_to_idx)
        assert inst.trade_id == "C3"
        assert hasattr(inst, "cap")
        assert inst.cap == 0.5


class TestBuildInstrumentDirection:
    def test_long_direction_preserves_notional(self):
        spec = {
            "trade_id": "T1",
            "direction": "long",
            "instrument_type": "VanillaOption",
            "params": {
                "maturity": 1.0,
                "notional": 1_000_000.0,
                "asset_indices": (0,),
                "strike": 100.0,
                "option_type": "call",
            },
            "modifiers": [],
        }
        inst = build_instrument(spec, {"X": 0})
        assert inst.notional == 1_000_000.0

    def test_short_direction_negates_notional(self):
        spec = {
            "trade_id": "T1",
            "direction": "short",
            "instrument_type": "VanillaOption",
            "params": {
                "maturity": 1.0,
                "notional": 1_000_000.0,
                "asset_indices": (0,),
                "strike": 100.0,
                "option_type": "call",
            },
            "modifiers": [],
        }
        inst = build_instrument(spec, {"X": 0})
        assert inst.notional == -1_000_000.0

    def test_short_does_not_mutate_original_spec(self):
        spec = {
            "trade_id": "T1",
            "direction": "short",
            "instrument_type": "VanillaOption",
            "params": {
                "maturity": 1.0,
                "notional": 1_000_000.0,
                "asset_indices": (0,),
                "strike": 100.0,
                "option_type": "call",
            },
            "modifiers": [],
        }
        build_instrument(spec, {"X": 0})
        assert spec["params"]["notional"] == 1_000_000.0

    def test_missing_direction_defaults_to_long(self):
        spec = {
            "trade_id": "T1",
            "instrument_type": "VanillaOption",
            "params": {
                "maturity": 1.0,
                "notional": 1_000_000.0,
                "asset_indices": (0,),
                "strike": 100.0,
                "option_type": "call",
            },
            "modifiers": [],
        }
        inst = build_instrument(spec, {"X": 0})
        assert inst.notional == 1_000_000.0


class TestBuildPortfolio:
    def test_two_trade_portfolio(self):
        state = {
            "asset_names": ["AAPL", "XYZ"],
            "asset_classes": ["EQUITY", "EQUITY"],
            "spots": [100.0, 50.0],
            "vols": [0.2, 0.3],
            "rates": [0.05, 0.05],
            "domestic_rate": 0.05,
            "corr_matrix": [[1.0, 0.5], [0.5, 1.0]],
        }
        market = build_market_data(state)
        specs = [
            {
                "trade_id": "C1",
                "instrument_type": "VanillaOption",
                "params": {"maturity": 1.0, "notional": 100_000, "asset_indices": [0], "strike": 100.0, "option_type": "call"},
                "modifiers": [],
            },
            {
                "trade_id": "WP1",
                "instrument_type": "WorstOfOption",
                "params": {"maturity": 1.0, "notional": 100_000, "asset_indices": [0, 1], "strikes": [100.0, 50.0], "option_type": "put"},
                "modifiers": [],
            },
        ]
        portfolio = build_portfolio(specs, market)
        assert len(portfolio) == 2
        assert portfolio[0].trade_id == "C1"
        assert portfolio[1].trade_id == "WP1"


class TestBuildConfig:
    def test_default_config(self):
        state = {}
        cfg = build_config(state)
        assert cfg.n_outer == 5000
        assert cfg.n_inner == 2000
        assert cfg.confidence_level == 0.95

    def test_custom_config(self):
        state = {
            "n_outer": 1000,
            "n_inner": 500,
            "confidence_level": 0.99,
            "grid_frequency": "monthly",
            "margined": True,
            "mpor_days": 10,
            "backend": "numpy",
            "seed": 123,
        }
        cfg = build_config(state)
        assert cfg.n_outer == 1000
        assert cfg.margined is True
        assert cfg.seed == 123
