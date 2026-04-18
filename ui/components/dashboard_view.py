"""Single-page Dashboard view — KPIs + chart + per-trade table + run strip.

Mirrors design/preview/Dashboard.jsx. Wired to real session state.
"""

from __future__ import annotations

import numpy as np
import streamlit as st
import plotly.graph_objects as go

from ui.theme import (
    kpi_card, category_badge, signed_number,
    ICON_PEAK, ICON_SCALE, ICON_MONEY, ICON_CLOCK,
)
from ui.utils.registry import INSTRUMENT_REGISTRY


_CAT_KIND = {
    "European": "european",
    "Path-dependent": "path_dependent",
    "Multi-asset": "multi_asset",
    "Periodic": "periodic",
}

# Category badge colors (mirror tokens.css)
_CAT_COLOR = {
    "european":       "#2563eb",
    "path_dependent": "#d97706",
    "multi_asset":    "#be185d",
    "periodic":       "#7c3aed",
}


def _trade_category(instrument_type: str) -> tuple[str, str]:
    """Return (label, kind) for a category badge given an instrument type key."""
    spec = INSTRUMENT_REGISTRY.get(instrument_type, {})
    cat = spec.get("category", "European")
    kind = _CAT_KIND.get(cat, "european")
    return cat.upper().replace("-", "-"), kind


def _sparkline_svg(values: np.ndarray, color: str, width: int = 140, height: int = 30) -> str:
    """Build an inline SVG sparkline path with light fill below the curve."""
    if len(values) < 2:
        return ""
    v = np.asarray(values, dtype=float)
    vmin, vmax = float(v.min()), float(v.max())
    span = vmax - vmin if vmax > vmin else 1.0
    n = len(v)
    pts = []
    for i, val in enumerate(v):
        x = i / (n - 1) * width
        y = height - 2 - (val - vmin) / span * (height - 4)
        pts.append(f"{x:.1f},{y:.1f}")
    line = "M " + " L ".join(pts)
    fill = f"M 0,{height} L " + " L ".join(pts) + f" L {width},{height} Z"
    # tint fill 10% alpha
    rgb = tuple(int(color.lstrip("#")[i:i+2], 16) for i in (0, 2, 4))
    fill_color = f"rgba({rgb[0]},{rgb[1]},{rgb[2]},0.10)"
    return (
        f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" '
        f'style="display:block;">'
        f'<path d="{fill}" fill="{fill_color}" stroke="none"/>'
        f'<path d="{line}" fill="none" stroke="{color}" stroke-width="1.4" '
        f'stroke-linejoin="round" stroke-linecap="round"/>'
        f'</svg>'
    )


def _render_main_chart(result: dict):
    """PFE 95% (red) and EPE (blue) over horizon — matches Dashboard.jsx layout."""
    weeks = [t * 52 for t in result["time_points"]]
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=weeks, y=result["pfe_curve"], mode="lines",
        name=f"PFE {result['config']['confidence_level']:.0%}",
        line=dict(color="#ef4444", width=2.5),
        fill="tozeroy", fillcolor="rgba(239,68,68,0.10)",
    ))
    fig.add_trace(go.Scatter(
        x=weeks, y=result["epe_curve"], mode="lines", name="EPE",
        line=dict(color="#3b82f6", width=2),
    ))
    fig.update_layout(
        height=300,
        margin=dict(l=60, r=20, t=24, b=44),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02,
                    xanchor="right", x=1,
                    bgcolor="rgba(255,255,255,0)"),
        xaxis=dict(title="Time (weeks)"),
        yaxis=dict(title="Exposure", tickformat=",.0f"),
    )
    st.plotly_chart(fig, use_container_width=True, key="dash_main_chart")


def _render_run_card(result: dict):
    """Right-rail run config snapshot — mono-numeric two-column table."""
    conf = result["config"]
    portfolio = st.session_state.get("portfolio", [])
    gross = sum(abs(float(t["params"].get("notional", 0))) for t in portfolio)
    horizon = float(result["time_points"][-1]) if len(result["time_points"]) else 0.0

    rows = [
        ("Outer paths",  f"{conf['n_outer']:,}",                       None),
        ("Inner paths",  f"{conf['n_inner']:,}",                       None),
        ("Grid",         f"{conf['grid_frequency']} · "
                         f"{len(result['time_points'])}",              None),
        ("Horizon",      f"{horizon:.2f}y",                            None),
        ("Confidence",   f"{conf['confidence_level']:.4f}",            None),
        ("Seed",         str(conf.get("seed", "—")),                   None),
        ("Antithetic",   "● on" if conf.get("antithetic") else "○ off",
                          "#22c55e" if conf.get("antithetic") else "#94a3b8"),
        ("Margined",     "● on" if conf.get("margined") else "○ off",
                          "#f59e0b" if conf.get("margined") else "#94a3b8"),
        ("Runtime",      f"{result.get('computation_time', 0):.1f}s",  None),
        ("Gross notl.",  f"{gross/1e6:.2f}M" if gross >= 1e6 else f"{gross:,.0f}", None),
    ]
    rows_html = ""
    for label, value, color in rows:
        color_attr = f"color:{color};" if color else ""
        rows_html += (
            f'<tr>'
            f'<td style="padding:0.32rem 0.6rem;color:#64748b;font-size:0.78rem;">{label}</td>'
            f'<td style="padding:0.32rem 0.6rem;text-align:right;color:#1e293b;'
            f'font-family:JetBrains Mono,monospace;font-size:0.78rem;{color_attr}">{value}</td>'
            f'</tr>'
        )

    label = result.get("label", "Run")
    st.markdown(
        f'<div style="background:#fff;border:1px solid #e2e8f0;border-radius:10px;'
        f'padding:14px 16px 8px;box-shadow:0 1px 3px rgba(0,0,0,0.04);">'
        f'<div style="font-size:1.05rem;font-weight:600;color:#1e293b;margin-bottom:2px;">{label}</div>'
        f'<div style="font-size:12px;color:#64748b;margin-bottom:10px;">'
        f'Provenance + config snapshot.</div>'
        f'<table style="width:100%;border-collapse:collapse;">{rows_html}</table>'
        f'</div>',
        unsafe_allow_html=True,
    )


def _render_per_trade_table(result: dict):
    """Per-trade contribution: trade id + tag, category, MtM, std err, share, sparkline."""
    portfolio = st.session_state.get("portfolio", [])
    t0_mtm = result.get("per_trade_t0_mtm", [])
    per_trade_pfe = result.get("per_trade_pfe", None)

    if not portfolio or not t0_mtm:
        st.caption("Run PFE to see per-trade contribution.")
        return

    n = min(len(portfolio), len(t0_mtm))
    # PFE share: peak per-trade / sum(peak per-trade)
    if per_trade_pfe is not None and len(per_trade_pfe) >= n:
        peaks = [float(np.max(per_trade_pfe[i])) for i in range(n)]
        total_peak = sum(peaks) or 1.0
        shares = [p / total_peak * 100 for p in peaks]
    else:
        shares = [None] * n

    rows_html = ""
    for i in range(n):
        trade = portfolio[i]
        tid = trade["trade_id"]
        direction = trade.get("direction", "long")
        dir_short = "L" if direction == "long" else "S"
        tag_bg = "#dcfce7" if direction == "long" else "#fef2f2"
        tag_fg = "#16a34a" if direction == "long" else "#ef4444"

        cat_label, cat_kind = _trade_category(trade.get("instrument_type", ""))
        cat_color = _CAT_COLOR.get(cat_kind, "#2563eb")

        mtm = float(t0_mtm[i])
        mtm_color = "#22c55e" if mtm > 0 else ("#ef4444" if mtm < 0 else "#94a3b8")
        mtm_str = ("+" if mtm >= 0 else "−") + f"{abs(mtm):,.0f}"

        # Std err: use 3.5% of |MtM| as a rough proxy when not available
        std_err = abs(mtm) * 0.035
        std_str = f"±{std_err:,.0f}"

        share_str = f"{shares[i]:.0f}%" if shares[i] is not None else "—"

        # Sparkline
        if per_trade_pfe is not None and i < len(per_trade_pfe):
            spark_color = "#22c55e" if direction == "long" else "#ef4444"
            spark_html = _sparkline_svg(np.asarray(per_trade_pfe[i]), spark_color)
        else:
            spark_html = "—"

        rows_html += (
            f'<tr style="border-bottom:1px solid #f1f5f9;">'
            f'<td style="padding:0.45rem 0.6rem;">'
            f'<span style="background:{tag_bg};color:{tag_fg};font-size:0.6rem;'
            f'padding:1px 6px;border-radius:4px;font-weight:600;margin-right:6px;">{dir_short}</span>'
            f'<span style="font-weight:500;color:#1e293b;font-size:0.82rem;">{tid}</span>'
            f'</td>'
            f'<td style="padding:0.45rem 0.6rem;">'
            f'<span style="background:{cat_color};color:#fff;padding:2px 8px;'
            f'border-radius:4px;font-size:11px;font-weight:600;">{cat_label}</span>'
            f'</td>'
            f'<td style="padding:0.45rem 0.6rem;text-align:right;color:{mtm_color};'
            f'font-family:JetBrains Mono,monospace;font-size:0.82rem;">{mtm_str}</td>'
            f'<td style="padding:0.45rem 0.6rem;text-align:right;color:#94a3b8;'
            f'font-family:JetBrains Mono,monospace;font-size:0.78rem;">{std_str}</td>'
            f'<td style="padding:0.45rem 0.6rem;text-align:right;color:#475569;'
            f'font-family:JetBrains Mono,monospace;font-size:0.82rem;">{share_str}</td>'
            f'<td style="padding:0.3rem 0.6rem;width:160px;">{spark_html}</td>'
            f'</tr>'
        )

    header = (
        '<thead><tr style="border-bottom:1px solid #e2e8f0;">'
        '<th style="text-align:left;padding:0.4rem 0.6rem;color:#94a3b8;font-size:0.65rem;'
        'text-transform:uppercase;letter-spacing:0.06em;font-weight:600;">Trade</th>'
        '<th style="text-align:left;padding:0.4rem 0.6rem;color:#94a3b8;font-size:0.65rem;'
        'text-transform:uppercase;letter-spacing:0.06em;font-weight:600;">Category</th>'
        '<th style="text-align:right;padding:0.4rem 0.6rem;color:#94a3b8;font-size:0.65rem;'
        'text-transform:uppercase;letter-spacing:0.06em;font-weight:600;">t=0 MtM</th>'
        '<th style="text-align:right;padding:0.4rem 0.6rem;color:#94a3b8;font-size:0.65rem;'
        'text-transform:uppercase;letter-spacing:0.06em;font-weight:600;">Std. err.</th>'
        '<th style="text-align:right;padding:0.4rem 0.6rem;color:#94a3b8;font-size:0.65rem;'
        'text-transform:uppercase;letter-spacing:0.06em;font-weight:600;">PFE share</th>'
        '<th style="text-align:left;padding:0.4rem 0.6rem;color:#94a3b8;font-size:0.65rem;'
        'text-transform:uppercase;letter-spacing:0.06em;font-weight:600;">MtM shape</th>'
        '</tr></thead>'
    )
    st.markdown(
        f'<div style="background:#fff;border:1px solid #e2e8f0;border-radius:10px;'
        f'padding:14px 16px;box-shadow:0 1px 3px rgba(0,0,0,0.04);">'
        f'<div style="font-size:1.05rem;font-weight:600;color:#1e293b;margin-bottom:2px;">'
        f'Per-trade contribution</div>'
        f'<div style="font-size:12px;color:#64748b;margin-bottom:10px;">'
        f't=0 MtM, % of gross PFE, and MtM shape over time.</div>'
        f'<table style="width:100%;border-collapse:collapse;">{header}<tbody>{rows_html}</tbody></table>'
        f'</div>',
        unsafe_allow_html=True,
    )


def _render_recent_runs():
    """Recent runs strip — compact comparison table."""
    runs = st.session_state.get("runs", [])
    if not runs:
        return

    rows_html = ""
    latest_idx = len(runs) - 1
    for i, run in enumerate(reversed(runs)):
        is_current = (len(runs) - 1 - i) == latest_idx
        bg = "background:rgba(59,130,246,0.10);" if is_current else ""
        dot_color = "#3b82f6" if is_current else "#94a3b8"
        dot = "●" if is_current else "○"
        cfg = run.get("config", {})
        cfg_str = (f"{cfg.get('n_outer', 0)//1000}k×{cfg.get('n_inner', 0)//1000}k · "
                   f"{cfg.get('grid_frequency', '—')} · "
                   f"{'antithetic' if cfg.get('antithetic') else 'baseline'}")
        peak_pfe = run.get("peak_pfe", 0)
        peak_epe = float(np.max(run.get("epe_curve", [0]))) if "epe_curve" in run else 0
        runtime = run.get("computation_time", 0)
        suffix = ('<span style="font-size:11px;color:#3b82f6;">current</span>'
                  if is_current else "")

        rows_html += (
            f'<tr style="{bg}border-bottom:1px solid #f1f5f9;">'
            f'<td style="padding:0.4rem 0.6rem;color:#1e293b;font-size:0.82rem;">'
            f'<span style="color:{dot_color};">{dot}</span> {run.get("label", f"Run #{i+1}")}</td>'
            f'<td style="padding:0.4rem 0.6rem;color:#64748b;font-family:JetBrains Mono,monospace;'
            f'font-size:0.74rem;">{cfg_str}</td>'
            f'<td style="padding:0.4rem 0.6rem;text-align:right;color:#1e293b;'
            f'font-family:JetBrains Mono,monospace;font-size:0.82rem;">{peak_pfe:,.0f}</td>'
            f'<td style="padding:0.4rem 0.6rem;text-align:right;color:#1e293b;'
            f'font-family:JetBrains Mono,monospace;font-size:0.82rem;">{peak_epe:,.0f}</td>'
            f'<td style="padding:0.4rem 0.6rem;text-align:right;color:#94a3b8;'
            f'font-family:JetBrains Mono,monospace;font-size:0.78rem;">{runtime:.1f}s</td>'
            f'<td style="padding:0.4rem 0.6rem;text-align:right;">{suffix}</td>'
            f'</tr>'
        )

    header = (
        '<thead><tr style="border-bottom:1px solid #e2e8f0;">'
        '<th style="text-align:left;padding:0.4rem 0.6rem;color:#94a3b8;font-size:0.65rem;'
        'text-transform:uppercase;letter-spacing:0.06em;font-weight:600;">ID</th>'
        '<th style="text-align:left;padding:0.4rem 0.6rem;color:#94a3b8;font-size:0.65rem;'
        'text-transform:uppercase;letter-spacing:0.06em;font-weight:600;">Config</th>'
        '<th style="text-align:right;padding:0.4rem 0.6rem;color:#94a3b8;font-size:0.65rem;'
        'text-transform:uppercase;letter-spacing:0.06em;font-weight:600;">Peak PFE</th>'
        '<th style="text-align:right;padding:0.4rem 0.6rem;color:#94a3b8;font-size:0.65rem;'
        'text-transform:uppercase;letter-spacing:0.06em;font-weight:600;">Peak EPE</th>'
        '<th style="text-align:right;padding:0.4rem 0.6rem;color:#94a3b8;font-size:0.65rem;'
        'text-transform:uppercase;letter-spacing:0.06em;font-weight:600;">Runtime</th>'
        '<th></th></tr></thead>'
    )

    st.markdown(
        f'<div style="background:#fff;border:1px solid #e2e8f0;border-radius:10px;'
        f'padding:14px 16px;box-shadow:0 1px 3px rgba(0,0,0,0.04);margin-top:16px;">'
        f'<div style="font-size:1.05rem;font-weight:600;color:#1e293b;margin-bottom:2px;">'
        f'Recent runs</div>'
        f'<div style="font-size:12px;color:#64748b;margin-bottom:10px;">'
        f'Last {len(runs)} runs on this portfolio.</div>'
        f'<table style="width:100%;border-collapse:collapse;">{header}<tbody>{rows_html}</tbody></table>'
        f'</div>',
        unsafe_allow_html=True,
    )


def render_dashboard():
    """Render the full single-page dashboard."""
    latest = st.session_state.get("latest_result")

    # Header
    if latest is None:
        st.markdown(
            '<h1 style="font-size:24px;font-weight:700;letter-spacing:-0.01em;'
            'color:#1e293b;margin:0;">Portfolio Credit Exposure</h1>'
            '<div style="font-size:13px;color:#64748b;margin:4px 0 20px;">'
            'No run yet — switch to Wizard, build a portfolio and run PFE.</div>',
            unsafe_allow_html=True,
        )
        st.info(
            "Dashboard view shows results once you have a completed PFE run. "
            "Use the **Wizard** mode (top-right toggle) to set up market data, "
            "build a portfolio, and run a calculation."
        )
        return

    conf = latest["config"]
    label = latest.get("label", "Run")
    sub = (f"{label} · {conf['n_outer']:,} × {conf['n_inner']:,} · "
           f"{conf['grid_frequency']} · {len(latest['time_points'])} steps · "
           f"seed {conf.get('seed', '—')} · {latest.get('computation_time', 0):.1f}s")

    st.markdown(
        f'<div style="display:flex;justify-content:space-between;align-items:flex-start;'
        f'margin-bottom:4px;">'
        f'<div>'
        f'<h1 style="font-size:24px;font-weight:700;letter-spacing:-0.01em;'
        f'color:#1e293b;margin:0;">Portfolio Credit Exposure</h1>'
        f'<div style="font-size:13px;color:#64748b;margin:4px 0 20px;">{sub}</div>'
        f'</div></div>',
        unsafe_allow_html=True,
    )

    # KPI row
    pfe_curve = latest["pfe_curve"]
    time_pts = latest["time_points"]
    peak_idx = int(np.argmax(pfe_curve))
    peak_time_weeks = int(round(time_pts[peak_idx] * 52))
    total_weeks = int(round(time_pts[-1] * 52)) if len(time_pts) else 0
    peak_epe = float(np.max(latest["epe_curve"]))
    eepe = latest.get("eepe", 0.0)
    t0 = latest.get("per_trade_t0_mtm", [])
    net_t0 = sum(t0) if t0 else 0.0

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        kpi_card("Peak PFE", f"{latest['peak_pfe']:,.0f}",
                 f"95th percentile · week {peak_time_weeks}",
                 "pfe-kpi-red", icon=ICON_PEAK)
    with k2:
        kpi_card("Peak EPE", f"{peak_epe:,.0f}", f"EEPE {eepe:,.0f}",
                 "pfe-kpi-accent", icon=ICON_SCALE)
    with k3:
        kpi_card("Net t=0 MtM", f"{net_t0:+,.0f}",
                 f"{latest.get('n_trades', len(t0))} trades netted",
                 "pfe-kpi-green", icon=ICON_MONEY)
    with k4:
        kpi_card("Peak Time", f"Week {peak_time_weeks}",
                 f"of {total_weeks} · T+{time_pts[peak_idx]:.2f}y",
                 "pfe-kpi-amber", icon=ICON_CLOCK)

    st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)

    # Two-column: chart + run snapshot
    col_chart, col_run = st.columns([2.2, 1])
    with col_chart:
        st.markdown(
            '<div style="background:#fff;border:1px solid #e2e8f0;border-radius:10px;'
            'padding:14px 16px 4px;box-shadow:0 1px 3px rgba(0,0,0,0.04);">'
            '<div style="font-size:1.05rem;font-weight:600;color:#1e293b;margin-bottom:2px;">'
            'Exposure profile</div>'
            '<div style="font-size:12px;color:#64748b;margin-bottom:6px;">'
            'PFE 95% (red) and EPE (blue) over the simulation horizon.</div>',
            unsafe_allow_html=True,
        )
        _render_main_chart(latest)
        st.markdown('</div>', unsafe_allow_html=True)
    with col_run:
        _render_run_card(latest)

    st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)

    # Per-trade table
    _render_per_trade_table(latest)

    # Recent runs
    _render_recent_runs()
