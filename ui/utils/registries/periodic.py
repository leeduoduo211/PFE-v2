"""Instrument registry entries for the Periodic category.

Contributes entries to INSTRUMENT_REGISTRY via ui.utils.registries.__init__. See ui.utils.registries/README or
ui/utils/registry.py for the field-spec schema.
"""
from pfev2.instruments import (
    TARF,
    Accumulator,  # registry key is "AccumulatorDecumulator" — the class is still Accumulator
    Autocallable,
)

ENTRIES = {
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
