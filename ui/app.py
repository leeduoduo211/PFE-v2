"""PFE-v2 Streamlit entry point — tab-based layout with sidebar."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st

st.set_page_config(
    page_title="PFE-v2",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)

from ui.theme import apply_theme, section_label, sidebar_portfolio_item
from ui.utils.session import init_session_state
from ui.utils.runner import run_pfe_calculation
from ui.components.market_data_input import render_market_data_input
from ui.components.trade_builder import render_trade_builder
from ui.components.portfolio_table import render_portfolio_table
from ui.components.config_panel import render_config_panel
from ui.components.results_viewer import (
    render_results_summary,
    render_t0_mtm_table,
    render_run_comparison,
)

apply_theme()
init_session_state()

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

with st.sidebar:
    st.markdown(
        '<div style="display:flex;align-items:center;gap:10px;padding:4px 0 12px;">'
        '<div style="width:32px;height:32px;background:linear-gradient(135deg,#3b82f6,#6366f1);'
        'border-radius:8px;display:flex;align-items:center;justify-content:center;'
        'color:#fff;font-weight:700;font-size:14px;">P</div>'
        '<div><div style="font-size:18px;font-weight:700;color:#1e293b;">PFE-v2</div>'
        '<div style="font-size:11px;color:#94a3b8;">Monte Carlo Engine</div></div>'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown('<hr style="margin:0.5rem 0;border-color:#f1f5f9;">', unsafe_allow_html=True)

    # Portfolio summary
    portfolio = st.session_state["portfolio"]
    latest = st.session_state.get("latest_result")
    t0_mtm_list = latest.get("per_trade_t0_mtm", []) if latest else []

    st.markdown(
        f'<div style="font-size:10px;text-transform:uppercase;letter-spacing:0.8px;'
        f'color:#94a3b8;font-weight:600;margin:8px 0 6px;">Portfolio ({len(portfolio)} trades)</div>',
        unsafe_allow_html=True,
    )

    if portfolio:
        for i, trade in enumerate(portfolio):
            direction = trade.get("direction", "long")
            mtm_str = ""
            if i < len(t0_mtm_list):
                mtm_val = t0_mtm_list[i]
                mtm_str = f"{mtm_val:+,.0f}"
            sidebar_portfolio_item(trade["trade_id"], direction, mtm_str)
    else:
        st.caption("No trades yet.")

    st.markdown('<hr style="margin:0.5rem 0;border-color:#f1f5f9;">', unsafe_allow_html=True)

    # Run history
    runs = st.session_state.get("runs", [])
    st.markdown(
        '<div style="font-size:10px;text-transform:uppercase;letter-spacing:0.8px;'
        'color:#94a3b8;font-weight:600;margin:8px 0 6px;">Run History</div>',
        unsafe_allow_html=True,
    )

    if runs:
        _bullet = "\u25cf"
        for run in reversed(runs):
            is_latest = latest and run.get("label") == latest.get("label")
            bg = "background:#f0f7ff;border:1px solid #bfdbfe;border-radius:6px;" if is_latest else ""
            dot = f"  {_bullet}" if is_latest else ""
            st.markdown(
                f'<div style="padding:4px 8px;font-size:0.72rem;margin-bottom:4px;{bg}">'
                f'<div style="display:flex;justify-content:space-between;">'
                f'<span style="color:#334155;font-weight:500;">{run["label"]}{dot}</span>'
                f'</div>'
                f'<div style="font-family:JetBrains Mono,monospace;font-size:0.68rem;color:#64748b;">'
                f'Peak PFE: {run["peak_pfe"]:,.0f}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
    else:
        st.caption("No runs yet.")

    # Snapshot save/load at bottom
    st.markdown('<hr style="margin:0.5rem 0;border-color:#f1f5f9;">', unsafe_allow_html=True)

    from ui.utils.snapshots import serialize_snapshot, deserialize_snapshot, validate_snapshot

    uploaded = st.file_uploader("Load snapshot", type=["json"], key="sidebar_upload",
                                 label_visibility="collapsed")
    if uploaded is not None:
        content = uploaded.read().decode("utf-8")
        data = deserialize_snapshot(content)
        errors = validate_snapshot(data)
        if errors:
            st.error("Invalid: " + "; ".join(errors))
        else:
            st.session_state["market"] = data
            st.rerun()

    market = st.session_state["market"]
    if market["asset_names"]:
        json_str = serialize_snapshot(market, name="snapshot")
        st.download_button(
            "Save Snapshot",
            data=json_str,
            file_name="pfe_snapshot.json",
            mime="application/json",
            key="sidebar_download",
        )

# ---------------------------------------------------------------------------
# Main content — tabs
# ---------------------------------------------------------------------------

n_trades = len(st.session_state["portfolio"])
tab_market, tab_portfolio, tab_config, tab_results = st.tabs([
    "Market Data",
    f"Portfolio ({n_trades})" if n_trades else "Portfolio",
    "Configuration",
    "Results",
])

with tab_market:
    st.markdown('<div style="font-size:22px;font-weight:700;color:#1e293b;margin-bottom:4px;">Market Data</div>',
                unsafe_allow_html=True)
    st.caption("Define assets, spot prices, volatilities, and correlation structure")
    is_psd = render_market_data_input(key_prefix="tab_mkt")
    if st.session_state["market"]["asset_names"] and not is_psd:
        st.warning("Correlation matrix is not positive semi-definite.")

with tab_portfolio:
    st.markdown('<div style="font-size:22px;font-weight:700;color:#1e293b;margin-bottom:4px;">Portfolio</div>',
                unsafe_allow_html=True)
    st.caption("Build trades and manage your portfolio")

    trade_spec = render_trade_builder(key_prefix="tab_tb")
    if trade_spec is not None:
        st.session_state["portfolio"].append(trade_spec)
        st.session_state["tab_tb_modifier_count"] = 0
        st.session_state["_switch_to_portfolio"] = True
        st.rerun()

    st.markdown('<hr style="margin:1rem 0;border-color:#f1f5f9;">', unsafe_allow_html=True)
    render_portfolio_table(key_prefix="tab_pt")

with tab_config:
    st.markdown('<div style="font-size:22px;font-weight:700;color:#1e293b;margin-bottom:4px;">Configuration</div>',
                unsafe_allow_html=True)
    st.caption("Set simulation parameters and run PFE calculation")

    render_config_panel(key_prefix="tab_cfg")

    st.markdown('<hr style="margin:1rem 0;border-color:#f1f5f9;">', unsafe_allow_html=True)

    portfolio_specs = st.session_state["portfolio"]
    if not portfolio_specs:
        st.button("Run PFE", key="tab_run", disabled=True)
        st.caption("Add at least one trade first.")
    else:
        if st.button("Run PFE", key="tab_run", type="primary"):
            run_pfe_calculation()
            st.session_state["_switch_to_results"] = True
            st.rerun()

with tab_results:
    st.markdown('<div style="font-size:22px;font-weight:700;color:#1e293b;margin-bottom:4px;">Exposure Analysis</div>',
                unsafe_allow_html=True)

    latest = st.session_state.get("latest_result")
    if latest is None:
        st.info("No results yet. Configure and run PFE in the Configuration tab.")
    else:
        conf = latest["config"]
        st.caption(
            f'{latest.get("label", "Run")} \u00b7 '
            f'{conf["n_outer"]:,} outer \u00d7 {conf["n_inner"]:,} inner \u00b7 '
            f'{conf["confidence_level"]:.0%} confidence \u00b7 '
            f'{latest["computation_time"]:.1f}s'
        )

        render_results_summary(latest)

        trade_ids = [t["trade_id"] for t in st.session_state["portfolio"]]
        render_t0_mtm_table(latest, trade_ids)

        st.markdown('<hr style="margin:1rem 0;border-color:#f1f5f9;">', unsafe_allow_html=True)
        render_run_comparison(key_prefix="tab_cmp")

# ---------------------------------------------------------------------------
# Auto-switch to Results tab after a run completes
# ---------------------------------------------------------------------------

if st.session_state.pop("_switch_to_results", False):
    _js = """
    <script>
    const tabs = window.parent.document.querySelectorAll('button[data-baseweb="tab"]');
    if (tabs.length >= 4) { tabs[3].click(); }
    </script>
    """
    st.components.v1.html(_js, height=0)

if st.session_state.pop("_switch_to_portfolio", False):
    _js = """
    <script>
    const tabs = window.parent.document.querySelectorAll('button[data-baseweb="tab"]');
    if (tabs.length >= 2) { tabs[1].click(); }
    </script>
    """
    st.components.v1.html(_js, height=0)
