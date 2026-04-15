"""Payoff display: formula text and sparkline chart for trade specs."""

from typing import Optional

import numpy as np
import plotly.graph_objects as go

from ui.utils.product_content import SPARKLINE_SUPPORTED
from ui.utils.registry import INSTRUMENT_REGISTRY


# ---------------------------------------------------------------------------
# Formula text
# ---------------------------------------------------------------------------

_BASE_FORMULAS = {
    "VanillaCall":    lambda p: f"max(S - {p['strike']:.4g}, 0)",
    "VanillaPut":     lambda p: f"max({p['strike']:.4g} - S, 0)",
    "Digital":        lambda p: f"1{{S {'>' if p.get('option_type','call')=='call' else '<'} {p['strike']:.4g}}}",
    "DualDigital":    lambda p: "1{S\u2081,S\u2082 conditions}",
    "TripleDigital":  lambda p: "1{S\u2081,S\u2082,S\u2083 conditions}",
    "WorstOfCall":    lambda p: f"max(min(S\u1d62/K\u1d62) - 1, 0)",
    "WorstOfPut":     lambda p: f"max(1 - min(S\u1d62/K\u1d62), 0)",
    "BestOfCall":     lambda p: f"max(max(S\u1d62/K\u1d62) - 1, 0)",
    "BestOfPut":      lambda p: f"max(1 - max(S\u1d62/K\u1d62), 0)",
    "DoubleNoTouch":  lambda p: f"1{{{p.get('lower',0):.4g} < path < {p.get('upper',0):.4g}}}",
    "Accumulator":    lambda p: f"\u03a3 (S_t - {p['strike']:.4g}) \u00d7 lev={p['leverage']:.4g} [{p.get('side','buy')}]",
    "Decumulator":    lambda p: f"\u03a3 ({p['strike']:.4g} - S_t) \u00d7 lev={p['leverage']:.4g} [{p.get('side','sell')}]",
    "ForwardStartingOption": lambda p: f"max(S_T - S_start, 0) [{p.get('option_type','call')}]",
    "RestrikeOption": lambda p: f"max(S_T - S_reset, 0) [{p.get('option_type','call')}]",
    "ContingentOption": lambda p: f"payoff(target) \u00d7 1{{trigger {'>' if p.get('trigger_direction','up')=='up' else '<'} {p.get('trigger_barrier',0):.4g}}}",
    "SingleBarrier": lambda p: (
        f"max(S {'−' if p.get('option_type','call')=='call' else '− S, '}"
        f"{p.get('strike',0):.4g}"
        f"{', 0)' if p.get('option_type','call')=='call' else ''}"
        f" \u00b7 1{{S(T) {'>' if p.get('barrier_direction','up')=='up' else '<'} {p.get('barrier',0):.4g}}}"
    ),
    "AsianOption": lambda p: (
        f"max({'avg(S)' if p.get('average_type','price')=='price' else 'S(T)'}"
        f" \u2212 {'K' if p.get('average_type','price')=='price' else 'avg(S)'}, 0)"
        f" [{p.get('option_type','call')}]"
    ),
    "Cliquet": lambda p: (
        f"N \u00b7 max(\u03a3 clip(r\u1d62, {p.get('local_floor',0):.4g}, {p.get('local_cap',0):.4g}), "
        f"{p.get('global_floor',0):.4g})"
    ),
    "RangeAccrual": lambda p: (
        f"N \u00b7 (days_in / total) \u00b7 {p.get('coupon_rate',0):.4g}"
    ),
    "Autocallable": lambda p: (
        f"if called: coupon \u00d7 i | if not: max(worst_perf \u2212 1, put_strike \u2212 1)"
    ),
    "TARF": lambda p: (
        f"\u03a3 units \u00b7 (S \u2212 {p.get('strike',0):.4g}) [target={p.get('target',0):.4g}]"
    ),
}

_MODIFIER_FORMULAS = {
    "KnockOut":          lambda p, inner: f"{inner} \u00b7 1{{path {'<' if p['direction']=='up' else '>'} {p['barrier']:.4g}}}",
    "KnockIn":           lambda p, inner: f"{inner} \u00b7 1{{path {'>' if p['direction']=='up' else '<'} {p['barrier']:.4g}}}",
    "PayoffCap":         lambda p, inner: f"min({inner}, {p['cap']:.4g})",
    "PayoffFloor":       lambda p, inner: f"max({inner}, {p['floor']:.4g})",
    "LeverageModifier":  lambda p, inner: f"{inner} \u00d7 {p['leverage']:.4g} [above {p['threshold']:.4g}]",
    "ObservationSchedule": lambda p, inner: inner,
    "RealizedVolKnockOut": lambda p, inner: f"{inner} \u00b7 1{{rv {'<' if p['direction']=='above' else '>'} {p['vol_barrier']:.4g}}}",
    "RealizedVolKnockIn":  lambda p, inner: f"{inner} \u00b7 1{{rv {'>' if p['direction']=='above' else '<'} {p['vol_barrier']:.4g}}}",
    "TargetProfit": lambda p, inner: f"min({inner}, {p.get('target',0):.4g})",
}


def payoff_formula(spec: dict) -> str:
    """Return a text formula for the trade spec."""
    inst_type = spec["instrument_type"]
    params = spec.get("params", {})
    direction = spec.get("direction", "long")

    formatter = _BASE_FORMULAS.get(inst_type)
    if formatter is None:
        formula = f"{inst_type}(S)"
    else:
        formula = formatter(params)

    for mod in spec.get("modifiers", []):
        mod_type = mod["type"]
        mod_params = mod.get("params", {})
        mod_formatter = _MODIFIER_FORMULAS.get(mod_type)
        if mod_formatter:
            formula = mod_formatter(mod_params, formula)

    if direction == "short":
        formula = f"-({formula})"

    return formula


# ---------------------------------------------------------------------------
# Sparkline chart
# ---------------------------------------------------------------------------

_PATH_DEPENDENT_TYPES = {
    "Accumulator", "Decumulator", "DoubleNoTouch",
    "ForwardStartingOption", "RestrikeOption",
    "AsianOption", "Cliquet", "RangeAccrual",
    "Autocallable", "TARF",
}

_PATH_DEPENDENT_MODIFIERS = {
    "KnockOut", "KnockIn", "RealizedVolKnockOut", "RealizedVolKnockIn",
    "TargetProfit",
}


def _compute_european_payoff(inst_type: str, params: dict, spots: np.ndarray) -> np.ndarray:
    """Compute payoff for a European instrument over a range of terminal spots."""
    reg = INSTRUMENT_REGISTRY.get(inst_type)
    if reg is None:
        return np.zeros_like(spots)
    cls = reg["cls"]
    n_assets = reg.get("n_assets", 1)
    if isinstance(n_assets, str):
        n_assets = int(n_assets.split("-")[0])

    kwargs = dict(params)
    kwargs["trade_id"] = "__preview__"
    kwargs.pop("assets", None)
    kwargs["asset_indices"] = tuple(range(n_assets))

    try:
        inst = cls(**kwargs)
    except Exception:
        return np.zeros_like(spots)

    spots_2d = np.tile(spots[:, np.newaxis], (1, n_assets))
    return inst.payoff(spots_2d, None)


def _compute_path_dependent_payoff(inst_type: str, params: dict, spots: np.ndarray) -> np.ndarray:
    """Compute simplified payoff for path-dependent instrument assuming flat path."""
    reg = INSTRUMENT_REGISTRY.get(inst_type)
    if reg is None:
        return np.zeros_like(spots)
    cls = reg["cls"]
    n_assets = reg.get("n_assets", 1)
    if isinstance(n_assets, str):
        n_assets = int(n_assets.split("-")[0])

    kwargs = dict(params)
    kwargs["trade_id"] = "__preview__"
    kwargs.pop("assets", None)
    kwargs["asset_indices"] = tuple(range(n_assets))

    try:
        inst = cls(**kwargs)
    except Exception:
        return np.zeros_like(spots)

    n_steps = 20
    payoffs = np.zeros(len(spots))
    for i, s in enumerate(spots):
        path = np.full((1, n_steps, n_assets), s)
        spots_terminal = np.full((1, n_assets), s)
        try:
            payoffs[i] = inst.payoff(spots_terminal, path)[0]
        except Exception:
            payoffs[i] = 0.0
    return payoffs


def _apply_non_path_modifier(mod_type: str, mod_params: dict, payoffs: np.ndarray) -> np.ndarray:
    """Apply a non-path-dependent modifier to a payoff array."""
    if mod_type == "PayoffCap":
        return np.minimum(payoffs, mod_params["cap"])
    if mod_type == "PayoffFloor":
        return np.maximum(payoffs, mod_params["floor"])
    if mod_type == "LeverageModifier":
        threshold = mod_params["threshold"]
        leverage = mod_params["leverage"]
        return np.where(payoffs > threshold, payoffs * leverage, payoffs)
    return payoffs


def payoff_sparkline(spec: dict, asset_names: list) -> Optional[go.Figure]:
    """Generate a compact Plotly sparkline of the payoff profile.

    Returns None for instrument types that cannot be meaningfully represented
    by a simple terminal-payoff sparkline (schedule-heavy / path-complex types).
    """
    inst_type = spec["instrument_type"]
    if inst_type not in SPARKLINE_SUPPORTED:
        return None
    params = spec.get("params", {})
    direction = spec.get("direction", "long")

    strike = params.get("strike", 100.0)
    if isinstance(strike, (list, tuple)):
        strike = strike[0]
    spot_lo = strike * 0.5
    spot_hi = strike * 1.5
    spots = np.linspace(spot_lo, spot_hi, 200)

    if inst_type in _PATH_DEPENDENT_TYPES:
        payoffs = _compute_path_dependent_payoff(inst_type, params, spots)
    else:
        payoffs = _compute_european_payoff(inst_type, params, spots)

    barrier_annotations = []
    for mod in spec.get("modifiers", []):
        mod_type = mod["type"]
        mod_params = mod.get("params", {})
        if mod_type in _PATH_DEPENDENT_MODIFIERS:
            barrier_annotations.append((mod_type, mod_params))
        else:
            payoffs = _apply_non_path_modifier(mod_type, mod_params, payoffs)

    if direction == "short":
        payoffs = -payoffs

    # Colors matching light fintech theme
    long_color = "#22c55e"
    long_fill = "rgba(34,197,94,0.08)"
    short_color = "#ef4444"
    short_fill = "rgba(239,68,68,0.08)"

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=spots, y=payoffs,
        mode="lines",
        name="Payoff",
        line=dict(color=long_color if direction == "long" else short_color, width=2),
        fill="tozeroy",
        fillcolor=long_fill if direction == "long" else short_fill,
    ))

    for mod_type, mod_params in barrier_annotations:
        barrier = mod_params.get("barrier", mod_params.get("vol_barrier"))
        if barrier is not None:
            label = mod_type.replace("RealizedVol", "RV ")
            y_lo = float(np.min(payoffs))
            y_hi = float(np.max(payoffs))
            fig.add_trace(go.Scatter(
                x=[barrier, barrier],
                y=[y_lo, y_hi],
                mode="lines",
                name=label,
                line=dict(color="#f59e0b", width=1.5, dash="dot"),
            ))

    fig.add_hline(y=0, line_color="#e2e8f0", line_width=0.5)

    fig.update_layout(
        height=100,
        margin=dict(l=0, r=0, t=0, b=0),
        showlegend=False,
        xaxis=dict(showticklabels=True, title="",
                   gridcolor="#f1f5f9", linecolor="#e2e8f0",
                   tickfont=dict(size=9, color="#94a3b8")),
        yaxis=dict(showticklabels=True, title="",
                   gridcolor="#f1f5f9", linecolor="#e2e8f0",
                   tickfont=dict(size=9, color="#94a3b8")),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )

    return fig
