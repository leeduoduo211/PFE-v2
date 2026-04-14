"""Trade economics: term-sheet style descriptions and scenario analysis."""

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
# Formatting helpers
# ---------------------------------------------------------------------------

def _fmt_money(n: float) -> str:
    return f"{n:,.0f}"


def _fmt_yrs(t: float) -> str:
    if t >= 1.0:
        return f"{t:.2f}y"
    return f"{t * 12:.1f}m"


def _fmt_num(x: float) -> str:
    return f"{x:.4g}"


def _asset_phrase(params: dict) -> str:
    assets = params.get("assets") or []
    if not assets:
        return "the underlying"
    if len(assets) == 1:
        return assets[0]
    if len(assets) == 2:
        return f"{assets[0]} and {assets[1]}"
    return ", ".join(assets[:-1]) + f", and {assets[-1]}"


def _strikes_phrase(params: dict) -> str:
    ks = params.get("strikes") or []
    return ", ".join(_fmt_num(k) for k in ks)


def _header(direction: str, label: str, params: dict) -> str:
    side = "Long" if direction == "long" else "Short"
    notional = _fmt_money(params.get("notional", 0.0))
    maturity = _fmt_yrs(params.get("maturity", 0.0))
    asset = _asset_phrase(params)
    return f"<b>{side} {label}</b> on <b>{asset}</b> &mdash; notional {notional}, maturity {maturity}"


# ---------------------------------------------------------------------------
# Term-sheet builders — one per instrument type.
# Each function returns a multi-sentence description that combines the
# trade's actual attributes with a brief economic interpretation.
# ---------------------------------------------------------------------------

def _ts_vanilla_call(params: dict, direction: str) -> str:
    K = _fmt_num(params.get("strike", 0.0))
    asset = _asset_phrase(params)
    head = _header(direction, "vanilla call", params) + f", strike {K}."
    if direction == "long":
        body = (
            f" The long pays an upfront premium and receives notional &times; max(S<sub>T</sub> &minus; {K}, 0) "
            f"at maturity, capturing unlimited upside above {K} with the maximum loss bounded by the premium. "
            f"Risk is dominated by delta and vega; the position bleeds theta in calm markets."
        )
    else:
        body = (
            f" The short collects the premium today and is obliged to pay notional &times; max(S<sub>T</sub> &minus; {K}, 0) "
            f"at maturity, profiting if {asset} stays at or below {K}. The exposure is unbounded if {asset} rallies, "
            f"which is why short calls dominate the upside tail of the PFE profile."
        )
    return head + body


def _ts_vanilla_put(params: dict, direction: str) -> str:
    K = _fmt_num(params.get("strike", 0.0))
    asset = _asset_phrase(params)
    head = _header(direction, "vanilla put", params) + f", strike {K}."
    if direction == "long":
        body = (
            f" The long pays a premium and receives notional &times; max({K} &minus; S<sub>T</sub>, 0) at maturity &mdash; "
            f"a textbook hedge against {asset} drawdowns, with maximum profit bounded by {K} (assuming a non-negative spot)."
        )
    else:
        body = (
            f" The short collects premium and accepts the obligation to pay notional &times; max({K} &minus; S<sub>T</sub>, 0). "
            f"Equivalent to selling crash insurance: comfortable carry in calm markets, large losses in a sharp decline of {asset}."
        )
    return head + body


def _ts_digital(params: dict, direction: str) -> str:
    K = _fmt_num(params.get("strike", 0.0))
    opt = params.get("option_type", "call")
    cmp_word = "above" if opt == "call" else "below"
    cmp_sym = "&gt;" if opt == "call" else "&lt;"
    asset = _asset_phrase(params)
    notional = _fmt_money(params.get("notional", 0.0))
    head = _header(direction, f"digital {opt}", params) + f", strike {K}."
    side = "long receives" if direction == "long" else "short pays"
    body = (
        f" At maturity the {side} the fixed amount {notional} if {asset} finishes {cmp_word} {K} "
        f"(S<sub>T</sub> {cmp_sym} {K}) and zero otherwise. The payoff is binary, so the trade concentrates "
        f"sharp gamma and pin risk near {K} at expiry &mdash; small spot moves can flip the entire P&amp;L."
    )
    return head + body


def _ts_dual_digital(params: dict, direction: str) -> str:
    assets = params.get("assets") or []
    a1 = assets[0] if len(assets) > 0 else "asset 1"
    a2 = assets[1] if len(assets) > 1 else "asset 2"
    strikes = params.get("strikes") or []
    types = params.get("option_types") or []
    k1 = _fmt_num(strikes[0]) if len(strikes) > 0 else "K1"
    k2 = _fmt_num(strikes[1]) if len(strikes) > 1 else "K2"
    op1 = "&gt;" if (types[0] if len(types) > 0 else "call") == "call" else "&lt;"
    op2 = "&gt;" if (types[1] if len(types) > 1 else "call") == "call" else "&lt;"
    notional = _fmt_money(params.get("notional", 0.0))
    head = _header(direction, "dual digital", params) + "."
    body = (
        f" Pays the fixed amount {notional} only if both legs satisfy their barrier conditions at maturity "
        f"({a1} {op1} {k1} <i>and</i> {a2} {op2} {k2}). The trade is implicitly long correlation: higher "
        f"co-movement between {a1} and {a2} raises the joint probability of payoff, lifting the premium."
    )
    return head + body


def _ts_triple_digital(params: dict, direction: str) -> str:
    assets = params.get("assets") or []
    strikes = params.get("strikes") or []
    types = params.get("option_types") or []
    parts = []
    for i in range(min(3, len(assets))):
        a = assets[i]
        k = _fmt_num(strikes[i]) if i < len(strikes) else "K"
        op = "&gt;" if (types[i] if i < len(types) else "call") == "call" else "&lt;"
        parts.append(f"{a} {op} {k}")
    cond = " <i>and</i> ".join(parts)
    notional = _fmt_money(params.get("notional", 0.0))
    head = _header(direction, "triple digital", params) + "."
    body = (
        f" Pays {notional} at maturity only if all three legs are simultaneously satisfied ({cond}). "
        f"Premium is low because the joint event is rare, but sensitivity to the full correlation matrix is "
        f"extreme &mdash; small mis-estimates of co-movement produce large MtM swings."
    )
    return head + body


def _ts_worst_of_call(params: dict, direction: str) -> str:
    head = _header(direction, "worst-of call", params) + f", strikes {_strikes_phrase(params)}."
    body = (
        " Terminal payoff is notional &times; max(min<sub>i</sub>(S<sub>i</sub>/K<sub>i</sub>) &minus; 1, 0) "
        "&mdash; only the weakest performer in the basket drives the payout. The long captures basket upside "
        "cheaply versus a strip of individual calls but is short dispersion: low correlation increases the chance "
        "the worst leg disappoints, hurting the buyer and benefiting the seller."
    )
    return head + body


def _ts_worst_of_put(params: dict, direction: str) -> str:
    head = _header(direction, "worst-of put", params) + f", strikes {_strikes_phrase(params)}."
    body = (
        " Pays notional &times; max(1 &minus; min<sub>i</sub>(S<sub>i</sub>/K<sub>i</sub>), 0) &mdash; the canonical "
        "downside-protection wrapper inside autocallable notes, since the put activates on whichever asset falls the most. "
        "The long is long correlation; the short carries the dispersion-crash tail (one stock collapses while the others hold up)."
    )
    return head + body


def _ts_best_of_call(params: dict, direction: str) -> str:
    head = _header(direction, "best-of call", params) + f", strikes {_strikes_phrase(params)}."
    body = (
        " Pays notional &times; max(max<sub>i</sub>(S<sub>i</sub>/K<sub>i</sub>) &minus; 1, 0) &mdash; only the best "
        "performer matters, so the structure automatically rotates into the strongest leg. The long is long dispersion: "
        "low correlation raises the chance that at least one asset rallies hard, lifting the premium."
    )
    return head + body


def _ts_best_of_put(params: dict, direction: str) -> str:
    head = _header(direction, "best-of put", params) + f", strikes {_strikes_phrase(params)}."
    body = (
        " Pays notional &times; max(1 &minus; max<sub>i</sub>(S<sub>i</sub>/K<sub>i</sub>), 0) &mdash; a deep-OTM bearish "
        "bet that requires every basket member, including the strongest, to finish below its strike. Premium is low and "
        "sellers are exposed only in severe correlated drawdowns, which produces a fat-tail asymmetry in the PFE profile."
    )
    return head + body


def _ts_double_no_touch(params: dict, direction: str) -> str:
    lo = _fmt_num(params.get("lower", 0.0))
    hi = _fmt_num(params.get("upper", 0.0))
    asset = _asset_phrase(params)
    notional = _fmt_money(params.get("notional", 0.0))
    head = _header(direction, "double no-touch", params) + f", corridor [{lo}, {hi}]."
    body = (
        f" Pays {notional} at maturity only if {asset} stays strictly inside [{lo}, {hi}] for the entire life &mdash; "
        f"the first touch of either barrier extinguishes the trade. The long is short volatility and short gamma: a quiet, "
        f"range-bound market wins, any spike loses everything. Sellers face large gap risk near the barriers."
    )
    return head + body


def _ts_accumulator(params: dict, direction: str) -> str:
    K = _fmt_num(params.get("strike", 0.0))
    lev = _fmt_num(params.get("leverage", 1.0))
    side = params.get("side", "buy")
    asset = _asset_phrase(params)
    head = _header(direction, "accumulator", params) + f", strike {K}, leverage {lev}&times; ({side} side)."
    body = (
        f" At each observation date the buyer accumulates {asset} at {K}; if spot prints below {K} the leverage clause "
        f"forces buying at {lev}&times; the standard quantity. Profitable in calm or rising markets above the strike, "
        f"but in a sharp decline the leveraged-buying clause forces continued purchases into a falling market &mdash; the "
        f"asymmetry that produced the famous 2008 Hong Kong accumulator losses and that dominates the long tail of exotic PFE."
    )
    return head + body


def _ts_decumulator(params: dict, direction: str) -> str:
    K = _fmt_num(params.get("strike", 0.0))
    lev = _fmt_num(params.get("leverage", 1.0))
    asset = _asset_phrase(params)
    head = _header(direction, "decumulator", params) + f", strike {K}, leverage {lev}&times;."
    body = (
        f" Mirror image of an accumulator: the holder periodically sells {asset} at {K}, with the leverage clause forcing "
        f"sales at {lev}&times; size if spot rises above {K}. Used by holders of concentrated long positions to monetise "
        f"gradually above market; the risk shows up in trending bull markets where forced selling at {K} crystallises a "
        f"large opportunity-cost loss."
    )
    return head + body


def _ts_forward_starting(params: dict, direction: str) -> str:
    t0 = _fmt_num(params.get("start_time", 0.0))
    opt = params.get("option_type", "call")
    asset = _asset_phrase(params)
    sign = "&minus;" if opt == "call" else "(reversed for puts)"
    head = _header(direction, f"forward-starting {opt}", params) + f", strike fixed at t = {t0}y."
    body = (
        f" The strike is set to the spot of {asset} observed at t = {t0}y; the option then pays "
        f"notional &times; max(S<sub>T</sub> {sign} S<sub>{t0}</sub>, 0) at maturity. Today's exposure is to the forward "
        f"volatility surface rather than spot level &mdash; the PFE profile is roughly flat at inception and only ramps up "
        f"once the strike is fixed."
    )
    return head + body


def _ts_restrike(params: dict, direction: str) -> str:
    tr = _fmt_num(params.get("reset_time", 0.0))
    opt = params.get("option_type", "call")
    head = _header(direction, f"restrike {opt}", params) + f", reset at t = {tr}y."
    body = (
        f" At t = {tr}y the strike resets to the prevailing spot, locking in any interim move and continuing with a fresh "
        f"strike for the remaining life of the trade. The long pays a higher premium for an automatic profit lock-in &mdash; "
        f"the structure is most common in retail \u201cguaranteed lock\u201d notes."
    )
    return head + body


def _ts_contingent(params: dict, direction: str) -> str:
    assets = params.get("assets") or []
    trig_idx = int(params.get("trigger_asset_idx", 0) or 0)
    targ_idx = int(params.get("target_asset_idx", 0) or 0)
    trig = assets[trig_idx] if trig_idx < len(assets) else "trigger asset"
    targ = assets[targ_idx] if targ_idx < len(assets) else "target asset"
    tb = _fmt_num(params.get("trigger_barrier", 0.0))
    tdir = params.get("trigger_direction", "up")
    breach = "breaches above" if tdir == "up" else "falls below"
    targ_type = params.get("target_type", "call")
    targ_K = _fmt_num(params.get("target_strike", 0.0))
    side = "Long" if direction == "long" else "Short"
    notional = _fmt_money(params.get("notional", 0.0))
    maturity = _fmt_yrs(params.get("maturity", 0.0))
    head = (
        f"<b>{side} contingent {targ_type}</b> on <b>{targ}</b> (strike {targ_K}), "
        f"triggered by <b>{trig}</b> &mdash; notional {notional}, maturity {maturity}."
    )
    body = (
        f" The {targ_type} payoff on {targ} activates only if {trig} {breach} {tb} at maturity; the trigger asset acts as "
        f"an on/off switch while {targ} determines the payoff size. Pricing is driven by the correlation between {trig} and "
        f"{targ}, and the trade is much cheaper than the unconditional vanilla because the trigger reduces the probability of payoff."
    )
    return head + body


_TERM_SHEETS: dict = {
    "VanillaCall":           _ts_vanilla_call,
    "VanillaPut":            _ts_vanilla_put,
    "Digital":               _ts_digital,
    "DualDigital":           _ts_dual_digital,
    "TripleDigital":         _ts_triple_digital,
    "WorstOfCall":           _ts_worst_of_call,
    "WorstOfPut":            _ts_worst_of_put,
    "BestOfCall":            _ts_best_of_call,
    "BestOfPut":             _ts_best_of_put,
    "DoubleNoTouch":         _ts_double_no_touch,
    "Accumulator":           _ts_accumulator,
    "Decumulator":           _ts_decumulator,
    "ForwardStartingOption": _ts_forward_starting,
    "RestrikeOption":        _ts_restrike,
    "ContingentOption":      _ts_contingent,
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

    # --- Term sheet (combined trade attributes + economic interpretation) ---
    ts_fn = _TERM_SHEETS.get(inst_type)
    if ts_fn is not None:
        term_sheet_html = ts_fn(params, direction)
    else:
        term_sheet_html = f"{inst_type} &mdash; no description available."

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
  <p style="color:#334155; font-size:0.8rem; line-height:1.55; margin:0 0 0.55rem 0;">{term_sheet_html}</p>
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
