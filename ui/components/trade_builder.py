"""Trade builder component with dynamic parameter forms and modifier stacking.

Returns a trade spec dict compatible with session state portfolio format:
  {
      "trade_id":        str,
      "instrument_type": str,   # key into INSTRUMENT_REGISTRY
      "params":          dict,  # constructor kwargs (assets, maturity, notional, ...)
      "modifiers":       list,  # [{"type": str, "params": dict}, ...]
  }
"""

import streamlit as st
from ui.utils.registry import INSTRUMENT_REGISTRY, MODIFIER_REGISTRY
from ui.utils.session import get_asset_names
from ui.components.payoff_display import payoff_formula, payoff_sparkline


# ---------------------------------------------------------------------------
# Edit-flow helper: seed widget session state from an existing trade spec.
# Must be called BEFORE any trade-builder widget is instantiated on the run,
# otherwise Streamlit raises "cannot be modified after widget instantiated".
# ---------------------------------------------------------------------------

def seed_builder_from_trade(trade: dict, key_prefix: str) -> None:
    ss = st.session_state
    params = trade.get("params", {}) or {}
    modifiers = trade.get("modifiers", []) or []
    inst_type = trade.get("instrument_type")
    inst_spec = INSTRUMENT_REGISTRY.get(inst_type)

    # Product (selectbox holds the label, not the type key)
    if inst_spec is not None:
        ss[f"{key_prefix}_product"] = inst_spec["label"]

    # Common fields
    ss[f"{key_prefix}_trade_id"] = trade.get("trade_id", "")
    ss[f"{key_prefix}_maturity"] = float(params.get("maturity", 1.0))
    ss[f"{key_prefix}_notional"] = float(params.get("notional", 1_000_000.0))
    ss[f"{key_prefix}_direction"] = "Short" if trade.get("direction") == "short" else "Long"

    # Assets — single-select uses `_asset_0`, multi-select uses `_assets_multi`
    assets = list(params.get("assets", []) or [])
    if inst_spec is not None:
        min_n, max_n = _parse_n_assets_spec(inst_spec["n_assets"])
    else:
        min_n, max_n = 1, 1
    if min_n == max_n == 1:
        if assets:
            ss[f"{key_prefix}_asset_0"] = assets[0]
    else:
        if assets:
            ss[f"{key_prefix}_assets_multi"] = assets

    # Instrument-specific fields
    if inst_spec is not None:
        for field in inst_spec["fields"]:
            fname = field["name"]
            if fname not in params:
                continue
            val = params[fname]
            ftype = field["type"]
            fkey = f"{key_prefix}_inst_{fname}"
            if ftype in ("float_list", "select_list"):
                for i, v in enumerate(val or []):
                    ss[f"{fkey}_{i}"] = v
            elif ftype == "schedule":
                # Schedule widgets regenerate from maturity; skip.
                pass
            else:
                ss[fkey] = val

    # Modifiers
    ss[f"{key_prefix}_modifier_count"] = len(modifiers)
    for i, mod in enumerate(modifiers):
        mod_type = mod.get("type")
        mod_spec = MODIFIER_REGISTRY.get(mod_type)
        if mod_spec is None:
            continue
        mod_key = f"{key_prefix}_mod_{i}"
        ss[f"{mod_key}_type"] = mod_spec["label"]
        mod_params = mod.get("params", {}) or {}
        for field in mod_spec["fields"]:
            fname = field["name"]
            if fname not in mod_params:
                continue
            val = mod_params[fname]
            ftype = field["type"]
            fkey = f"{mod_key}_{fname}"
            if ftype in ("float_list", "select_list"):
                for j, v in enumerate(val or []):
                    ss[f"{fkey}_{j}"] = v
            elif ftype == "schedule":
                pass
            else:
                ss[fkey] = val


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _parse_n_assets_spec(spec) -> tuple[int, int]:
    """Return (min_assets, max_assets) from n_assets spec (int or "2-5")."""
    if isinstance(spec, int):
        return spec, spec
    if isinstance(spec, str) and "-" in spec:
        lo, hi = spec.split("-", 1)
        return int(lo), int(hi)
    return 1, 1


def _render_field(field: dict, key: str, asset_names: list[str], n_selected: int):
    """Render a single field widget and return its value.

    Parameters
    ----------
    field:        field_spec dict from registry
    key:          unique Streamlit widget key
    asset_names:  current asset names (for asset_select types)
    n_selected:   number of assets already selected for this trade
    """
    ftype   = field["type"]
    label   = field["label"]
    default = field.get("default")
    help_   = field.get("help", "")

    # ---- float ----
    if ftype == "float":
        val = float(default) if default is not None else 0.0
        return st.number_input(label, value=val, format="%.4f", help=help_, key=key)

    # ---- select ----
    if ftype == "select":
        choices = field.get("choices", [])
        idx = choices.index(default) if default in choices else 0
        return st.selectbox(label, choices, index=idx, help=help_, key=key)

    # ---- float_list ----
    if ftype == "float_list":
        defaults = default if isinstance(default, list) else []
        count = max(n_selected, len(defaults))
        st.caption(label + (f" — {help_}" if help_ else ""))
        values = []
        cols = st.columns(min(count, 5))
        for i in range(count):
            d = float(defaults[i]) if i < len(defaults) else 0.0
            v = cols[i % len(cols)].number_input(
                f"[{i}]", value=d, format="%.4f", key=f"{key}_{i}",
                label_visibility="visible",
            )
            values.append(v)
        return values

    # ---- select_list ----
    if ftype == "select_list":
        choices  = field.get("choices", [])
        defaults = default if isinstance(default, list) else []
        count = max(n_selected, len(defaults))
        st.caption(label + (f" — {help_}" if help_ else ""))
        values = []
        cols = st.columns(min(count, 5))
        for i in range(count):
            d   = defaults[i] if i < len(defaults) else choices[0]
            idx = choices.index(d) if d in choices else 0
            v   = cols[i % len(cols)].selectbox(
                f"[{i}]", choices, index=idx, key=f"{key}_{i}",
                label_visibility="visible",
            )
            values.append(v)
        return values

    # ---- asset_select ----
    if ftype == "asset_select":
        if not asset_names:
            st.warning(f"{label}: no assets defined yet")
            return 0
        idx = st.selectbox(
            label,
            options=list(range(len(asset_names))),
            format_func=lambda i: f"[{i}] {asset_names[i]}",
            help=help_,
            key=key,
        )
        return int(idx)

    # ---- asset_select_optional ----
    if ftype == "asset_select_optional":
        if not asset_names:
            st.warning(f"{label}: no assets defined yet")
            return None
        options = [None] + list(range(len(asset_names)))
        fmt = lambda i: "None (first asset)" if i is None else f"[{i}] {asset_names[i]}"
        val = st.selectbox(label, options=options, format_func=fmt, help=help_, key=key)
        return val  # None or int

    # ---- schedule ----
    if ftype == "schedule":
        st.caption(label + (f" — {help_}" if help_ else ""))
        sched_mode = st.radio(
            "Schedule type",
            ["Monthly", "Weekly", "Custom"],
            horizontal=True,
            key=f"{key}_mode",
        )
        mat_key = f"{key}_maturity_ref"
        # We can't directly read the maturity widget here, so we ask the user
        # to supply the maturity numerically for auto-generation.
        if sched_mode == "Monthly":
            mat = st.number_input(
                "Maturity for schedule (years)", value=1.0, min_value=0.01,
                format="%.2f", key=f"{key}_mat",
            )
            n_months = max(1, round(mat * 12))
            dates = [round((i + 1) / 12, 6) for i in range(n_months) if (i + 1) / 12 <= mat + 1e-9]
            st.caption(f"Generated {len(dates)} monthly dates")
            return dates

        if sched_mode == "Weekly":
            mat = st.number_input(
                "Maturity for schedule (years)", value=1.0, min_value=0.01,
                format="%.2f", key=f"{key}_mat",
            )
            n_weeks = max(1, round(mat * 52))
            dates = [round((i + 1) / 52, 6) for i in range(n_weeks) if (i + 1) / 52 <= mat + 1e-9]
            st.caption(f"Generated {len(dates)} weekly dates")
            return dates

        # Custom: free-text comma-separated
        raw = st.text_input(
            "Comma-separated times (years), e.g. 0.25, 0.5, 0.75, 1.0",
            value="0.25, 0.5, 0.75, 1.0",
            key=f"{key}_custom",
        )
        try:
            dates = [float(x.strip()) for x in raw.split(",") if x.strip()]
            dates = sorted(set(dates))
            st.caption(f"{len(dates)} observation dates")
            return dates
        except ValueError:
            st.error("Invalid schedule — enter comma-separated numbers")
            return []

    # Fallback: treat as string
    return st.text_input(label, value=str(default or ""), help=help_, key=key)


def _render_modifier(idx, key_prefix, asset_names, n_trade_assets):
    """Render one modifier block. Returns {"type": str, "params": dict} or None."""
    mod_key = f"{key_prefix}_mod_{idx}"

    mod_names  = list(MODIFIER_REGISTRY.keys())
    mod_labels = [MODIFIER_REGISTRY[k]["label"] for k in mod_names]

    chosen_label = st.selectbox(
        f"Modifier #{idx + 1} type",
        mod_labels,
        key=f"{mod_key}_type",
    )
    chosen_type = mod_names[mod_labels.index(chosen_label)]
    spec = MODIFIER_REGISTRY[chosen_type]

    params = {}
    for field in spec["fields"]:
        fkey = f"{mod_key}_{field['name']}"
        val = _render_field(field, fkey, asset_names, n_trade_assets)
        params[field["name"]] = val

    return {"type": chosen_type, "params": params}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def render_trade_builder(key_prefix="tb"):
    """Render the full trade builder form.

    Parameters
    ----------
    key_prefix : str
        Namespace prefix for all Streamlit widget keys.  Use distinct prefixes
        when embedding the builder in multiple locations.

    Returns
    -------
    dict or None
        Trade spec dict on "Add to Portfolio" click, otherwise None.
    """
    # Consume any pending-edit payload before instantiating widgets, so
    # session_state seeding happens pre-widget-creation (Streamlit requirement).
    _pending = st.session_state.pop("_pending_edit_trade", None)
    if _pending is not None:
        seed_builder_from_trade(_pending, key_prefix)

    asset_names = get_asset_names()

    # -----------------------------------------------------------------------
    # 1. Product selector
    # -----------------------------------------------------------------------
    inst_keys   = list(INSTRUMENT_REGISTRY.keys())
    inst_labels = [INSTRUMENT_REGISTRY[k]["label"] for k in inst_keys]

    chosen_label = st.selectbox(
        "Product type",
        inst_labels,
        key=f"{key_prefix}_product",
    )
    chosen_type = inst_keys[inst_labels.index(chosen_label)]
    inst_spec   = INSTRUMENT_REGISTRY[chosen_type]
    n_assets_spec = inst_spec["n_assets"]
    min_assets, max_assets = _parse_n_assets_spec(n_assets_spec)

    # -----------------------------------------------------------------------
    # 2. Common fields: trade_id, maturity, notional
    # -----------------------------------------------------------------------
    col1, col2, col3, col4 = st.columns([2, 1.5, 1.5, 1])
    with col1:
        trade_id = st.text_input("Trade ID", value="TRD_001", key=f"{key_prefix}_trade_id")
    with col2:
        maturity = st.number_input(
            "Maturity (years)", value=1.0, min_value=0.01, format="%.4f",
            key=f"{key_prefix}_maturity",
        )
    with col3:
        notional = st.number_input(
            "Notional", value=1_000_000.0, min_value=1.0, format="%.2f",
            key=f"{key_prefix}_notional",
        )
    with col4:
        direction = st.selectbox(
            "Direction", ["Long", "Short"],
            key=f"{key_prefix}_direction",
        )

    # -----------------------------------------------------------------------
    # 3. Asset selection
    # -----------------------------------------------------------------------

    selected_assets: list[str] = []

    if not asset_names:
        st.warning("No assets defined. Add assets in the Market Data step first.")
        n_selected = 0
    else:
        if min_assets == max_assets and min_assets == 1:
            # Single select
            asset = st.selectbox(
                "Underlying asset",
                asset_names,
                key=f"{key_prefix}_asset_0",
            )
            selected_assets = [asset]
            n_selected = 1

        elif min_assets == max_assets:
            # Exact-N multiselect
            selected_assets = st.multiselect(
                f"Select exactly {min_assets} assets",
                asset_names,
                default=asset_names[:min_assets],
                key=f"{key_prefix}_assets_multi",
            )
            n_selected = len(selected_assets)
            if n_selected != min_assets:
                st.warning(f"Please select exactly {min_assets} assets (currently {n_selected}).")

        else:
            # Range multiselect  (e.g. "2-5")
            default_pick = asset_names[:min_assets]
            selected_assets = st.multiselect(
                f"Select {min_assets}–{max_assets} assets",
                asset_names,
                default=default_pick,
                key=f"{key_prefix}_assets_multi",
            )
            n_selected = len(selected_assets)
            if not (min_assets <= n_selected <= max_assets):
                st.warning(
                    f"Please select between {min_assets} and {max_assets} assets "
                    f"(currently {n_selected})."
                )

    # -----------------------------------------------------------------------
    # 4. Dynamic instrument fields
    # -----------------------------------------------------------------------
    instrument_params: dict = {}
    for field in inst_spec["fields"]:
        fkey = f"{key_prefix}_inst_{field['name']}"
        val = _render_field(field, fkey, asset_names, n_selected)
        instrument_params[field["name"]] = val

    # -----------------------------------------------------------------------
    # 5. Modifier stacking
    # -----------------------------------------------------------------------
    st.caption("Modifiers (optional)")

    mod_count_key = f"{key_prefix}_modifier_count"
    if mod_count_key not in st.session_state:
        st.session_state[mod_count_key] = 0

    col_add, col_remove, _ = st.columns([1, 1, 4])
    with col_add:
        if st.button("+ Add modifier", key=f"{key_prefix}_add_mod"):
            st.session_state[mod_count_key] += 1
    with col_remove:
        if st.button("- Remove last", key=f"{key_prefix}_rem_mod"):
            if st.session_state[mod_count_key] > 0:
                st.session_state[mod_count_key] -= 1

    n_mods = st.session_state[mod_count_key]
    modifiers: list[dict] = []

    for i in range(n_mods):
        with st.expander(f"Modifier #{i + 1}", expanded=True):
            mod = _render_modifier(i, key_prefix, asset_names, n_selected)
            if mod is not None:
                modifiers.append(mod)

    # -----------------------------------------------------------------------
    # 5.5. Payoff preview
    # -----------------------------------------------------------------------
    # Validation gate: asset count must satisfy spec
    assets_valid = (
        (min_assets == max_assets and n_selected == min_assets) or
        (min_assets != max_assets and min_assets <= n_selected <= max_assets)
    ) if asset_names else False

    if asset_names and assets_valid:
        preview_spec = {
            "direction": direction.lower(),
            "instrument_type": chosen_type,
            "params": {"maturity": maturity, "notional": notional,
                        "assets": selected_assets, **instrument_params},
            "modifiers": modifiers,
        }
        st.caption(payoff_formula(preview_spec))
        fig = payoff_sparkline(preview_spec, asset_names)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False},
                        key=f"{key_prefix}_payoff_preview")

    # -----------------------------------------------------------------------
    # 6. "Add to Portfolio" button
    # -----------------------------------------------------------------------

    if not asset_names:
        st.button("Add to Portfolio", disabled=True, key=f"{key_prefix}_submit")
        st.caption("Define market assets first.")
        return None

    if not assets_valid:
        st.button("Add to Portfolio", disabled=True, key=f"{key_prefix}_submit")
        return None

    if st.button("Add to Portfolio", type="primary", key=f"{key_prefix}_submit"):
        # Assemble params dict
        params: dict = {
            "maturity":  maturity,
            "notional":  notional,
            "assets":    selected_assets,
            **instrument_params,
        }

        trade_spec = {
            "trade_id":        trade_id.strip() or f"TRD_{id(params)}",
            "direction":       direction.lower(),
            "instrument_type": chosen_type,
            "params":          params,
            "modifiers":       modifiers,
        }
        return trade_spec

    return None
