import numpy as np

from ui.components.payoff_display import payoff_formula, payoff_sparkline
from ui.components.trade_economics import compute_scenarios


class TestPayoffFormula:
    def test_vanilla_call_long(self):
        spec = {
            "direction": "long",
            "instrument_type": "VanillaOption",
            "params": {"strike": 100.0, "option_type": "call"},
            "modifiers": [],
        }
        f = payoff_formula(spec)
        assert "max(S - 100" in f
        assert not f.startswith("-")

    def test_vanilla_call_short(self):
        spec = {
            "direction": "short",
            "instrument_type": "VanillaOption",
            "params": {"strike": 100.0, "option_type": "call"},
            "modifiers": [],
        }
        f = payoff_formula(spec)
        assert f.startswith("-")

    def test_vanilla_put_long(self):
        spec = {
            "direction": "long",
            "instrument_type": "VanillaOption",
            "params": {"strike": 100.0, "option_type": "put"},
            "modifiers": [],
        }
        f = payoff_formula(spec)
        assert "max(100" in f

    def test_digital_long(self):
        spec = {
            "direction": "long",
            "instrument_type": "Digital",
            "params": {"strike": 100.0, "option_type": "call"},
            "modifiers": [],
        }
        f = payoff_formula(spec)
        assert "100" in f

    def test_with_knock_out(self):
        spec = {
            "direction": "long",
            "instrument_type": "VanillaOption",
            "params": {"strike": 100.0, "option_type": "call"},
            "modifiers": [{"type": "KnockOut", "params": {"barrier": 120.0, "direction": "up"}}],
        }
        f = payoff_formula(spec)
        assert "120" in f

    def test_with_cap(self):
        spec = {
            "direction": "long",
            "instrument_type": "VanillaOption",
            "params": {"strike": 100.0, "option_type": "call"},
            "modifiers": [{"type": "PayoffCap", "params": {"cap": 50.0}}],
        }
        f = payoff_formula(spec)
        assert "50" in f

    def test_accumulator(self):
        spec = {
            "direction": "long",
            "instrument_type": "AccumulatorDecumulator",
            "params": {"strike": 100.0, "leverage": 2.0, "side": "buy"},
            "modifiers": [],
        }
        f = payoff_formula(spec)
        assert "100" in f

    def test_missing_direction_defaults_long(self):
        spec = {
            "instrument_type": "VanillaOption",
            "params": {"strike": 100.0, "option_type": "call"},
            "modifiers": [],
        }
        f = payoff_formula(spec)
        assert not f.startswith("-")


class TestPayoffSparkline:
    def test_vanilla_call_returns_figure(self):
        spec = {
            "direction": "long",
            "instrument_type": "VanillaOption",
            "params": {"strike": 100.0, "option_type": "call", "maturity": 1.0, "notional": 1.0,
                        "assets": ["X"]},
            "modifiers": [],
        }
        fig = payoff_sparkline(spec, asset_names=["X"])
        assert fig is not None
        assert len(fig.data) >= 1

    def test_short_negates_payoff(self):
        long_spec = {
            "direction": "long",
            "instrument_type": "VanillaOption",
            "params": {"strike": 100.0, "option_type": "call", "maturity": 1.0, "notional": 1.0,
                        "assets": ["X"]},
            "modifiers": [],
        }
        short_spec = dict(long_spec, direction="short")
        fig_long = payoff_sparkline(long_spec, asset_names=["X"])
        fig_short = payoff_sparkline(short_spec, asset_names=["X"])
        y_long = np.array(fig_long.data[0].y)
        y_short = np.array(fig_short.data[0].y)
        np.testing.assert_allclose(y_short, -y_long)

    def test_cap_modifier_limits_payoff(self):
        spec = {
            "direction": "long",
            "instrument_type": "VanillaOption",
            "params": {"strike": 100.0, "option_type": "call", "maturity": 1.0, "notional": 1.0,
                        "assets": ["X"]},
            "modifiers": [{"type": "PayoffCap", "params": {"cap": 10.0}}],
        }
        fig = payoff_sparkline(spec, asset_names=["X"])
        y = np.array(fig.data[0].y)
        assert np.max(y) <= 10.0 + 1e-9

    def test_ko_modifier_adds_barrier_trace(self):
        spec = {
            "direction": "long",
            "instrument_type": "VanillaOption",
            "params": {"strike": 100.0, "option_type": "call", "maturity": 1.0, "notional": 1.0,
                        "assets": ["X"]},
            "modifiers": [{"type": "KnockOut", "params": {"barrier": 120.0, "direction": "up"}}],
        }
        fig = payoff_sparkline(spec, asset_names=["X"])
        assert len(fig.data) >= 2

    def test_accumulator_returns_figure(self):
        spec = {
            "direction": "long",
            "instrument_type": "AccumulatorDecumulator",
            "params": {"strike": 100.0, "maturity": 1.0, "notional": 1.0,
                        "leverage": 2.0, "side": "buy",
                        "schedule": [0.25, 0.5, 0.75, 1.0],
                        "assets": ["X"]},
            "modifiers": [],
        }
        fig = payoff_sparkline(spec, asset_names=["X"])
        assert fig is not None


class TestNewInstrumentFormulas:
    def test_single_barrier_formula(self):
        spec = {
            "direction": "long",
            "instrument_type": "SingleBarrier",
            "params": {
                "strike": 100.0,
                "barrier": 120.0,
                "option_type": "call",
                "barrier_direction": "up",
                "barrier_type": "out",
            },
            "modifiers": [],
        }
        f = payoff_formula(spec)
        assert "100" in f
        assert "120" in f

    def test_asian_formula(self):
        spec = {
            "direction": "long",
            "instrument_type": "AsianOption",
            "params": {
                "strike": 100.0,
                "option_type": "call",
                "average_type": "price",
            },
            "modifiers": [],
        }
        f = payoff_formula(spec)
        assert "avg" in f.lower() or "S" in f

    def test_cliquet_formula(self):
        spec = {
            "direction": "long",
            "instrument_type": "Cliquet",
            "params": {
                "local_cap": 0.05,
                "local_floor": 0.0,
                "global_floor": 0.0,
            },
            "modifiers": [],
        }
        f = payoff_formula(spec)
        assert "0.05" in f

    def test_range_accrual_formula(self):
        spec = {
            "direction": "long",
            "instrument_type": "RangeAccrual",
            "params": {
                "coupon_rate": 0.08,
            },
            "modifiers": [],
        }
        f = payoff_formula(spec)
        assert "0.08" in f

    def test_autocallable_formula(self):
        spec = {
            "direction": "long",
            "instrument_type": "Autocallable",
            "params": {
                "autocall_trigger": 1.0,
                "coupon_rate": 0.05,
                "put_strike": 0.7,
            },
            "modifiers": [],
        }
        f = payoff_formula(spec)
        assert len(f) > 0

    def test_tarf_formula(self):
        spec = {
            "direction": "long",
            "instrument_type": "TARF",
            "params": {
                "strike": 100.0,
                "target": 10.0,
                "leverage": 2.0,
                "side": "buy",
            },
            "modifiers": [],
        }
        f = payoff_formula(spec)
        assert "100" in f
        assert "10" in f

    def test_target_profit_modifier_formula(self):
        spec = {
            "direction": "long",
            "instrument_type": "VanillaOption",
            "params": {"strike": 100.0, "option_type": "call"},
            "modifiers": [{"type": "TargetProfit", "params": {"target": 15.0}}],
        }
        f = payoff_formula(spec)
        assert "15" in f


class TestSparklineGating:
    def test_asian_returns_none(self):
        spec = {
            "direction": "long",
            "instrument_type": "AsianOption",
            "params": {
                "strike": 100.0,
                "maturity": 1.0,
                "notional": 1.0,
                "average_type": "price",
                "option_type": "call",
                "assets": ["X"],
            },
            "modifiers": [],
        }
        result = payoff_sparkline(spec, asset_names=["X"])
        assert result is None

    def test_cliquet_returns_none(self):
        spec = {
            "direction": "long",
            "instrument_type": "Cliquet",
            "params": {
                "strike": 100.0,
                "maturity": 1.0,
                "notional": 1.0,
                "local_cap": 0.05,
                "local_floor": 0.0,
                "global_floor": 0.0,
                "assets": ["X"],
            },
            "modifiers": [],
        }
        result = payoff_sparkline(spec, asset_names=["X"])
        assert result is None

    def test_autocallable_returns_none(self):
        spec = {
            "direction": "long",
            "instrument_type": "Autocallable",
            "params": {
                "strike": 100.0,
                "maturity": 1.0,
                "notional": 1.0,
                "autocall_trigger": 1.0,
                "coupon_rate": 0.05,
                "put_strike": 0.7,
                "assets": ["X"],
            },
            "modifiers": [],
        }
        result = payoff_sparkline(spec, asset_names=["X"])
        assert result is None

    def test_vanilla_still_returns_figure(self):
        spec = {
            "direction": "long",
            "instrument_type": "VanillaOption",
            "params": {
                "strike": 100.0,
                "option_type": "call",
                "maturity": 1.0,
                "notional": 1.0,
                "assets": ["X"],
            },
            "modifiers": [],
        }
        result = payoff_sparkline(spec, asset_names=["X"])
        assert result is not None

    def test_empty_schedule_scenarios_do_not_warn(self, recwarn):
        spec = {
            "direction": "long",
            "instrument_type": "AsianOption",
            "params": {
                "strike": 100.0,
                "maturity": 1.0,
                "notional": 1.0,
                "average_type": "price",
                "option_type": "call",
                "schedule": [],
                "assets": ["X"],
            },
            "modifiers": [],
        }

        scenarios = compute_scenarios(spec, spot=100.0, notional=1.0)

        assert len(scenarios) == 3
        assert len(recwarn) == 0
