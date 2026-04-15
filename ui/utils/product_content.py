"""
Presentation-layer data for all 21 instruments and 9 modifiers.

Pure data — no rendering logic. Consumed by the Streamlit trade builder
and related UI components.
"""

# ---------------------------------------------------------------------------
# Category colors
# ---------------------------------------------------------------------------

CATEGORY_COLORS = {
    "European":       "#3b82f6",
    "Path-dependent": "#22c55e",
    "Multi-asset":    "#8b5cf6",
    "Periodic":       "#f59e0b",
}

# ---------------------------------------------------------------------------
# Product descriptions — one-liner per instrument
# ---------------------------------------------------------------------------

PRODUCT_DESCRIPTIONS = {
    # European
    "VanillaCall": (
        "Pays max(S − K, 0) at expiry; the standard upside participation contract."
    ),
    "VanillaPut": (
        "Pays max(K − S, 0) at expiry; classic downside protection instrument."
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
    "WorstOfCall": (
        "Call payoff based on the worst-performing asset in the basket; "
        "sells correlation to enhance the strike."
    ),
    "WorstOfPut": (
        "Put payoff based on the worst-performing asset in the basket; "
        "common downside protection structure."
    ),
    "BestOfCall": (
        "Call payoff based on the best-performing asset in the basket; "
        "buys correlation at a premium."
    ),
    "BestOfPut": (
        "Put payoff based on the best-performing asset in the basket; "
        "targeted protection on the strongest mover."
    ),
    # Periodic
    "Accumulator": (
        "Client buys a fixed notional at a discounted strike on each observation "
        "date; leveraged exposure below strike."
    ),
    "Decumulator": (
        "Client sells a fixed notional at a premium strike on each observation "
        "date; leveraged obligation above strike."
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

# Colour shorthand
_BLUE   = "#3b82f6"
_GREEN  = "#22c55e"
_AMBER  = "#f59e0b"
_RED    = "#ef4444"
_PURPLE = "#8b5cf6"
_INDIGO = "#6366f1"

PRODUCT_SECTIONS = {
    # ── European ─────────────────────────────────────────────────────────────
    "VanillaCall": [
        {
            "label": "Option Terms",
            "color": _BLUE,
            "fields": ["strike"],
        },
    ],
    "VanillaPut": [
        {
            "label": "Option Terms",
            "color": _BLUE,
            "fields": ["strike"],
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
            "fields": ["trigger_asset_idx", "trigger_barrier", "trigger_direction"],
        },
        {
            "label": "Target Payoff",
            "color": _BLUE,
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
            "fields": ["barrier", "barrier_direction", "barrier_type"],
        },
    ],
    # ── Path-dependent ────────────────────────────────────────────────────────
    "DoubleNoTouch": [
        {
            "label": "Barrier Corridor",
            "color": _GREEN,
            "fields": ["lower", "upper"],
        },
    ],
    "ForwardStartingOption": [
        {
            "label": "Forward Start Terms",
            "color": _GREEN,
            "fields": ["start_time", "option_type"],
        },
    ],
    "RestrikeOption": [
        {
            "label": "Restrike Terms",
            "color": _GREEN,
            "fields": ["reset_time", "option_type"],
        },
    ],
    "AsianOption": [
        {
            "label": "Option Terms",
            "color": _GREEN,
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
            "fields": ["local_cap", "local_floor"],
        },
        {
            "label": "Global Protection",
            "color": _RED,
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
    "WorstOfCall": [
        {
            "label": "Basket Terms",
            "color": _PURPLE,
            "fields": ["strikes"],
        },
    ],
    "WorstOfPut": [
        {
            "label": "Basket Terms",
            "color": _PURPLE,
            "fields": ["strikes"],
        },
    ],
    "BestOfCall": [
        {
            "label": "Basket Terms",
            "color": _PURPLE,
            "fields": ["strikes"],
        },
    ],
    "BestOfPut": [
        {
            "label": "Basket Terms",
            "color": _PURPLE,
            "fields": ["strikes"],
        },
    ],
    # ── Periodic ──────────────────────────────────────────────────────────────
    "Accumulator": [
        {
            "label": "Accumulation Terms",
            "color": _AMBER,
            "fields": ["strike", "leverage", "side"],
        },
        {
            "label": "Observation Schedule",
            "color": _AMBER,
            "fields": ["schedule"],
        },
    ],
    "Decumulator": [
        {
            "label": "Decumulation Terms",
            "color": _AMBER,
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
            "fields": ["autocall_trigger", "coupon_rate"],
        },
        {
            "label": "Downside Protection",
            "color": _RED,
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
            "fields": ["strike", "leverage", "side"],
        },
        {
            "label": "Target Redemption",
            "color": _RED,
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
    "Barrier": {
        "color":      "#f59e0b",
        "badge_bg":   "#fef3c7",
        "badge_text": "#92400e",
    },
    "Payoff shaper": {
        "color":      "#8b5cf6",
        "badge_bg":   "#ede9fe",
        "badge_text": "#6d28d9",
    },
    "Structural": {
        "color":      "#3b82f6",
        "badge_bg":   "#dbeafe",
        "badge_text": "#1e40af",
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

# All 21 instrument types except schedule-heavy / path-complex types that
# can't be meaningfully represented by a simple sparkline payoff diagram.
SPARKLINE_SUPPORTED = {
    # European
    "VanillaCall",
    "VanillaPut",
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
    "WorstOfCall",
    "WorstOfPut",
    "BestOfCall",
    "BestOfPut",
    # Periodic
    "Accumulator",
    "Decumulator",
    # Excluded: AsianOption, Cliquet, RangeAccrual, Autocallable, TARF
}

# ---------------------------------------------------------------------------
# Product scenarios
# ---------------------------------------------------------------------------

PRODUCT_SCENARIOS = {
    "VanillaCall": [
        {
            "label": "At-the-money",
            "description": "Spot at strike; maximum time-value region.",
            "spot_mult": 1.0,
        },
        {
            "label": "In-the-money (+20%)",
            "description": "Spot 20% above strike; call is deep in the money.",
            "spot_mult": 1.2,
        },
        {
            "label": "Out-of-the-money (−15%)",
            "description": "Spot 15% below strike; call expires worthless if unchanged.",
            "spot_mult": 0.85,
        },
    ],
    "VanillaPut": [
        {
            "label": "At-the-money",
            "description": "Spot at strike; maximum optionality for downside protection.",
            "spot_mult": 1.0,
        },
        {
            "label": "Deep in-the-money (−25%)",
            "description": "Spot 25% below strike; put has high intrinsic value.",
            "spot_mult": 0.75,
        },
        {
            "label": "Out-of-the-money (+15%)",
            "description": "Spot 15% above strike; put expires worthless if unchanged.",
            "spot_mult": 1.15,
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
    "Accumulator": [
        {
            "label": "Spot above strike (no accumulation)",
            "description": "Spot above strike; client buys at strike — below-market price.",
            "spot_mult": 1.05,
        },
        {
            "label": "Spot below strike (leveraged)",
            "description": "Spot below strike; leveraged obligation forces client to buy above market.",
            "spot_mult": 0.9,
        },
        {
            "label": "Sharp sell-off",
            "description": "Spot falls sharply; leveraged accumulation creates significant losses.",
            "spot_mult": 0.75,
        },
    ],
    "Decumulator": [
        {
            "label": "Spot below strike (no decumulation)",
            "description": "Spot below strike; client sells at premium — above-market price.",
            "spot_mult": 0.95,
        },
        {
            "label": "Spot above strike (leveraged)",
            "description": "Spot above strike; leveraged obligation forces client to sell below market.",
            "spot_mult": 1.1,
        },
        {
            "label": "Sharp rally",
            "description": "Spot rallies sharply; leveraged decumulation generates significant losses.",
            "spot_mult": 1.25,
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
    "WorstOfCall": [
        {
            "label": "All assets rally",
            "description": "Worst performer still above all strikes; basket call pays on every asset.",
            "spot_mult": 1.15,
        },
        {
            "label": "One asset lags",
            "description": "Worst performer barely above its strike; payoff driven by weakest link.",
            "spot_mult": 1.02,
        },
        {
            "label": "One asset declines",
            "description": "Worst performer below strike; entire basket call expires worthless.",
            "spot_mult": 0.9,
        },
    ],
    "WorstOfPut": [
        {
            "label": "All assets decline",
            "description": "Worst performer well below its strike; worst-of put pays maximum intrinsic value.",
            "spot_mult": 0.8,
        },
        {
            "label": "Mixed performance",
            "description": "One asset falls while others rise; payoff determined by the worst mover.",
            "spot_mult": 0.95,
        },
        {
            "label": "All assets above strike",
            "description": "No asset finishes below its strike; worst-of put expires worthless.",
            "spot_mult": 1.1,
        },
    ],
}
