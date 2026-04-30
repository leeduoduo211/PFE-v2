"""PFE-v2 Streamlit entry point — tab-based layout with sidebar."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st

st.set_page_config(
    page_title="PFE-v2",
    page_icon="P",
    layout="wide",
    initial_sidebar_state="expanded",
)

from ui.components.config_panel import render_config_panel
from ui.components.dashboard_view import render_dashboard
from ui.components.market_data_input import render_market_data_input
from ui.components.portfolio_table import render_portfolio_table
from ui.components.results_viewer import (
    render_result_exports,
    render_results_summary,
    render_run_comparison,
    render_t0_mtm_table,
)
from ui.components.trade_builder import render_trade_builder
from ui.theme import (
    app_header,
    apply_theme,
    card_title,
    run_banner,
    sidebar_brand,
    sidebar_overline,
    sidebar_portfolio_item,
    sidebar_summary,
    workflow_steps,
)
from ui.utils.runner import run_pfe_calculation
from ui.utils.session import init_session_state

apply_theme()
init_session_state()

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

with st.sidebar:
    sidebar_brand()

    # Portfolio summary
    portfolio = st.session_state["portfolio"]
    latest = st.session_state.get("latest_result")
    t0_mtm_list = latest.get("per_trade_t0_mtm", []) if latest else []

    sidebar_overline(f"Portfolio ({len(portfolio)} trades)")

    if portfolio:
        # Portfolio summary: gross / net notional and max maturity.
        # Gross is sum of |notional|; net accounts for long/short direction.
        gross = sum(float(t["params"].get("notional", 0)) for t in portfolio)
        net = sum(
            float(t["params"].get("notional", 0))
            * (-1.0 if t.get("direction") == "short" else 1.0)
            for t in portfolio
        )
        max_mat = max((float(t["params"].get("maturity", 0)) for t in portfolio),
                      default=0.0)

        def _fmt(n):
            # Compact notional formatter: 1.2M / 850K / 1,000
            if abs(n) >= 1e6:
                return f"{n / 1e6:.2f}M"
            if abs(n) >= 1e3:
                return f"{n / 1e3:.0f}K"
            return f"{n:.0f}"

        sidebar_summary(
            [
                ("Gross notl.", _fmt(gross)),
                ("Net notl.", f'{"+" if net >= 0 else ""}{_fmt(net)}'),
                ("Max maturity", f"{max_mat:.2f}y"),
            ]
        )

        for i, trade in enumerate(portfolio):
            direction = trade.get("direction", "long")
            mtm_str = ""
            if i < len(t0_mtm_list):
                mtm_val = t0_mtm_list[i]
                mtm_str = f"{mtm_val:+,.0f}"
            sidebar_portfolio_item(trade["trade_id"], direction, mtm_str)
    else:
        st.caption("No trades yet.")

    # Run history
    runs = st.session_state.get("runs", [])
    sidebar_overline("Run history")

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

    # Session save/load — grouped in a collapsed expander. A snapshot can be
    # either market-only (legacy v1) or a full session bundle (v2 = market +
    # portfolio + config).
    sidebar_overline("Save & load")

    from ui.utils.snapshots import (
        deserialize_session,
        deserialize_snapshot,
        serialize_session,
        serialize_snapshot,
        validate_snapshot,
    )

    with st.expander("Session snapshots", expanded=False):
        st.caption(
            "Save just the market, or the full session (market + portfolio + config)."
        )
        uploaded = st.file_uploader(
            "Load snapshot (.json)", type=["json"], key="sidebar_upload",
        )
        if uploaded is not None:
            content = uploaded.read().decode("utf-8")
            try:
                bundle = deserialize_session(content)
            except Exception:
                bundle = None
            if bundle is None:
                st.error("Could not parse snapshot.")
            else:
                market_data = bundle.get("market") or {}
                errors = validate_snapshot(market_data) if market_data else ["missing market"]
                if errors:
                    # Fall back to legacy market-only schema
                    legacy = deserialize_snapshot(content)
                    errors2 = validate_snapshot(legacy)
                    if errors2:
                        st.error("Invalid: " + "; ".join(errors2))
                    else:
                        st.session_state["market"] = legacy
                        st.rerun()
                else:
                    st.session_state["market"] = market_data
                    if bundle.get("portfolio") is not None:
                        st.session_state["portfolio"] = bundle["portfolio"]
                    if bundle.get("config"):
                        st.session_state["config"].update(bundle["config"])
                    st.rerun()

        market = st.session_state["market"]
        portfolio = st.session_state["portfolio"]
        config = st.session_state["config"]

        if market["asset_names"]:
            st.download_button(
                "Save market only",
                data=serialize_snapshot(market, name="market"),
                file_name="pfe_market.json",
                mime="application/json",
                key="sidebar_download_market",
                use_container_width=True,
            )
            st.download_button(
                "Save full session",
                data=serialize_session(market, portfolio, config, name="session"),
                file_name="pfe_session.json",
                mime="application/json",
                key="sidebar_download_session",
                use_container_width=True,
                disabled=not portfolio,
                help=("Disabled until the portfolio has at least one trade."
                      if not portfolio else "Saves market + portfolio + config."),
            )
        else:
            st.caption("Define assets first, then return here to save.")

# ---------------------------------------------------------------------------
# View mode toggle (Wizard / Dashboard) — top-right
# ---------------------------------------------------------------------------

if "view_mode" not in st.session_state:
    st.session_state["view_mode"] = "wizard"

_tog_left, _tog_right = st.columns([5, 2])
with _tog_right:
    st.markdown('<div class="pfe-mode-label">View mode</div>', unsafe_allow_html=True)
    _mode = st.radio(
        "View",
        options=["wizard", "dashboard"],
        format_func=lambda v: "Wizard" if v == "wizard" else "Dashboard",
        index=0 if st.session_state["view_mode"] == "wizard" else 1,
        horizontal=True,
        label_visibility="collapsed",
        key="_view_mode_radio",
    )
    if _mode != st.session_state["view_mode"]:
        st.session_state["view_mode"] = _mode
        st.rerun()

if st.session_state["view_mode"] == "dashboard":
    render_dashboard()
    st.stop()

# ---------------------------------------------------------------------------
# Main content — tabs (Wizard mode)
# ---------------------------------------------------------------------------

# Page header — gives orientation before the tabbed workflow
n_trades = len(st.session_state["portfolio"])
has_market = bool(st.session_state["market"]["asset_names"])
has_results = st.session_state.get("latest_result") is not None
n_assets = len(st.session_state["market"]["asset_names"])
latest = st.session_state.get("latest_result")

header_chips = [
    ("Assets", str(n_assets)),
    ("Trades", str(n_trades)),
]
if latest is not None:
    header_chips.append(("Peak PFE", f'{latest.get("peak_pfe", 0):,.0f}'))

app_header(
    "Portfolio Credit Exposure",
    "Nested Monte Carlo Potential Future Exposure on exotic derivative portfolios.",
    chips=header_chips,
)

workflow_steps(
    [
        {"number": "01", "title": "Market Data", "state": "done" if has_market else "next"},
        {
            "number": "02",
            "title": f"Portfolio ({n_trades})" if n_trades else "Portfolio",
            "state": "done" if n_trades else ("next" if has_market else "pending"),
        },
        {
            "number": "03",
            "title": "Configuration",
            "state": "done" if has_results else ("next" if has_market and n_trades else "pending"),
        },
        {"number": "04", "title": "Results", "state": "done" if has_results else "pending"},
    ]
)

tab_labels = ["1. Market Data", f"2. Portfolio ({n_trades})", "3. Configuration", "4. Results"]
tab_market, tab_portfolio, tab_config, tab_results = st.tabs(tab_labels)

with tab_market:
    card_title("Market Data", "Define assets, spot prices, volatilities, and correlation structure.")

    # Quick-start presets — always visible, but collapsed once the user has
    # built more than one asset or added any trades. This keeps the prominent
    # slot free for experienced users while still letting them reload.
    from ui.utils.presets import PRESETS, load_preset
    _market = st.session_state["market"]
    _portfolio = st.session_state["portfolio"]
    _fresh = len(_market["asset_names"]) <= 1 and len(_portfolio) == 0

    with st.expander("Quick start from a preset", expanded=_fresh):
        st.caption(
            "One click loads a realistic market + portfolio. Safe to use even "
            "mid-session \u2014 overwrites current market and portfolio."
        )
        cols = st.columns(len(PRESETS))
        for col, (preset_key, (label, desc, _)) in zip(cols, PRESETS.items()):
            with col:
                if st.button(label, key=f"preset_{preset_key}",
                             use_container_width=True):
                    loaded = load_preset(preset_key)
                    if loaded is not None:
                        market, portfolio = loaded
                        # Bump the market tab's key-prefix generation so every
                        # widget below gets a fresh key on the next rerun.
                        # This sidesteps Streamlit's session-state caching
                        # without us having to enumerate every input we depend
                        # on (number/text/selectbox all in different files).
                        st.session_state["_market_form_gen"] = (
                            st.session_state.get("_market_form_gen", 0) + 1
                        )
                        st.session_state["market"] = market
                        st.session_state["portfolio"] = portfolio
                        st.rerun()
                st.caption(desc)

    # The key prefix includes a "generation" counter that bumps each time a
    # preset is loaded, forcing a clean widget tree (bypasses Streamlit's
    # session-state caching of inputs).
    _gen = st.session_state.get("_market_form_gen", 0)
    is_psd = render_market_data_input(key_prefix=f"tab_mkt_g{_gen}")
    if st.session_state["market"]["asset_names"] and not is_psd:
        st.warning("Correlation matrix is not positive semi-definite.")

with tab_portfolio:
    card_title("Portfolio", "Build trades, stack modifiers, and manage term sheets.")

    trade_spec = render_trade_builder(key_prefix="tab_tb")
    if trade_spec is not None:
        st.session_state["portfolio"].append(trade_spec)
        st.session_state["tab_tb_modifier_count"] = 0
        st.session_state["_switch_to_portfolio"] = True

        # Auto-increment trade ID for the next trade. Parses a trailing
        # numeric suffix (e.g. "TRD_001" -> "TRD_002"). If no suffix is
        # found, appends "_2", "_3", ...
        import re
        last_id = trade_spec["trade_id"]
        m = re.match(r"^(.*?)(\d+)$", last_id)
        if m:
            prefix, num = m.group(1), m.group(2)
            next_id = f"{prefix}{int(num) + 1:0{len(num)}d}"
        else:
            next_id = f"{last_id}_2"
        # Stash in a pending slot; the trade builder consumes it before
        # instantiating its trade_id widget next run (Streamlit forbids
        # modifying a widget's session_state key after instantiation).
        st.session_state["_pending_next_trade_id"] = next_id

        st.rerun()

    st.markdown('<hr style="margin:1rem 0;border-color:#f1f5f9;">', unsafe_allow_html=True)
    render_portfolio_table(key_prefix="tab_pt")

with tab_config:
    card_title("Configuration", "Set simulation parameters and run the nested Monte Carlo engine.")

    render_config_panel(key_prefix="tab_cfg")

    st.markdown('<hr style="margin:1rem 0;border-color:#f1f5f9;">', unsafe_allow_html=True)

    portfolio_specs = st.session_state["portfolio"]
    if not portfolio_specs:
        st.button("Run PFE", key="tab_run", disabled=True)
        st.caption("Add at least one trade first.")
    else:
        cfg = st.session_state["config"]
        steps = {"daily": 252, "weekly": 52, "monthly": 12}.get(cfg["grid_frequency"], 52)
        run_banner(
            "Ready to run",
            f'{cfg["n_outer"]:,} outer x {steps} steps x {cfg["n_inner"]:,} inner x '
            f'{len(portfolio_specs)} trade{"s" if len(portfolio_specs) != 1 else ""}',
        )
        if st.button("Run PFE", key="tab_run", type="primary"):
            run_pfe_calculation()
            st.session_state["_switch_to_results"] = True
            st.rerun()

with tab_results:
    latest = st.session_state.get("latest_result")
    if latest is None:
        card_title("Results", "Peak PFE, EPE, per-trade standalone PFE, and exports.")
        st.info("No results yet. Configure and run PFE in the Configuration tab.")
    else:
        conf = latest["config"]
        card_title(
            "Results",
            (
                f'{latest.get("label", "Run")} | '
                f'{conf["n_outer"]:,} outer x {conf["n_inner"]:,} inner | '
                f'{conf["confidence_level"]:.0%} confidence | '
                f'{latest["computation_time"]:.1f}s'
            ),
        )

        render_results_summary(latest)

        trade_ids = [t["trade_id"] for t in st.session_state["portfolio"]]
        render_t0_mtm_table(latest, trade_ids)

        st.markdown('<hr style="margin:1rem 0;border-color:#f1f5f9;">', unsafe_allow_html=True)
        render_result_exports(latest, key_prefix="tab_export")

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
