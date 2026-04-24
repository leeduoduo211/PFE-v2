"""
Presentation-layer data for all 18 instruments and 9 modifiers.

Pure data — no rendering logic. Consumed by the Streamlit trade builder
and related UI components.
"""

# ---------------------------------------------------------------------------
# Category colors — derived from the single source of truth in ui.theme.
# The dict shape is preserved for call-site compatibility.
# ---------------------------------------------------------------------------

from ui.theme import COLORS as _THEME

CATEGORY_COLORS = {
    "European":       _THEME["cat_european"],
    "Path-dependent": _THEME["cat_path_dependent"],
    "Multi-asset":    _THEME["cat_multi_asset"],
    "Periodic":       _THEME["cat_periodic"],
}

# ---------------------------------------------------------------------------
# Product descriptions — one-liner per instrument
# ---------------------------------------------------------------------------

PRODUCT_DESCRIPTIONS = {
    # European
    "VanillaOption": (
        "Pays max(S - K, 0) for a call or max(K - S, 0) for a put at expiry; "
        "the standard directional participation contract."
    ),
    "Digital": (
        "Pays a fixed amount (1) if spot finishes on the correct side of the strike."
    ),
    "ContingentOption": (
        "Vanilla payoff on a target asset that only activates when a trigger asset "
        "crosses a barrier at expiry."
    ),
    "SingleBarrier": (
        "European call/put whose payoff is activated (knock-in) or cancelled "
        "(knock-out) if spot crosses a barrier at expiry."
    ),
    # Path-dependent
    "DoubleNoTouch": (
        "Pays 1 if spot never touches either barrier throughout the life of the trade."
    ),
    "ForwardStartingOption": (
        "Strike is set to spot at a future start date, giving exposure to "
        "forward volatility rather than spot."
    ),
    "RestrikeOption": (
        "Strike resets to the prevailing spot at a specified reset date, "
        "locking in gains up to that point."
    ),
    "AsianOption": (
        "Payoff based on the average of spot observations, reducing sensitivity "
        "to spot manipulation at expiry."
    ),
    "Cliquet": (
        "Sums period-by-period capped/floored returns, providing inflation-linked "
        "or ratcheting exposure."
    ),
    "RangeAccrual": (
        "Accrues coupon for each observation day that spot remains within "
        "a predefined corridor."
    ),
    # Multi-asset
    "DualDigital": (
        "Pays 1 only if both assets finish on the correct side of their respective "
        "strikes — a correlation product."
    ),
    "TripleDigital": (
        "Pays 1 only if all three assets satisfy their strike conditions — "
        "maximises carry via multi-asset correlation."
    ),
    "WorstOfOption": (
        "Call or put payoff based on the worst-performing asset in the basket; "
        "sells correlation to enhance the strike."
    ),
    "BestOfOption": (
        "Call or put payoff based on the best-performing asset in the basket; "
        "buys correlation at a premium."
    ),
    "Dispersion": (
        "Long individual component options versus a short basket option; "
        "profits when single-stock moves diverge from the basket."
    ),
    # Periodic
    "AccumulatorDecumulator": (
        "Client buys (accumulator) or sells (decumulator) a fixed notional at a "
        "strike on each observation date; leveraged exposure on the unfavorable side."
    ),
    "Autocallable": (
        "Redeems early with a coupon if underlying clears the autocall trigger; "
        "otherwise provides contingent downside protection."
    ),
    "TARF": (
        "Series of forwards that terminate once cumulative gains hit a target "
        "profit; leveraged on unfavourable fixings."
    ),
}

# ---------------------------------------------------------------------------
# Product sections — field groupings for each instrument
# ---------------------------------------------------------------------------

# Form-section accent colours — aliased to the theme palette so the whole
# UI draws from one source of truth. These are semantic accents for grouping
# fields inside a trade builder form, NOT category colours.
_BLUE   = _THEME["blue"]
_GREEN  = _THEME["green"]
_AMBER  = _THEME["amber"]
_RED    = _THEME["red"]
_PURPLE = _THEME["purple"]
_INDIGO = "#6366f1"  # indigo is only used for the PFE-v2 sidebar logo gradient

PRODUCT_SECTIONS = {
    # ── European ─────────────────────────────────────────────────────────────
    "VanillaOption": [
        {
            "label": "Option Terms",
            "color": _BLUE,
            "fields": ["option_type", "strike"],
        },
    ],
    "Digital": [
        {
            "label": "Option Terms",
            "color": _BLUE,
            "fields": ["strike", "option_type"],
        },
    ],
    "ContingentOption": [
        {
            "label": "Trigger Condition",
            "color": _AMBER,
            "help": "The trigger asset acts as an on/off switch for the payoff",
            "fields": ["trigger_asset_idx", "trigger_barrier", "trigger_direction"],
        },
        {
            "label": "Target Payoff",
            "color": _BLUE,
            "help": "Vanilla payoff computed on the target asset if trigger fires",
            "fields": ["target_asset_idx", "target_strike", "target_type"],
        },
    ],
    "SingleBarrier": [
        {
            "label": "Option Terms",
            "color": _BLUE,
            "fields": ["strike", "option_type"],
        },
        {
            "label": "Barrier Condition (at expiry only)",
            "color": _AMBER,
            "help": "Checked at maturity only — distinct from path-dependent KO/KI modifiers",
            "fields": ["barrier", "barrier_direction", "barrier_type"],
        },
    ],
    # ── Path-dependent ────────────────────────────────────────────────────────
    "DoubleNoTouch": [
        {
            "label": "Barrier Corridor",
            "color": _GREEN,
            "help": "Pays if spot stays strictly inside the corridor for the entire life",
            "fields": ["lower", "upper"],
        },
    ],
    "ForwardStartingOption": [
        {
            "label": "Forward Start Terms",
            "color": _GREEN,
            "help": "Strike fixed to spot at start time",
            "fields": ["start_time", "option_type"],
        },
    ],
    "RestrikeOption": [
        {
            "label": "Restrike Terms",
            "color": _GREEN,
            "help": "Strike resets to spot at reset time",
            "fields": ["reset_time", "option_type"],
        },
    ],
    "AsianOption": [
        {
            "label": "Option Terms",
            "color": _GREEN,
            "help": "Price averaging: average vs fixed strike. Strike averaging: terminal vs average strike.",
            "fields": ["strike", "option_type", "average_type"],
        },
        {
            "label": "Averaging Schedule",
            "color": _AMBER,
            "fields": ["schedule"],
        },
    ],
    "Cliquet": [
        {
            "label": "Return Clipping",
            "color": _GREEN,
            "help": "Each period's return is clipped to [floor, cap] before summing",
            "fields": ["local_cap", "local_floor"],
        },
        {
            "label": "Global Protection",
            "color": _RED,
            "help": "Minimum total payoff across all periods",
            "fields": ["global_floor"],
        },
        {
            "label": "Reset Schedule",
            "color": _AMBER,
            "fields": ["schedule"],
        },
    ],
    "RangeAccrual": [
        {
            "label": "Accrual Range",
            "color": _GREEN,
            "help": "Coupon accrues proportional to observations where spot is inside the range",
            "fields": ["lower", "upper"],
        },
        {
            "label": "Coupon",
            "color": _BLUE,
            "fields": ["coupon_rate"],
        },
        {
            "label": "Observation Schedule",
            "color": _AMBER,
            "fields": ["schedule"],
        },
    ],
    # ── Multi-asset ───────────────────────────────────────────────────────────
    "DualDigital": [
        {
            "label": "Barrier Conditions",
            "color": _PURPLE,
            "fields": ["strikes", "option_types"],
        },
    ],
    "TripleDigital": [
        {
            "label": "Barrier Conditions",
            "color": _PURPLE,
            "fields": ["strikes", "option_types"],
        },
    ],
    "WorstOfOption": [
        {
            "label": "Basket Terms",
            "color": _PURPLE,
            "fields": ["option_type", "strikes"],
        },
    ],
    "BestOfOption": [
        {
            "label": "Basket Terms",
            "color": _PURPLE,
            "fields": ["option_type", "strikes"],
        },
    ],
    "Dispersion": [
        {
            "label": "Component Legs",
            "color": _PURPLE,
            "help": "Individual component options per underlying",
            "fields": ["component_types", "strikes", "weights"],
        },
        {
            "label": "Basket Leg",
            "color": _INDIGO,
            "help": "Short basket option offsetting the component legs",
            "fields": ["basket_strike", "basket_type"],
        },
    ],
    # ── Periodic ──────────────────────────────────────────────────────────────
    "AccumulatorDecumulator": [
        {
            "label": "Accumulation / Decumulation Terms",
            "color": _AMBER,
            "help": "Buys or sells at strike each period; leverage multiplies quantity when spot is unfavorable",
            "fields": ["strike", "leverage", "side"],
        },
        {
            "label": "Observation Schedule",
            "color": _AMBER,
            "fields": ["schedule"],
        },
    ],
    "Autocallable": [
        {
            "label": "Autocall Terms",
            "color": _INDIGO,
            "help": "Redeems early if worst-of performance >= trigger",
            "fields": ["autocall_trigger", "coupon_rate"],
        },
        {
            "label": "Downside Protection",
            "color": _RED,
            "help": "Below put strike at maturity, loss = worst_perf - 1.0",
            "fields": ["put_strike"],
        },
        {
            "label": "Observation Schedule",
            "color": _AMBER,
            "fields": ["schedule"],
        },
    ],
    "TARF": [
        {
            "label": "Forward Terms",
            "color": _AMBER,
            "help": "Periodic forward with leverage on unfavorable side",
            "fields": ["strike", "leverage", "side"],
        },
        {
            "label": "Target Redemption",
            "color": _RED,
            "help": "Terminates when cumulative profit reaches target; partial fill on final fixing",
            "fields": ["target"],
        },
        {
            "label": "Fixing Schedule",
            "color": _AMBER,
            "fields": ["schedule"],
        },
    ],
}

# ---------------------------------------------------------------------------
# Modifier group colours
# ---------------------------------------------------------------------------

MODIFIER_GROUP_COLORS = {
    # Primary accent colours come from the theme; badge backgrounds and text
    # are shade-matched pairs kept here since the theme doesn't currently
    # encode them (a future refactor could move them into theme.COLORS).
    "Barrier": {
        "color":      _THEME["mod_barrier"],     # amber
        "badge_bg":   "#fef3c7",
        "badge_text": "#92400e",
    },
    "Payoff shaper": {
        "color":      _THEME["mod_payoff"],      # green (semantic shift from purple)
        "badge_bg":   "#dcfce7",
        "badge_text": "#166534",
    },
    "Structural": {
        "color":      _THEME["mod_structural"],  # purple
        "badge_bg":   "#ede9fe",
        "badge_text": "#5b21b6",
    },
}

# ---------------------------------------------------------------------------
# Modifier sections
# ---------------------------------------------------------------------------

_OBS_FIELDS = ["observation_style", "observation_dates", "window_start", "window_end"]

MODIFIER_SECTIONS = {
    # ── Barrier ───────────────────────────────────────────────────────────────
    "KnockOut": {
        "group":              "Barrier",
        "core_fields":        ["barrier", "direction", "asset_idx"],
        "observation_fields": _OBS_FIELDS,
        "extra_fields":       ["rebate"],
    },
    "KnockIn": {
        "group":              "Barrier",
        "core_fields":        ["barrier", "direction", "asset_idx"],
        "observation_fields": _OBS_FIELDS,
        "extra_fields":       [],
    },
    "RealizedVolKnockOut": {
        "group":              "Barrier",
        "core_fields":        ["vol_barrier", "direction", "asset_idx", "annualization_factor"],
        "observation_fields": _OBS_FIELDS,
        "extra_fields":       [],
    },
    "RealizedVolKnockIn": {
        "group":              "Barrier",
        "core_fields":        ["vol_barrier", "direction", "asset_idx", "annualization_factor"],
        "observation_fields": _OBS_FIELDS,
        "extra_fields":       [],
    },
    # ── Payoff shapers ────────────────────────────────────────────────────────
    "PayoffCap": {
        "group":              "Payoff shaper",
        "core_fields":        ["cap"],
        "observation_fields": [],
        "extra_fields":       [],
    },
    "PayoffFloor": {
        "group":              "Payoff shaper",
        "core_fields":        ["floor"],
        "observation_fields": [],
        "extra_fields":       [],
    },
    "LeverageModifier": {
        "group":              "Payoff shaper",
        "core_fields":        ["threshold", "leverage"],
        "observation_fields": [],
        "extra_fields":       [],
    },
    # ── Structural ────────────────────────────────────────────────────────────
    "ObservationSchedule": {
        "group":              "Structural",
        "core_fields":        ["dates"],
        "observation_fields": [],
        "extra_fields":       [],
    },
    "TargetProfit": {
        "group":              "Structural",
        "core_fields":        ["target", "partial_fill"],
        "observation_fields": [],
        "extra_fields":       [],
    },
}

# ---------------------------------------------------------------------------
# Sparkline support
# ---------------------------------------------------------------------------

# All 18 instrument types except schedule-heavy / path-complex types that
# can't be meaningfully represented by a simple sparkline payoff diagram.
SPARKLINE_SUPPORTED = {
    # European
    "VanillaOption",
    "Digital",
    "ContingentOption",
    "SingleBarrier",
    # Path-dependent (simple enough for a sparkline)
    "DoubleNoTouch",
    "ForwardStartingOption",
    "RestrikeOption",
    # Multi-asset
    "DualDigital",
    "TripleDigital",
    "WorstOfOption",
    "BestOfOption",
    "Dispersion",
    # Periodic
    "AccumulatorDecumulator",
    # Excluded: AsianOption, Cliquet, RangeAccrual, Autocallable, TARF
}

# ---------------------------------------------------------------------------
# Product scenarios
# ---------------------------------------------------------------------------

PRODUCT_SCENARIOS = {
    "VanillaOption": [
        {
            "label": "At-the-money",
            "description": "Spot at strike; maximum time-value region for call or put.",
            "spot_mult": 1.0,
        },
        {
            "label": "Spot +20%",
            "description": "Spot 20% above strike; call deep ITM, put OTM.",
            "spot_mult": 1.2,
        },
        {
            "label": "Spot -15%",
            "description": "Spot 15% below strike; put deep ITM, call OTM.",
            "spot_mult": 0.85,
        },
    ],
    "SingleBarrier": [
        {
            "label": "Spot below barrier (live)",
            "description": "Spot below barrier; option remains active.",
            "spot_mult": 0.95,
        },
        {
            "label": "Spot at barrier",
            "description": "Spot at barrier level; critical transition zone.",
            "spot_mult": 1.0,
        },
        {
            "label": "Spot above barrier (knocked out)",
            "description": "Spot has crossed barrier; knock-out terminates payoff.",
            "spot_mult": 1.1,
        },
    ],
    "AsianOption": [
        {
            "label": "Trending upward",
            "description": "Average accumulates above strike; call accrues value steadily.",
            "spot_mult": 1.1,
        },
        {
            "label": "Mean-reverting",
            "description": "Spot oscillates around strike; averaging dampens extreme outcomes.",
            "spot_mult": 1.0,
        },
        {
            "label": "Trending downward",
            "description": "Average drifts below strike; put gains intrinsic value.",
            "spot_mult": 0.9,
        },
    ],
    "Cliquet": [
        {
            "label": "Sustained bull market",
            "description": "Each period return hits the local cap; payoff accumulates at maximum.",
            "spot_mult": 1.15,
        },
        {
            "label": "Volatile sideways",
            "description": "Returns alternate positive/negative; floor prevents losses, cap limits gains.",
            "spot_mult": 1.0,
        },
        {
            "label": "Bear market",
            "description": "Negative returns capped by floor; global floor protects total payoff.",
            "spot_mult": 0.85,
        },
    ],
    "RangeAccrual": [
        {
            "label": "Spot inside range",
            "description": "Spot anchored in corridor; coupon accrues on most observation dates.",
            "spot_mult": 1.0,
        },
        {
            "label": "Spot near upper boundary",
            "description": "Spot drifts toward upper barrier; accrual days start to drop.",
            "spot_mult": 1.08,
        },
        {
            "label": "Spot outside range",
            "description": "Spot exits the corridor; no coupon accrues while outside.",
            "spot_mult": 1.2,
        },
    ],
    "Autocallable": [
        {
            "label": "Early redemption",
            "description": "Underlying clears autocall trigger at first observation; redeems with coupon.",
            "spot_mult": 1.05,
        },
        {
            "label": "Stays alive, above barrier",
            "description": "Underlying below trigger but above put strike at maturity; par returned.",
            "spot_mult": 0.85,
        },
        {
            "label": "Barrier breached at maturity",
            "description": "Underlying below put strike; investor suffers loss proportional to decline.",
            "spot_mult": 0.6,
        },
    ],
    "TARF": [
        {
            "label": "Target hit early",
            "description": "Favourable fixings accumulate quickly; contract terminates after hitting target.",
            "spot_mult": 1.1,
        },
        {
            "label": "Fixings near strike",
            "description": "Spot hovers near strike; small gains per fixing, full term runs.",
            "spot_mult": 1.0,
        },
        {
            "label": "Adverse fixings",
            "description": "Spot moves against the client; leveraged losses accumulate each period.",
            "spot_mult": 0.85,
        },
    ],
    "AccumulatorDecumulator": [
        {
            "label": "Favorable side",
            "description": "Spot on the favorable side of strike; client transacts at a better-than-market price.",
            "spot_mult": 1.05,
        },
        {
            "label": "Unfavorable side (leveraged)",
            "description": "Spot on the unfavorable side; leveraged obligation forces larger transactions.",
            "spot_mult": 0.9,
        },
        {
            "label": "Sharp adverse move",
            "description": "Spot moves sharply against the client; leveraged exposure creates significant losses.",
            "spot_mult": 0.75,
        },
    ],
    "DoubleNoTouch": [
        {
            "label": "Spot anchored in corridor",
            "description": "Spot stays well within barriers; high probability of receiving the fixed payout.",
            "spot_mult": 1.0,
        },
        {
            "label": "Spot approaching upper barrier",
            "description": "Spot drifts toward upper barrier; payout probability diminishes.",
            "spot_mult": 1.08,
        },
        {
            "label": "Barrier breached",
            "description": "Spot touches one barrier; contract terminates with zero payoff.",
            "spot_mult": 1.2,
        },
    ],
    "WorstOfOption": [
        {
            "label": "All assets rally",
            "description": "Worst performer still above all strikes; call pays, put expires worthless.",
            "spot_mult": 1.15,
        },
        {
            "label": "One asset lags",
            "description": "Worst performer barely at its strike; payoff driven by weakest link.",
            "spot_mult": 1.02,
        },
        {
            "label": "One asset declines",
            "description": "Worst performer below strike; call expires worthless, put gains intrinsic value.",
            "spot_mult": 0.9,
        },
    ],
}
