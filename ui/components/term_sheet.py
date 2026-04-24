"""Read-only term-sheet renderer for portfolio table expanders.

Renders a trade spec dict as formatted HTML using st.markdown — no input widgets.
Counterpart to trade_builder.py: displays values instead of collecting them.
"""

import streamlit as st

from ui.components.payoff_display import payoff_formula, payoff_sparkline
from ui.components.trade_economics import render_trade_economics
from ui.utils.product_content import (
    CATEGORY_COLORS,
    MODIFIER_GROUP_COLORS,
    MODIFIER_SECTIONS,
    PRODUCT_DESCRIPTIONS,
    PRODUCT_SECTIONS,
)
from ui.utils.registry import INSTRUMENT_REGISTRY, MODIFIER_REGISTRY

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _render_readonly_value(label: str, value, field_type: str) -> str:
    """Return HTML string for a single read-only field.

    Handles types:
        float       — formatted with :.4g
        schedule    — shows count (e.g. "12 dates")
        float_list  — comma-joined items each :.4g
        select_list — comma-joined items as strings
        else        — str(value)
    """
    if field_type == "float":
        try:
            display = f"{float(value):.4g}"
        except (TypeError, ValueError):
            display = str(value)
    elif field_type == "schedule":
        try:
            count = len(value) if value else 0
            display = f"{count} dates"
        except TypeError:
            display = str(value)
    elif field_type == "float_list":
        try:
            display = ", ".join(f"{float(v):.4g}" for v in (value or []))
        except (TypeError, ValueError):
            display = str(value)
    elif field_type == "select_list":
        try:
            display = ", ".join(str(v) for v in (value or []))
        except TypeError:
            display = str(value)
    else:
        display = str(value) if value is not None else "—"

    return (
        f'<div style="min-width:100px;margin-right:20px;">'
        f'<div style="font-size:10px;color:#94a3b8;text-transform:uppercase;'
        f'letter-spacing:0.5px;font-weight:600;">{label}</div>'
        f'<div style="font-size:13px;color:#1e293b;font-weight:500;">{display}</div>'
        f'</div>'
    )


def _flex_row(html_items: list[str]) -> str:
    """Wrap HTML items in a flex row div."""
    inner = "".join(html_items)
    return (
        f'<div style="display:flex;flex-wrap:wrap;gap:8px 4px;'
        f'padding:6px 0 4px 0;">{inner}</div>'
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def render_term_sheet(
    spec: dict,
    asset_names: list,
    market_spots: list,
) -> None:
    """Render a read-only term sheet for a trade spec.

    Parameters
    ----------
    spec:          Trade spec dict (trade_id, instrument_type, direction, params, modifiers).
    asset_names:   Asset names aligned with market_spots.
    market_spots:  Current spot prices (list[float]).
    """
    inst_type = spec.get("instrument_type", "")
    inst_spec = INSTRUMENT_REGISTRY.get(inst_type, {})
    params = spec.get("params", {}) or {}
    direction = spec.get("direction", "long")
    trade_id = spec.get("trade_id", "")
    modifiers = spec.get("modifiers", []) or []

    # -----------------------------------------------------------------------
    # A. Product header — category badge + label + description
    # -----------------------------------------------------------------------
    category = inst_spec.get("category", "")
    cat_color = CATEGORY_COLORS.get(category, "#94a3b8")
    label = inst_spec.get("label", inst_type)
    description = PRODUCT_DESCRIPTIONS.get(inst_type, "")

    st.markdown(
        f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;">'
        f'<span style="background:{cat_color};color:#fff;padding:2px 8px;border-radius:4px;'
        f'font-size:11px;font-weight:600;">{category}</span>'
        f'<span style="font-weight:700;font-size:15px;color:#1e293b;">{label}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )
    if description:
        st.caption(description)

    # -----------------------------------------------------------------------
    # B. Key terms row — direction, trade_id, maturity, notional, underlyings
    # -----------------------------------------------------------------------
    maturity = params.get("maturity", "")
    notional = params.get("notional", "")
    assets = params.get("assets", []) or []
    underlyings = ", ".join(str(a) for a in assets) if assets else "—"

    key_items = [
        _render_readonly_value("Direction", direction.capitalize(), "str"),
        _render_readonly_value("Trade ID", trade_id, "str"),
        _render_readonly_value("Maturity (yrs)", maturity, "float"),
        _render_readonly_value("Notional", f"{float(notional):,.0f}" if notional else "—", "str"),
        _render_readonly_value("Underlyings", underlyings, "str"),
    ]
    st.markdown(_flex_row(key_items), unsafe_allow_html=True)

    # -----------------------------------------------------------------------
    # C. Grouped instrument sections (from PRODUCT_SECTIONS)
    # -----------------------------------------------------------------------
    sections = PRODUCT_SECTIONS.get(inst_type, [])
    fields_by_name = {f["name"]: f for f in inst_spec.get("fields", [])}

    for section in sections:
        color = section.get("color", "#94a3b8")
        sec_label = section.get("label", "")
        sec_help = section.get("help", "")

        st.markdown(
            f'<div style="border-left:3px solid {color};padding-left:12px;'
            f'margin-bottom:4px;margin-top:8px;">'
            f'<div style="font-weight:600;color:#1e293b;font-size:13px;">{sec_label}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
        if sec_help:
            st.caption(sec_help)

        field_items = []
        for field_name in section.get("fields", []):
            field = fields_by_name.get(field_name)
            if field is None:
                continue
            val = params.get(field_name)
            field_items.append(
                _render_readonly_value(field["label"], val, field["type"])
            )
        if field_items:
            st.markdown(_flex_row(field_items), unsafe_allow_html=True)

    # -----------------------------------------------------------------------
    # D. Modifier sections (from MODIFIER_SECTIONS)
    # -----------------------------------------------------------------------
    for mod in modifiers:
        mod_type = mod.get("type", "")
        mod_params = mod.get("params", {}) or {}
        mod_spec = MODIFIER_REGISTRY.get(mod_type)
        section_config = MODIFIER_SECTIONS.get(mod_type, {})

        group = section_config.get("group", "")
        group_style = MODIFIER_GROUP_COLORS.get(group, {})
        mod_label = mod_spec["label"] if mod_spec else mod_type

        st.markdown(
            f'<div style="border-left:3px solid {group_style.get("color","#94a3b8")};'
            f'padding-left:12px;margin-top:8px;">'
            f'<span style="font-weight:600;color:#1e293b;font-size:13px;">'
            f'Modifier: {mod_label}</span> '
            f'<span style="background:{group_style.get("badge_bg","#f1f5f9")};'
            f'color:{group_style.get("badge_text","#64748b")};'
            f'padding:1px 6px;border-radius:3px;font-size:9px;font-weight:600;">'
            f'{group.upper()}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

        if mod_spec:
            mod_fields_by_name = {f["name"]: f for f in mod_spec.get("fields", [])}
            all_field_names = (
                list(section_config.get("core_fields", []))
                + list(section_config.get("observation_fields", []))
                + list(section_config.get("extra_fields", []))
            )
            mod_items = []
            for field_name in all_field_names:
                field = mod_fields_by_name.get(field_name)
                if field is None:
                    continue
                val = mod_params.get(field_name)
                mod_items.append(
                    _render_readonly_value(field["label"], val, field["type"])
                )
            if mod_items:
                st.markdown(_flex_row(mod_items), unsafe_allow_html=True)

    # -----------------------------------------------------------------------
    # E. Economics description
    # -----------------------------------------------------------------------
    render_trade_economics(spec, asset_names, market_spots)

    # -----------------------------------------------------------------------
    # F. Formula
    # -----------------------------------------------------------------------
    formula = payoff_formula(spec)
    st.caption(formula)

    # -----------------------------------------------------------------------
    # G. Sparkline
    # -----------------------------------------------------------------------
    fig = payoff_sparkline(spec, asset_names)
    if fig is not None:
        st.plotly_chart(
            fig,
            use_container_width=True,
            config={"displayModeBar": False},
            key=f"ts_spark_{spec.get('trade_id', 'x')}",
        )
