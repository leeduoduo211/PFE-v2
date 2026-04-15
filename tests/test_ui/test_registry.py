import pytest
from ui.utils.registry import INSTRUMENT_REGISTRY, MODIFIER_REGISTRY


class TestInstrumentRegistry:
    def test_all_instruments_present(self):
        expected = {
            # European
            "VanillaOption", "Digital", "ContingentOption", "SingleBarrier",
            # Path-dependent
            "DoubleNoTouch", "ForwardStartingOption", "RestrikeOption",
            "AsianOption", "Cliquet", "RangeAccrual",
            # Multi-asset
            "DualDigital", "TripleDigital",
            "WorstOfOption", "BestOfOption", "Dispersion",
            # Periodic
            "AccumulatorDecumulator", "Autocallable", "TARF",
        }
        assert set(INSTRUMENT_REGISTRY.keys()) == expected

    def test_registry_count(self):
        assert len(INSTRUMENT_REGISTRY) == 18

    def test_vanilla_option_spec(self):
        spec = INSTRUMENT_REGISTRY["VanillaOption"]
        assert spec["n_assets"] == 1
        field_names = [f["name"] for f in spec["fields"]]
        assert "strike" in field_names
        assert "option_type" in field_names
        assert spec["cls"].__name__ == "VanillaOption"

    def test_accumulator_decumulator_spec(self):
        spec = INSTRUMENT_REGISTRY["AccumulatorDecumulator"]
        field_names = [f["name"] for f in spec["fields"]]
        assert "strike" in field_names
        assert "leverage" in field_names
        assert "side" in field_names
        assert "schedule" in field_names

    def test_dual_digital_requires_two_assets(self):
        spec = INSTRUMENT_REGISTRY["DualDigital"]
        assert spec["n_assets"] == 2

    def test_worst_of_variable_assets(self):
        spec = INSTRUMENT_REGISTRY["WorstOfOption"]
        assert spec["n_assets"] == "2-5"

    def test_contingent_requires_two_assets(self):
        spec = INSTRUMENT_REGISTRY["ContingentOption"]
        assert spec["n_assets"] == 2

    def test_dispersion_spec(self):
        spec = INSTRUMENT_REGISTRY["Dispersion"]
        assert spec["n_assets"] == "2-5"
        field_names = [f["name"] for f in spec["fields"]]
        assert "component_types" in field_names
        assert "strikes" in field_names
        assert "weights" in field_names
        assert "basket_strike" in field_names
        assert "basket_type" in field_names


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
