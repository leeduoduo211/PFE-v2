"""
Instrument and modifier registry for dynamic UI form generation.

Each registry entry maps a type name to a spec dict:
  {
      "cls":      <class>,
      "label":    <human-readable name>,
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
    VanillaCall,
    VanillaPut,
    Digital,
    DualDigital,
    TripleDigital,
    WorstOfCall,
    WorstOfPut,
    BestOfCall,
    BestOfPut,
    DoubleNoTouch,
    Accumulator,
    ForwardStartingOption,
    RestrikeOption,
    ContingentOption,
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
)

# ---------------------------------------------------------------------------
# Instrument registry
# ---------------------------------------------------------------------------

INSTRUMENT_REGISTRY = {
    "VanillaCall": {
        "cls": VanillaCall,
        "label": "Vanilla Call",
        "n_assets": 1,
        "fields": [
            {
                "name": "strike",
                "label": "Strike",
                "type": "float",
                "default": 100.0,
                "help": "Option strike price",
            },
        ],
    },
    "VanillaPut": {
        "cls": VanillaPut,
        "label": "Vanilla Put",
        "n_assets": 1,
        "fields": [
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
    "DualDigital": {
        "cls": DualDigital,
        "label": "Dual Digital",
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
    "WorstOfCall": {
        "cls": WorstOfCall,
        "label": "Worst-Of Call",
        "n_assets": "2-5",
        "fields": [
            {
                "name": "strikes",
                "label": "Strikes",
                "type": "float_list",
                "default": [100.0, 100.0],
                "help": "Strike for each asset; payoff based on worst performer",
            },
        ],
    },
    "WorstOfPut": {
        "cls": WorstOfPut,
        "label": "Worst-Of Put",
        "n_assets": "2-5",
        "fields": [
            {
                "name": "strikes",
                "label": "Strikes",
                "type": "float_list",
                "default": [100.0, 100.0],
                "help": "Strike for each asset; payoff based on worst performer",
            },
        ],
    },
    "BestOfCall": {
        "cls": BestOfCall,
        "label": "Best-Of Call",
        "n_assets": "2-5",
        "fields": [
            {
                "name": "strikes",
                "label": "Strikes",
                "type": "float_list",
                "default": [100.0, 100.0],
                "help": "Strike for each asset; payoff based on best performer",
            },
        ],
    },
    "BestOfPut": {
        "cls": BestOfPut,
        "label": "Best-Of Put",
        "n_assets": "2-5",
        "fields": [
            {
                "name": "strikes",
                "label": "Strikes",
                "type": "float_list",
                "default": [100.0, 100.0],
                "help": "Strike for each asset; payoff based on best performer",
            },
        ],
    },
    "DoubleNoTouch": {
        "cls": DoubleNoTouch,
        "label": "Double No-Touch",
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
    "Accumulator": {
        "cls": Accumulator,
        "label": "Accumulator",
        "n_assets": 1,
        "fields": [
            {
                "name": "strike",
                "label": "Strike",
                "type": "float",
                "default": 100.0,
                "help": "Accumulation strike price",
            },
            {
                "name": "leverage",
                "label": "Leverage",
                "type": "float",
                "default": 2.0,
                "help": "Multiplier applied when spot is below strike (buy direction)",
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
    "Decumulator": {
        "cls": Accumulator,
        "label": "Decumulator",
        "n_assets": 1,
        "fields": [
            {
                "name": "strike",
                "label": "Strike",
                "type": "float",
                "default": 100.0,
                "help": "Decumulation strike price",
            },
            {
                "name": "leverage",
                "label": "Leverage",
                "type": "float",
                "default": 2.0,
                "help": "Multiplier applied when spot is above strike (sell direction)",
            },
            {
                "name": "side",
                "label": "Side",
                "type": "select",
                "default": "sell",
                "choices": ["buy", "sell"],
                "help": "Side is fixed to sell for a decumulator",
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
    "ForwardStartingOption": {
        "cls": ForwardStartingOption,
        "label": "Forward-Starting Option",
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
    "ContingentOption": {
        "cls": ContingentOption,
        "label": "Contingent Option",
        "n_assets": 2,
        "fields": [
            {
                "name": "trigger_asset_idx",
                "label": "Trigger Asset",
                "type": "asset_select",
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
}

# ---------------------------------------------------------------------------
# Modifier registry
# ---------------------------------------------------------------------------

MODIFIER_REGISTRY = {
    "KnockOut": {
        "cls": KnockOut,
        "label": "Knock-Out Barrier",
        "fields": [
            {
                "name": "barrier",
                "label": "Barrier Level",
                "type": "float",
                "default": 120.0,
                "help": "Barrier level; payoff becomes zero if breached",
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
        ],
    },
    "KnockIn": {
        "cls": KnockIn,
        "label": "Knock-In Barrier",
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
        ],
    },
    "PayoffCap": {
        "cls": PayoffCap,
        "label": "Payoff Cap",
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
    "ObservationSchedule": {
        "cls": ObservationSchedule,
        "label": "Observation Schedule",
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
    "RealizedVolKnockOut": {
        "cls": RealizedVolKnockOut,
        "label": "Realized Vol Knock-Out",
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
        ],
    },
    "RealizedVolKnockIn": {
        "cls": RealizedVolKnockIn,
        "label": "Realized Vol Knock-In",
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
        ],
    },
}
