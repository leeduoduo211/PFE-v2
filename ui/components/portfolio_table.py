# ui/components/portfolio_table.py
"""Editable portfolio table with add/edit/clone/delete actions."""

import copy
from html import escape

import streamlit as st

from ui.components.term_sheet import render_term_sheet
from ui.theme import category_badge
from ui.utils.registry import INSTRUMENT_REGISTRY
from ui.utils.session import invalidate_results

_CAT_KIND = {
    "European": "european",
    "Path-dependent": "path_dependent",
    "Multi-asset": "multi_asset",
    "Periodic": "periodic",
}


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


def render_portfolio_table(key_prefix: str = "pt"):
    """Render the portfolio table from session_state['portfolio'].
    Returns the index of a trade to edit (or None).
    """
    portfolio = st.session_state["portfolio"]

    trade_word = "trade" if len(portfolio) == 1 else "trades"
    st.markdown(
        f'<div class="pfe-table-title">Portfolio '
        f'<span>({len(portfolio)} {trade_word})</span></div>',
        unsafe_allow_html=True,
    )

    if not portfolio:
        st.info("No trades yet. Use the trade builder to add instruments.")
        return None

    # Check if t=0 MtM data is available
    latest = st.session_state.get("latest_result", {})
    t0_mtm_list = latest.get("per_trade_t0_mtm", [])
    has_t0 = len(t0_mtm_list) == len(portfolio)

    if has_t0:
        cols = st.columns([2, 0.5, 1.8, 1.2, 1.2, 1.2, 0.8, 0.8, 0.8])
    else:
        cols = st.columns([2, 0.5, 2, 1.5, 1.5, 1, 1, 1])
    cols[0].markdown(_header("Trade ID"), unsafe_allow_html=True)
    cols[1].markdown(_header("Dir"), unsafe_allow_html=True)
    cols[2].markdown(_header("Type"), unsafe_allow_html=True)
    cols[3].markdown(_header("Maturity"), unsafe_allow_html=True)
    cols[4].markdown(_header("Notional"), unsafe_allow_html=True)
    if has_t0:
        cols[5].markdown(_header("t=0 MtM"), unsafe_allow_html=True)
        cols[6].markdown(_header("Edit"), unsafe_allow_html=True)
        cols[7].markdown(_header("Clone"), unsafe_allow_html=True)
        cols[8].markdown(_header("Delete"), unsafe_allow_html=True)
    else:
        cols[5].markdown(_header("Edit"), unsafe_allow_html=True)
        cols[6].markdown(_header("Clone"), unsafe_allow_html=True)
        cols[7].markdown(_header("Delete"), unsafe_allow_html=True)

    edit_idx = None
    for i, trade in enumerate(portfolio):
        if has_t0:
            cols = st.columns([2, 0.5, 1.8, 1.2, 1.2, 1.2, 0.8, 0.8, 0.8])
        else:
            cols = st.columns([2, 0.5, 2, 1.5, 1.5, 1, 1, 1])
        cols[0].markdown(
            _cell(escape(str(trade["trade_id"]), quote=True), mono=True),
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
            edit_col, clone_col, del_col = cols[6], cols[7], cols[8]
        else:
            edit_col, clone_col, del_col = cols[5], cols[6], cols[7]

        if edit_col.button("Edit", key=f"{key_prefix}_edit_{i}"):
            # Stash the trade for the trade builder to consume on next run
            st.session_state["_pending_edit_trade"] = copy.deepcopy(trade)
            portfolio.pop(i)
            invalidate_results()
            st.session_state["_switch_to_portfolio"] = True
            st.rerun()

        if clone_col.button("Clone", key=f"{key_prefix}_clone_{i}"):
            clone = copy.deepcopy(trade)
            clone["trade_id"] = f"{trade['trade_id']}_copy"
            portfolio.append(clone)
            invalidate_results()
            st.rerun()

        if del_col.button("Del", key=f"{key_prefix}_del_{i}"):
            portfolio.pop(i)
            invalidate_results()
            st.rerun()

        # Term-sheet view
        with st.expander(f"Term Sheet: {trade['trade_id']}", expanded=False):
            asset_names_list = st.session_state.get("market", {}).get("asset_names", [])
            market_spots = st.session_state.get("market", {}).get("spots", [])
            if asset_names_list:
                render_term_sheet(trade, asset_names_list, market_spots)
            else:
                st.caption("Add market data to see term-sheet details.")

    return edit_idx
