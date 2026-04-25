"""Instrument registry entries for the Path-dependent category.

Contributes entries to INSTRUMENT_REGISTRY via ui.utils.registries.__init__. See ui.utils.registries/README or
ui/utils/registry.py for the field-spec schema.
"""
from pfev2.instruments import (
    AsianOption,
    Cliquet,
    DoubleNoTouch,
    ForwardStartingOption,
    RangeAccrual,
    RestrikeOption,
)

ENTRIES = {
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
}
