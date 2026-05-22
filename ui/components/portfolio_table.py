# ui/components/portfolio_table.py
"""Editable portfolio table with add/edit/clone/delete actions."""

import copy
from html import escape

import streamlit as st

from ui.components.term_sheet import render_term_sheet
from ui.theme import category_badge
from ui.utils.registry import INSTRUMENT_REGISTRY
from ui.utils.session import invalidate_results, request_portfolio_tab

_CAT_KIND = {
    "European": "european",
    "Path-dependent": "path_dependent",
    "Multi-asset": "multi_asset",
    "Periodic": "periodic",
}


def _format_notional(value, *, compact=False, signed=False):
    """Format a monetary/notional value for compact portfolio display."""
    amount = float(value or 0.0)
    absolute = abs(amount)

    if compact and absolute >= 1_000_000_000:
        body = f"{absolute / 1_000_000_000:.2f}B"
    elif compact and absolute >= 1_000_000:
        body = f"{absolute / 1_000_000:.2f}M"
    elif compact and absolute >= 1_000:
        body = f"{absolute / 1_000:.0f}K"
    else:
        body = f"{absolute:,.0f}"

    if amount < 0:
        return f"-{body}"
    if signed and amount > 0:
        return f"+{body}"
    return body


def _trade_notional(trade):
    params = trade.get("params", {}) or {}
    return float(params.get("notional", 0.0) or 0.0)


def _trade_signed_notional(trade):
    sign = -1.0 if trade.get("direction") == "short" else 1.0
    return _trade_notional(trade) * sign


def _portfolio_summary_rows(portfolio, latest_result=None):
    """Return portfolio summary rows as (label, value) pairs."""
    gross = sum(abs(_trade_notional(trade)) for trade in portfolio)
    net = sum(_trade_signed_notional(trade) for trade in portfolio)
    max_maturity = max(
        (
            float((trade.get("params", {}) or {}).get("maturity", 0.0) or 0.0)
            for trade in portfolio
        ),
        default=0.0,
    )

    t0_status = "No run"
    if latest_result:
        t0_values = latest_result.get("per_trade_t0_mtm", []) or []
        if len(t0_values) == len(portfolio) and portfolio:
            t0_status = _format_notional(
                sum(float(v) for v in t0_values),
                compact=True,
                signed=True,
            )
        else:
            t0_status = "Run stale"

    return [
        ("Trades", str(len(portfolio))),
        ("Gross notional", _format_notional(gross, compact=True)),
        ("Net notional", _format_notional(net, compact=True, signed=True)),
        ("Max maturity", f"{max_maturity:.2f}y"),
        ("t=0 MtM", t0_status),
    ]


def _resolve_selected_trade_id(portfolio, selected_trade_id):
    trade_ids = [str(trade.get("trade_id", "")) for trade in portfolio]
    if selected_trade_id in trade_ids:
        return selected_trade_id
    if trade_ids:
        return trade_ids[0]
    return None


def _next_clone_trade_id(portfolio, trade_id):
    existing = {str(trade.get("trade_id", "")) for trade in portfolio}
    base = f"{trade_id}_copy"
    if base not in existing:
        return base
    suffix = 2
    while f"{base}_{suffix}" in existing:
        suffix += 1
    return f"{base}_{suffix}"


def _header(label: str):
    return (
        f'<div class="pfe-table-head">{escape(str(label), quote=True)}</div>'
    )


def _cell(content: str, *, mono: bool = False, center: bool = False):
    classes = ["pfe-table-cell"]
    if mono:
        classes.append("mono")
    if center:
        classes.append("center")
    return f'<div class="{" ".join(classes)}">{content}</div>'


def _render_summary_strip(portfolio, latest_result):
    items = []
    for label, value in _portfolio_summary_rows(portfolio, latest_result):
        items.append(
            '<div class="pfe-portfolio-kpi">'
            f'<div class="pfe-portfolio-kpi-label">{escape(label, quote=True)}</div>'
            f'<div class="pfe-portfolio-kpi-value">{escape(value, quote=True)}</div>'
            '</div>'
        )
    st.markdown(
        f'<div class="pfe-portfolio-summary">{"".join(items)}</div>',
        unsafe_allow_html=True,
    )


def _selected_trade(portfolio, selected_trade_id):
    for trade in portfolio:
        if str(trade.get("trade_id", "")) == selected_trade_id:
            return trade
    return None


def _render_detail_panel(trade):
    trade_id = escape(str(trade.get("trade_id", "")), quote=True)
    inst_type = trade.get("instrument_type", "")
    inst_spec = INSTRUMENT_REGISTRY.get(inst_type, {})
    inst_label = escape(str(inst_spec.get("label", inst_type)), quote=True)

    st.markdown(
        '<div class="pfe-detail-panel">'
        '<div class="pfe-detail-head">'
        '<div>'
        f'<div class="pfe-detail-title">Selected trade: {trade_id}</div>'
        f'<div class="pfe-detail-sub">{inst_label}</div>'
        '</div>'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    asset_names_list = st.session_state.get("market", {}).get("asset_names", [])
    market_spots = st.session_state.get("market", {}).get("spots", [])
    if asset_names_list:
        render_term_sheet(trade, asset_names_list, market_spots)
    else:
        st.caption("Add market data to see term-sheet details.")


def render_portfolio_table(key_prefix: str = "pt", builder_open_key=None):
    """Render the portfolio table from session_state['portfolio']."""
    portfolio = st.session_state["portfolio"]
    latest = st.session_state.get("latest_result") or {}

    _render_summary_strip(portfolio, latest)

    trade_word = "trade" if len(portfolio) == 1 else "trades"
    st.markdown(
        '<div class="pfe-portfolio-toolbar-title">Portfolio Review</div>'
        f'<div class="pfe-portfolio-toolbar-sub">{len(portfolio)} {trade_word}</div>',
        unsafe_allow_html=True,
    )

    if not portfolio:
        st.markdown(
            '<div class="pfe-portfolio-empty">'
            "No trades yet. Use Add Trade to build the portfolio."
            '</div>',
            unsafe_allow_html=True,
        )
        return None

    t0_mtm_list = latest.get("per_trade_t0_mtm", [])
    has_t0 = len(t0_mtm_list) == len(portfolio)
    selected_key = f"{key_prefix}_selected_trade_id"
    selected_trade_id = _resolve_selected_trade_id(
        portfolio,
        st.session_state.get(selected_key),
    )
    st.session_state[selected_key] = selected_trade_id

    if has_t0:
        widths = [1.45, 0.35, 1.95, 0.85, 1.0, 1.0, 0.68, 0.68, 0.78, 0.68]
    else:
        widths = [1.45, 0.35, 2.2, 0.9, 1.05, 0.68, 0.68, 0.78, 0.68]

    cols = st.columns(widths)
    cols[0].markdown(_header("Trade ID"), unsafe_allow_html=True)
    cols[1].markdown(_header("Dir"), unsafe_allow_html=True)
    cols[2].markdown(_header("Type"), unsafe_allow_html=True)
    cols[3].markdown(_header("Maturity"), unsafe_allow_html=True)
    cols[4].markdown(_header("Notional"), unsafe_allow_html=True)
    if has_t0:
        cols[5].markdown(_header("t=0 MtM"), unsafe_allow_html=True)
        cols[6].markdown(_header("View"), unsafe_allow_html=True)
        cols[7].markdown(_header("Edit"), unsafe_allow_html=True)
        cols[8].markdown(_header("Clone"), unsafe_allow_html=True)
        cols[9].markdown(_header("Delete"), unsafe_allow_html=True)
    else:
        cols[5].markdown(_header("View"), unsafe_allow_html=True)
        cols[6].markdown(_header("Edit"), unsafe_allow_html=True)
        cols[7].markdown(_header("Clone"), unsafe_allow_html=True)
        cols[8].markdown(_header("Delete"), unsafe_allow_html=True)

    for i, trade in enumerate(portfolio):
        cols = st.columns(widths)
        trade_id = str(trade["trade_id"])
        is_selected = trade_id == selected_trade_id
        selected_dot = '<span class="pfe-selected-dot"></span>' if is_selected else ""
        cols[0].markdown(
            _cell(selected_dot + escape(trade_id, quote=True), mono=True),
            unsafe_allow_html=True,
        )

        direction = trade.get("direction", "long")
        if direction == "short":
            cols[1].markdown(
                _cell('<span class="pfe-dir-short">S</span>', center=True),
                unsafe_allow_html=True,
            )
        else:
            cols[1].markdown(
                _cell('<span class="pfe-dir-long">L</span>', center=True),
                unsafe_allow_html=True,
            )

        inst_type = trade["instrument_type"]
        spec = INSTRUMENT_REGISTRY.get(inst_type, {})
        cat_label = spec.get("category", "European")
        cat_kind = _CAT_KIND.get(cat_label, "european")
        inst_label = spec.get("label", inst_type)
        mod_suffix = ""
        if trade.get("modifiers"):
            mod_names = [escape(str(m["type"]), quote=True) for m in trade["modifiers"]]
            mod_suffix = (
                ' <span style="color:#94a3b8;font-size:11px;">'
                + " \u2192 ".join(mod_names) + " \u2192</span>"
            )
        cols[2].markdown(
            _cell(
                mod_suffix + " " + category_badge(cat_label.upper(), cat_kind)
                + f' <span style="color:#475569;font-size:12px;margin-left:4px;">'
                f'{escape(str(inst_label), quote=True)}</span>'
            ),
            unsafe_allow_html=True,
        )
        cols[3].markdown(
            _cell(f"{trade['params']['maturity']:.2f}Y", mono=True),
            unsafe_allow_html=True,
        )
        cols[4].markdown(
            _cell(f"{trade['params']['notional']:,.0f}", mono=True),
            unsafe_allow_html=True,
        )

        if has_t0:
            mtm_val = t0_mtm_list[i]
            if mtm_val > 0:
                mtm_html = f'<span class="pfe-pos">{mtm_val:,.0f}</span>'
            elif mtm_val < 0:
                mtm_html = f'<span class="pfe-neg">{mtm_val:,.0f}</span>'
            else:
                mtm_html = '<span class="pfe-num">0</span>'
            cols[5].markdown(_cell(mtm_html), unsafe_allow_html=True)
            view_col, edit_col, clone_col, del_col = cols[6], cols[7], cols[8], cols[9]
        else:
            view_col, edit_col, clone_col, del_col = cols[5], cols[6], cols[7], cols[8]

        if view_col.button(
            "View",
            key=f"{key_prefix}_view_{i}",
            disabled=is_selected,
        ):
            st.session_state[selected_key] = trade_id
            request_portfolio_tab()
            st.rerun()

        if edit_col.button("Edit", key=f"{key_prefix}_edit_{i}"):
            # Stash the trade for the trade builder to consume on next run
            st.session_state["_pending_edit_trade"] = copy.deepcopy(trade)
            if builder_open_key:
                st.session_state[builder_open_key] = True
            portfolio.pop(i)
            st.session_state[selected_key] = _resolve_selected_trade_id(
                portfolio,
                selected_trade_id,
            )
            invalidate_results()
            request_portfolio_tab()
            st.rerun()

        if clone_col.button("Clone", key=f"{key_prefix}_clone_{i}"):
            clone = copy.deepcopy(trade)
            clone["trade_id"] = _next_clone_trade_id(portfolio, trade_id)
            portfolio.append(clone)
            st.session_state[selected_key] = str(clone["trade_id"])
            invalidate_results()
            request_portfolio_tab()
            st.rerun()

        if del_col.button("Del", key=f"{key_prefix}_del_{i}"):
            portfolio.pop(i)
            st.session_state[selected_key] = _resolve_selected_trade_id(
                portfolio,
                selected_trade_id,
            )
            invalidate_results()
            request_portfolio_tab()
            st.rerun()

    selected = _selected_trade(portfolio, selected_trade_id)
    if selected:
        _render_detail_panel(selected)

    return selected_trade_id
