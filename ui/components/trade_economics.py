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
# Extended narrative — 1-2 paragraph explanation per instrument
# Covers: economic intent, typical use case, key risks, P&L profile.
# ---------------------------------------------------------------------------

_INSTRUMENT_NARRATIVE: dict = {
    "VanillaCall": (
        "A vanilla call gives the holder the right (but not the obligation) to buy the underlying at the strike "
        "on the maturity date. The long position pays an upfront premium in exchange for unlimited upside above "
        "the strike, while downside is capped at the premium paid. It is the simplest expression of a bullish view "
        "with leverage \u2014 a small premium controls a large notional exposure to upward moves.\n\n"
        "From a risk perspective, the long is exposed to time decay (theta) and changes in implied volatility (vega), "
        "and benefits from realized moves above the strike. The short side collects the premium but takes on unlimited "
        "tail risk if the underlying rallies sharply, which is why short calls drive the largest counterparty exposures "
        "in PFE calculations."
    ),

    "VanillaPut": (
        "A vanilla put gives the holder the right to sell the underlying at the strike on the maturity date. "
        "Long puts are the textbook hedge against downside risk \u2014 portfolio managers buy them as insurance "
        "against equity drawdowns or to express a bearish directional view with limited downside (the premium paid). "
        "The maximum profit is bounded by the strike (assuming the underlying can't go negative).\n\n"
        "Short puts are functionally equivalent to selling insurance: you collect a premium and accept the obligation "
        "to buy at the strike if assigned. This generates carry in calm markets but exposes the writer to large losses "
        "in a crash, making short put PFE profiles particularly sensitive to skew and tail-event scenarios."
    ),

    "Digital": (
        "A digital (or binary) option pays a fixed cash amount if the underlying finishes on the right side of the "
        "strike at maturity \u2014 and zero otherwise. The payoff is discontinuous: a one-cent move across the strike "
        "is the difference between full payout and nothing. Digitals are popular for expressing precise event views "
        "(e.g. \u201cwill stock close above $100 at year-end?\u201d) without paying for the convex tail of a vanilla option.\n\n"
        "Risk-wise, digitals concentrate gamma and delta around the strike near expiry, making them difficult to hedge "
        "and inherently exposed to pin risk. Sellers face binary outcomes that can flip the entire P&L on small spot "
        "moves close to maturity, which shows up as sharp local spikes in the PFE profile."
    ),

    "DualDigital": (
        "A dual digital pays a fixed amount only if both reference assets satisfy their respective barrier conditions "
        "at maturity. It is a compact way to express a joint-event view across two markets \u2014 for example, "
        "\u201cEUR/USD above 1.10 AND S&P above 4500\u201d \u2014 at a fraction of the cost of two separate digitals, "
        "since the joint probability is lower than either marginal probability.\n\n"
        "Pricing depends heavily on the correlation between the two underlyings: a long dual digital benefits from "
        "high positive correlation (when conditions naturally co-move), while the short side is most exposed under "
        "those same correlation regimes. This makes the trade an implicit correlation play as much as a directional one."
    ),

    "TripleDigital": (
        "A triple digital extends the dual digital concept to three reference assets: payment occurs only when all "
        "three barrier conditions are simultaneously satisfied at maturity. This is a deeply out-of-the-money joint "
        "event play, used to monetise convictions about cross-asset co-movement \u2014 e.g. simultaneous moves across "
        "FX, rates, and equities.\n\n"
        "Because the payoff requires three independent (or partially correlated) events to align, premium is very low "
        "but sensitivity to the full correlation matrix is extreme. Small mis-estimates of correlation can cause large "
        "MtM swings, and the joint barrier structure produces lumpy, non-monotonic exposure profiles."
    ),

    "WorstOfCall": (
        "A worst-of call pays the upside of the worst-performing asset in a basket relative to its strike. From the "
        "buyer's perspective, this is much cheaper than a basket of individual calls because you only get paid on the "
        "weakest performer \u2014 the seller benefits from any divergence in the basket. Investors use worst-of structures "
        "to express bullish views on a sector while accepting limited dispersion risk in exchange for a lower entry cost.\n\n"
        "The trade is short correlation: the lower the correlation between basket members, the cheaper it is, because "
        "low correlation increases the chance that at least one asset will underperform. Worst-of calls are common "
        "ingredients in autocallables and structured equity notes, and their PFE exposure tends to grow as basket "
        "dispersion increases."
    ),

    "WorstOfPut": (
        "A worst-of put pays out based on the decline of the worst-performing asset in a basket. It is the canonical "
        "downside-protection wrapper inside autocallable notes: it gives the structure issuer cheap basket protection "
        "because the put activates on whichever asset falls the most, regardless of the basket's average performance.\n\n"
        "Buyers (often retail-note issuers hedging their books) are long correlation \u2014 high correlation makes the "
        "basket move together, reducing the chance that any single name falls catastrophically. Sellers face significant "
        "tail risk in dispersion-heavy crashes, where one stock collapses while the others hold up, and this asymmetry "
        "drives the bulk of the exposure in many structured-product portfolios."
    ),

    "BestOfCall": (
        "A best-of call pays the upside of the best-performing asset in a basket. Unlike a worst-of, the buyer captures "
        "whichever asset rallies the most, making it strictly more expensive than any individual call in the basket. "
        "It is used when an investor wants exposure to a theme but doesn't want to pick a winner \u2014 the structure "
        "automatically rotates into the strongest performer.\n\n"
        "From a risk angle, the trade is long dispersion (short correlation): low correlation between basket members "
        "increases the chance that at least one will rally strongly, raising the premium. Best-of calls are popular in "
        "thematic notes (e.g. \u201cbest-of three EV manufacturers\u201d) and their PFE profile reflects strong upside "
        "convexity, particularly in low-correlation regimes."
    ),

    "BestOfPut": (
        "A best-of put pays based on the decline of the best-performing asset in a basket. It is an unusual structure "
        "because it requires the basket's strongest member to still finish below its strike for any payoff to occur \u2014 "
        "effectively a deep-OTM bearish bet on the entire basket. As a result, premiums are low and the trade is rarely "
        "used outside of bespoke hedging contexts.\n\n"
        "The trade is structurally short tail risk on broad market crashes, since a payoff requires every asset in the "
        "basket to be down hard. Sellers can be hurt only in severe correlated drawdowns, which is exactly when liquidity "
        "and recovery are also impaired \u2014 the PFE profile reflects this fat-tail asymmetry."
    ),

    "DoubleNoTouch": (
        "A double no-touch pays a fixed amount only if the underlying stays strictly inside a defined range "
        "[lower, upper] for the entire life of the trade. The first time spot touches either barrier, the option is "
        "extinguished. It is a pure short-volatility, range-bound play: holders profit from quiet, mean-reverting "
        "markets and lose if any volatility spike pushes spot to a barrier.\n\n"
        "Because the payoff is binary and path-dependent, sellers face very large gap risk near the barriers \u2014 a "
        "single intraday spike can wipe out the entire position. The trade is most popular in FX markets during "
        "low-vol regimes, and its PFE profile typically shows sharp localized spikes as spot approaches either edge "
        "of the range."
    ),

    "Accumulator": (
        "An accumulator (also known as a target redemption forward or, infamously, an \u2018I-kill-you-later\u2019) is "
        "a periodic forward contract: at each observation date, the buyer accumulates a fixed quantity of the underlying "
        "at a discounted strike. If spot is above the strike, accumulation continues at single size; if spot is below, "
        "leverage kicks in and the buyer is forced to take a multiple of the standard quantity (typically 2x). "
        "Some accumulators include a knock-out that terminates the structure once the buyer is sufficiently in the money.\n\n"
        "Buyers love accumulators because the strike is below current spot \u2014 they get a discount in calm or rising "
        "markets. The danger is asymmetric: in a sharp decline, the leveraged-buying clause forces the holder to keep "
        "buying into a falling market at twice the notional, generating large mark-to-market losses. This asymmetry "
        "produced the famous 2008 Hong Kong accumulator losses and is why the structure dominates the long tail of "
        "exotic-derivative PFE."
    ),

    "Decumulator": (
        "A decumulator is the mirror image of an accumulator: the holder periodically sells a fixed quantity of the "
        "underlying at a strike that is above current spot, with leverage kicking in if spot rises above the strike "
        "(forced selling at 2x size). It is used by holders of concentrated long positions to monetise gradually "
        "above market \u2014 typical clients are corporates or strategic shareholders unwinding a stake.\n\n"
        "The risk is symmetric to the accumulator: in a sharp rally, the leverage clause forces the seller to deliver "
        "double quantity at a price well below market, generating large opportunity-cost losses. Decumulator PFE profiles "
        "are dominated by upside scenarios and grow worst in trending bull markets."
    ),

    "ForwardStartingOption": (
        "A forward-starting option is one whose strike is not fixed today but is set at a future date \u2014 typically "
        "as a percentage (e.g. 100%) of the spot observed on that date. This effectively decouples the trade from "
        "today's level and gives pure exposure to the realized volatility and behaviour of the underlying between the "
        "strike-setting date and maturity.\n\n"
        "Forward starts are a building block in cliquet structures and employee stock plans, where the strike resets "
        "periodically. Their pricing depends on the forward volatility surface rather than spot vol, and their PFE "
        "profile is notable for being roughly flat at inception (no strike yet) and only ramping up after the strike "
        "fixing date."
    ),

    "RestrikeOption": (
        "A restrike (or ratchet) option is one whose strike is reset on a specified date \u2014 typically locking in "
        "any favourable spot move to that point. If spot has rallied, the long restrike call captures the interim move "
        "and then continues with a higher strike for the remaining life. This is a way to monetise interim performance "
        "without needing to close and re-open positions.\n\n"
        "The structure trades a higher upfront premium for the convenience of an automatic profit lock-in, and is most "
        "common in retail structured products marketed as \u201cguaranteed profit lock\u201d notes. PFE profiles show a "
        "characteristic step at the restrike date as the option's intrinsic value crystallises into the new strike."
    ),

    "ContingentOption": (
        "A contingent option pays out a target payoff (usually a vanilla call or put) only if a separate trigger asset "
        "satisfies a barrier condition at maturity. The two assets are independent: the trigger acts purely as a switch, "
        "while the target asset determines the payoff size. Investors use it to express conditional views \u2014 "
        "e.g. \u201cI want upside on Stock A, but only if oil is above $80\u201d.\n\n"
        "The trade is much cheaper than the equivalent unconditional vanilla because the trigger condition reduces the "
        "probability of payoff. Pricing is sensitive to the correlation between trigger and target assets, and PFE "
        "profiles can be lumpy because the conditional structure introduces a discrete dependence on the trigger path."
    ),
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

    # --- Extended narrative (1-2 paragraphs) ---
    narrative = _INSTRUMENT_NARRATIVE.get(inst_type, "")
    narrative_paragraphs = [p.strip() for p in narrative.split("\n\n") if p.strip()]

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

    narrative_html = "".join(
        f'<p style="color:#475569; font-size:0.78rem; line-height:1.55; '
        f'margin:0 0 0.55rem 0;">{p}</p>'
        for p in narrative_paragraphs
    )

    html = f"""
<div style="padding:0.3rem 0;">
  {narrative_html}
  <p style="color:#64748b; font-size:0.72rem; font-style:italic; margin-bottom:0.4rem; margin-top:0;">{econ_text}</p>
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
