"""Quick-start presets: canonical market + portfolio combinations.

Used on the Market Data tab so new users can skip the blank-slate problem.
Each preset returns a (market_dict, portfolio_list) pair ready to be written
straight into st.session_state.
"""

from __future__ import annotations

from typing import Callable


def _preset_eq_2asset():
    """2 correlated equities, one vanilla call + one worst-of put."""
    market = {
        "asset_names": ["AAPL", "XYZ"],
        "asset_classes": ["EQUITY", "EQUITY"],
        "spots": [100.0, 50.0],
        "vols": [0.20, 0.30],
        "rates": [0.05, 0.05],
        "domestic_rate": 0.05,
        "corr_matrix": [[1.0, 0.5], [0.5, 1.0]],
    }
    portfolio = [
        {
            "trade_id": "CALL_001",
            "instrument_type": "VanillaOption",
            "direction": "long",
            "params": {
                "maturity": 1.0,
                "notional": 100_000.0,
                "assets": ["AAPL"],
                "strike": 100.0,
                "option_type": "call",
            },
            "modifiers": [],
        },
        {
            "trade_id": "WOP_001",
            "instrument_type": "WorstOfOption",
            "direction": "long",
            "params": {
                "maturity": 1.0,
                "notional": 100_000.0,
                "assets": ["AAPL", "XYZ"],
                "strikes": [100.0, 50.0],
                "option_type": "put",
            },
            "modifiers": [],
        },
    ]
    return market, portfolio


def _preset_fx_pair():
    """EURUSD accumulator with an up-and-out knock-out (classic FX hedging trade)."""
    market = {
        "asset_names": ["EURUSD"],
        "asset_classes": ["FX"],
        "spots": [1.085],
        "vols": [0.08],
        "rates": [0.02],          # foreign (EUR)
        "domestic_rate": 0.04,     # domestic (USD)
        "corr_matrix": [[1.0]],
    }
    schedule = [round(i / 12, 4) for i in range(1, 13)]
    portfolio = [
        {
            "trade_id": "ACC_EURUSD",
            "instrument_type": "AccumulatorDecumulator",
            "direction": "long",
            "params": {
                "maturity": 1.0,
                "notional": 1_000_000.0,
                "assets": ["EURUSD"],
                "strike": 1.10,
                "leverage": 2.0,
                "side": "buy",
                "schedule": schedule,
            },
            "modifiers": [
                {
                    "type": "KnockOut",
                    "params": {
                        "barrier": 1.15,
                        "direction": "up",
                        "observation_style": "continuous",
                    },
                },
            ],
        },
    ]
    return market, portfolio


def _preset_basket_3asset():
    """3-asset basket with capped worst-of put + best-of call + short hedge."""
    market = {
        "asset_names": ["AAPL", "TSLA", "MSFT"],
        "asset_classes": ["EQUITY", "EQUITY", "EQUITY"],
        "spots": [100.0, 80.0, 120.0],
        "vols": [0.25, 0.30, 0.20],
        "rates": [0.05, 0.05, 0.05],
        "domestic_rate": 0.05,
        "corr_matrix": [
            [1.0, 0.6, 0.3],
            [0.6, 1.0, 0.4],
            [0.3, 0.4, 1.0],
        ],
    }
    portfolio = [
        {
            "trade_id": "WOP_BASKET",
            "instrument_type": "WorstOfOption",
            "direction": "long",
            "params": {
                "maturity": 1.0,
                "notional": 500_000.0,
                "assets": ["AAPL", "TSLA", "MSFT"],
                "strikes": [100.0, 80.0, 120.0],
                "option_type": "put",
            },
            "modifiers": [
                {"type": "PayoffCap", "params": {"cap": 0.3}},
            ],
        },
        {
            "trade_id": "BOC_BASKET",
            "instrument_type": "BestOfOption",
            "direction": "long",
            "params": {
                "maturity": 1.0,
                "notional": 200_000.0,
                "assets": ["AAPL", "TSLA", "MSFT"],
                "strikes": [100.0, 80.0, 120.0],
                "option_type": "call",
            },
            "modifiers": [],
        },
        {
            "trade_id": "HEDGE_AAPL",
            "instrument_type": "VanillaOption",
            "direction": "short",
            "params": {
                "maturity": 0.5,
                "notional": 100_000.0,
                "assets": ["AAPL"],
                "strike": 105.0,
                "option_type": "call",
            },
            "modifiers": [],
        },
    ]
    return market, portfolio


PRESETS: dict[str, tuple[str, str, Callable]] = {
    "eq_2asset": (
        "Equity \u2014 2 assets",
        "AAPL + XYZ, vanilla call + worst-of put",
        _preset_eq_2asset,
    ),
    "fx_pair": (
        "FX \u2014 accumulator",
        "EURUSD monthly accumulator with up-and-out barrier, margined",
        _preset_fx_pair,
    ),
    "basket_3asset": (
        "Equity \u2014 3-asset basket",
        "Capped worst-of put + best-of call + short vanilla hedge",
        _preset_basket_3asset,
    ),
}


def load_preset(name: str) -> tuple[dict, list] | None:
    """Look up a preset and return (market, portfolio). None on unknown name."""
    entry = PRESETS.get(name)
    if entry is None:
        return None
    _, _, builder = entry
    return builder()
