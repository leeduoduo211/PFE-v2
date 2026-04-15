# UI Term-Sheet & Product-Specific Input — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add product-specific grouped inputs in the trade builder, a read-only term-sheet view in the portfolio table, and full content coverage (term-sheet text, formulas, scenarios) for all 21 instruments and 9 modifiers.

**Architecture:** A new `product_content.py` data module defines per-product section groupings, descriptions, modifier section config, product-specific scenarios, and sparkline eligibility. Rendering components (`trade_builder.py`, `term_sheet.py`, `portfolio_table.py`) consume this data layer. Content modules (`trade_economics.py`, `payoff_display.py`) get new builders for the 6 new instruments and TargetProfit modifier.

**Tech Stack:** Python 3.9+, Streamlit, Plotly, NumPy

**Spec:** `docs/specs/2026-04-15-ui-term-sheet-design.md`

---

## File Structure

### New files

| File | Responsibility |
|---|---|
| `ui/utils/product_content.py` | Data layer: `PRODUCT_SECTIONS`, `CATEGORY_COLORS`, `PRODUCT_DESCRIPTIONS`, `MODIFIER_GROUP_COLORS`, `MODIFIER_SECTIONS`, `PRODUCT_SCENARIOS`, `SPARKLINE_SUPPORTED` |
| `ui/components/term_sheet.py` | Read-only term-sheet renderer: `render_term_sheet()` |
| `tests/test_ui/test_product_content.py` | Completeness tests: every product has sections, descriptions, fields assigned, modifiers covered |
| `tests/test_ui/test_trade_economics.py` | Coverage tests: every instrument has a term-sheet builder, every modifier has economics text |
| `tests/test_ui/test_term_sheet.py` | Smoke tests: `render_term_sheet()` doesn't raise for each product |

### Modified files

| File | Changes |
|---|---|
| `ui/components/trade_builder.py` | Import product_content; add `_render_section()` + `_render_modifier_styled()` + product header; replace flat field loop with section-aware rendering; replace modifier expanders with styled sections; handle `None` sparkline return |
| `ui/components/trade_economics.py` | Add 6 `_ts_*` functions for new instruments; add `_obs_style_text()` helper; update `_MODIFIER_ECONOMICS` for barrier observation styles + TargetProfit; extend `compute_scenarios()` for product-specific scenarios |
| `ui/components/payoff_display.py` | Add 6 formula entries to `_BASE_FORMULAS`; add TargetProfit to `_MODIFIER_FORMULAS`; update `_PATH_DEPENDENT_TYPES`/`_PATH_DEPENDENT_MODIFIERS`; add `SPARKLINE_SUPPORTED` set; modify `payoff_sparkline()` to return `None` for unsupported types |
| `ui/components/portfolio_table.py` | Replace expander content with `render_term_sheet()` call; handle `None` sparkline |
| `tests/test_ui/test_payoff_display.py` | Add formula tests for 6 new instruments; add sparkline `None` return test for excluded types |

---

## Task 1: Product Content Data Module

**Files:**
- Create: `ui/utils/product_content.py`
- Create: `tests/test_ui/test_product_content.py`

This task builds the data layer that all subsequent tasks depend on.

- [ ] **Step 1: Write the completeness tests**

Create `tests/test_ui/test_product_content.py`:

```python
import pytest
from ui.utils.registry import INSTRUMENT_REGISTRY, MODIFIER_REGISTRY
from ui.utils.product_content import (
    PRODUCT_SECTIONS,
    CATEGORY_COLORS,
    PRODUCT_DESCRIPTIONS,
    MODIFIER_GROUP_COLORS,
    MODIFIER_SECTIONS,
    PRODUCT_SCENARIOS,
    SPARKLINE_SUPPORTED,
)


class TestProductSections:
    def test_every_product_has_sections(self):
        """Every registered instrument has a PRODUCT_SECTIONS entry."""
        for key in INSTRUMENT_REGISTRY:
            assert key in PRODUCT_SECTIONS, f"Missing PRODUCT_SECTIONS for {key}"

    def test_every_field_assigned_to_section(self):
        """Every field in the registry appears in exactly one section."""
        for key, spec in INSTRUMENT_REGISTRY.items():
            section_fields = []
            for section in PRODUCT_SECTIONS[key]:
                section_fields.extend(section["fields"])
            registry_fields = [f["name"] for f in spec["fields"]]
            assert set(section_fields) == set(registry_fields), (
                f"{key}: section fields {set(section_fields)} != registry fields {set(registry_fields)}"
            )

    def test_sections_have_required_keys(self):
        """Each section dict has label, color, and fields."""
        for key, sections in PRODUCT_SECTIONS.items():
            for i, section in enumerate(sections):
                assert "label" in section, f"{key} section {i} missing 'label'"
                assert "color" in section, f"{key} section {i} missing 'color'"
                assert "fields" in section, f"{key} section {i} missing 'fields'"


class TestProductDescriptions:
    def test_every_product_has_description(self):
        for key in INSTRUMENT_REGISTRY:
            assert key in PRODUCT_DESCRIPTIONS, f"Missing description for {key}"

    def test_descriptions_are_nonempty(self):
        for key, desc in PRODUCT_DESCRIPTIONS.items():
            assert len(desc) > 10, f"Description for {key} too short"


class TestCategoryColors:
    def test_category_colors_complete(self):
        categories = {
            spec.get("category")
            for spec in INSTRUMENT_REGISTRY.values()
            if spec.get("category")
        }
        for cat in categories:
            assert cat in CATEGORY_COLORS, f"Missing color for category {cat}"


class TestModifierSections:
    def test_modifier_sections_complete(self):
        for key in MODIFIER_REGISTRY:
            assert key in MODIFIER_SECTIONS, f"Missing MODIFIER_SECTIONS for {key}"

    def test_modifier_fields_assigned(self):
        """Every modifier field appears in core, observation, or extra."""
        for key, spec in MODIFIER_REGISTRY.items():
            section = MODIFIER_SECTIONS[key]
            all_assigned = (
                section["core_fields"]
                + section.get("observation_fields", [])
                + section.get("extra_fields", [])
            )
            registry_fields = [f["name"] for f in spec["fields"]]
            assert set(all_assigned) == set(registry_fields), (
                f"{key}: assigned {set(all_assigned)} != registry {set(registry_fields)}"
            )

    def test_modifier_groups_have_colors(self):
        for key, section in MODIFIER_SECTIONS.items():
            group = section["group"]
            assert group in MODIFIER_GROUP_COLORS, f"Missing group color for {group}"


class TestSparklineSupported:
    def test_subset_of_registry(self):
        assert SPARKLINE_SUPPORTED.issubset(set(INSTRUMENT_REGISTRY.keys()))

    def test_complex_types_excluded(self):
        excluded = {"AsianOption", "Cliquet", "RangeAccrual", "Autocallable", "TARF"}
        for t in excluded:
            assert t not in SPARKLINE_SUPPORTED, f"{t} should not be in SPARKLINE_SUPPORTED"


class TestProductScenarios:
    def test_scenarios_structure(self):
        for key, scenarios in PRODUCT_SCENARIOS.items():
            assert key in INSTRUMENT_REGISTRY, f"Scenario for unknown product {key}"
            for s in scenarios:
                assert "label" in s, f"Scenario for {key} missing 'label'"
                assert "description" in s, f"Scenario for {key} missing 'description'"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest tests/test_ui/test_product_content.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'ui.utils.product_content'`

- [ ] **Step 3: Create the product content module**

Create `ui/utils/product_content.py` with the full content from spec sections 4.1–4.6. The file should contain:

```python
"""Product-specific content data for UI rendering.

This module is the single source of truth for how products are grouped,
labeled, and described in the trade builder and term-sheet views.
It is pure data — no rendering logic.
"""

# --- Section 4.1: Section Groupings ---
PRODUCT_SECTIONS = {
    # ── European ──────────────────────────────────────────────
    "VanillaCall": [
        {"label": "Option Terms", "color": "#3b82f6", "fields": ["strike"]},
    ],
    "VanillaPut": [
        {"label": "Option Terms", "color": "#3b82f6", "fields": ["strike"]},
    ],
    "Digital": [
        {"label": "Option Terms", "color": "#3b82f6", "fields": ["strike", "option_type"]},
    ],
    "ContingentOption": [
        {
            "label": "Trigger Condition",
            "color": "#f59e0b",
            "fields": ["trigger_asset_idx", "trigger_barrier", "trigger_direction"],
            "help": "The trigger asset acts as an on/off switch for the payoff",
        },
        {
            "label": "Target Payoff",
            "color": "#3b82f6",
            "fields": ["target_asset_idx", "target_strike", "target_type"],
            "help": "Vanilla payoff computed on the target asset if trigger fires",
        },
    ],
    "SingleBarrier": [
        {
            "label": "Option Terms",
            "color": "#3b82f6",
            "fields": ["strike", "option_type"],
        },
        {
            "label": "Barrier Condition (at expiry only)",
            "color": "#f59e0b",
            "fields": ["barrier", "barrier_direction", "barrier_type"],
            "help": "Checked at maturity only — distinct from path-dependent KO/KI modifiers",
        },
    ],
    # ── Path-dependent ────────────────────────────────────────
    "DoubleNoTouch": [
        {
            "label": "Barrier Corridor",
            "color": "#22c55e",
            "fields": ["lower", "upper"],
            "help": "Pays if spot stays strictly inside the corridor for the entire life",
        },
    ],
    "ForwardStartingOption": [
        {
            "label": "Forward Start Terms",
            "color": "#22c55e",
            "fields": ["start_time", "option_type"],
            "help": "Strike fixed to spot at start time",
        },
    ],
    "RestrikeOption": [
        {
            "label": "Restrike Terms",
            "color": "#22c55e",
            "fields": ["reset_time", "option_type"],
            "help": "Strike resets to spot at reset time",
        },
    ],
    "AsianOption": [
        {
            "label": "Option Terms",
            "color": "#22c55e",
            "fields": ["strike", "option_type", "average_type"],
            "help": "Price averaging: average vs fixed strike. Strike averaging: terminal vs average strike.",
        },
        {
            "label": "Averaging Schedule",
            "color": "#f59e0b",
            "fields": ["schedule"],
        },
    ],
    "Cliquet": [
        {
            "label": "Return Clipping",
            "color": "#22c55e",
            "fields": ["local_cap", "local_floor"],
            "help": "Each period's return is clipped to [floor, cap] before summing",
        },
        {
            "label": "Global Protection",
            "color": "#ef4444",
            "fields": ["global_floor"],
            "help": "Minimum total payoff across all periods",
        },
        {
            "label": "Reset Schedule",
            "color": "#f59e0b",
            "fields": ["schedule"],
        },
    ],
    "RangeAccrual": [
        {
            "label": "Accrual Range",
            "color": "#22c55e",
            "fields": ["lower", "upper"],
            "help": "Coupon accrues proportional to observations where spot is inside the range",
        },
        {
            "label": "Coupon",
            "color": "#3b82f6",
            "fields": ["coupon_rate"],
        },
        {
            "label": "Observation Schedule",
            "color": "#f59e0b",
            "fields": ["schedule"],
        },
    ],
    # ── Multi-asset ───────────────────────────────────────────
    "DualDigital": [
        {"label": "Barrier Conditions", "color": "#8b5cf6", "fields": ["strikes", "option_types"]},
    ],
    "TripleDigital": [
        {"label": "Barrier Conditions", "color": "#8b5cf6", "fields": ["strikes", "option_types"]},
    ],
    "WorstOfCall": [
        {"label": "Basket Terms", "color": "#8b5cf6", "fields": ["strikes"]},
    ],
    "WorstOfPut": [
        {"label": "Basket Terms", "color": "#8b5cf6", "fields": ["strikes"]},
    ],
    "BestOfCall": [
        {"label": "Basket Terms", "color": "#8b5cf6", "fields": ["strikes"]},
    ],
    "BestOfPut": [
        {"label": "Basket Terms", "color": "#8b5cf6", "fields": ["strikes"]},
    ],
    # ── Periodic ──────────────────────────────────────────────
    "Accumulator": [
        {
            "label": "Accumulation Terms",
            "color": "#f59e0b",
            "fields": ["strike", "leverage", "side"],
            "help": "Buys at strike each period; leverage multiplies quantity when spot is unfavorable",
        },
        {
            "label": "Observation Schedule",
            "color": "#f59e0b",
            "fields": ["schedule"],
        },
    ],
    "Decumulator": [
        {
            "label": "Decumulation Terms",
            "color": "#f59e0b",
            "fields": ["strike", "leverage", "side"],
            "help": "Sells at strike each period; leverage multiplies quantity when spot is unfavorable",
        },
        {
            "label": "Observation Schedule",
            "color": "#f59e0b",
            "fields": ["schedule"],
        },
    ],
    "Autocallable": [
        {
            "label": "Autocall Terms",
            "color": "#6366f1",
            "fields": ["autocall_trigger", "coupon_rate"],
            "help": "Redeems early if worst-of performance >= trigger",
        },
        {
            "label": "Downside Protection",
            "color": "#ef4444",
            "fields": ["put_strike"],
            "help": "Below put strike at maturity, loss = worst_perf - 1.0",
        },
        {
            "label": "Observation Schedule",
            "color": "#f59e0b",
            "fields": ["schedule"],
        },
    ],
    "TARF": [
        {
            "label": "Forward Terms",
            "color": "#f59e0b",
            "fields": ["strike", "leverage", "side"],
            "help": "Periodic forward with leverage on unfavorable side",
        },
        {
            "label": "Target Redemption",
            "color": "#ef4444",
            "fields": ["target"],
            "help": "Terminates when cumulative profit reaches target; partial fill on final fixing",
        },
        {
            "label": "Fixing Schedule",
            "color": "#f59e0b",
            "fields": ["schedule"],
        },
    ],
}

# --- Section 4.2: Category Colors ---
CATEGORY_COLORS = {
    "European": "#3b82f6",
    "Path-dependent": "#22c55e",
    "Multi-asset": "#8b5cf6",
    "Periodic": "#f59e0b",
}

# --- Section 4.3: Product Descriptions ---
PRODUCT_DESCRIPTIONS = {
    "VanillaCall": "European call option — pays max(S - K, 0) at maturity.",
    "VanillaPut": "European put option — pays max(K - S, 0) at maturity.",
    "Digital": "Binary option — pays fixed amount if spot finishes above/below strike.",
    "ContingentOption": "Vanilla payoff on one asset, conditional on a second asset breaching a trigger.",
    "SingleBarrier": "European barrier option — barrier checked at expiry only, not along the path.",
    "DoubleNoTouch": "Pays fixed amount if spot stays within a corridor for the entire life.",
    "ForwardStartingOption": "Option whose strike is set to spot at a future date.",
    "RestrikeOption": "Option whose strike resets to spot at a specified time.",
    "AsianOption": "Arithmetic average option — averaging reduces volatility exposure.",
    "Cliquet": "Periodic reset option summing clipped local returns with global floor protection.",
    "RangeAccrual": "Pays coupon proportional to time spot stays within a defined range.",
    "DualDigital": "Joint digital — pays only if both assets satisfy their barrier conditions.",
    "TripleDigital": "Joint digital on three assets — all conditions must be met simultaneously.",
    "WorstOfCall": "Call on the worst performer in a basket — long is short dispersion.",
    "WorstOfPut": "Put on the worst performer — the downside wrapper inside autocallable notes.",
    "BestOfCall": "Call on the best performer — automatically rotates into strongest leg.",
    "BestOfPut": "Put on the best performer — requires all assets to fall below strike.",
    "Accumulator": "Periodic forward purchase with leverage on unfavorable side.",
    "Decumulator": "Periodic forward sale with leverage on unfavorable side.",
    "Autocallable": "Early redemption note with coupon accrual and worst-of downside at maturity.",
    "TARF": "Target accrual redemption forward — terminates when cumulative profit hits target.",
}

# --- Section 4.4: Modifier Section Config ---
MODIFIER_GROUP_COLORS = {
    "Barrier": {"color": "#f59e0b", "badge_bg": "#fef3c7", "badge_text": "#92400e"},
    "Payoff shaper": {"color": "#8b5cf6", "badge_bg": "#ede9fe", "badge_text": "#6d28d9"},
    "Structural": {"color": "#3b82f6", "badge_bg": "#dbeafe", "badge_text": "#1e40af"},
}

MODIFIER_SECTIONS = {
    "KnockOut": {
        "group": "Barrier",
        "core_fields": ["barrier", "direction", "asset_idx"],
        "observation_fields": ["observation_style", "observation_dates", "window_start", "window_end"],
        "extra_fields": ["rebate"],
    },
    "KnockIn": {
        "group": "Barrier",
        "core_fields": ["barrier", "direction", "asset_idx"],
        "observation_fields": ["observation_style", "observation_dates", "window_start", "window_end"],
        "extra_fields": [],
    },
    "RealizedVolKnockOut": {
        "group": "Barrier",
        "core_fields": ["vol_barrier", "direction", "asset_idx", "annualization_factor"],
        "observation_fields": ["observation_style", "observation_dates", "window_start", "window_end"],
        "extra_fields": [],
    },
    "RealizedVolKnockIn": {
        "group": "Barrier",
        "core_fields": ["vol_barrier", "direction", "asset_idx", "annualization_factor"],
        "observation_fields": ["observation_style", "observation_dates", "window_start", "window_end"],
        "extra_fields": [],
    },
    "PayoffCap": {
        "group": "Payoff shaper",
        "core_fields": ["cap"],
        "observation_fields": [],
        "extra_fields": [],
    },
    "PayoffFloor": {
        "group": "Payoff shaper",
        "core_fields": ["floor"],
        "observation_fields": [],
        "extra_fields": [],
    },
    "LeverageModifier": {
        "group": "Payoff shaper",
        "core_fields": ["threshold", "leverage"],
        "observation_fields": [],
        "extra_fields": [],
    },
    "ObservationSchedule": {
        "group": "Structural",
        "core_fields": ["dates"],
        "observation_fields": [],
        "extra_fields": [],
    },
    "TargetProfit": {
        "group": "Structural",
        "core_fields": ["target", "partial_fill"],
        "observation_fields": [],
        "extra_fields": [],
    },
}

# --- Section 4.5: Product-Specific Scenarios ---
PRODUCT_SCENARIOS = {
    "VanillaCall": [
        {"label": "Deep ITM", "spot_mult": 1.5, "description": "Spot 50% above strike"},
    ],
    "VanillaPut": [
        {"label": "Deep ITM", "spot_mult": 0.5, "description": "Spot 50% below strike"},
    ],
    "SingleBarrier": [
        {"label": "Barrier met at expiry", "spot_mult": 1.3, "description": "S(T) above barrier — in-barrier activates / out-barrier extinguishes"},
        {"label": "Barrier not met", "spot_mult": 1.1, "description": "S(T) below barrier — opposite outcome"},
    ],
    "AsianOption": [
        {"label": "Averaging dampens spike", "description": "Volatile path averages to near-strike despite high terminal"},
    ],
    "Cliquet": [
        {"label": "All periods hit cap", "description": "Steady rise — each period capped at local_cap"},
        {"label": "Single large drop", "description": "One period drops sharply but local floor limits damage"},
    ],
    "RangeAccrual": [
        {"label": "Full coupon", "description": "Spot stays in range for all observations"},
        {"label": "Breakout early", "description": "Spot exits range quickly — minimal accrual"},
    ],
    "Autocallable": [
        {"label": "Called at obs 2", "description": "All assets >= trigger at 2nd observation — receives 2 x coupon"},
        {"label": "Not called, worst at 60%", "description": "Worst performer below put strike — loss = worst_perf - 1"},
    ],
    "TARF": [
        {"label": "Target hit at obs 5", "description": "Cumulative profit reaches target — partial fill, trade terminates"},
        {"label": "Never hit, spot drops", "description": "Leverage-amplified losses accumulate without target cap"},
    ],
    "Accumulator": [
        {"label": "Leverage trap", "description": "Spot drops 30% — forced buying at leverage x quantity"},
    ],
    "Decumulator": [
        {"label": "Rally trap", "description": "Spot rises 30% — forced selling at leverage x quantity"},
    ],
    "DoubleNoTouch": [
        {"label": "Touch lower barrier", "description": "Spot touches lower — entire payoff extinguished"},
    ],
    "WorstOfCall": [
        {"label": "One leg collapses", "description": "Best asset +40% but worst asset -5% — payoff is zero"},
    ],
    "WorstOfPut": [
        {"label": "Correlated crash", "description": "All assets fall 30% — worst-of put payoff is large"},
    ],
}

# --- Section 4.6: Sparkline Eligibility ---
SPARKLINE_SUPPORTED = {
    "VanillaCall", "VanillaPut", "Digital", "SingleBarrier", "ContingentOption",
    "DoubleNoTouch", "ForwardStartingOption", "RestrikeOption",
    "WorstOfCall", "WorstOfPut", "BestOfCall", "BestOfPut",
    "DualDigital", "TripleDigital",
    "Accumulator", "Decumulator",
}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m pytest tests/test_ui/test_product_content.py -v`
Expected: All 12 tests PASS

- [ ] **Step 5: Commit**

```bash
git add ui/utils/product_content.py tests/test_ui/test_product_content.py
git commit -m "feat(ui): add product content data module with completeness tests"
```

---

## Task 2: Payoff Display — New Formulas and Sparkline Gating

**Files:**
- Modify: `ui/components/payoff_display.py:15-81` (formula dicts and path-dependent sets)
- Modify: `ui/components/payoff_display.py:153-230` (`payoff_sparkline()`)
- Modify: `tests/test_ui/test_payoff_display.py`

- [ ] **Step 1: Write failing tests for new formulas and sparkline gating**

Add to `tests/test_ui/test_payoff_display.py`:

```python
class TestNewInstrumentFormulas:
    """Formula coverage for the 6 new instruments."""

    def test_single_barrier_formula(self):
        spec = {
            "direction": "long",
            "instrument_type": "SingleBarrier",
            "params": {"strike": 100.0, "option_type": "call",
                       "barrier": 120.0, "barrier_direction": "up", "barrier_type": "out"},
            "modifiers": [],
        }
        f = payoff_formula(spec)
        assert "100" in f
        assert "120" in f

    def test_asian_formula(self):
        spec = {
            "direction": "long",
            "instrument_type": "AsianOption",
            "params": {"strike": 100.0, "option_type": "call", "average_type": "price"},
            "modifiers": [],
        }
        f = payoff_formula(spec)
        assert "avg" in f.lower() or "S" in f

    def test_cliquet_formula(self):
        spec = {
            "direction": "long",
            "instrument_type": "Cliquet",
            "params": {"local_cap": 0.05, "local_floor": 0.0, "global_floor": 0.0},
            "modifiers": [],
        }
        f = payoff_formula(spec)
        assert "0.05" in f

    def test_range_accrual_formula(self):
        spec = {
            "direction": "long",
            "instrument_type": "RangeAccrual",
            "params": {"coupon_rate": 0.08, "lower": 90.0, "upper": 110.0},
            "modifiers": [],
        }
        f = payoff_formula(spec)
        assert "0.08" in f

    def test_autocallable_formula(self):
        spec = {
            "direction": "long",
            "instrument_type": "Autocallable",
            "params": {"autocall_trigger": 1.0, "coupon_rate": 0.05, "put_strike": 0.7},
            "modifiers": [],
        }
        f = payoff_formula(spec)
        assert len(f) > 0

    def test_tarf_formula(self):
        spec = {
            "direction": "long",
            "instrument_type": "TARF",
            "params": {"strike": 100.0, "target": 10.0, "leverage": 2.0, "side": "buy"},
            "modifiers": [],
        }
        f = payoff_formula(spec)
        assert "100" in f
        assert "10" in f

    def test_target_profit_modifier_formula(self):
        spec = {
            "direction": "long",
            "instrument_type": "VanillaCall",
            "params": {"strike": 100.0},
            "modifiers": [{"type": "TargetProfit", "params": {"target": 15.0}}],
        }
        f = payoff_formula(spec)
        assert "15" in f


class TestSparklineGating:
    """Sparkline returns None for complex path-dependent types."""

    def test_asian_returns_none(self):
        spec = {
            "direction": "long",
            "instrument_type": "AsianOption",
            "params": {"strike": 100.0, "option_type": "call",
                       "average_type": "price", "maturity": 1.0,
                       "notional": 1.0, "schedule": [0.25, 0.5, 0.75, 1.0],
                       "assets": ["X"]},
            "modifiers": [],
        }
        result = payoff_sparkline(spec, asset_names=["X"])
        assert result is None

    def test_cliquet_returns_none(self):
        spec = {
            "direction": "long",
            "instrument_type": "Cliquet",
            "params": {"local_cap": 0.05, "local_floor": 0.0, "global_floor": 0.0,
                       "maturity": 1.0, "notional": 1.0,
                       "schedule": [0.25, 0.5, 0.75, 1.0], "assets": ["X"]},
            "modifiers": [],
        }
        result = payoff_sparkline(spec, asset_names=["X"])
        assert result is None

    def test_autocallable_returns_none(self):
        spec = {
            "direction": "long",
            "instrument_type": "Autocallable",
            "params": {"autocall_trigger": 1.0, "coupon_rate": 0.05,
                       "put_strike": 0.7, "maturity": 1.0, "notional": 1.0,
                       "schedule": [0.25, 0.5, 0.75, 1.0], "assets": ["X"]},
            "modifiers": [],
        }
        result = payoff_sparkline(spec, asset_names=["X"])
        assert result is None

    def test_vanilla_still_returns_figure(self):
        spec = {
            "direction": "long",
            "instrument_type": "VanillaCall",
            "params": {"strike": 100.0, "maturity": 1.0, "notional": 1.0,
                       "assets": ["X"]},
            "modifiers": [],
        }
        result = payoff_sparkline(spec, asset_names=["X"])
        assert result is not None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest tests/test_ui/test_payoff_display.py::TestNewInstrumentFormulas -v`
Expected: FAIL (formulas not yet in `_BASE_FORMULAS`)

Run: `python3 -m pytest tests/test_ui/test_payoff_display.py::TestSparklineGating -v`
Expected: FAIL (sparkline returns a Figure, not None, for excluded types)

- [ ] **Step 3: Add new formulas to `_BASE_FORMULAS` and `_MODIFIER_FORMULAS`**

In `ui/components/payoff_display.py`, add to `_BASE_FORMULAS` dict (after `"ContingentOption"` entry):

```python
    "SingleBarrier": lambda p: (
        f"max(S {'−' if p.get('option_type','call')=='call' else '− S, '}"
        f"{p.get('strike',0):.4g}"
        f"{', 0)' if p.get('option_type','call')=='call' else ''}"
        f" · 1{{S(T) {'>' if p.get('barrier_direction','up')=='up' else '<'} {p.get('barrier',0):.4g}}}"
    ),
    "AsianOption": lambda p: (
        f"max({'avg(S)' if p.get('average_type','price')=='price' else 'S(T)'}"
        f" − {'K' if p.get('average_type','price')=='price' else 'avg(S)'}, 0)"
        f" [{p.get('option_type','call')}]"
    ),
    "Cliquet": lambda p: (
        f"N · max(Σ clip(rᵢ, {p.get('local_floor',0):.4g}, {p.get('local_cap',0):.4g}), "
        f"{p.get('global_floor',0):.4g})"
    ),
    "RangeAccrual": lambda p: (
        f"N · (days_in / total) · {p.get('coupon_rate',0):.4g}"
    ),
    "Autocallable": lambda p: (
        f"if called: coupon × i | if not: max(worst_perf − 1, put_strike − 1)"
    ),
    "TARF": lambda p: (
        f"Σ units · (S − {p.get('strike',0):.4g}) [target={p.get('target',0):.4g}]"
    ),
```

Add to `_MODIFIER_FORMULAS`:

```python
    "TargetProfit": lambda p, inner: f"min({inner}, {p.get('target',0):.4g})",
```

- [ ] **Step 4: Update path-dependent sets**

In `ui/components/payoff_display.py`, update `_PATH_DEPENDENT_TYPES`:

```python
_PATH_DEPENDENT_TYPES = {
    "Accumulator", "Decumulator", "DoubleNoTouch",
    "ForwardStartingOption", "RestrikeOption",
    "AsianOption", "Cliquet", "RangeAccrual",
    "Autocallable", "TARF",
}
```

Update `_PATH_DEPENDENT_MODIFIERS`:

```python
_PATH_DEPENDENT_MODIFIERS = {
    "KnockOut", "KnockIn", "RealizedVolKnockOut", "RealizedVolKnockIn",
    "TargetProfit",
}
```

- [ ] **Step 5: Add sparkline gating**

Import `SPARKLINE_SUPPORTED` from `product_content` at top of file:

```python
from ui.utils.product_content import SPARKLINE_SUPPORTED
```

Modify `payoff_sparkline()` to return `None` for unsupported types. Change the function signature to return `Optional[go.Figure]` and add the gating check as the first line of the function body:

```python
def payoff_sparkline(spec: dict, asset_names: list) -> Optional[go.Figure]:
    """Generate a compact Plotly sparkline of the payoff profile.

    Returns None for complex path-dependent types where a single-axis
    sparkline would be misleading.
    """
    inst_type = spec["instrument_type"]
    if inst_type not in SPARKLINE_SUPPORTED:
        return None
    # ... rest unchanged
```

- [ ] **Step 6: Run all payoff display tests**

Run: `python3 -m pytest tests/test_ui/test_payoff_display.py -v`
Expected: All tests PASS (old + new)

- [ ] **Step 7: Commit**

```bash
git add ui/components/payoff_display.py tests/test_ui/test_payoff_display.py
git commit -m "feat(ui): add formulas for 6 new instruments, gate sparkline for complex types"
```

---

## Task 3: Trade Economics — New Term-Sheet Builders and Modifier Updates

**Files:**
- Modify: `ui/components/trade_economics.py`
- Create: `tests/test_ui/test_trade_economics.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_ui/test_trade_economics.py`:

```python
import pytest
from ui.utils.registry import INSTRUMENT_REGISTRY, MODIFIER_REGISTRY
from ui.components.trade_economics import (
    _TERM_SHEETS,
    _MODIFIER_ECONOMICS,
    compute_scenarios,
)
from ui.utils.product_content import PRODUCT_SCENARIOS


def _make_default_params(inst_type):
    """Build a minimal params dict from registry defaults."""
    spec = INSTRUMENT_REGISTRY[inst_type]
    params = {"maturity": 1.0, "notional": 1_000_000, "assets": ["AAPL"]}
    for field in spec["fields"]:
        if field.get("default") is not None:
            params[field["name"]] = field["default"]
        elif field["type"] == "schedule":
            params[field["name"]] = [0.25, 0.5, 0.75, 1.0]
        elif field["type"] == "float":
            params[field["name"]] = 100.0
        elif field["type"] == "select":
            params[field["name"]] = field.get("choices", ["call"])[0]
        elif field["type"] == "float_list":
            params[field["name"]] = [100.0, 100.0]
        elif field["type"] == "select_list":
            params[field["name"]] = [field.get("choices", ["call"])[0]] * 2
        elif field["type"] in ("asset_select", "asset_select_optional"):
            params[field["name"]] = 0
    n_assets = spec.get("n_assets", 1)
    if isinstance(n_assets, str):
        n_assets = int(n_assets.split("-")[0])
    if n_assets > 1:
        params["assets"] = [f"ASSET_{i}" for i in range(n_assets)]
    return params


class TestTermSheetCoverage:
    def test_every_instrument_has_builder(self):
        for key in INSTRUMENT_REGISTRY:
            assert key in _TERM_SHEETS, f"Missing _TERM_SHEETS entry for {key}"

    def test_every_builder_returns_nonempty_html(self):
        for key in INSTRUMENT_REGISTRY:
            params = _make_default_params(key)
            fn = _TERM_SHEETS[key]
            result = fn(params, "long")
            assert len(result) > 20, f"Term sheet text for {key} too short"

    def test_every_builder_handles_short_direction(self):
        for key in INSTRUMENT_REGISTRY:
            params = _make_default_params(key)
            fn = _TERM_SHEETS[key]
            result = fn(params, "short")
            assert len(result) > 20


class TestModifierEconomicsCoverage:
    def test_every_modifier_has_economics(self):
        for key in MODIFIER_REGISTRY:
            assert key in _MODIFIER_ECONOMICS, f"Missing _MODIFIER_ECONOMICS entry for {key}"

    def test_every_economics_returns_nonempty(self):
        for key in MODIFIER_REGISTRY:
            spec = MODIFIER_REGISTRY[key]
            params = {}
            for field in spec["fields"]:
                if field.get("default") is not None:
                    params[field["name"]] = field["default"]
                elif field["type"] == "float":
                    params[field["name"]] = 1.0
                elif field["type"] == "select":
                    params[field["name"]] = field.get("choices", ["up"])[0]
                elif field["type"] == "schedule":
                    params[field["name"]] = [0.25, 0.5, 0.75, 1.0]
            fn = _MODIFIER_ECONOMICS[key]
            result = fn(params)
            assert len(result) > 10, f"Modifier economics for {key} too short"


class TestScenarios:
    def test_compute_scenarios_returns_three_rows(self):
        spec = {
            "instrument_type": "VanillaCall",
            "params": {"strike": 100.0, "maturity": 1.0, "notional": 1e6,
                       "assets": ["X"]},
            "modifiers": [],
            "direction": "long",
        }
        rows = compute_scenarios(spec, 100.0, 1e6)
        assert len(rows) == 3

    def test_product_scenarios_structure(self):
        for key, scenarios in PRODUCT_SCENARIOS.items():
            for s in scenarios:
                assert "label" in s
                assert "description" in s
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest tests/test_ui/test_trade_economics.py -v`
Expected: FAIL on `test_every_instrument_has_builder` (missing 6 new instruments) and `test_every_modifier_has_economics` (missing TargetProfit)

- [ ] **Step 3: Add `_obs_style_text()` helper**

In `ui/components/trade_economics.py`, add after the `_header()` function:

```python
def _obs_style_text(p: dict) -> str:
    """Format observation style text for barrier modifier economics."""
    style = p.get("observation_style", "continuous")
    if style == "discrete":
        dates = p.get("observation_dates") or []
        return f", discrete on {len(dates)} dates"
    if style == "window":
        ws = p.get("window_start", 0.0)
        we = p.get("window_end", 1.0)
        return f", window [{ws:.2g}y, {we:.2g}y]"
    return ""
```

- [ ] **Step 4: Add 6 new `_ts_*` functions**

Add the following functions to `ui/components/trade_economics.py`, before `_TERM_SHEETS`:

```python
def _ts_single_barrier(params: dict, direction: str) -> str:
    K = _fmt_num(params.get("strike", 0.0))
    B = _fmt_num(params.get("barrier", 0.0))
    opt = params.get("option_type", "call")
    bdir = params.get("barrier_direction", "up")
    btype = params.get("barrier_type", "out")
    asset = _asset_phrase(params)
    head = _header(direction, f"single-barrier {opt}", params) + f", strike {K}, barrier {B}."
    breach_word = "above" if bdir == "up" else "below"
    if btype == "out":
        body = (
            f" At maturity, the {opt} payoff is computed only if {asset} finishes {breach_word} {B}; "
            f"otherwise the contract expires worthless. Unlike path-dependent KO/KI modifiers, this barrier is "
            f"checked at expiry only — the spot can cross {B} intraday or mid-life without consequence."
        )
    else:
        body = (
            f" At maturity, the {opt} payoff activates only if {asset} finishes {breach_word} {B}. "
            f"This is a terminal-check barrier (not path-dependent) — cheaper than a full KI modifier "
            f"because interim moves don't count."
        )
    return head + body


def _ts_asian(params: dict, direction: str) -> str:
    K = _fmt_num(params.get("strike", 0.0))
    opt = params.get("option_type", "call")
    avg_type = params.get("average_type", "price")
    schedule = params.get("schedule") or []
    asset = _asset_phrase(params)
    head = _header(direction, f"Asian {opt} ({avg_type} avg)", params) + f", strike {K}."
    if avg_type == "price":
        body = (
            f" The arithmetic average of {asset} over {len(schedule)} observation dates replaces the terminal "
            f"spot in the payoff formula. Averaging smooths out price spikes, reducing effective vol and making "
            f"the option cheaper than a vanilla — but also capping the upside in a strong trend."
        )
    else:
        body = (
            f" The strike is replaced by the arithmetic average of {asset} over {len(schedule)} dates, "
            f"and the payoff is computed against the terminal spot. This 'floating strike' variant is used "
            f"by corporates to lock in a recent average as the effective strike."
        )
    return head + body


def _ts_cliquet(params: dict, direction: str) -> str:
    lc = _fmt_num(params.get("local_cap", 0.0))
    lf = _fmt_num(params.get("local_floor", 0.0))
    gf = _fmt_num(params.get("global_floor", 0.0))
    schedule = params.get("schedule") or []
    asset = _asset_phrase(params)
    head = _header(direction, "cliquet", params) + f", local [{lf}, {lc}], global floor {gf}."
    body = (
        f" At each of {len(schedule)} reset dates, {asset}'s period return is clipped to [{lf}, {lc}] "
        f"before summing. The global floor of {gf} guarantees a minimum total payoff. "
        f"The cliquet is effectively a strip of forward-starting clipplets — the structure is long skew and "
        f"vol-of-vol because each period's cap/floor optionality has distinct Greeks."
    )
    return head + body


def _ts_range_accrual(params: dict, direction: str) -> str:
    lo = _fmt_num(params.get("lower", 0.0))
    hi = _fmt_num(params.get("upper", 0.0))
    coupon = _fmt_num(params.get("coupon_rate", 0.0))
    schedule = params.get("schedule") or []
    asset = _asset_phrase(params)
    head = _header(direction, "range accrual", params) + f", range [{lo}, {hi}], coupon {coupon}."
    body = (
        f" Coupon of {coupon} accrues proportional to the fraction of {len(schedule)} observation dates "
        f"where {asset} sits inside [{lo}, {hi}]. Full range = full coupon; early breakout = minimal accrual. "
        f"The structure is implicitly short vol: a calm, range-bound market maximises the payout, while "
        f"a directional move outside the range rapidly erodes accrual."
    )
    return head + body


def _ts_autocallable(params: dict, direction: str) -> str:
    trigger = _fmt_num(params.get("autocall_trigger", 1.0))
    coupon = _fmt_num(params.get("coupon_rate", 0.05))
    ps = _fmt_num(params.get("put_strike", 0.7))
    schedule = params.get("schedule") or []
    asset = _asset_phrase(params)
    head = _header(direction, "autocallable", params) + f", trigger {trigger}, coupon {coupon}, put {ps}."
    body = (
        f" On each of {len(schedule)} observation dates, if the worst-of performance of {asset} is at or above "
        f"{trigger}, the note redeems early, paying par plus accumulated coupon ({coupon} per period). "
        f"If never called and worst-of performance is below {ps} at maturity, the investor absorbs the loss "
        f"(worst_perf - 1). The structure is short correlation, short vol, and short tail: the coupon compensates "
        f"the investor for accepting gap risk in a joint-crash scenario."
    )
    return head + body


def _ts_tarf(params: dict, direction: str) -> str:
    K = _fmt_num(params.get("strike", 0.0))
    target = _fmt_num(params.get("target", 0.0))
    lev = _fmt_num(params.get("leverage", 1.0))
    side = params.get("side", "buy")
    schedule = params.get("schedule") or []
    asset = _asset_phrase(params)
    head = _header(direction, "TARF", params) + f", strike {K}, target {target}, leverage {lev}x ({side})."
    body = (
        f" At each of {len(schedule)} fixing dates, the buyer transacts {asset} at {K}. Favorable fixings "
        f"accumulate profit; unfavorable fixings are leveraged at {lev}x. Once cumulative profit reaches {target}, "
        f"the trade terminates with a partial fill on the final fixing. The target caps the buyer's upside but "
        f"the leverage clause creates an asymmetric downside — the defining risk of TARF-type structures."
    )
    return head + body
```

- [ ] **Step 5: Update `_TERM_SHEETS` dict**

Add the 6 new entries:

```python
    "SingleBarrier":    _ts_single_barrier,
    "AsianOption":      _ts_asian,
    "Cliquet":          _ts_cliquet,
    "RangeAccrual":     _ts_range_accrual,
    "Autocallable":     _ts_autocallable,
    "TARF":             _ts_tarf,
```

- [ ] **Step 6: Update `_MODIFIER_ECONOMICS` dict**

Update existing barrier entries to use `_obs_style_text()` and add TargetProfit:

```python
_MODIFIER_ECONOMICS: dict = {
    "KnockOut": lambda p: (
        f"Knock-Out ({p.get('direction','up')}, barrier={p.get('barrier',0.0):.4g}"
        f"{_obs_style_text(p)}): "
        f"entire payoff lost if barrier is breached."
        f"{' Rebate: ' + str(p.get('rebate', 0.0)) if p.get('rebate', 0.0) > 0 else ''}"
    ),
    "KnockIn": lambda p: (
        f"Knock-In ({p.get('direction','down')}, barrier={p.get('barrier',0.0):.4g}"
        f"{_obs_style_text(p)}): "
        f"payoff only activates if barrier is breached."
    ),
    # ... PayoffCap, PayoffFloor, LeverageModifier, ObservationSchedule unchanged ...
    "RealizedVolKnockOut": lambda p: (
        f"Knocks out if realized vol "
        f"{'exceeds' if p.get('direction','above') == 'above' else 'falls below'} "
        f"{p.get('vol_barrier',0.0):.4g}"
        f"{_obs_style_text(p)}. Vol-contingent barrier."
    ),
    "RealizedVolKnockIn": lambda p: (
        f"Knocks in if realized vol "
        f"{'exceeds' if p.get('direction','above') == 'above' else 'falls below'} "
        f"{p.get('vol_barrier',0.0):.4g}"
        f"{_obs_style_text(p)}. Vol-contingent activation."
    ),
    "TargetProfit": lambda p: (
        f"Target Profit (target={p.get('target',0.0):.4g}, "
        f"partial_fill={'yes' if p.get('partial_fill','true') == 'true' else 'no'}): "
        f"caps cumulative payoff at target. Reduces tail exposure for periodic instruments."
    ),
}
```

- [ ] **Step 7: Run all trade economics tests**

Run: `python3 -m pytest tests/test_ui/test_trade_economics.py -v`
Expected: All tests PASS

- [ ] **Step 8: Commit**

```bash
git add ui/components/trade_economics.py tests/test_ui/test_trade_economics.py
git commit -m "feat(ui): add term-sheet text for 6 new instruments, update modifier economics"
```

---

## Task 4: Trade Builder — Grouped Sections, Product Header, Styled Modifiers

**Files:**
- Modify: `ui/components/trade_builder.py`

This task modifies the rendering logic only. No new tests beyond manual Streamlit testing, since the trade builder uses Streamlit widgets that can't be unit-tested without a running app. The existing data layer (product_content) is already tested.

- [ ] **Step 1: Add imports**

At the top of `ui/components/trade_builder.py`, add:

```python
from ui.utils.product_content import (
    PRODUCT_SECTIONS,
    CATEGORY_COLORS,
    PRODUCT_DESCRIPTIONS,
    MODIFIER_GROUP_COLORS,
    MODIFIER_SECTIONS,
    PRODUCT_SCENARIOS,
    SPARKLINE_SUPPORTED,
)
```

- [ ] **Step 2: Add `_render_section()` helper**

Add after the `_render_field()` function (after line 244):

```python
def _render_section(section: dict, inst_spec: dict, key_prefix: str, asset_names, n_selected):
    """Render a grouped section with colored left border."""
    st.markdown(
        f'<div style="border-left:3px solid {section["color"]};padding-left:12px;margin-bottom:4px;">'
        f'<div style="font-weight:600;color:#1e293b;font-size:13px;">{section["label"]}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )
    if "help" in section:
        st.caption(section["help"])

    values = {}
    for field_name in section["fields"]:
        field = next(f for f in inst_spec["fields"] if f["name"] == field_name)
        fkey = f"{key_prefix}_inst_{field_name}"
        values[field_name] = _render_field(field, fkey, asset_names, n_selected)
    return values
```

- [ ] **Step 3: Add `_render_modifier_styled()` helper**

Replace the existing `_render_modifier()` function with `_render_modifier_styled()`:

```python
def _render_modifier_styled(idx, key_prefix, asset_names, n_trade_assets):
    """Render one modifier with group badge and structured sections."""
    mod_key = f"{key_prefix}_mod_{idx}"

    mod_names = list(MODIFIER_REGISTRY.keys())
    mod_labels = [MODIFIER_REGISTRY[k]["label"] for k in mod_names]

    chosen_label = st.selectbox(
        f"Modifier #{idx + 1} type",
        mod_labels,
        key=f"{mod_key}_type",
    )
    chosen_type = mod_names[mod_labels.index(chosen_label)]
    mod_spec = MODIFIER_REGISTRY[chosen_type]
    section_config = MODIFIER_SECTIONS.get(chosen_type, {})
    group = section_config.get("group", "")
    group_style = MODIFIER_GROUP_COLORS.get(group, {})

    # Section header with group badge
    st.markdown(
        f'<div style="border-left:3px solid {group_style.get("color", "#94a3b8")};padding-left:12px;">'
        f'<span style="font-weight:600;color:#1e293b;font-size:13px;">Modifier: {mod_spec["label"]}</span> '
        f'<span style="background:{group_style.get("badge_bg","#f1f5f9")};color:{group_style.get("badge_text","#64748b")};'
        f'padding:1px 6px;border-radius:3px;font-size:9px;font-weight:600;">{group.upper()}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    params = {}
    # Core fields
    for field_name in section_config.get("core_fields", []):
        field = next(f for f in mod_spec["fields"] if f["name"] == field_name)
        params[field_name] = _render_field(field, f"{mod_key}_{field_name}", asset_names, n_trade_assets)

    # Observation style sub-section (barrier modifiers only)
    obs_fields = section_config.get("observation_fields", [])
    if obs_fields:
        for field_name in obs_fields:
            field = next(f for f in mod_spec["fields"] if f["name"] == field_name)
            params[field_name] = _render_field(field, f"{mod_key}_{field_name}", asset_names, n_trade_assets)

    # Extra fields (e.g., rebate)
    for field_name in section_config.get("extra_fields", []):
        field = next(f for f in mod_spec["fields"] if f["name"] == field_name)
        params[field_name] = _render_field(field, f"{mod_key}_{field_name}", asset_names, n_trade_assets)

    return {"type": chosen_type, "params": params}
```

- [ ] **Step 4: Add product header after product selector**

In `render_trade_builder()`, after `inst_spec = INSTRUMENT_REGISTRY[chosen_type]` (line 314), add:

```python
    # Product header with category badge and description
    category = inst_spec.get("category", "")
    cat_color = CATEGORY_COLORS.get(category, "#94a3b8")
    description = PRODUCT_DESCRIPTIONS.get(chosen_type, "")

    st.markdown(
        f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;">'
        f'<span style="background:{cat_color};color:#fff;padding:2px 8px;border-radius:4px;'
        f'font-size:11px;font-weight:600;">{category}</span>'
        f'<span style="font-weight:700;font-size:15px;color:#1e293b;">{inst_spec["label"]}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )
    if description:
        st.caption(description)
```

- [ ] **Step 5: Replace flat field loop with grouped sections**

Replace the "Dynamic instrument fields" section (lines 390-396) with:

```python
    # -----------------------------------------------------------------------
    # 4. Grouped instrument sections
    # -----------------------------------------------------------------------
    sections = PRODUCT_SECTIONS.get(chosen_type, [])
    instrument_params: dict = {}
    if sections:
        for section in sections:
            section_values = _render_section(section, inst_spec, key_prefix, asset_names, n_selected)
            instrument_params.update(section_values)
    else:
        # Fallback to flat rendering for any unlisted product
        for field in inst_spec["fields"]:
            fkey = f"{key_prefix}_inst_{field['name']}"
            val = _render_field(field, fkey, asset_names, n_selected)
            instrument_params[field["name"]] = val
```

- [ ] **Step 6: Replace modifier rendering with styled version**

Replace the modifier loop (lines 418-422) to use `_render_modifier_styled`:

```python
    for i in range(n_mods):
        with st.expander(f"Modifier #{i + 1}", expanded=True):
            mod = _render_modifier_styled(i, key_prefix, asset_names, n_selected)
            if mod is not None:
                modifiers.append(mod)
```

- [ ] **Step 7: Handle `None` sparkline return in payoff preview**

Replace the sparkline display in the payoff preview section (lines 441-444) with:

```python
        st.caption(payoff_formula(preview_spec))
        fig = payoff_sparkline(preview_spec, asset_names)
        if fig is not None:
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False},
                            key=f"{key_prefix}_payoff_preview")
        else:
            st.caption("Payoff depends on full path — chart not available. See scenarios below.")
```

- [ ] **Step 8: Add live scenario panel after payoff preview**

After the sparkline/fallback, add scenario display (still inside the `if asset_names and assets_valid:` block):

```python
        # Live scenario panel
        from ui.components.trade_economics import compute_scenarios
        from ui.utils.product_content import PRODUCT_SCENARIOS

        market_spots = st.session_state.get("market", {}).get("spots", [])
        spot = 100.0
        if market_spots and asset_names:
            trade_assets = preview_spec["params"].get("assets", [])
            target_name = trade_assets[0] if trade_assets else asset_names[0]
            if target_name in asset_names:
                idx = asset_names.index(target_name)
                if idx < len(market_spots):
                    spot = float(market_spots[idx])
            elif market_spots:
                spot = float(market_spots[0])

        scenarios = compute_scenarios(preview_spec, spot, notional)
        # Generic scenarios
        for row in scenarios:
            pnl = row["direction_payoff"]
            color = "#22c55e" if pnl > 0 else "#ef4444" if pnl < 0 else "#64748b"
            st.markdown(
                f'<div style="display:flex;justify-content:space-between;font-size:12px;'
                f'padding:2px 0;border-bottom:1px solid #f1f5f9;">'
                f'<span style="color:#64748b;">{row["label"]} ({row["spot"]:.2f})</span>'
                f'<span style="color:{color};font-weight:600;">{pnl:+,.0f}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )

        # Product-specific structural scenarios
        prod_scenarios = PRODUCT_SCENARIOS.get(chosen_type, [])
        if prod_scenarios:
            st.markdown(
                '<div style="color:#94a3b8;font-size:10px;text-transform:uppercase;'
                'letter-spacing:0.5px;margin-top:8px;font-weight:600;">Structural Scenarios</div>',
                unsafe_allow_html=True,
            )
            for s in prod_scenarios:
                st.markdown(
                    f'<div style="font-size:11px;color:#334155;padding:2px 0;">'
                    f'<b>{s["label"]}</b>: {s["description"]}</div>',
                    unsafe_allow_html=True,
                )
```

- [ ] **Step 9: Run existing tests to verify no regressions**

Run: `python3 -m pytest tests/ -v --tb=short`
Expected: All tests PASS

- [ ] **Step 10: Commit**

```bash
git add ui/components/trade_builder.py
git commit -m "feat(ui): grouped sections, product header, styled modifiers in trade builder"
```

---

## Task 5: Term Sheet Renderer

**Files:**
- Create: `ui/components/term_sheet.py`
- Create: `tests/test_ui/test_term_sheet.py`

- [ ] **Step 1: Write smoke tests**

Create `tests/test_ui/test_term_sheet.py`:

```python
"""Smoke tests for the read-only term-sheet renderer.

These tests mock Streamlit calls since the renderer produces st.markdown() output.
"""
import pytest
from unittest.mock import patch, MagicMock
from ui.utils.registry import INSTRUMENT_REGISTRY


def _make_trade_spec(inst_type):
    """Build a minimal trade spec for testing."""
    spec = INSTRUMENT_REGISTRY[inst_type]
    params = {"maturity": 1.0, "notional": 1_000_000, "assets": ["AAPL"]}
    for field in spec["fields"]:
        if field.get("default") is not None:
            params[field["name"]] = field["default"]
        elif field["type"] == "schedule":
            params[field["name"]] = [0.25, 0.5, 0.75, 1.0]
        elif field["type"] == "float":
            params[field["name"]] = 100.0
        elif field["type"] == "select":
            params[field["name"]] = field.get("choices", ["call"])[0]
        elif field["type"] == "float_list":
            params[field["name"]] = [100.0, 100.0]
        elif field["type"] == "select_list":
            params[field["name"]] = [field.get("choices", ["call"])[0]] * 2
        elif field["type"] in ("asset_select", "asset_select_optional"):
            params[field["name"]] = 0
    n_assets = spec.get("n_assets", 1)
    if isinstance(n_assets, str):
        n_assets = int(n_assets.split("-")[0])
    if n_assets > 1:
        params["assets"] = [f"ASSET_{i}" for i in range(n_assets)]
    return {
        "trade_id": f"TEST_{inst_type}",
        "instrument_type": inst_type,
        "direction": "long",
        "params": params,
        "modifiers": [],
    }


@pytest.fixture
def mock_streamlit():
    """Mock all Streamlit calls used by term_sheet."""
    with patch("ui.components.term_sheet.st") as mock_st:
        mock_st.markdown = MagicMock()
        mock_st.caption = MagicMock()
        mock_st.plotly_chart = MagicMock()
        yield mock_st


class TestTermSheetRenderer:
    @pytest.mark.parametrize("inst_type", list(INSTRUMENT_REGISTRY.keys()))
    def test_render_does_not_raise(self, mock_streamlit, inst_type):
        from ui.components.term_sheet import render_term_sheet
        trade = _make_trade_spec(inst_type)
        asset_names = trade["params"]["assets"]
        market_spots = [100.0] * len(asset_names)
        # Should not raise
        render_term_sheet(trade, asset_names, market_spots)
        # Should have produced some output
        assert mock_streamlit.markdown.call_count > 0

    def test_render_with_modifier(self, mock_streamlit):
        from ui.components.term_sheet import render_term_sheet
        trade = _make_trade_spec("VanillaCall")
        trade["modifiers"] = [
            {"type": "KnockOut", "params": {"barrier": 120.0, "direction": "up",
                                            "asset_idx": None, "observation_style": "continuous",
                                            "observation_dates": [], "window_start": 0.0,
                                            "window_end": 1.0, "rebate": 0.0}},
        ]
        render_term_sheet(trade, ["AAPL"], [100.0])
        assert mock_streamlit.markdown.call_count > 0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest tests/test_ui/test_term_sheet.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'ui.components.term_sheet'`

- [ ] **Step 3: Create the term sheet renderer**

Create `ui/components/term_sheet.py`:

```python
"""Read-only term-sheet renderer for portfolio table expanders.

Takes a trade spec dict and renders a formatted summary using
st.markdown() for structured content and st.plotly_chart() for sparklines.
"""

import streamlit as st
from ui.utils.registry import INSTRUMENT_REGISTRY, MODIFIER_REGISTRY
from ui.utils.product_content import (
    PRODUCT_SECTIONS,
    CATEGORY_COLORS,
    PRODUCT_DESCRIPTIONS,
    MODIFIER_GROUP_COLORS,
    MODIFIER_SECTIONS,
    PRODUCT_SCENARIOS,
)
from ui.components.payoff_display import payoff_formula, payoff_sparkline
from ui.components.trade_economics import (
    render_trade_economics,
    _TERM_SHEETS,
    _MODIFIER_ECONOMICS,
    compute_scenarios,
)


def _render_readonly_value(label: str, value, field_type: str) -> str:
    """Return HTML for a single read-only field."""
    if field_type == "float":
        display = f"{value:.4g}"
    elif field_type == "schedule":
        display = f"{len(value)} dates" if value else "none"
    elif field_type == "float_list":
        display = ", ".join(f"{v:.4g}" for v in value) if value else "none"
    elif field_type == "select_list":
        display = ", ".join(str(v) for v in value) if value else "none"
    else:
        display = str(value) if value is not None else "—"

    return (
        f'<div style="flex:1;">'
        f'<div style="color:#94a3b8;font-size:10px;text-transform:uppercase;">{label}</div>'
        f'<div style="color:#1e293b;font-size:13px;font-weight:500;">{display}</div>'
        f'</div>'
    )


def render_term_sheet(spec: dict, asset_names: list, market_spots: list) -> None:
    """Render a read-only term-sheet for a trade spec."""
    inst_type = spec["instrument_type"]
    params = spec.get("params", {})
    direction = spec.get("direction", "long")
    inst_spec = INSTRUMENT_REGISTRY.get(inst_type)

    if inst_spec is None:
        st.markdown(f"Unknown instrument type: {inst_type}")
        return

    # 1. Product header
    category = inst_spec.get("category", "")
    cat_color = CATEGORY_COLORS.get(category, "#94a3b8")
    description = PRODUCT_DESCRIPTIONS.get(inst_type, "")

    st.markdown(
        f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;">'
        f'<span style="background:{cat_color};color:#fff;padding:2px 8px;border-radius:4px;'
        f'font-size:11px;font-weight:600;">{category}</span>'
        f'<span style="font-weight:700;font-size:15px;color:#1e293b;">{inst_spec["label"]}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )
    if description:
        st.caption(description)

    # 2. Key terms
    side_label = "Long" if direction == "long" else "Short"
    side_color = "#22c55e" if direction == "long" else "#ef4444"
    assets_str = ", ".join(params.get("assets", []))
    key_terms_html = (
        f'<div style="display:flex;gap:16px;margin-bottom:12px;flex-wrap:wrap;">'
        f'{_render_readonly_value("Direction", side_label, "select")}'
        f'{_render_readonly_value("Trade ID", spec.get("trade_id", ""), "str")}'
        f'{_render_readonly_value("Maturity", params.get("maturity", 0), "float")}'
        f'{_render_readonly_value("Notional", f"{params.get(\"notional\", 0):,.0f}", "str")}'
        f'{_render_readonly_value("Underlyings", assets_str, "str")}'
        f'</div>'
    )
    st.markdown(key_terms_html, unsafe_allow_html=True)

    # 3. Grouped instrument sections (read-only)
    sections = PRODUCT_SECTIONS.get(inst_type, [])
    for section in sections:
        st.markdown(
            f'<div style="border-left:3px solid {section["color"]};padding-left:12px;margin-bottom:4px;">'
            f'<div style="font-weight:600;color:#1e293b;font-size:13px;">{section["label"]}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
        if "help" in section:
            st.caption(section["help"])

        fields_html = '<div style="display:flex;gap:16px;margin-bottom:8px;flex-wrap:wrap;">'
        for field_name in section["fields"]:
            field = next((f for f in inst_spec["fields"] if f["name"] == field_name), None)
            if field is None:
                continue
            val = params.get(field_name, field.get("default"))
            fields_html += _render_readonly_value(field["label"], val, field["type"])
        fields_html += '</div>'
        st.markdown(fields_html, unsafe_allow_html=True)

    # 4. Modifier sections (read-only)
    modifiers = spec.get("modifiers", [])
    for mod in modifiers:
        mod_type = mod["type"]
        mod_params = mod.get("params", {})
        mod_spec = MODIFIER_REGISTRY.get(mod_type)
        if mod_spec is None:
            continue

        section_config = MODIFIER_SECTIONS.get(mod_type, {})
        group = section_config.get("group", "")
        group_style = MODIFIER_GROUP_COLORS.get(group, {})

        st.markdown(
            f'<div style="border-left:3px solid {group_style.get("color", "#94a3b8")};padding-left:12px;">'
            f'<span style="font-weight:600;color:#1e293b;font-size:13px;">Modifier: {mod_spec["label"]}</span> '
            f'<span style="background:{group_style.get("badge_bg","#f1f5f9")};color:{group_style.get("badge_text","#64748b")};'
            f'padding:1px 6px;border-radius:3px;font-size:9px;font-weight:600;">{group.upper()}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

        all_fields = (
            section_config.get("core_fields", [])
            + section_config.get("observation_fields", [])
            + section_config.get("extra_fields", [])
        )
        fields_html = '<div style="display:flex;gap:16px;margin-bottom:8px;flex-wrap:wrap;">'
        for field_name in all_fields:
            field = next((f for f in mod_spec["fields"] if f["name"] == field_name), None)
            if field is None:
                continue
            val = mod_params.get(field_name, field.get("default"))
            fields_html += _render_readonly_value(field["label"], val, field["type"])
        fields_html += '</div>'
        st.markdown(fields_html, unsafe_allow_html=True)

    # 5. Economics description
    render_trade_economics(spec, asset_names, market_spots)

    # 6. Formula
    st.caption(payoff_formula(spec))

    # 7. Sparkline (if supported)
    fig = payoff_sparkline(spec, asset_names)
    if fig is not None:
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    else:
        st.caption("Payoff depends on full path — chart not available.")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m pytest tests/test_ui/test_term_sheet.py -v`
Expected: All tests PASS (21 parametrized + 1 modifier test)

- [ ] **Step 5: Commit**

```bash
git add ui/components/term_sheet.py tests/test_ui/test_term_sheet.py
git commit -m "feat(ui): add read-only term-sheet renderer with smoke tests"
```

---

## Task 6: Portfolio Table — Use Term Sheet Renderer

**Files:**
- Modify: `ui/components/portfolio_table.py`

- [ ] **Step 1: Update imports**

In `ui/components/portfolio_table.py`, replace the import of `render_trade_economics`:

```python
from ui.components.term_sheet import render_term_sheet
```

Keep the `payoff_formula` and `payoff_sparkline` imports removed (they're now handled by `render_term_sheet`). The new imports block should be:

```python
import copy
import streamlit as st
from ui.components.term_sheet import render_term_sheet
```

- [ ] **Step 2: Replace expander content with `render_term_sheet()`**

Replace the expander block (lines 98-109) with:

```python
        # Term-sheet view
        with st.expander(f"Term Sheet: {trade['trade_id']}", expanded=False):
            asset_names_list = st.session_state.get("market", {}).get("asset_names", [])
            market_spots = st.session_state.get("market", {}).get("spots", [])
            if asset_names_list:
                render_term_sheet(trade, asset_names_list, market_spots)
            else:
                st.caption("Add market data to see term-sheet details.")
```

- [ ] **Step 3: Run all tests to verify no regressions**

Run: `python3 -m pytest tests/ -v --tb=short`
Expected: All tests PASS

- [ ] **Step 4: Commit**

```bash
git add ui/components/portfolio_table.py
git commit -m "feat(ui): portfolio table uses read-only term-sheet renderer"
```

---

## Task 7: Final Verification

**Files:** None (verification only)

- [ ] **Step 1: Run full test suite**

Run: `python3 -m pytest tests/ -v`
Expected: All tests PASS (236 existing + new tests)

- [ ] **Step 2: Verify import chain**

Run: `python3 -c "from ui.utils.product_content import PRODUCT_SECTIONS, SPARKLINE_SUPPORTED; print(f'{len(PRODUCT_SECTIONS)} products, {len(SPARKLINE_SUPPORTED)} sparkline-eligible')"`
Expected: `21 products, 16 sparkline-eligible`

Run: `python3 -c "from ui.components.term_sheet import render_term_sheet; print('OK')"`
Expected: `OK`

Run: `python3 -c "from ui.components.trade_economics import _TERM_SHEETS; print(f'{len(_TERM_SHEETS)} term-sheet builders')"`
Expected: `21 term-sheet builders`

- [ ] **Step 3: Verify no circular imports**

Run: `python3 -c "from ui.components.trade_builder import render_trade_builder; print('trade_builder OK')"`
Run: `python3 -c "from ui.components.portfolio_table import render_portfolio_table; print('portfolio_table OK')"`
Expected: Both print "OK" with no import errors

- [ ] **Step 4: Commit any remaining fixes**

```bash
git add -A
git commit -m "chore: final verification — all tests pass, imports clean"
```
