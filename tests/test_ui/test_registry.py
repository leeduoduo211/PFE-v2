import pytest
from ui.utils.registry import INSTRUMENT_REGISTRY, MODIFIER_REGISTRY


class TestInstrumentRegistry:
    def test_all_instruments_present(self):
        expected = {
            # European
            "VanillaCall", "VanillaPut", "Digital", "ContingentOption", "SingleBarrier",
            # Path-dependent
            "DoubleNoTouch", "ForwardStartingOption", "RestrikeOption",
            "AsianOption", "Cliquet", "RangeAccrual",
            # Multi-asset
            "DualDigital", "TripleDigital",
            "WorstOfCall", "WorstOfPut", "BestOfCall", "BestOfPut",
            # Periodic
            "Accumulator", "Decumulator", "Autocallable", "TARF",
        }
        assert set(INSTRUMENT_REGISTRY.keys()) == expected

    def test_vanilla_call_spec(self):
        spec = INSTRUMENT_REGISTRY["VanillaCall"]
        assert spec["n_assets"] == 1
        assert "strike" in [f["name"] for f in spec["fields"]]
        assert spec["cls"].__name__ == "VanillaCall"

    def test_accumulator_spec(self):
        spec = INSTRUMENT_REGISTRY["Accumulator"]
        field_names = [f["name"] for f in spec["fields"]]
        assert "strike" in field_names
        assert "leverage" in field_names
        assert "side" in field_names
        assert "schedule" in field_names

    def test_dual_digital_requires_two_assets(self):
        spec = INSTRUMENT_REGISTRY["DualDigital"]
        assert spec["n_assets"] == 2

    def test_worst_of_variable_assets(self):
        spec = INSTRUMENT_REGISTRY["WorstOfCall"]
        assert spec["n_assets"] == "2-5"

    def test_contingent_requires_two_assets(self):
        spec = INSTRUMENT_REGISTRY["ContingentOption"]
        assert spec["n_assets"] == 2

    def test_decumulator_defaults_to_sell(self):
        spec = INSTRUMENT_REGISTRY["Decumulator"]
        side_field = next(f for f in spec["fields"] if f["name"] == "side")
        assert side_field["default"] == "sell"


class TestModifierRegistry:
    def test_all_modifiers_present(self):
        expected = {
            # Barrier
            "KnockOut", "KnockIn", "RealizedVolKnockOut", "RealizedVolKnockIn",
            # Payoff shapers
            "PayoffCap", "PayoffFloor", "LeverageModifier",
            # Structural
            "ObservationSchedule", "TargetProfit",
        }
        assert set(MODIFIER_REGISTRY.keys()) == expected

    def test_knock_out_spec(self):
        spec = MODIFIER_REGISTRY["KnockOut"]
        field_names = [f["name"] for f in spec["fields"]]
        assert "barrier" in field_names
        assert "direction" in field_names

    def test_cap_spec(self):
        spec = MODIFIER_REGISTRY["PayoffCap"]
        assert len(spec["fields"]) == 1
        assert spec["fields"][0]["name"] == "cap"
