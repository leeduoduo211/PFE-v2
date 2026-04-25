# ui/components/portfolio_table.py
"""Editable portfolio table with add/edit/clone/delete actions."""

import copy

import streamlit as st

from ui.components.term_sheet import render_term_sheet
from ui.theme import category_badge
from ui.utils.registry import INSTRUMENT_REGISTRY

_CAT_KIND = {
    "European": "european",
    "Path-dependent": "path_dependent",
    "Multi-asset": "multi_asset",
    "Periodic": "periodic",
}


def render_portfolio_table(key_prefix: str = "pt"):
    """Render the portfolio table from session_state['portfolio'].
    Returns the index of a trade to edit (or None).
    """
    portfolio = st.session_state["portfolio"]

    st.subheader(f"Portfolio ({len(portfolio)} trades)")

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
    cols[0].write("**Trade ID**")
    cols[1].write("**Dir**")
    cols[2].write("**Type**")
    cols[3].write("**Maturity**")
    cols[4].write("**Notional**")
    if has_t0:
        cols[5].write("**t=0 MtM**")
        cols[6].write("**Edit**")
        cols[7].write("**Clone**")
        cols[8].write("**Delete**")
    else:
        cols[5].write("**Edit**")
        cols[6].write("**Clone**")
        cols[7].write("**Delete**")

    edit_idx = None
    for i, trade in enumerate(portfolio):
        if has_t0:
            cols = st.columns([2, 0.5, 1.8, 1.2, 1.2, 1.2, 0.8, 0.8, 0.8])
        else:
            cols = st.columns([2, 0.5, 2, 1.5, 1.5, 1, 1, 1])
        cols[0].write(trade["trade_id"])

        direction = trade.get("direction", "long")
        if direction == "short":
            cols[1].write(":red[S]")
        else:
            cols[1].write(":green[L]")

        inst_type = trade["instrument_type"]
        spec = INSTRUMENT_REGISTRY.get(inst_type, {})
        cat_label = spec.get("category", "European")
        cat_kind = _CAT_KIND.get(cat_label, "european")
        inst_label = spec.get("label", inst_type)
        mod_suffix = ""
        if trade.get("modifiers"):
            mod_names = [m["type"] for m in trade["modifiers"]]
            mod_suffix = (
                ' <span style="color:#94a3b8;font-size:11px;">'
                + " \u2192 ".join(mod_names) + " \u2192</span>"
            )
        cols[2].markdown(
            mod_suffix + " " + category_badge(cat_label.upper(), cat_kind)
            + f' <span style="color:#475569;font-size:12px;margin-left:4px;">{inst_label}</span>',
            unsafe_allow_html=True,
        )
        cols[3].write(f"{trade['params']['maturity']:.2f}Y")
        cols[4].write(f"{trade['params']['notional']:,.0f}")

        if has_t0:
            mtm_val = t0_mtm_list[i]
            if mtm_val > 0:
                cols[5].write(f":green[{mtm_val:,.0f}]")
            elif mtm_val < 0:
                cols[5].write(f":red[{mtm_val:,.0f}]")
            else:
                cols[5].write("0")
            edit_col, clone_col, del_col = cols[6], cols[7], cols[8]
        else:
            edit_col, clone_col, del_col = cols[5], cols[6], cols[7]

        if edit_col.button("Edit", key=f"{key_prefix}_edit_{i}"):
            # Stash the trade for the trade builder to consume on next run
            st.session_state["_pending_edit_trade"] = copy.deepcopy(trade)
            portfolio.pop(i)
            st.session_state["_switch_to_portfolio"] = True
            st.rerun()

        if clone_col.button("Clone", key=f"{key_prefix}_clone_{i}"):
            clone = copy.deepcopy(trade)
            clone["trade_id"] = f"{trade['trade_id']}_copy"
            portfolio.append(clone)
            st.rerun()

        if del_col.button("Del", key=f"{key_prefix}_del_{i}"):
            portfolio.pop(i)
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
