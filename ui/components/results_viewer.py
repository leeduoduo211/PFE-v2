"""Results viewer: summary, PFE/EPE charts, fan chart, run comparison.

All Plotly charts use the pfe_light template registered by ui.theme.
"""

import io

import numpy as np
import streamlit as st
import plotly.graph_objects as go

from ui.theme import (
    section_label, kpi_card,
    ICON_PEAK, ICON_SCALE, ICON_MONEY, ICON_CLOCK,
)

# Chart trace colors
_PFE = "#ef4444"
_PFE_DIM = "rgba(239,68,68,0.10)"
_EPE = "#3b82f6"
_EPE_DIM = "rgba(59,130,246,0.10)"
_MEDIAN = "#f59e0b"
_FAN = [
    "rgba(239,68,68,0.05)",
    "rgba(239,68,68,0.12)",
    "rgba(239,68,68,0.22)",
]
_TRADE_PALETTE = [
    "#3b82f6", "#ef4444", "#22c55e", "#f59e0b", "#8b5cf6",
    "#06b6d4", "#ec4899", "#14b8a6", "#f97316", "#a855f7",
]


def render_results_summary(result: dict):
    """Side-by-side layout: KPI cards left, main chart right."""

    # Find peak time
    pfe_curve = result["pfe_curve"]
    time_pts = result["time_points"]
    peak_idx = int(np.argmax(pfe_curve))
    peak_time_weeks = int(round(time_pts[peak_idx] * 52))
    total_weeks = int(round(time_pts[-1] * 52)) if len(time_pts) > 0 else 0

    col_kpi, col_chart = st.columns([1, 2.5])

    with col_kpi:
        kpi_card("Peak PFE", f"{result['peak_pfe']:,.0f}", "95th percentile",
                 "pfe-kpi-red", icon=ICON_PEAK)
        # Peak EPE replaces EEPE on the dashboard: it's a point on the plotted
        # blue curve, so the scalar matches what the user sees. EEPE is still
        # available as result.eepe for regulatory / scripted reporting.
        peak_epe = float(np.max(result["epe_curve"]))
        kpi_card("Peak EPE", f"{peak_epe:,.0f}", "max of EPE profile",
                 "pfe-kpi-accent", icon=ICON_SCALE)

        # Net t=0 MtM
        t0_mtm = result.get("per_trade_t0_mtm", [])
        if t0_mtm:
            net = sum(t0_mtm)
            kpi_card("Net t=0 MtM", f"{net:+,.0f}",
                     f"{result.get('n_trades', 0)} trades netted",
                     "pfe-kpi-green", icon=ICON_MONEY)

        kpi_card("Peak Time", f"Week {peak_time_weeks}",
                 f"of {total_weeks} weeks", "pfe-kpi-amber", icon=ICON_CLOCK)

    with col_chart:
        chart_tab1, chart_tab2, chart_tab3 = st.tabs(["PFE / EPE", "Fan Chart", "Per Trade"])

        with chart_tab1:
            _render_pfe_epe(result)

        with chart_tab2:
            _render_fan(result)

        with chart_tab3:
            trade_ids = [t["trade_id"] for t in st.session_state.get("portfolio", [])]
            _render_per_trade(result, trade_ids)


def render_t0_mtm_table(result: dict, trade_ids: list):
    """Per-trade t=0 Mark-to-Market table — light theme."""
    per_trade_t0 = result.get("per_trade_t0_mtm")
    if not per_trade_t0:
        return

    section_label("Per-Trade t=0 Mark-to-Market")

    total = sum(per_trade_t0)

    rows_html = ""
    for tid, mtm in zip(trade_ids, per_trade_t0):
        pct = mtm / abs(total) * 100 if total != 0 else 0.0
        if mtm > 0:
            mtm_color = "#22c55e"
        elif mtm < 0:
            mtm_color = "#ef4444"
        else:
            mtm_color = "#94a3b8"

        rows_html += (
            f'<tr style="border-bottom:1px solid #f1f5f9;">'
            f'<td style="padding:0.35rem 0.6rem;color:#334155;">{tid}</td>'
            f'<td style="padding:0.35rem 0.6rem;text-align:right;color:{mtm_color};'
            f'font-family:JetBrains Mono,monospace;">{mtm:,.0f}</td>'
            f'<td style="padding:0.35rem 0.6rem;text-align:right;color:#94a3b8;'
            f'font-family:JetBrains Mono,monospace;">{pct:.1f}%</td>'
            f'</tr>'
        )

    total_color = "#22c55e" if total > 0 else ("#ef4444" if total < 0 else "#94a3b8")

    html = (
        f'<table style="width:100%;border-collapse:collapse;font-family:Inter,sans-serif;font-size:0.8rem;">'
        f'<thead>'
        f'<tr style="border-bottom:1px solid #e2e8f0;">'
        f'<th style="text-align:left;padding:0.4rem 0.6rem;color:#94a3b8;font-size:0.65rem;'
        f'text-transform:uppercase;letter-spacing:0.06em;font-weight:600;">Trade ID</th>'
        f'<th style="text-align:right;padding:0.4rem 0.6rem;color:#94a3b8;font-size:0.65rem;'
        f'text-transform:uppercase;letter-spacing:0.06em;font-weight:600;">t=0 MtM</th>'
        f'<th style="text-align:right;padding:0.4rem 0.6rem;color:#94a3b8;font-size:0.65rem;'
        f'text-transform:uppercase;letter-spacing:0.06em;font-weight:600;">% of Portfolio</th>'
        f'</tr>'
        f'</thead>'
        f'<tbody>{rows_html}'
        f'<tr style="border-top:1px solid #e2e8f0;font-weight:600;">'
        f'<td style="padding:0.35rem 0.6rem;color:#1e293b;">Total</td>'
        f'<td style="padding:0.35rem 0.6rem;text-align:right;color:{total_color};'
        f'font-family:JetBrains Mono,monospace;">{total:,.0f}</td>'
        f'<td style="padding:0.35rem 0.6rem;text-align:right;color:#94a3b8;'
        f'font-family:JetBrains Mono,monospace;">100%</td>'
        f'</tr>'
        f'</tbody></table>'
    )
    st.markdown(html, unsafe_allow_html=True)


def _time_in_weeks(time_points):
    return [t * 52 for t in time_points]


def _render_pfe_epe(result: dict):
    """PFE and EPE curves."""
    time_points = _time_in_weeks(result["time_points"])
    is_margined = result["config"].get("margined", False)

    show_unmargined = False
    if is_margined:
        show_unmargined = st.checkbox("Overlay unmargined", value=False, key="overlay_unmargined")

    fig = go.Figure()

    pfe_label = f"PFE {result['config']['confidence_level']:.0%}"
    epe_label = "EPE"
    if is_margined and show_unmargined:
        pfe_label += " (margined)"
        epe_label += " (margined)"

    fig.add_trace(go.Scatter(
        x=time_points, y=result["pfe_curve"],
        mode="lines", name=pfe_label,
        line=dict(color=_PFE, width=2.5),
        fill="tozeroy", fillcolor=_PFE_DIM,
    ))
    fig.add_trace(go.Scatter(
        x=time_points, y=result["epe_curve"],
        mode="lines", name=epe_label,
        line=dict(color=_EPE, width=2),
    ))

    if show_unmargined and "unmargined_pfe_curve" in result:
        fig.add_trace(go.Scatter(
            x=time_points, y=result["unmargined_pfe_curve"],
            mode="lines", name=f"PFE {result['config']['confidence_level']:.0%} (unmargined)",
            line=dict(color=_PFE, width=1.5, dash="dot"),
        ))
        fig.add_trace(go.Scatter(
            x=time_points, y=result["unmargined_epe_curve"],
            mode="lines", name="EPE (unmargined)",
            line=dict(color=_EPE, width=1.5, dash="dot"),
        ))

    fig.update_layout(
        xaxis_title="Time (weeks)", yaxis_title="Exposure",
        hovermode="x unified", height=320,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                    bgcolor="rgba(255,255,255,0)", bordercolor="rgba(0,0,0,0)"),
    )
    st.plotly_chart(fig, use_container_width=True, key="pfe_epe_chart")


def _render_fan(result: dict):
    """Exposure percentile fan chart."""
    if "exposure_matrix" not in result:
        st.info("No exposure matrix available.")
        return

    exposure = np.array(result["exposure_matrix"])
    time_points = _time_in_weeks(result["time_points"])

    percentiles = [5, 25, 50, 75, 95]
    quantiles = np.percentile(exposure, percentiles, axis=0)

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=list(time_points) + list(time_points[::-1]),
        y=list(quantiles[4]) + list(quantiles[0][::-1]),
        fill="toself", fillcolor=_FAN[0],
        line=dict(width=0), name="5th\u201395th", hoverinfo="skip",
    ))
    fig.add_trace(go.Scatter(
        x=list(time_points) + list(time_points[::-1]),
        y=list(quantiles[3]) + list(quantiles[1][::-1]),
        fill="toself", fillcolor=_FAN[1],
        line=dict(width=0), name="25th\u201375th", hoverinfo="skip",
    ))
    fig.add_trace(go.Scatter(
        x=time_points, y=quantiles[2],
        mode="lines", name="Median",
        line=dict(color=_MEDIAN, width=2.5),
    ))

    fig.update_layout(
        xaxis_title="Time (weeks)", yaxis_title="Exposure", height=280,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                    bgcolor="rgba(255,255,255,0)", bordercolor="rgba(0,0,0,0)"),
    )
    st.plotly_chart(fig, use_container_width=True, key="fan_chart")


def _render_per_trade(result: dict, trade_ids: list):
    """Per-trade PFE contribution stacked area."""
    if "per_trade_pfe" not in result:
        st.info("No per-trade data available.")
        return

    time_points = _time_in_weeks(result["time_points"])
    per_trade = result["per_trade_pfe"]

    # Guard: portfolio may have changed since this run was computed
    n_available = min(len(trade_ids), len(per_trade))
    if n_available < len(trade_ids):
        st.caption(
            f"Showing {n_available} of {len(trade_ids)} trades \u2014 "
            f"portfolio has changed since the last run. Re-run PFE to refresh."
        )

    fig = go.Figure()
    for i, tid in enumerate(trade_ids[:n_available]):
        color = _TRADE_PALETTE[i % len(_TRADE_PALETTE)]
        if color.startswith("#") and len(color) == 7:
            r, g, b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
            fill = f"rgba({r},{g},{b},0.3)"
        else:
            fill = color
        fig.add_trace(go.Scatter(
            x=time_points, y=per_trade[i],
            mode="lines", name=tid,
            stackgroup="one",
            line=dict(width=0.5, color=color),
            fillcolor=fill,
        ))

    fig.update_layout(
        xaxis_title="Time (weeks)", yaxis_title="PFE Contribution", height=280,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                    bgcolor="rgba(255,255,255,0)", bordercolor="rgba(0,0,0,0)"),
    )
    st.plotly_chart(fig, use_container_width=True, key="per_trade_chart")


# These are still called from app.py for backward compat — they delegate to internal fns
def render_pfe_epe_chart(result: dict):
    """Standalone PFE/EPE chart — now rendered inside summary sub-tabs."""
    pass


def render_fan_chart(result: dict):
    """Standalone fan chart — now rendered inside summary sub-tabs."""
    pass


def render_per_trade_breakdown(result: dict, trade_ids: list):
    """Standalone per-trade breakdown — now rendered inside summary sub-tabs."""
    pass


def render_run_comparison(key_prefix: str = "cmp"):
    """Side-by-side comparison of two runs — light theme."""
    runs = st.session_state.get("runs", [])
    if len(runs) < 2:
        st.caption("Run PFE multiple times with different settings to compare.")
        return

    section_label("Run Comparison")

    labels = [r["label"] for r in runs]

    col1, col2 = st.columns(2)
    run_a_idx = col1.selectbox("Run A", range(len(runs)), format_func=lambda i: labels[i], key=f"{key_prefix}_a")
    run_b_idx = col2.selectbox("Run B", range(len(runs)), index=min(1, len(runs)-1),
                                format_func=lambda i: labels[i], key=f"{key_prefix}_b")

    run_a = runs[run_a_idx]
    run_b = runs[run_b_idx]

    # Summary deltas above the chart — most important comparison surface.
    peak_a, peak_b = run_a.get("peak_pfe", 0), run_b.get("peak_pfe", 0)
    eepe_a, eepe_b = run_a.get("eepe", 0), run_b.get("eepe", 0)

    def _delta(a, b):
        if a == 0:
            return (b - a, 0.0)
        return (b - a, (b - a) / a * 100)

    peak_d, peak_pct = _delta(peak_a, peak_b)
    eepe_d, eepe_pct = _delta(eepe_a, eepe_b)

    def _color(d):
        return "#ef4444" if d > 0 else ("#22c55e" if d < 0 else "#94a3b8")

    st.markdown(
        f'<div style="display:flex;gap:12px;margin:6px 0 10px;">'
        f'<div style="flex:1;background:#f8fafc;border:1px solid #e2e8f0;'
        f'border-radius:8px;padding:8px 12px;">'
        f'<div style="font-size:10px;text-transform:uppercase;letter-spacing:0.06em;'
        f'color:#94a3b8;font-weight:600;">Peak PFE</div>'
        f'<div style="font-family:JetBrains Mono,monospace;font-size:0.85rem;color:#334155;">'
        f'{peak_a:,.0f} \u2192 {peak_b:,.0f}</div>'
        f'<div style="font-family:JetBrains Mono,monospace;font-size:0.8rem;color:{_color(peak_d)};">'
        f'{"+" if peak_d >= 0 else ""}{peak_d:,.0f} ({"+" if peak_pct >= 0 else ""}{peak_pct:.1f}%)'
        f'</div></div>'
        f'<div style="flex:1;background:#f8fafc;border:1px solid #e2e8f0;'
        f'border-radius:8px;padding:8px 12px;">'
        f'<div style="font-size:10px;text-transform:uppercase;letter-spacing:0.06em;'
        f'color:#94a3b8;font-weight:600;">EEPE</div>'
        f'<div style="font-family:JetBrains Mono,monospace;font-size:0.85rem;color:#334155;">'
        f'{eepe_a:,.0f} \u2192 {eepe_b:,.0f}</div>'
        f'<div style="font-family:JetBrains Mono,monospace;font-size:0.8rem;color:{_color(eepe_d)};">'
        f'{"+" if eepe_d >= 0 else ""}{eepe_d:,.0f} ({"+" if eepe_pct >= 0 else ""}{eepe_pct:.1f}%)'
        f'</div></div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=_time_in_weeks(run_a["time_points"]), y=run_a["pfe_curve"],
        mode="lines", name="A: PFE", line=dict(color=_PFE, width=2.5),
    ))
    fig.add_trace(go.Scatter(
        x=_time_in_weeks(run_b["time_points"]), y=run_b["pfe_curve"],
        mode="lines", name="B: PFE", line=dict(color=_PFE, width=1.5, dash="dot"),
    ))
    fig.add_trace(go.Scatter(
        x=_time_in_weeks(run_a["time_points"]), y=run_a["epe_curve"],
        mode="lines", name="A: EPE", line=dict(color=_EPE, width=2.5),
    ))
    fig.add_trace(go.Scatter(
        x=_time_in_weeks(run_b["time_points"]), y=run_b["epe_curve"],
        mode="lines", name="B: EPE", line=dict(color=_EPE, width=1.5, dash="dot"),
    ))

    fig.update_layout(
        xaxis_title="Time (weeks)", yaxis_title="Exposure",
        hovermode="x unified", height=300,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                    bgcolor="rgba(255,255,255,0)", bordercolor="rgba(0,0,0,0)"),
    )
    st.plotly_chart(fig, use_container_width=True, key=f"{key_prefix}_comparison_chart")

    # Comparison table — light theme
    st.markdown(
        f"""<table style="width:100%;border-collapse:collapse;font-family:Inter,sans-serif;font-size:0.8rem;">
        <thead>
        <tr style="border-bottom:1px solid #e2e8f0;">
            <th style="text-align:left;padding:0.5rem 0.8rem;color:#94a3b8;font-size:0.65rem;
                text-transform:uppercase;letter-spacing:0.06em;">Metric</th>
            <th style="text-align:right;padding:0.5rem 0.8rem;color:#3b82f6;font-size:0.65rem;
                text-transform:uppercase;letter-spacing:0.06em;">Run A</th>
            <th style="text-align:right;padding:0.5rem 0.8rem;color:#8b5cf6;font-size:0.65rem;
                text-transform:uppercase;letter-spacing:0.06em;">Run B</th>
        </tr>
        </thead>
        <tbody>
        <tr style="border-bottom:1px solid #f1f5f9;">
            <td style="padding:0.4rem 0.8rem;color:#64748b;">Peak PFE</td>
            <td style="padding:0.4rem 0.8rem;text-align:right;color:#1e293b;font-family:JetBrains Mono,monospace;">{run_a['peak_pfe']:,.2f}</td>
            <td style="padding:0.4rem 0.8rem;text-align:right;color:#1e293b;font-family:JetBrains Mono,monospace;">{run_b['peak_pfe']:,.2f}</td>
        </tr>
        <tr style="border-bottom:1px solid #f1f5f9;">
            <td style="padding:0.4rem 0.8rem;color:#64748b;">EEPE</td>
            <td style="padding:0.4rem 0.8rem;text-align:right;color:#1e293b;font-family:JetBrains Mono,monospace;">{run_a['eepe']:,.2f}</td>
            <td style="padding:0.4rem 0.8rem;text-align:right;color:#1e293b;font-family:JetBrains Mono,monospace;">{run_b['eepe']:,.2f}</td>
        </tr>
        <tr>
            <td style="padding:0.4rem 0.8rem;color:#64748b;">Compute Time</td>
            <td style="padding:0.4rem 0.8rem;text-align:right;color:#1e293b;font-family:JetBrains Mono,monospace;">{run_a['computation_time']:.2f}s</td>
            <td style="padding:0.4rem 0.8rem;text-align:right;color:#1e293b;font-family:JetBrains Mono,monospace;">{run_b['computation_time']:.2f}s</td>
        </tr>
        </tbody>
        </table>""",
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Export helpers
# ---------------------------------------------------------------------------

def _result_to_csv(result: dict) -> str:
    """Serialize time_points + PFE + EPE curves to a simple CSV string."""
    t = np.asarray(result["time_points"])
    pfe = np.asarray(result["pfe_curve"])
    epe = np.asarray(result["epe_curve"])
    buf = io.StringIO()
    buf.write("time_years,time_weeks,pfe,epe\n")
    for ti, pi, ei in zip(t, pfe, epe):
        buf.write(f"{ti:.6f},{ti * 52:.3f},{pi:.6f},{ei:.6f}\n")
    return buf.getvalue()


def _result_to_python(result: dict) -> str:
    """Emit a runnable Python snippet that reproduces the result's config."""
    conf = result.get("config", {})
    label = result.get("label", "Run")
    return f'''# Reproduces {label}. Paste into a script after building market + portfolio.
from pfev2 import PFEConfig, compute_pfe

config = PFEConfig(
    n_outer={conf.get("n_outer", 1000)},
    n_inner={conf.get("n_inner", 1000)},
    confidence_level={conf.get("confidence_level", 0.95)},
    grid_frequency="{conf.get("grid_frequency", "weekly")}",
    margined={conf.get("margined", False)},
    mpor_days={conf.get("mpor_days", 10)},
    seed={conf.get("seed", 42)},
    backend="{conf.get("backend", "numpy")}",
    n_workers={conf.get("n_workers", 1)},
    antithetic={conf.get("antithetic", False)},
)

result = compute_pfe(portfolio, market, config)
print(result.summary())
'''


def render_result_exports(result: dict, key_prefix: str = "export"):
    """Render a compact row of download buttons for the current result."""
    section_label("Export")
    c1, c2, c3 = st.columns(3)
    label = result.get("label", "run").replace(" ", "_").replace("#", "n")

    with c1:
        st.download_button(
            "Download CSV (PFE + EPE profile)",
            data=_result_to_csv(result),
            file_name=f"pfe_{label}.csv",
            mime="text/csv",
            key=f"{key_prefix}_csv",
            use_container_width=True,
        )
    with c2:
        st.download_button(
            "Download Python snippet",
            data=_result_to_python(result),
            file_name=f"pfe_{label}.py",
            mime="text/x-python",
            key=f"{key_prefix}_py",
            use_container_width=True,
        )
    with c3:
        st.caption(
            "Tip: use Plotly's camera icon on the chart above to save a PNG."
        )

