"""
Tests for ui.utils.product_content — the presentation-layer data module.

These tests verify structural completeness and consistency with the registry,
not rendering logic.
"""

import pytest
from ui.utils.registry import INSTRUMENT_REGISTRY, MODIFIER_REGISTRY
from ui.utils.product_content import (
    PRODUCT_SECTIONS,
    PRODUCT_DESCRIPTIONS,
    CATEGORY_COLORS,
    MODIFIER_SECTIONS,
    MODIFIER_GROUP_COLORS,
    PRODUCT_SCENARIOS,
    SPARKLINE_SUPPORTED,
)


# ---------------------------------------------------------------------------
# TestProductSections
# ---------------------------------------------------------------------------

class TestProductSections:
    def test_every_product_has_sections(self):
        """Every instrument key in the registry must have a sections entry."""
        for key in INSTRUMENT_REGISTRY:
            assert key in PRODUCT_SECTIONS, f"Missing sections for {key}"

    def test_every_field_assigned_to_section(self):
        """Every field in the registry must appear in exactly one section."""
        for key, spec in INSTRUMENT_REGISTRY.items():
            registry_fields = {f["name"] for f in spec["fields"]}
            section_fields = []
            for section in PRODUCT_SECTIONS[key]:
                for field in section["fields"]:
                    section_fields.append(field)
            assert len(section_fields) == len(set(section_fields)), (
                f"{key}: duplicate field assignments detected in sections: "
                f"{[f for f in section_fields if section_fields.count(f) > 1]}"
            )
            assert registry_fields == set(section_fields), (
                f"{key}: registry fields {registry_fields} != "
                f"section fields {set(section_fields)}"
            )

    def test_sections_have_required_keys(self):
        """Each section dict must have label, color, and fields keys."""
        for key, sections in PRODUCT_SECTIONS.items():
            assert isinstance(sections, list), f"{key}: sections must be a list"
            assert len(sections) >= 1, f"{key}: must have at least one section"
            for i, section in enumerate(sections):
                assert "label" in section, f"{key}[{i}]: missing 'label'"
                assert "color" in section, f"{key}[{i}]: missing 'color'"
                assert "fields" in section, f"{key}[{i}]: missing 'fields'"
                assert isinstance(section["fields"], list), (
                    f"{key}[{i}]: 'fields' must be a list"
                )


# ---------------------------------------------------------------------------
# TestProductDescriptions
# ---------------------------------------------------------------------------

class TestProductDescriptions:
    def test_every_product_has_description(self):
        """Every instrument key must have a description entry."""
        for key in INSTRUMENT_REGISTRY:
            assert key in PRODUCT_DESCRIPTIONS, f"Missing description for {key}"

    def test_descriptions_are_nonempty(self):
        """All descriptions must be non-empty strings."""
        for key, desc in PRODUCT_DESCRIPTIONS.items():
            assert isinstance(desc, str), f"{key}: description must be a string"
            assert len(desc.strip()) > 0, f"{key}: description must be non-empty"


# ---------------------------------------------------------------------------
# TestCategoryColors
# ---------------------------------------------------------------------------

class TestCategoryColors:
    def test_category_colors_complete(self):
        """CATEGORY_COLORS must cover all four categories used in the registry."""
        expected_categories = {"European", "Path-dependent", "Multi-asset", "Periodic"}
        assert set(CATEGORY_COLORS.keys()) == expected_categories
        for cat, color in CATEGORY_COLORS.items():
            assert isinstance(color, str) and color.startswith("#"), (
                f"{cat}: color must be a hex string starting with #"
            )


# ---------------------------------------------------------------------------
# TestModifierSections
# ---------------------------------------------------------------------------

class TestModifierSections:
    def test_modifier_sections_complete(self):
        """Every modifier key in the registry must appear in MODIFIER_SECTIONS."""
        for key in MODIFIER_REGISTRY:
            assert key in MODIFIER_SECTIONS, f"Missing modifier section for {key}"

    def test_modifier_fields_assigned(self):
        """All fields in the modifier registry must appear in core/obs/extra lists."""
        for key, spec in MODIFIER_REGISTRY.items():
            registry_fields = {f["name"] for f in spec["fields"]}
            ms = MODIFIER_SECTIONS[key]
            section_fields = (
                set(ms.get("core_fields", []))
                | set(ms.get("observation_fields", []))
                | set(ms.get("extra_fields", []))
            )
            assert registry_fields == section_fields, (
                f"{key}: registry fields {registry_fields} != "
                f"modifier section fields {section_fields}"
            )

    def test_modifier_groups_have_colors(self):
        """Every group referenced in MODIFIER_SECTIONS must exist in MODIFIER_GROUP_COLORS."""
        for key, ms in MODIFIER_SECTIONS.items():
            group = ms.get("group")
            assert group is not None, f"{key}: missing 'group'"
            assert group in MODIFIER_GROUP_COLORS, (
                f"{key}: group '{group}' not in MODIFIER_GROUP_COLORS"
            )


# ---------------------------------------------------------------------------
# TestSparklineSupported
# ---------------------------------------------------------------------------

_COMPLEX_TYPES = {"AsianOption", "Cliquet", "RangeAccrual", "Autocallable", "TARF"}

# Note: VanillaOption replaces VanillaCall/VanillaPut,
# WorstOfOption replaces WorstOfCall/WorstOfPut, etc.


class TestSparklineSupported:
    def test_subset_of_registry(self):
        """SPARKLINE_SUPPORTED must be a subset of instrument registry keys."""
        assert SPARKLINE_SUPPORTED <= set(INSTRUMENT_REGISTRY.keys()), (
            "SPARKLINE_SUPPORTED contains keys not in the registry"
        )

    def test_complex_types_excluded(self):
        """Complex schedule-heavy types must not be in SPARKLINE_SUPPORTED."""
        for key in _COMPLEX_TYPES:
            assert key not in SPARKLINE_SUPPORTED, (
                f"{key} should be excluded from SPARKLINE_SUPPORTED"
            )


# ---------------------------------------------------------------------------
# TestProductScenarios
# ---------------------------------------------------------------------------

class TestProductScenarios:
    def test_scenarios_structure(self):
        """Each product's scenarios must be a list of dicts with label and description."""
        required_products = {
            "VanillaOption", "SingleBarrier", "AsianOption",
            "Cliquet", "RangeAccrual", "Autocallable", "TARF",
            "AccumulatorDecumulator", "DoubleNoTouch",
            "WorstOfOption",
        }
        for key in required_products:
            assert key in PRODUCT_SCENARIOS, f"Missing scenarios for {key}"
            scenarios = PRODUCT_SCENARIOS[key]
            assert isinstance(scenarios, list), f"{key}: scenarios must be a list"
            assert len(scenarios) >= 1, f"{key}: must have at least one scenario"
            for i, scenario in enumerate(scenarios):
                assert "label" in scenario, f"{key}[{i}]: missing 'label'"
                assert "description" in scenario, f"{key}[{i}]: missing 'description'"
                assert isinstance(scenario["label"], str) and scenario["label"].strip(), (
                    f"{key}[{i}]: 'label' must be a non-empty string"
                )
                assert isinstance(scenario["description"], str) and scenario["description"].strip(), (
                    f"{key}[{i}]: 'description' must be a non-empty string"
                )
