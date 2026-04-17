"""
Instrument and modifier registry for dynamic UI form generation.

Each registry entry maps a type name to a spec dict:
  {
      "cls":      <class>,
      "label":    <human-readable name>,
      "category": <str>,  # European / Path-dependent / Multi-asset / Periodic
      "n_assets": <int> | "2-5",  # number of required assets
      "fields":   [<field_spec>, ...],
  }

Each field_spec is a dict:
  {
      "name":     <str>,   # constructor keyword argument name
      "label":    <str>,   # UI display label
      "type":     <str>,   # one of: float, select, float_list, select_list,
                           #         asset_select, asset_select_optional, schedule
      "default":  <any>,   # optional default value
      "choices":  [<str>], # required for select / select_list
      "help":     <str>,   # optional tooltip text
  }
"""

from pfev2.instruments import (
    VanillaOption,
    Digital,
    DualDigital,
    TripleDigital,
    WorstOfOption,
    BestOfOption,
    Dispersion,
    DoubleNoTouch,
    Accumulator,
    ForwardStartingOption,
    RestrikeOption,
    ContingentOption,
    SingleBarrier,
    AsianOption,
    Cliquet,
    RangeAccrual,
    Autocallable,
    TARF,
)
from pfev2.modifiers import (
    KnockOut,
    KnockIn,
    PayoffCap,
    PayoffFloor,
    LeverageModifier,
    ObservationSchedule,
    RealizedVolKnockOut,
    RealizedVolKnockIn,
    TargetProfit,
)

# ---------------------------------------------------------------------------
# Instrument registry
# ---------------------------------------------------------------------------

INSTRUMENT_REGISTRY = {
    # ── Category 1: European ──────────────────────────────────────────────
    "VanillaOption": {
        "cls": VanillaOption,
        "label": "Vanilla Option",
        "category": "European",
        "n_assets": 1,
        "fields": [
            {
                "name": "option_type",
                "label": "Option Type",
                "type": "select",
                "default": "call",
                "choices": ["call", "put"],
                "help": "Call or put option",
            },
            {
                "name": "strike",
                "label": "Strike",
                "type": "float",
                "default": 100.0,
                "help": "Option strike price",
            },
        ],
    },
    "Digital": {
        "cls": Digital,
        "label": "Digital Option",
        "category": "European",
        "n_assets": 1,
        "fields": [
            {
                "name": "strike",
                "label": "Strike",
                "type": "float",
                "default": 100.0,
                "help": "Barrier level for digital payoff",
            },
            {
                "name": "option_type",
                "label": "Option Type",
                "type": "select",
                "default": "call",
                "choices": ["call", "put"],
                "help": "Call pays 1 if S > strike; Put pays 1 if S < strike",
            },
        ],
    },
    "ContingentOption": {
        "cls": ContingentOption,
        "label": "Contingent Option",
        "category": "European",
        "n_assets": 2,
        "fields": [
            {
                "name": "trigger_asset_idx",
                "label": "Trigger Asset",
                "type": "asset_select",
                "default": 0,
                "help": "Asset index used to determine if the option is triggered",
            },
            {
                "name": "trigger_barrier",
                "label": "Trigger Barrier",
                "type": "float",
                "default": 100.0,
                "help": "Barrier level for the trigger asset",
            },
            {
                "name": "trigger_direction",
                "label": "Trigger Direction",
                "type": "select",
                "default": "up",
                "choices": ["up", "down"],
                "help": "Trigger fires when spot moves up/down through the barrier",
            },
            {
                "name": "target_asset_idx",
                "label": "Target Asset",
                "type": "asset_select",
                "default": 1,
                "help": "Asset on which the vanilla payoff is computed",
            },
            {
                "name": "target_strike",
                "label": "Target Strike",
                "type": "float",
                "default": 100.0,
                "help": "Strike of the vanilla payoff on the target asset",
            },
            {
                "name": "target_type",
                "label": "Target Option Type",
                "type": "select",
                "default": "call",
                "choices": ["call", "put"],
                "help": "Call or put payoff on the target asset",
            },
        ],
    },
    "SingleBarrier": {
        "cls": SingleBarrier,
        "label": "Single Barrier (European)",
        "category": "European",
        "n_assets": 1,
        "fields": [
            {
                "name": "strike",
                "label": "Strike",
                "type": "float",
                "default": 100.0,
                "help": "Option strike price",
            },
            {
                "name": "barrier",
                "label": "Barrier Level",
                "type": "float",
                "default": 120.0,
                "help": "Barrier checked at expiry only",
            },
            {
                "name": "option_type",
                "label": "Option Type",
                "type": "select",
                "default": "call",
                "choices": ["call", "put"],
                "help": "Call or put payoff",
            },
            {
                "name": "barrier_direction",
                "label": "Barrier Direction",
                "type": "select",
                "default": "up",
                "choices": ["up", "down"],
                "help": "up = barrier at expiry is S(T) > barrier; down = S(T) < barrier",
            },
            {
                "name": "barrier_type",
                "label": "Barrier Type",
                "type": "select",
                "default": "out",
                "choices": ["in", "out"],
                "help": "in = payoff only if barrier met; out = payoff only if barrier NOT met",
            },
        ],
    },
    # ── Category 2: Path-dependent ────────────────────────────────────────
    "DoubleNoTouch": {
        "cls": DoubleNoTouch,
        "label": "Double No-Touch",
        "category": "Path-dependent",
        "n_assets": 1,
        "fields": [
            {
                "name": "lower",
                "label": "Lower Barrier",
                "type": "float",
                "default": 80.0,
                "help": "Lower barrier level; pay 1 if never touched",
            },
            {
                "name": "upper",
                "label": "Upper Barrier",
                "type": "float",
                "default": 120.0,
                "help": "Upper barrier level; pay 1 if never touched",
            },
        ],
    },
    "ForwardStartingOption": {
        "cls": ForwardStartingOption,
        "label": "Forward-Starting Option",
        "category": "Path-dependent",
        "n_assets": 1,
        "fields": [
            {
                "name": "start_time",
                "label": "Start Time (years)",
                "type": "float",
                "default": 0.5,
                "help": "Time at which the strike is set (must be in (0, maturity))",
            },
            {
                "name": "option_type",
                "label": "Option Type",
                "type": "select",
                "default": "call",
                "choices": ["call", "put"],
                "help": "Call or put on the forward performance",
            },
        ],
    },
    "RestrikeOption": {
        "cls": RestrikeOption,
        "label": "Restrike Option",
        "category": "Path-dependent",
        "n_assets": 1,
        "fields": [
            {
                "name": "reset_time",
                "label": "Reset Time (years)",
                "type": "float",
                "default": 0.5,
                "help": "Time at which the strike resets to spot level",
            },
            {
                "name": "option_type",
                "label": "Option Type",
                "type": "select",
                "default": "call",
                "choices": ["call", "put"],
                "help": "Call or put after the restrike event",
            },
        ],
    },
    "AsianOption": {
        "cls": AsianOption,
        "label": "Asian Option",
        "category": "Path-dependent",
        "n_assets": 1,
        "fields": [
            {
                "name": "strike",
                "label": "Strike",
                "type": "float",
                "default": 100.0,
                "help": "Fixed strike (for price averaging) or initial reference (for strike averaging)",
            },
            {
                "name": "option_type",
                "label": "Option Type",
                "type": "select",
                "default": "call",
                "choices": ["call", "put"],
                "help": "Call or put payoff",
            },
            {
                "name": "average_type",
                "label": "Average Type",
                "type": "select",
                "default": "price",
                "choices": ["price", "strike"],
                "help": "price = average vs fixed strike; strike = terminal vs average strike",
            },
            {
                "name": "schedule",
                "label": "Averaging Schedule",
                "type": "schedule",
                "default": [],
                "help": "Observation dates for computing the average (in years)",
            },
        ],
    },
    "Cliquet": {
        "cls": Cliquet,
        "label": "Cliquet (Ratchet)",
        "category": "Path-dependent",
        "n_assets": 1,
        "fields": [
            {
                "name": "local_cap",
                "label": "Local Cap",
                "type": "float",
                "default": 0.05,
                "help": "Maximum return per period (e.g. 0.05 = 5%)",
            },
            {
                "name": "local_floor",
                "label": "Local Floor",
                "type": "float",
                "default": 0.0,
                "help": "Minimum return per period (e.g. 0.0 = no negative returns)",
            },
            {
                "name": "global_floor",
                "label": "Global Floor",
                "type": "float",
                "default": 0.0,
                "help": "Minimum total payoff across all periods",
            },
            {
                "name": "schedule",
                "label": "Reset Schedule",
                "type": "schedule",
                "default": [],
                "help": "Reset dates for periodic returns (in years)",
            },
        ],
    },
    "RangeAccrual": {
        "cls": RangeAccrual,
        "label": "Range Accrual",
        "category": "Path-dependent",
        "n_assets": 1,
        "fields": [
            {
                "name": "lower",
                "label": "Range Lower Bound",
                "type": "float",
                "default": 90.0,
                "help": "Lower bound of the accrual range",
            },
            {
                "name": "upper",
                "label": "Range Upper Bound",
                "type": "float",
                "default": 110.0,
                "help": "Upper bound of the accrual range",
            },
            {
                "name": "coupon_rate",
                "label": "Coupon Rate",
                "type": "float",
                "default": 0.08,
                "help": "Annualized coupon rate (e.g. 0.08 = 8%)",
            },
            {
                "name": "schedule",
                "label": "Observation Schedule",
                "type": "schedule",
                "default": [],
                "help": "Observation dates for range checking (in years)",
            },
        ],
    },
    # ── Category 3: Multi-asset ───────────────────────────────────────────
    "DualDigital": {
        "cls": DualDigital,
        "label": "Dual Digital",
        "category": "Multi-asset",
        "n_assets": 2,
        "fields": [
            {
                "name": "strikes",
                "label": "Strikes",
                "type": "float_list",
                "default": [100.0, 100.0],
                "help": "Strike for each asset (one per asset)",
            },
            {
                "name": "option_types",
                "label": "Option Types",
                "type": "select_list",
                "default": ["call", "call"],
                "choices": ["call", "put"],
                "help": "Call/put type for each asset",
            },
        ],
    },
    "TripleDigital": {
        "cls": TripleDigital,
        "label": "Triple Digital",
        "category": "Multi-asset",
        "n_assets": 3,
        "fields": [
            {
                "name": "strikes",
                "label": "Strikes",
                "type": "float_list",
                "default": [100.0, 100.0, 100.0],
                "help": "Strike for each asset (one per asset)",
            },
            {
                "name": "option_types",
                "label": "Option Types",
                "type": "select_list",
                "default": ["call", "call", "call"],
                "choices": ["call", "put"],
                "help": "Call/put type for each asset",
            },
        ],
    },
    "WorstOfOption": {
        "cls": WorstOfOption,
        "label": "Worst-Of Option",
        "category": "Multi-asset",
        "n_assets": "2-5",
        "fields": [
            {
                "name": "option_type",
                "label": "Option Type",
                "type": "select",
                "default": "call",
                "choices": ["call", "put"],
                "help": "Call or put payoff on the worst performer",
            },
            {
                "name": "strikes",
                "label": "Strikes",
                "type": "float_list",
                "default": [100.0, 100.0],
                "help": "Strike for each asset; payoff based on worst performer",
            },
        ],
    },
    "BestOfOption": {
        "cls": BestOfOption,
        "label": "Best-Of Option",
        "category": "Multi-asset",
        "n_assets": "2-5",
        "fields": [
            {
                "name": "option_type",
                "label": "Option Type",
                "type": "select",
                "default": "call",
                "choices": ["call", "put"],
                "help": "Call or put payoff on the best performer",
            },
            {
                "name": "strikes",
                "label": "Strikes",
                "type": "float_list",
                "default": [100.0, 100.0],
                "help": "Strike for each asset; payoff based on best performer",
            },
        ],
    },
    "Dispersion": {
        "cls": Dispersion,
        "label": "Dispersion",
        "category": "Multi-asset",
        "n_assets": "2-5",
        "fields": [
            {
                "name": "component_types",
                "label": "Component Types",
                "type": "select_list",
                "default": ["call", "call"],
                "choices": ["call", "put"],
                "help": "Call or put per component",
            },
            {
                "name": "strikes",
                "label": "Component Strikes",
                "type": "float_list",
                "default": [100.0, 100.0],
                "help": "Strike price per component",
            },
            {
                "name": "weights",
                "label": "Basket Weights",
                "type": "float_list",
                "default": [0.5, 0.5],
                "help": "Weight per component (must sum to 1)",
            },
            {
                "name": "basket_strike",
                "label": "Basket Strike",
                "type": "float",
                "default": 100.0,
                "help": "Strike for the basket leg",
            },
            {
                "name": "basket_type",
                "label": "Basket Type",
                "type": "select",
                "default": "call",
                "choices": ["call", "put"],
                "help": "Call or put for basket leg",
            },
        ],
    },
    # ── Category 4: Periodic ──────────────────────────────────────────────
    "AccumulatorDecumulator": {
        "cls": Accumulator,
        "label": "Accumulator / Decumulator",
        "category": "Periodic",
        "n_assets": 1,
        "fields": [
            {
                "name": "strike",
                "label": "Strike",
                "type": "float",
                "default": 100.0,
                "help": "Accumulation/decumulation strike price",
            },
            {
                "name": "leverage",
                "label": "Leverage",
                "type": "float",
                "default": 2.0,
                "help": "Multiplier applied when spot is on the unfavorable side",
            },
            {
                "name": "side",
                "label": "Side",
                "type": "select",
                "default": "buy",
                "choices": ["buy", "sell"],
                "help": "buy = accumulate when S >= strike; sell = decumulate",
            },
            {
                "name": "schedule",
                "label": "Observation Schedule",
                "type": "schedule",
                "default": [],
                "help": "List of observation times (in years)",
            },
        ],
    },
    "Autocallable": {
        "cls": Autocallable,
        "label": "Autocallable",
        "category": "Periodic",
        "n_assets": "1-5",
        "fields": [
            {
                "name": "autocall_trigger",
                "label": "Autocall Trigger",
                "type": "float",
                "default": 1.0,
                "help": "Trigger level as fraction of initial (e.g. 1.0 = 100%)",
            },
            {
                "name": "coupon_rate",
                "label": "Coupon Rate",
                "type": "float",
                "default": 0.05,
                "help": "Per-period coupon accrued on early redemption",
            },
            {
                "name": "put_strike",
                "label": "Put Strike",
                "type": "float",
                "default": 0.7,
                "help": "Downside barrier at maturity as fraction of initial (e.g. 0.7 = 70%)",
            },
            {
                "name": "schedule",
                "label": "Observation Schedule",
                "type": "schedule",
                "default": [],
                "help": "Autocall observation dates (in years)",
            },
        ],
    },
    "TARF": {
        "cls": TARF,
        "label": "TARF",
        "category": "Periodic",
        "n_assets": 1,
        "fields": [
            {
                "name": "strike",
                "label": "Strike",
                "type": "float",
                "default": 100.0,
                "help": "Forward strike price",
            },
            {
                "name": "target",
                "label": "Target",
                "type": "float",
                "default": 10.0,
                "help": "Cumulative profit cap; terminates on breach",
            },
            {
                "name": "leverage",
                "label": "Leverage",
                "type": "float",
                "default": 2.0,
                "help": "Multiplier for unfavorable side fixings",
            },
            {
                "name": "side",
                "label": "Side",
                "type": "select",
                "default": "buy",
                "choices": ["buy", "sell"],
                "help": "buy = client buys at strike; sell = client sells at strike",
            },
            {
                "name": "schedule",
                "label": "Observation Schedule",
                "type": "schedule",
                "default": [],
                "help": "Fixing dates (in years)",
            },
        ],
    },
}

# ---------------------------------------------------------------------------
# Modifier registry
# ---------------------------------------------------------------------------

# Shared observation style fields used by all barrier modifiers
_OBSERVATION_STYLE_FIELDS = [
    {
        "name": "observation_style",
        "label": "Observation Style",
        "type": "select",
        "default": "continuous",
        "choices": ["continuous", "discrete", "window"],
        "help": "continuous = every step; discrete = specific dates only; window = continuous within time window",
    },
    {
        "name": "observation_dates",
        "label": "Observation Dates (discrete)",
        "type": "schedule",
        "default": [],
        "help": "Required if style=discrete; dates to check barrier (in years)",
    },
    {
        "name": "window_start",
        "label": "Window Start (years)",
        "type": "float",
        "default": 0.0,
        "help": "Required if style=window; start of monitoring window",
    },
    {
        "name": "window_end",
        "label": "Window End (years)",
        "type": "float",
        "default": 1.0,
        "help": "Required if style=window; end of monitoring window",
    },
]

MODIFIER_REGISTRY = {
    # ── Group A: Barrier modifiers ────────────────────────────────────────
    "KnockOut": {
        "cls": KnockOut,
        "label": "Knock-Out Barrier",
        "group": "Barrier",
        "fields": [
            {
                "name": "barrier",
                "label": "Barrier Level",
                "type": "float",
                "default": 120.0,
                "help": "Barrier level; payoff becomes zero (or rebate) if breached",
            },
            {
                "name": "direction",
                "label": "Direction",
                "type": "select",
                "default": "up",
                "choices": ["up", "down"],
                "help": "up = knocked out if spot ever rises above barrier",
            },
            {
                "name": "asset_idx",
                "label": "Monitor Asset",
                "type": "asset_select_optional",
                "default": None,
                "help": "Asset to monitor for barrier breach (None = first asset)",
            },
            *_OBSERVATION_STYLE_FIELDS,
            {
                "name": "rebate",
                "label": "Rebate",
                "type": "float",
                "default": 0.0,
                "help": "Fixed payment when knock-out is triggered (0 = no rebate)",
            },
        ],
    },
    "KnockIn": {
        "cls": KnockIn,
        "label": "Knock-In Barrier",
        "group": "Barrier",
        "fields": [
            {
                "name": "barrier",
                "label": "Barrier Level",
                "type": "float",
                "default": 80.0,
                "help": "Barrier level; payoff activates only if breached",
            },
            {
                "name": "direction",
                "label": "Direction",
                "type": "select",
                "default": "down",
                "choices": ["up", "down"],
                "help": "down = knocked in if spot ever falls below barrier",
            },
            {
                "name": "asset_idx",
                "label": "Monitor Asset",
                "type": "asset_select_optional",
                "default": None,
                "help": "Asset to monitor for barrier breach (None = first asset)",
            },
            *_OBSERVATION_STYLE_FIELDS,
        ],
    },
    "RealizedVolKnockOut": {
        "cls": RealizedVolKnockOut,
        "label": "Realized Vol Knock-Out",
        "group": "Barrier",
        "fields": [
            {
                "name": "vol_barrier",
                "label": "Vol Barrier",
                "type": "float",
                "default": 0.30,
                "help": "Annualized realized vol threshold (e.g. 0.30 = 30%). Payoff is zeroed when breached.",
            },
            {
                "name": "direction",
                "label": "Direction",
                "type": "select",
                "default": "above",
                "choices": ["above", "below"],
                "help": "above = knocked out if realized vol exceeds barrier; below = knocked out if below barrier",
            },
            {
                "name": "asset_idx",
                "label": "Monitor Asset",
                "type": "asset_select_optional",
                "default": None,
                "help": "Asset whose price path is used to compute realized vol (None = first asset)",
            },
            {
                "name": "annualization_factor",
                "label": "Annualization Factor",
                "type": "float",
                "default": 52.0,
                "help": "Steps per year in the inner MC grid: 252 (daily), 52 (weekly), 12 (monthly)",
            },
            *_OBSERVATION_STYLE_FIELDS,
        ],
    },
    "RealizedVolKnockIn": {
        "cls": RealizedVolKnockIn,
        "label": "Realized Vol Knock-In",
        "group": "Barrier",
        "fields": [
            {
                "name": "vol_barrier",
                "label": "Vol Barrier",
                "type": "float",
                "default": 0.30,
                "help": "Annualized realized vol threshold (e.g. 0.30 = 30%). Payoff activates when breached.",
            },
            {
                "name": "direction",
                "label": "Direction",
                "type": "select",
                "default": "above",
                "choices": ["above", "below"],
                "help": "above = activated if realized vol exceeds barrier; below = activated if below barrier",
            },
            {
                "name": "asset_idx",
                "label": "Monitor Asset",
                "type": "asset_select_optional",
                "default": None,
                "help": "Asset whose price path is used to compute realized vol (None = first asset)",
            },
            {
                "name": "annualization_factor",
                "label": "Annualization Factor",
                "type": "float",
                "default": 52.0,
                "help": "Steps per year in the inner MC grid: 252 (daily), 52 (weekly), 12 (monthly)",
            },
            *_OBSERVATION_STYLE_FIELDS,
        ],
    },
    # ── Group B: Payoff shapers ───────────────────────────────────────────
    "PayoffCap": {
        "cls": PayoffCap,
        "label": "Payoff Cap",
        "group": "Payoff shaper",
        "fields": [
            {
                "name": "cap",
                "label": "Cap Level",
                "type": "float",
                "default": 50.0,
                "help": "Maximum payoff; truncates upside",
            },
        ],
    },
    "PayoffFloor": {
        "cls": PayoffFloor,
        "label": "Payoff Floor",
        "group": "Payoff shaper",
        "fields": [
            {
                "name": "floor",
                "label": "Floor Level",
                "type": "float",
                "default": 0.0,
                "help": "Minimum payoff; provides downside protection",
            },
        ],
    },
    "LeverageModifier": {
        "cls": LeverageModifier,
        "label": "Leverage Modifier",
        "group": "Payoff shaper",
        "fields": [
            {
                "name": "threshold",
                "label": "Threshold",
                "type": "float",
                "default": 0.0,
                "help": "Payoff must exceed this threshold for leverage to apply",
            },
            {
                "name": "leverage",
                "label": "Leverage Factor",
                "type": "float",
                "default": 2.0,
                "help": "Multiplier applied to payoff when above threshold",
            },
        ],
    },
    # ── Group C: Structural modifiers ─────────────────────────────────────
    "ObservationSchedule": {
        "cls": ObservationSchedule,
        "label": "Observation Schedule",
        "group": "Structural",
        "fields": [
            {
                "name": "dates",
                "label": "Observation Dates",
                "type": "schedule",
                "default": [],
                "help": "List of observation times (in years) for path-dependent payoff",
            },
        ],
    },
    "TargetProfit": {
        "cls": TargetProfit,
        "label": "Target Profit",
        "group": "Structural",
        "fields": [
            {
                "name": "target",
                "label": "Target",
                "type": "float",
                "default": 10.0,
                "help": "Cumulative payoff cap; terminates when reached",
            },
            {
                "name": "partial_fill",
                "label": "Partial Fill",
                "type": "select",
                "default": "true",
                "choices": ["true", "false"],
                "help": "true = pro-rate last fixing to exact target; false = allow overshoot",
            },
        ],
    },
}
