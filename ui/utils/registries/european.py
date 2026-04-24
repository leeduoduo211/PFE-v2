"""Instrument registry entries for the European category.

Contributes entries to INSTRUMENT_REGISTRY via ui.utils.registries.__init__. See ui.utils.registries/README or
ui/utils/registry.py for the field-spec schema.
"""
from pfev2.instruments import (
    ContingentOption,
    Digital,
    SingleBarrier,
    VanillaOption,
)

ENTRIES = {
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
}
