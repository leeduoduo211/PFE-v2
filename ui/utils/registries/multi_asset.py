"""Instrument registry entries for the Multi-asset category.

Contributes entries to INSTRUMENT_REGISTRY via ui.utils.registries.__init__. See ui.utils.registries/README or
ui/utils/registry.py for the field-spec schema.
"""
from pfev2.instruments import (
    BestOfOption,
    Dispersion,
    DualDigital,
    TripleDigital,
    WorstOfOption,
)

ENTRIES = {
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
}
