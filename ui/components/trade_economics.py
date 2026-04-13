"""Trade economics: one-liner explanations and scenario analysis for trade specs."""

from __future__ import annotations

from typing import Optional

import numpy as np
import streamlit as st

from ui.components.payoff_display import (
    _compute_european_payoff,
    _compute_path_dependent_payoff,
    _apply_non_path_modifier,
    _PATH_DEPENDENT_TYPES,
    _PATH_DEPENDENT_MODIFIERS,
)


# ---------------------------------------------------------------------------
# Economics text — one-sentence descriptions per instrument type
# ---------------------------------------------------------------------------

def _econ_vanilla_call(params: dict, spot: float, direction: str) -> str:
    strike = params.get("strike", 0.0)
    if direction == "long":
        return (
            f"Long: pays notional \u00d7 max(spot \u2212 {strike:.4g}, 0) at maturity. "
            f"Profits when spot rises above {strike:.4g}."
        )
    return (
        f"Short: receives premium and pays notional \u00d7 max(spot \u2212 {strike:.4g}, 0) at maturity. "
        f"Profits when spot stays below {strike:.4g}."
    )


def _econ_vanilla_put(params: dict, spot: float, direction: str) -> str:
    strike = params.get("strike", 0.0)
    if direction == "long":
        return (
            f"Long: pays notional \u00d7 max({strike:.4g} \u2212 spot, 0) at maturity. "
            f"Profits when spot falls below {strike:.4g}."
        )
    return (
        f"Short: receives premium and pays notional \u00d7 max({strike:.4g} \u2212 spot, 0) at maturity. "
        f"Profits when spot stays above {strike:.4g}."
    )


def _econ_digital(params: dict, spot: float, direction: str) -> str:
    strike = params.get("strike", 0.0)
    opt_type = params.get("option_type", "call")
    condition = f"exceeds {strike:.4g}" if opt_type == "call" else f"falls below {strike:.4g}"
    prefix = "Long" if direction == "long" else "Short"
    return (
        f"{prefix}: pays fixed amount if spot {condition} at maturity. "
        f"Binary outcome \u2014 all or nothing."
    )


def _econ_dual_digital(params: dict, spot: float, direction: str) -> str:
    prefix = "Long" if direction == "long" else "Short"
    return (
        f"{prefix}: pays if both assets satisfy their respective barrier conditions at maturity. "
        f"Joint probability play."
    )


def _econ_triple_digital(params: dict, spot: float, direction: str) -> str:
    prefix = "Long" if direction == "long" else "Short"
    return (
        f"{prefix}: pays if all three assets satisfy their conditions. "
        f"Multi-asset correlation bet."
    )


def _econ_worst_of_call(params: dict, spot: float, direction: str) -> str:
    prefix = "Long" if direction == "long" else "Short"
    return (
        f"{prefix}: call on the worst-performing asset in the basket. "
        f"Cheaper than individual calls but exposed to the weakest link."
    )


def _econ_worst_of_put(params: dict, spot: float, direction: str) -> str:
    prefix = "Long" if direction == "long" else "Short"
    return (
        f"{prefix}: put on the worst-performing asset. "
        f"Protects against broad basket decline."
    )


def _econ_best_of_call(params: dict, spot: float, direction: str) -> str:
    prefix = "Long" if direction == "long" else "Short"
    return (
        f"{prefix}: call on the best-performing asset. "
        f"Captures upside from the strongest performer."
    )


def _econ_best_of_put(params: dict, spot: float, direction: str) -> str:
    prefix = "Long" if direction == "long" else "Short"
    return (
        f"{prefix}: put on the best-performing asset. "
        f"Protects the strongest asset\u2019s gains."
    )


def _econ_double_no_touch(params: dict, spot: float, direction: str) -> str:
    lower = params.get("lower", 0.0)
    upper = params.get("upper", 0.0)
    prefix = "Long" if direction == "long" else "Short"
    return (
        f"{prefix}: pays if spot stays within [{lower:.4g}, {upper:.4g}] throughout the life. "
        f"A volatility-selling strategy."
    )


def _econ_accumulator(params: dict, spot: float, direction: str) -> str:
    strike = params.get("strike", 0.0)
    leverage = params.get("leverage", 1.0)
    prefix = "Long" if direction == "long" else "Short"
    return (
        f"{prefix}: periodically buys at {strike:.4g} with {leverage:.4g}x leverage. "
        f"Accumulates below strike, forced accumulation above. Profits in range-bound markets."
    )


def _econ_decumulator(params: dict, spot: float, direction: str) -> str:
    strike = params.get("strike", 0.0)
    leverage = params.get("leverage", 1.0)
    prefix = "Long" if direction == "long" else "Short"
    return (
        f"{prefix}: periodically sells at {strike:.4g} with {leverage:.4g}x leverage. "
        f"Mirror of accumulator for sellers."
    )


def _econ_forward_starting(params: dict, spot: float, direction: str) -> str:
    prefix = "Long" if direction == "long" else "Short"
    return (
        f"{prefix}: option whose strike is set at a future date. "
        f"Exposure to future realized vol rather than current spot level."
    )


def _econ_restrike(params: dict, spot: float, direction: str) -> str:
    prefix = "Long" if direction == "long" else "Short"
    return (
        f"{prefix}: option whose strike resets at a specified date. "
        f"Locks in interim moves."
    )


def _econ_contingent(params: dict, spot: float, direction: str) -> str:
    trigger_barrier = params.get("trigger_barrier", 0.0)
    trigger_dir = params.get("trigger_direction", "up")
    action = "breaches above" if trigger_dir == "up" else "falls below"
    prefix = "Long" if direction == "long" else "Short"
    return (
        f"{prefix}: target payoff activates only if trigger asset {action} {trigger_barrier:.4g}. "
        f"Cross-asset conditional exposure."
    )


_ECONOMICS_TEXT: dict = {
    "VanillaCall":           _econ_vanilla_call,
    "VanillaPut":            _econ_vanilla_put,
    "Digital":               _econ_digital,
    "DualDigital":           _econ_dual_digital,
    "TripleDigital":         _econ_triple_digital,
    "WorstOfCall":           _econ_worst_of_call,
    "WorstOfPut":            _econ_worst_of_put,
    "BestOfCall":            _econ_best_of_call,
    "BestOfPut":             _econ_best_of_put,
    "DoubleNoTouch":         _econ_double_no_touch,
    "Accumulator":           _econ_accumulator,
    "Decumulator":           _econ_decumulator,
    "ForwardStartingOption": _econ_forward_starting,
    "RestrikeOption":        _econ_restrike,
    "ContingentOption":      _econ_contingent,
}


# ---------------------------------------------------------------------------
# Modifier economics text
# ---------------------------------------------------------------------------

_MODIFIER_ECONOMICS: dict = {
    "KnockOut": lambda p: (
        f"Knock-Out ({p.get('direction','up')}, barrier={p.get('barrier',0.0):.4g}): "
        f"entire payoff lost if barrier is breached. Reduces cost but adds gap risk."
    ),
    "KnockIn": lambda p: (
        f"Knock-In ({p.get('direction','down')}, barrier={p.get('barrier',0.0):.4g}): "
        f"payoff only activates if barrier is breached. Cheaper entry with activation condition."
    ),
    "PayoffCap": lambda p: (
        f"Payoff capped at {p.get('cap',0.0):.4g}. "
        f"Seller retains upside above cap \u2014 reduces premium."
    ),
    "PayoffFloor": lambda p: (
        f"Payoff floored at {p.get('floor',0.0):.4g}. "
        f"Guarantees minimum recovery."
    ),
    "LeverageModifier": lambda p: (
        f"Payoff leveraged {p.get('leverage',1.0):.4g}x above threshold {p.get('threshold',0.0):.4g}. "
        f"Amplifies gains (and losses) in the tail."
    ),
    "ObservationSchedule": lambda p: (
        "Custom observation dates override default schedule."
    ),
    "RealizedVolKnockOut": lambda p: (
        f"Knocks out if realized vol "
        f"{'exceeds' if p.get('direction','above') == 'above' else 'falls below'} "
        f"{p.get('vol_barrier',0.0):.4g}. Vol-contingent barrier."
    ),
    "RealizedVolKnockIn": lambda p: (
        f"Knocks in if realized vol "
        f"{'exceeds' if p.get('direction','above') == 'above' else 'falls below'} "
        f"{p.get('vol_barrier',0.0):.4g}. Vol-contingent activation."
    ),
}


# ---------------------------------------------------------------------------
# Scenario analysis
# ---------------------------------------------------------------------------

def compute_scenarios(
    spec: dict,
    spot: float,
    notional: float,
) -> list:
    """Compute payoffs at spot × 1.2, spot × 1.0, and spot × 0.8.

    Returns a list of dicts with keys:
        label, spot, raw_payoff, notional_payoff, direction_payoff
    """
    inst_type = spec["instrument_type"]
    params = spec.get("params", {})
    direction = spec.get("direction", "long")
    direction_sign = -1.0 if direction == "short" else 1.0

    multipliers = [1.2, 1.0, 0.8]
    labels = ["Spot +20%", "Spot  \u00b10%", "Spot \u221220%"]

    results = []
    for mult, label in zip(multipliers, labels):
        scenario_spot = spot * mult
        scenario_spots = np.array([scenario_spot])

        if inst_type in _PATH_DEPENDENT_TYPES:
            raw_arr = _compute_path_dependent_payoff(inst_type, params, scenario_spots)
        else:
            raw_arr = _compute_european_payoff(inst_type, params, scenario_spots)

        # Apply non-path modifiers
        for mod in spec.get("modifiers", []):
            mod_type = mod["type"]
            mod_params = mod.get("params", {})
            if mod_type not in _PATH_DEPENDENT_MODIFIERS:
                raw_arr = _apply_non_path_modifier(mod_type, mod_params, raw_arr)

        raw_payoff = float(raw_arr[0])
        notional_payoff = raw_payoff * notional
        direction_payoff = notional_payoff * direction_sign

        results.append({
            "label": label,
            "spot": scenario_spot,
            "raw_payoff": raw_payoff,
            "notional_payoff": notional_payoff,
            "direction_payoff": direction_payoff,
        })

    return results


# ---------------------------------------------------------------------------
# Render
# ---------------------------------------------------------------------------

def render_trade_economics(
    spec: dict,
    asset_names: list,
    market_spots,
) -> None:
    """Render trade economics explanation and scenario table via st.markdown.

    market_spots is a list[float] aligned with asset_names (session state format).
    """
    inst_type = spec["instrument_type"]
    params = spec.get("params", {})
    direction = spec.get("direction", "long")

    # Resolve spot for scenario table — market_spots is a list aligned with asset_names
    spot: float = 100.0
    if market_spots and asset_names:
        spots_list = list(market_spots)
        # Find which asset this trade references
        trade_assets = params.get("assets", [])
        target_name = trade_assets[0] if trade_assets else asset_names[0]
        if target_name in asset_names:
            idx = asset_names.index(target_name)
            if idx < len(spots_list):
                spot = float(spots_list[idx])
        elif spots_list:
            spot = float(spots_list[0])

    notional: float = float(params.get("notional", 1_000_000))

    # --- Economics text ---
    econ_fn = _ECONOMICS_TEXT.get(inst_type)
    if econ_fn is not None:
        econ_text = econ_fn(params, spot, direction)
    else:
        econ_text = f"{inst_type} — no economics description available."

    # --- Modifier texts ---
    modifier_lines: list = []
    for mod in spec.get("modifiers", []):
        mod_type = mod["type"]
        mod_params = mod.get("params", {})
        mod_fn = _MODIFIER_ECONOMICS.get(mod_type)
        if mod_fn is not None:
            modifier_lines.append(mod_fn(mod_params))

    # --- Scenario rows ---
    scenarios = compute_scenarios(spec, spot, notional)

    # --- Build HTML ---
    modifier_html = ""
    if modifier_lines:
        mod_items = "".join(
            f'<p style="color:#64748b; font-size:0.68rem; font-style:italic; margin:0.15rem 0;">'
            f"\u2022 {line}</p>"
            for line in modifier_lines
        )
        modifier_html = f'<div style="margin-bottom:0.4rem;">{mod_items}</div>'

    th_style = (
        "text-align:right; padding:0.3rem 0.5rem; color:#94a3b8; "
        "font-size:0.58rem; text-transform:uppercase; letter-spacing:0.08em;"
    )
    th_left_style = (
        "text-align:left; padding:0.3rem 0.5rem; color:#94a3b8; "
        "font-size:0.58rem; text-transform:uppercase; letter-spacing:0.08em;"
    )

    rows_html = ""
    for i, row in enumerate(scenarios):
        bg = "background:rgba(248,250,252,1);" if i % 2 == 0 else ""
        pnl = row["direction_payoff"]
        if pnl > 0:
            pnl_color = "#22c55e"
        elif pnl < 0:
            pnl_color = "#ef4444"
        else:
            pnl_color = "#64748b"

        pnl_str = f"{pnl:+,.0f}"

        rows_html += (
            f'<tr style="border-bottom:1px solid #f1f5f9; {bg}">'
            f'<td style="padding:0.25rem 0.5rem; color:#334155; font-size:0.72rem;">'
            f"{row['label']}</td>"
            f'<td style="padding:0.25rem 0.5rem; text-align:right; color:#64748b; font-size:0.72rem;">'
            f"{row['spot']:.4f}</td>"
            f'<td style="padding:0.25rem 0.5rem; text-align:right; color:#64748b; font-size:0.72rem;">'
            f"{row['raw_payoff']:.4f}</td>"
            f'<td style="padding:0.25rem 0.5rem; text-align:right; color:{pnl_color}; font-size:0.72rem;">'
            f"{pnl_str}</td>"
            f"</tr>"
        )

    html = f"""
<div style="padding:0.3rem 0;">
  <p style="color:#64748b; font-size:0.72rem; margin-bottom:0.4rem; margin-top:0;">{econ_text}</p>
  {modifier_html}
  <table style="width:100%; border-collapse:collapse; font-family:'JetBrains Mono',monospace; font-size:0.72rem; margin-top:0.4rem;">
    <thead>
      <tr style="border-bottom:1px solid #e2e8f0;">
        <th style="{th_left_style}">Scenario</th>
        <th style="{th_style}">Spot</th>
        <th style="{th_style}">Payoff</th>
        <th style="{th_style}">Notional P&amp;L</th>
      </tr>
    </thead>
    <tbody>
      {rows_html}
    </tbody>
  </table>
</div>
"""

    st.markdown(html, unsafe_allow_html=True)
