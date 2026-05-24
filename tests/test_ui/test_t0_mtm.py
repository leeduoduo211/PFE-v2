from ui.utils.t0_mtm import compute_t0_mtm_preview


def _market_state():
    return {
        "asset_names": ["AAPL"],
        "asset_classes": ["EQUITY"],
        "spots": [100.0],
        "vols": [0.20],
        "rates": [0.05],
        "domestic_rate": 0.05,
        "corr_matrix": [[1.0]],
    }


def _vanilla_trade(trade_id, direction):
    return {
        "trade_id": trade_id,
        "direction": direction,
        "instrument_type": "VanillaOption",
        "params": {
            "maturity": 1.0,
            "notional": 100_000.0,
            "assets": ["AAPL"],
            "strike": 100.0,
            "option_type": "call",
        },
        "modifiers": [],
    }


def test_compute_t0_mtm_preview_returns_one_value_per_trade_with_direction():
    config_state = {
        "n_inner": 200,
        "grid_frequency": "monthly",
        "seed": 42,
        "backend": "numpy",
        "antithetic": False,
    }
    portfolio = [
        _vanilla_trade("LONG_CALL", "long"),
        _vanilla_trade("SHORT_CALL", "short"),
    ]

    values = compute_t0_mtm_preview(_market_state(), portfolio, config_state)

    assert len(values) == 2
    assert values[0] > 0.0
    assert values[1] < 0.0
