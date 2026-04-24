"""Modifier registry entries. Contributes to MODIFIER_REGISTRY."""
from pfev2.modifiers import (
    KnockIn,
    KnockOut,
    LeverageModifier,
    ObservationSchedule,
    PayoffCap,
    PayoffFloor,
    RealizedVolKnockIn,
    RealizedVolKnockOut,
    TargetProfit,
)

# Shared observation-style fields spread into every barrier-style modifier.
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

ENTRIES = {
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
