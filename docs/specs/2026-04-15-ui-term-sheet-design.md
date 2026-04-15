# UI Term-Sheet & Product-Specific Input — Design Spec

**Date:** 2026-04-15
**Scope:** Product-specific trade builder inputs, term-sheet views, and scenario analysis for all 21 instruments and 9 modifiers

---

## 1. Goals

1. **Product-specific input layout** — replace flat generic field rendering with grouped sections (colored borders, product-specific labels, contextual help) in the trade builder
2. **Live scenario panel** — show generic 3-spot scenarios + product-specific structural scenarios that update as the user configures a trade
3. **Modifier sections** — each modifier rendered as a styled section with group badge (Barrier/Payoff Shaper/Structural), observation style toggle for barrier modifiers
4. **Read-only term-sheet** in portfolio table — formatted summary of trade terms, economics description, scenarios, and payoff chart
5. **Full coverage** — term-sheet text, formulas, and scenarios for all 6 new instruments (SingleBarrier, AsianOption, Cliquet, RangeAccrual, Autocallable, TARF) and the TargetProfit modifier, plus updated modifier descriptions

## 2. Architecture

### Approach: Extract product-specific content into a data layer

Product-specific content (section groupings, term-sheet text, scenario logic, formula strings) is data, not rendering logic. A central `product_content.py` module holds all per-product configuration. Rendering components stay thin and consume this module.

### Data flow

```
registry.py          → what fields exist (unchanged)
product_content.py   → how to group/label/describe them per product
trade_builder.py     → renders editable form using both
term_sheet.py        → renders read-only view using both
trade_economics.py   → term-sheet text + scenarios (content)
payoff_display.py    → formula strings + sparkline (content)
```

## 3. File Changes

### New files

| File | Description |
|---|---|
| `ui/utils/product_content.py` | Per-product content: section groupings, category colors, modifier section config, product-specific scenarios, sparkline eligibility |
| `ui/components/term_sheet.py` | Read-only term-sheet renderer for portfolio table expander |
| `tests/test_ui/test_product_content.py` | Unit tests for product content completeness |
| `tests/test_ui/test_trade_economics.py` | Unit tests for term-sheet text and scenario generators |
| `tests/test_ui/test_term_sheet.py` | Smoke tests for term-sheet renderer |

### Modified files

| File | Changes |
|---|---|
| `ui/components/trade_builder.py` | Replace flat field rendering with grouped-section layout; add live scenario panel; replace modifier expanders with styled modifier sections |
| `ui/components/portfolio_table.py` | Replace current expander content with `render_term_sheet()` call |
| `ui/components/payoff_display.py` | Add formula strings for 6 new instruments; add new products to `_PATH_DEPENDENT_TYPES`; return `None` for sparkline on complex path-dependent types |
| `ui/components/trade_economics.py` | Add term-sheet text builders for 6 new instruments; add product-specific scenario generators; add TargetProfit modifier economics; update barrier modifier text with observation style |

### Unchanged files

| File | Reason |
|---|---|
| `ui/utils/registry.py` | Already has all products and modifiers with fields — no structural changes needed |
| `ui/app.py` | Tab structure unchanged |
| `ui/theme.py` | Existing color palette sufficient |

## 4. Product Content Module (`ui/utils/product_content.py`)

### 4.1 Section Groupings

Each product maps to an ordered list of sections. Each section has a label, color, field names, and optional help text.

```python
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
            "help": "Redeems early if worst-of performance ≥ trigger",
        },
        {
            "label": "Downside Protection",
            "color": "#ef4444",
            "fields": ["put_strike"],
            "help": "Below put strike at maturity, loss = worst_perf − 1.0",
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
```

### 4.2 Category Colors

```python
CATEGORY_COLORS = {
    "European": "#3b82f6",       # blue
    "Path-dependent": "#22c55e", # green
    "Multi-asset": "#8b5cf6",    # purple
    "Periodic": "#f59e0b",       # amber
}
```

### 4.3 Product Descriptions (one-liners)

```python
PRODUCT_DESCRIPTIONS = {
    "VanillaCall": "European call option — pays max(S − K, 0) at maturity.",
    "VanillaPut": "European put option — pays max(K − S, 0) at maturity.",
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
```

### 4.4 Modifier Section Config

```python
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
```

### 4.5 Product-Specific Scenarios

Each product defines 1-3 structural scenarios that highlight the key risk of that product. These are computed using the same `compute_scenarios()` infrastructure but with product-aware spot levels and labels.

```python
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
        {"label": "Called at obs 2", "description": "All assets ≥ trigger at 2nd observation — receives 2 × coupon"},
        {"label": "Not called, worst at 60%", "description": "Worst performer below put strike — loss = worst_perf − 1"},
    ],
    "TARF": [
        {"label": "Target hit at obs 5", "description": "Cumulative profit reaches target — partial fill, trade terminates"},
        {"label": "Never hit, spot drops", "description": "Leverage-amplified losses accumulate without target cap"},
    ],
    "Accumulator": [
        {"label": "Leverage trap", "description": "Spot drops 30% — forced buying at leverage × quantity"},
    ],
    "Decumulator": [
        {"label": "Rally trap", "description": "Spot rises 30% — forced selling at leverage × quantity"},
    ],
    "DoubleNoTouch": [
        {"label": "Touch lower barrier", "description": "Spot touches lower — entire payoff extinguished"},
    ],
    "WorstOfCall": [
        {"label": "One leg collapses", "description": "Best asset +40% but worst asset −5% — payoff is zero"},
    ],
    "WorstOfPut": [
        {"label": "Correlated crash", "description": "All assets fall 30% — worst-of put payoff is large"},
    ],
}
```

Scenarios for products with only generic behavior (DualDigital, TripleDigital, BestOfCall, BestOfPut, ForwardStartingOption, RestrikeOption) use only the standard 3-spot table with no additional structural scenarios.

### 4.6 Sparkline Eligibility

```python
SPARKLINE_SUPPORTED = {
    # European — terminal payoff is a function of spot
    "VanillaCall", "VanillaPut", "Digital", "SingleBarrier", "ContingentOption",
    # Path-dependent — flat-path approximation is reasonable
    "DoubleNoTouch", "ForwardStartingOption", "RestrikeOption",
    # Multi-asset — flat-path approximation across assets
    "WorstOfCall", "WorstOfPut", "BestOfCall", "BestOfPut",
    "DualDigital", "TripleDigital",
    # Periodic — flat-path approximation
    "Accumulator", "Decumulator",
}
# Excluded: AsianOption, Cliquet, RangeAccrual, Autocallable, TARF
# These have payoffs that depend on the path shape, not terminal spot level.
# Show formula + scenario table instead.
```

## 5. Trade Builder Changes (`ui/components/trade_builder.py`)

### 5.1 New rendering flow

```
1. Product selector with category badge
2. One-line product description
3. Common fields row (trade ID, maturity, notional, direction) — unchanged
4. Asset selection — unchanged
5. Grouped instrument sections (from PRODUCT_SECTIONS)
6. Styled modifier sections (from MODIFIER_SECTIONS)
7. Live scenario panel:
   a. Formula string
   b. Sparkline chart (if SPARKLINE_SUPPORTED, else "Payoff is path-dependent — see scenarios")
   c. Generic 3-spot scenario table
   d. Product-specific structural scenarios
8. Submit button — unchanged
```

### 5.2 Grouped section rendering

Replace the current flat field loop with section-aware rendering. A new helper function renders a section:

```python
def _render_section(section: dict, inst_spec: dict, key_prefix: str, asset_names, n_selected):
    """Render a grouped section with colored left border."""
    # Streamlit container with custom HTML for the section header
    st.markdown(
        f'<div style="border-left:3px solid {section["color"]};padding-left:12px;margin-bottom:4px;">'
        f'<div style="font-weight:600;color:#1e293b;font-size:13px;">{section["label"]}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )
    if "help" in section:
        st.caption(section["help"])

    # Render fields in this section
    values = {}
    for field_name in section["fields"]:
        field = next(f for f in inst_spec["fields"] if f["name"] == field_name)
        fkey = f"{key_prefix}_inst_{field_name}"
        values[field_name] = _render_field(field, fkey, asset_names, n_selected)
    return values
```

The existing `_render_field()` function is unchanged.

### 5.3 Styled modifier rendering

Replace the current flat expander with a section-aware modifier renderer:

```python
def _render_modifier_styled(idx, key_prefix, asset_names, n_trade_assets):
    """Render one modifier with group badge and structured sections."""
    mod_key = f"{key_prefix}_mod_{idx}"

    # Modifier type selector
    chosen_type = _select_modifier_type(mod_key)
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

    # Core fields
    params = {}
    for field_name in section_config.get("core_fields", []):
        field = next(f for f in mod_spec["fields"] if f["name"] == field_name)
        params[field_name] = _render_field(field, f"{mod_key}_{field_name}", asset_names, n_trade_assets)

    # Observation style sub-section (barrier modifiers only)
    obs_fields = section_config.get("observation_fields", [])
    if obs_fields:
        # Render as highlighted sub-block
        for field_name in obs_fields:
            field = next(f for f in mod_spec["fields"] if f["name"] == field_name)
            params[field_name] = _render_field(field, f"{mod_key}_{field_name}", asset_names, n_trade_assets)

    # Extra fields (e.g., rebate)
    for field_name in section_config.get("extra_fields", []):
        field = next(f for f in mod_spec["fields"] if f["name"] == field_name)
        params[field_name] = _render_field(field, f"{mod_key}_{field_name}", asset_names, n_trade_assets)

    return {"type": chosen_type, "params": params}
```

### 5.4 Product header

At the top of the trade builder, after product selection:

```python
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

## 6. Term Sheet Renderer (`ui/components/term_sheet.py`)

### 6.1 Purpose

Read-only term-sheet used in the portfolio table expander. Takes a trade spec dict and renders a formatted summary using `st.markdown()` for structured content and `st.plotly_chart()` for the sparkline.

### 6.2 Render flow

```python
def render_term_sheet(spec: dict, asset_names: list, market_spots: list) -> None:
    """Render a read-only term-sheet for a trade spec."""

    inst_type = spec["instrument_type"]
    params = spec.get("params", {})
    direction = spec.get("direction", "long")
    inst_spec = INSTRUMENT_REGISTRY.get(inst_type)

    # 1. Product header — category badge + name + description
    # 2. Key terms grid — trade ID, direction, maturity, notional, underlyings
    # 3. Grouped instrument sections — read-only values with colored borders
    # 4. Modifier sections — read-only with group badges
    # 5. Term-sheet description from trade_economics.py
    # 6. Combined payoff formula
    # 7. Scenario table — generic 3-spot + product-specific
    # 8. Sparkline chart (if SPARKLINE_SUPPORTED)
```

### 6.3 Read-only value rendering

Instead of `st.number_input` / `st.selectbox`, values are rendered as styled text in the same section layout:

```python
def _render_readonly_value(label: str, value, field_type: str) -> str:
    """Return HTML for a single read-only field."""
    if field_type == "float":
        display = f"{value:.4g}"
    elif field_type == "schedule":
        display = f"{len(value)} dates" if value else "none"
    elif field_type == "float_list":
        display = ", ".join(f"{v:.4g}" for v in value)
    else:
        display = str(value)

    return (
        f'<div style="flex:1;">'
        f'<div style="color:#94a3b8;font-size:10px;text-transform:uppercase;">{label}</div>'
        f'<div style="color:#1e293b;font-size:13px;font-weight:500;">{display}</div>'
        f'</div>'
    )
```

## 7. Content Updates

### 7.1 New term-sheet text builders (`trade_economics.py`)

Add `_ts_*` functions for each new product, following the existing pattern. Each returns an HTML string combining trade attributes with economic interpretation.

| Function | Product | Key narrative |
|---|---|---|
| `_ts_single_barrier` | SingleBarrier | European barrier at expiry — contrast with path-dependent KO/KI modifiers |
| `_ts_asian` | AsianOption | Averaging reduces volatility — price avg vs strike avg distinction |
| `_ts_cliquet` | Cliquet | Periodic reset locks in returns — local cap/floor asymmetry |
| `_ts_range_accrual` | RangeAccrual | Coupon proportional to time in range — short vol position |
| `_ts_autocallable` | Autocallable | Early redemption with coupon — worst-of correlation risk |
| `_ts_tarf` | TARF | Accumulator with target cap — partial fill, leverage asymmetry |

Add to `_TERM_SHEETS` dict and `_MODIFIER_ECONOMICS` dict (for TargetProfit).

### 7.2 Updated modifier economics

Update existing `_MODIFIER_ECONOMICS` entries for KnockOut, KnockIn, RealizedVolKnockOut, RealizedVolKnockIn to include observation style information when present:

```python
"KnockOut": lambda p: (
    f"Knock-Out ({p.get('direction','up')}, barrier={p.get('barrier',0.0):.4g}"
    f"{_obs_style_text(p)}): "
    f"entire payoff lost if barrier is breached."
    f"{' Rebate: ' + str(p.get('rebate', 0.0)) if p.get('rebate', 0.0) > 0 else ''}"
),
```

Where `_obs_style_text(p)` returns e.g., `, discrete on 4 dates` or `, window [0.25y, 0.75y]` or empty string for continuous.

Add TargetProfit:
```python
"TargetProfit": lambda p: (
    f"Target Profit (target={p.get('target',0.0):.4g}, "
    f"partial_fill={'yes' if p.get('partial_fill','true') == 'true' else 'no'}): "
    f"caps cumulative payoff at target. Reduces tail exposure for periodic instruments."
),
```

### 7.3 New formula strings (`payoff_display.py`)

Add to `_BASE_FORMULAS`:

```python
"SingleBarrier": lambda p: (
    f"max(S {'−' if p.get('option_type','call')=='call' else '− S, '}"
    f"{p.get('strike',0):.4g}"
    f"{', 0)' if p.get('option_type','call')=='call' else ''}"
    f" · 1{{S(T) {'>' if p.get('barrier_direction','up')=='up' else '<'} {p.get('barrier',0):.4g}}}"
    # Simplified — actual rendering varies by barrier_type (in/out)
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

### 7.4 Updated sparkline support

Add new path-dependent types to `_PATH_DEPENDENT_TYPES`:
```python
_PATH_DEPENDENT_TYPES = {
    "Accumulator", "Decumulator", "DoubleNoTouch",
    "ForwardStartingOption", "RestrikeOption",
    "AsianOption", "Cliquet", "RangeAccrual",
    "Autocallable", "TARF",
}
```

Add `_PATH_DEPENDENT_MODIFIERS` update:
```python
_PATH_DEPENDENT_MODIFIERS = {
    "KnockOut", "KnockIn", "RealizedVolKnockOut", "RealizedVolKnockIn",
    "TargetProfit",
}
```

Modify `payoff_sparkline()` to return `None` when product is not in `SPARKLINE_SUPPORTED`:
```python
def payoff_sparkline(spec, asset_names):
    if spec["instrument_type"] not in SPARKLINE_SUPPORTED:
        return None
    # ... existing logic
```

Both callers of `payoff_sparkline()` — `trade_builder.py` (payoff preview) and `portfolio_table.py` (term-sheet expander) — must handle a `None` return by showing a text fallback (e.g., "Payoff depends on full path — chart not available") instead of rendering a chart.

### 7.5 Product-specific scenario computation

Extend `compute_scenarios()` in `trade_economics.py` to accept an optional `product_scenarios` parameter. The product-specific scenarios from `PRODUCT_SCENARIOS` are descriptive labels — the actual P&L computation reuses the existing `_compute_*_payoff` functions with the specified spot multipliers where available, or renders as descriptive text for scenarios that can't be reduced to a spot level (e.g., "Volatile path averages to near-strike").

## 8. Testing

### 8.1 `tests/test_ui/test_product_content.py`

```python
def test_every_product_has_sections():
    """Every registered instrument has a PRODUCT_SECTIONS entry."""
    for key in INSTRUMENT_REGISTRY:
        assert key in PRODUCT_SECTIONS

def test_every_field_assigned_to_section():
    """Every field in the registry appears in exactly one section."""
    for key, spec in INSTRUMENT_REGISTRY.items():
        section_fields = []
        for section in PRODUCT_SECTIONS[key]:
            section_fields.extend(section["fields"])
        registry_fields = [f["name"] for f in spec["fields"]]
        assert set(section_fields) == set(registry_fields)

def test_every_product_has_description():
    for key in INSTRUMENT_REGISTRY:
        assert key in PRODUCT_DESCRIPTIONS

def test_category_colors_complete():
    categories = {spec.get("category") for spec in INSTRUMENT_REGISTRY.values() if spec.get("category")}
    for cat in categories:
        assert cat in CATEGORY_COLORS

def test_modifier_sections_complete():
    for key in MODIFIER_REGISTRY:
        assert key in MODIFIER_SECTIONS

def test_modifier_fields_assigned():
    """Every modifier field appears in core, observation, or extra."""
    for key, spec in MODIFIER_REGISTRY.items():
        section = MODIFIER_SECTIONS[key]
        all_assigned = section["core_fields"] + section.get("observation_fields", []) + section.get("extra_fields", [])
        registry_fields = [f["name"] for f in spec["fields"]]
        assert set(all_assigned) == set(registry_fields)

def test_sparkline_supported_subset():
    assert SPARKLINE_SUPPORTED.issubset(set(INSTRUMENT_REGISTRY.keys()))
```

### 8.2 `tests/test_ui/test_trade_economics.py`

```python
def test_term_sheet_text_all_instruments():
    """Every instrument has a term-sheet text builder that returns non-empty HTML."""
    for key in INSTRUMENT_REGISTRY:
        params = _make_default_params(key)
        fn = _TERM_SHEETS.get(key)
        assert fn is not None, f"Missing term-sheet builder for {key}"
        result = fn(params, "long")
        assert len(result) > 0

def test_modifier_economics_all_modifiers():
    """Every modifier has an economics text generator."""
    for key in MODIFIER_REGISTRY:
        fn = _MODIFIER_ECONOMICS.get(key)
        assert fn is not None, f"Missing modifier economics for {key}"

def test_product_scenarios_structure():
    """Product scenarios return correct dict structure."""
    for key, scenarios in PRODUCT_SCENARIOS.items():
        for s in scenarios:
            assert "label" in s
            assert "description" in s
```

### 8.3 `tests/test_ui/test_term_sheet.py`

Smoke tests verifying `render_term_sheet()` doesn't raise for each product type. These tests mock `st.markdown` and `st.plotly_chart` since they can't render in a test context.

### 8.4 Existing test updates

- `tests/test_ui/test_payoff_display.py` — add formula tests for 6 new instruments, test that sparkline returns `None` for excluded types

## 9. Out of Scope

- No changes to `ui/app.py` tab structure
- No changes to `ui/theme.py` color palette (existing palette is sufficient)
- No changes to instrument/modifier Python classes or their tests
- No new Streamlit pages or tabs
- No print/export functionality for term sheets
- No interactive scenario sliders (scenarios are computed from fixed multipliers and product-specific configs)
