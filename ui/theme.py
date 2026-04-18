"""PFE-v2 UI Theme: Clean Finance Light.

Provides CSS injection and Plotly chart templates for a professional
light-mode quantitative finance aesthetic.

v2 refinements (design-system alignment):
  - Added text_body color stop (#475569).
  - Added category-badge and modifier-group CSS + helpers.
  - Added semantic number utility classes (pos/neg).
  - Added grouped-section (left-stripe accent) helper.
  - Nudged stMetric padding up for breathing room.
  - Plotly template: horizontal top legend, softer margins.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.io as pio


# ---------------------------------------------------------------------------
# Color palette
# ---------------------------------------------------------------------------

COLORS = {
    "bg_page": "#f8fafc",
    "bg_card": "#ffffff",
    "bg_surface": "#f1f5f9",
    "bg_hover": "#f8fafc",
    "border": "#e2e8f0",
    "border_strong": "#cbd5e1",
    "border_focus": "#3b82f6",
    "text_primary": "#1e293b",
    "text_body": "#475569",      # new: body copy, slate-600
    "text_secondary": "#64748b",
    "text_muted": "#94a3b8",
    "blue": "#3b82f6",
    "blue_hover": "#2563eb",
    "blue_dim": "rgba(59,130,246,0.1)",
    "red": "#ef4444",
    "red_dim": "rgba(239,68,68,0.12)",
    "green": "#22c55e",
    "green_dim": "rgba(34,197,94,0.1)",
    "amber": "#f59e0b",
    "amber_dim": "rgba(245,158,11,0.1)",
    "purple": "#8b5cf6",
    "cyan": "#06b6d4",
    # Product-category badge fills
    "cat_european": "#2563eb",
    "cat_path_dependent": "#d97706",
    "cat_multi_asset": "#be185d",
    "cat_periodic": "#7c3aed",
    # Modifier group accents
    "mod_barrier": "#f59e0b",
    "mod_payoff": "#22c55e",
    "mod_structural": "#8b5cf6",
}

# Chart trace colors
PFE_COLOR = "#ef4444"
PFE_COLOR_DIM = "rgba(239,68,68,0.10)"
EPE_COLOR = "#3b82f6"
EPE_COLOR_DIM = "rgba(59,130,246,0.10)"
MEDIAN_COLOR = "#f59e0b"
FAN_COLORS = [
    "rgba(239,68,68,0.05)",
    "rgba(239,68,68,0.12)",
    "rgba(239,68,68,0.22)",
]
# Per-trade colorway (10 colors; wraps for portfolios with more than 10 trades)
TRADE_COLORWAY = [
    "#3b82f6", "#ef4444", "#22c55e", "#f59e0b", "#8b5cf6",
    "#06b6d4", "#ec4899", "#14b8a6", "#f97316", "#a855f7",
]


# ---------------------------------------------------------------------------
# Custom CSS
# ---------------------------------------------------------------------------

_CSS = """
<style>
/* ── Fonts ─────────────────────────────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

/* ── Global overrides ─────────────────────────────────────────────── */
html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
}

/* Hide default Streamlit header chrome */
header[data-testid="stHeader"] {
    background: transparent !important;
    height: 0 !important;
    min-height: 0 !important;
    padding: 0 !important;
}
#MainMenu, footer,
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stStatusWidget"],
[data-testid="stBaseButton-header"],
button[kind="header"],
button[kind="headerNoPadding"],
.stDeployButton,
[data-testid="stAppDeployButton"] {
    display: none !important;
    visibility: hidden !important;
}

.block-container {
    padding-top: 2.5rem !important;
    padding-bottom: 1rem !important;
    max-width: 1200px !important;
}

/* ── Sidebar ──────────────────────────────────────────────────────── */
section[data-testid="stSidebar"] {
    background: #ffffff !important;
    border-right: 1px solid #e2e8f0 !important;
}

section[data-testid="stSidebar"] [data-testid="stMarkdown"] h1 {
    font-family: 'Inter', sans-serif !important;
    font-weight: 700 !important;
    color: #1e293b !important;
    font-size: 1.4rem !important;
}

/* ── Headers ──────────────────────────────────────────────────────── */
h1, h2, h3, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    color: #1e293b !important;
}

/* ── Metric cards ─────────────────────────────────────────────────── */
[data-testid="stMetric"] {
    background: #ffffff !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 10px !important;
    padding: 1rem 1.2rem !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04) !important;
}

[data-testid="stMetric"]:hover {
    border-color: #cbd5e1 !important;
}

[data-testid="stMetric"] label {
    color: #94a3b8 !important;
    font-size: 0.62rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.06em !important;
    font-weight: 600 !important;
}

[data-testid="stMetric"] [data-testid="stMetricValue"] {
    color: #1e293b !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-variant-numeric: tabular-nums !important;
    font-weight: 700 !important;
    font-size: 1.3rem !important;
}

/* ── Buttons ──────────────────────────────────────────────────────── */
button[kind="primary"],
.stButton > button[kind="primary"] {
    background: #3b82f6 !important;
    color: #ffffff !important;
    font-weight: 500 !important;
    border: none !important;
    border-radius: 7px !important;
    font-size: 0.85rem !important;
    transition: all 0.15s ease !important;
}

button[kind="primary"]:hover {
    background: #2563eb !important;
}

button[kind="secondary"],
.stButton > button:not([kind="primary"]) {
    background: #ffffff !important;
    border: 1px solid #e2e8f0 !important;
    color: #475569 !important;
    border-radius: 7px !important;
    font-size: 0.8rem !important;
    transition: all 0.15s ease !important;
}

button[kind="secondary"]:hover,
.stButton > button:not([kind="primary"]):hover {
    border-color: #cbd5e1 !important;
    background: #f8fafc !important;
}

/* ── Expanders ────────────────────────────────────────────────────── */
details[data-testid="stExpander"] {
    background: #ffffff !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 10px !important;
    margin-bottom: 0.5rem !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04) !important;
}

details[data-testid="stExpander"][open] {
    border-color: #cbd5e1 !important;
}

/* ── Inputs ───────────────────────────────────────────────────────── */
[data-testid="stNumberInput"] input,
[data-testid="stTextInput"] input {
    background: #ffffff !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 6px !important;
    color: #1e293b !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-variant-numeric: tabular-nums !important;
}

[data-testid="stNumberInput"] input:focus,
[data-testid="stTextInput"] input:focus {
    border-color: #3b82f6 !important;
    box-shadow: 0 0 0 3px rgba(59,130,246,0.1) !important;
}

[data-baseweb="select"] > div {
    background: #ffffff !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 6px !important;
}

/* ── Dividers ─────────────────────────────────────────────────────── */
hr {
    border-color: #e2e8f0 !important;
    margin: 1rem 0 !important;
}

/* ── Tabs ─────────────────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
    gap: 0 !important;
    border-bottom: 1px solid #e2e8f0 !important;
}

.stTabs [data-baseweb="tab"] {
    font-family: 'Inter', sans-serif !important;
    font-size: 0.85rem !important;
    font-weight: 500 !important;
    padding: 0.6rem 1.2rem !important;
    color: #94a3b8 !important;
}

.stTabs [data-baseweb="tab"][aria-selected="true"] {
    color: #3b82f6 !important;
    border-bottom: 2px solid #3b82f6 !important;
}

/* ── Progress bar ─────────────────────────────────────────────────── */
[data-testid="stProgress"] > div > div {
    background: #3b82f6 !important;
    border-radius: 4px !important;
}

/* ── Plotly chart container ───────────────────────────────────────── */
[data-testid="stPlotlyChart"] {
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    overflow: hidden;
}

/* ── File uploader ───────────────────────────────────────────────── */
[data-testid="stFileUploader"] {
    border: 1px dashed #e2e8f0 !important;
    border-radius: 8px !important;
}

/* ── Section label ────────────────────────────────────────────────── */
.pfe-section-label {
    font-size: 0.65rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #94a3b8;
    margin: 1rem 0 0.5rem 0;
    font-family: 'Inter', sans-serif;
    font-weight: 600;
    border-bottom: 1px solid #f1f5f9;
    padding-bottom: 0.3rem;
}

/* ── KPI cards (results) ─────────────────────────────────────────── */
.pfe-kpi {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 16px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    margin-bottom: 10px;
}

.pfe-kpi-accent { border-left: 3px solid #3b82f6; }
.pfe-kpi-red    { border-left: 3px solid #ef4444; }
.pfe-kpi-green  { border-left: 3px solid #22c55e; }
.pfe-kpi-amber  { border-left: 3px solid #f59e0b; }

.pfe-kpi-label {
    font-size: 0.62rem;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: #94a3b8;
    font-weight: 600;
    font-family: 'Inter', sans-serif;
    margin-bottom: 4px;
}

.pfe-kpi-value {
    font-size: 1.5rem;
    font-weight: 700;
    color: #1e293b;
    font-family: 'JetBrains Mono', monospace;
    font-variant-numeric: tabular-nums;
}

.pfe-kpi-sub {
    font-size: 0.68rem;
    color: #94a3b8;
    margin-top: 2px;
    font-family: 'Inter', sans-serif;
}

/* ── Sidebar portfolio items ─────────────────────────────────────── */
.pfe-sidebar-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 4px 8px;
    border-radius: 6px;
    font-size: 0.75rem;
    margin-bottom: 2px;
}

.pfe-sidebar-item:hover {
    background: #f8fafc;
}

.pfe-tag-long {
    background: #dcfce7;
    color: #16a34a;
    font-size: 0.6rem;
    padding: 1px 6px;
    border-radius: 4px;
    font-weight: 600;
}

.pfe-tag-short {
    background: #fef2f2;
    color: #ef4444;
    font-size: 0.6rem;
    padding: 1px 6px;
    border-radius: 4px;
    font-weight: 600;
}

/* ── Product category badges ──────────────────────────────────────── */
.pfe-cat {
    color: #ffffff;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 11px;
    font-weight: 600;
    font-family: 'Inter', sans-serif;
    letter-spacing: 0.02em;
}
.pfe-cat-eu { background: #2563eb; }   /* EUROPEAN       */
.pfe-cat-pd { background: #d97706; }   /* PATH-DEPENDENT */
.pfe-cat-ma { background: #be185d; }   /* MULTI-ASSET    */
.pfe-cat-pe { background: #7c3aed; }   /* PERIODIC       */

/* ── Modifier group badges ───────────────────────────────────────── */
.pfe-mg {
    padding: 1px 6px;
    border-radius: 3px;
    font-size: 9px;
    font-weight: 600;
    letter-spacing: 0.04em;
    margin-left: 6px;
    font-family: 'Inter', sans-serif;
}
.pfe-mg-barrier { background: #fef3c7; color: #d97706; }
.pfe-mg-payoff  { background: #dcfce7; color: #16a34a; }
.pfe-mg-struct  { background: #ede9fe; color: #7c3aed; }

/* ── Grouped-section (trade builder) ─────────────────────────────── */
.pfe-group {
    padding-left: 12px;
    margin: 14px 0 10px;
}
.pfe-group-blue   { border-left: 3px solid #2563eb; }
.pfe-group-amber  { border-left: 3px solid #f59e0b; }
.pfe-group-green  { border-left: 3px solid #22c55e; }
.pfe-group-purple { border-left: 3px solid #8b5cf6; }
.pfe-group > h4 { margin: 0; font-size: 13px; font-weight: 600; color: #1e293b; }
.pfe-group > p  { margin: 2px 0 0; font-size: 12px; color: #64748b; }

/* ── Semantic number utilities (tables) ──────────────────────────── */
.pfe-pos { color: #22c55e; font-family: 'JetBrains Mono', monospace; font-variant-numeric: tabular-nums; }
.pfe-neg { color: #ef4444; font-family: 'JetBrains Mono', monospace; font-variant-numeric: tabular-nums; }
.pfe-num { color: #1e293b; font-family: 'JetBrains Mono', monospace; font-variant-numeric: tabular-nums; }

/* ── Scrollbar ────────────────────────────────────────────────────── */
::-webkit-scrollbar {
    width: 6px;
    height: 6px;
}
::-webkit-scrollbar-track {
    background: #f1f5f9;
}
::-webkit-scrollbar-thumb {
    background: #cbd5e1;
    border-radius: 3px;
}
::-webkit-scrollbar-thumb:hover {
    background: #94a3b8;
}
</style>
"""


# ---------------------------------------------------------------------------
# Plotly template
# ---------------------------------------------------------------------------

_PLOTLY_TEMPLATE = go.layout.Template(
    layout=go.Layout(
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        font=dict(
            family="Inter, -apple-system, sans-serif",
            color="#64748b",
            size=12,
        ),
        title=dict(
            font=dict(size=14, color="#1e293b"),
            x=0,
            xanchor="left",
        ),
        xaxis=dict(
            gridcolor="#f1f5f9",
            gridwidth=1,
            zerolinecolor="#e2e8f0",
            zerolinewidth=1,
            linecolor="#e2e8f0",
            linewidth=1,
            tickfont=dict(size=10, color="#94a3b8"),
            title_font=dict(size=11, color="#64748b"),
        ),
        yaxis=dict(
            gridcolor="#f1f5f9",
            gridwidth=1,
            zerolinecolor="#e2e8f0",
            zerolinewidth=1,
            linecolor="#e2e8f0",
            linewidth=1,
            tickfont=dict(size=10, color="#94a3b8"),
            title_font=dict(size=11, color="#64748b"),
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            bgcolor="rgba(255,255,255,0)",
            bordercolor="rgba(0,0,0,0)",
            font=dict(size=11, color="#475569"),
        ),
        hoverlabel=dict(
            bgcolor="#1e293b",
            bordercolor="#334155",
            font=dict(
                family="JetBrains Mono, monospace",
                size=11,
                color="#f8fafc",
            ),
        ),
        margin=dict(l=50, r=20, t=30, b=44),
        colorway=["#3b82f6", "#ef4444", "#22c55e", "#f59e0b", "#8b5cf6", "#06b6d4"],
    ),
)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def apply_theme():
    """Inject custom CSS and register Plotly template. Call once in app.py."""
    st.markdown(_CSS, unsafe_allow_html=True)
    pio.templates["pfe_light"] = _PLOTLY_TEMPLATE
    pio.templates.default = "pfe_light"


def section_label(text: str):
    """Render an uppercase section divider label."""
    st.markdown(f'<div class="pfe-section-label">{text}</div>', unsafe_allow_html=True)


def kpi_card(label: str, value: str, sub: str = "", css_class: str = "", icon: str = ""):
    """Render a single KPI card via HTML.

    icon: optional inline SVG or text glyph shown before the label.
    """
    icon_html = (
        f'<span style="display:inline-flex;align-items:center;justify-content:center;'
        f'width:14px;height:14px;margin-right:5px;vertical-align:-2px;">{icon}</span>'
    ) if icon else ""
    html = (
        f'<div class="pfe-kpi {css_class}">'
        f'<div class="pfe-kpi-label">{icon_html}{label}</div>'
        f'<div class="pfe-kpi-value">{value}</div>'
        f'<div class="pfe-kpi-sub">{sub}</div>'
        f'</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


# Inline SVG icons for KPI cards (slate-500 stroke, size 14)
ICON_PEAK = (
    '<svg width="14" height="14" viewBox="0 0 14 14" fill="none" '
    'stroke="#64748b" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">'
    '<path d="M1 11l3.5-4 2 2L10 4l3 5"/><circle cx="10" cy="4" r="1" fill="#ef4444" stroke="none"/>'
    '</svg>'
)
ICON_SCALE = (
    '<svg width="14" height="14" viewBox="0 0 14 14" fill="none" '
    'stroke="#64748b" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">'
    '<path d="M7 1v12M2 4h10M3 7l-1.5 3h3zM11 7l-1.5 3h3z"/>'
    '</svg>'
)
ICON_MONEY = (
    '<svg width="14" height="14" viewBox="0 0 14 14" fill="none" '
    'stroke="#64748b" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">'
    '<path d="M7 1v12M9.5 3.5h-3a1.8 1.8 0 000 3.6h2a1.8 1.8 0 010 3.6h-3"/>'
    '</svg>'
)
ICON_CLOCK = (
    '<svg width="14" height="14" viewBox="0 0 14 14" fill="none" '
    'stroke="#64748b" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">'
    '<circle cx="7" cy="7" r="5.5"/><path d="M7 4v3l2 1.5"/>'
    '</svg>'
)


def sidebar_portfolio_item(name: str, direction: str, mtm: str = ""):
    """Render a sidebar portfolio summary item."""
    tag_cls = "pfe-tag-long" if direction == "long" else "pfe-tag-short"
    tag_text = "L" if direction == "long" else "S"
    mtm_html = f'<span style="font-family:JetBrains Mono,monospace;font-size:0.7rem;color:#64748b;">{mtm}</span>' if mtm else ""
    html = (
        f'<div class="pfe-sidebar-item">'
        f'<span style="color:#334155;font-weight:500;">{name}</span>'
        f'<span><span class="{tag_cls}">{tag_text}</span> {mtm_html}</span>'
        f'</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Taxonomy helpers (new in v2)
# ---------------------------------------------------------------------------

_CAT_CLS = {
    "european":       "pfe-cat-eu",
    "path_dependent": "pfe-cat-pd",
    "multi_asset":    "pfe-cat-ma",
    "periodic":       "pfe-cat-pe",
}

_MG_CLS = {
    "barrier":    "pfe-mg-barrier",
    "payoff":     "pfe-mg-payoff",
    "structural": "pfe-mg-struct",
}

_GROUP_CLS = {
    "blue":   "pfe-group-blue",
    "amber":  "pfe-group-amber",
    "green":  "pfe-group-green",
    "purple": "pfe-group-purple",
}


def category_badge(label: str, kind: str) -> str:
    """Return HTML for a product-category pill. kind ∈ {european, path_dependent, multi_asset, periodic}."""
    cls = _CAT_CLS.get(kind, "pfe-cat-eu")
    return f'<span class="pfe-cat {cls}">{label}</span>'


def modifier_badge(label: str, group: str) -> str:
    """Return HTML for a modifier-group pill. group ∈ {barrier, payoff, structural}."""
    cls = _MG_CLS.get(group, "pfe-mg-struct")
    return f'<span class="pfe-mg {cls}">{label}</span>'


def grouped_section(title: str, subtitle: str = "", accent: str = "blue",
                    trailing_html: str = ""):
    """Render a left-stripe grouped section header.

    accent ∈ {blue, amber, green, purple}.
    trailing_html: optional HTML appended after the title (e.g. a modifier_badge).
    """
    cls = _GROUP_CLS.get(accent, "pfe-group-blue")
    sub = f'<p>{subtitle}</p>' if subtitle else ''
    st.markdown(
        f'<div class="pfe-group {cls}">'
        f'<h4>{title}{trailing_html}</h4>{sub}</div>',
        unsafe_allow_html=True,
    )


def signed_number(value: float, fmt: str = ",.0f") -> str:
    """Return HTML for a mono-tabular number colored by sign."""
    cls = "pfe-pos" if value >= 0 else "pfe-neg"
    sign = "+" if value >= 0 else "−"
    return f'<span class="{cls}">{sign}{abs(value):{fmt}}</span>'
