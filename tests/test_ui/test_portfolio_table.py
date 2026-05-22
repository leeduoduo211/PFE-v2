from ui.components.portfolio_table import (
    _format_notional,
    _next_clone_trade_id,
    _portfolio_summary_rows,
    _resolve_selected_trade_id,
)


def _trade(
    trade_id,
    *,
    direction="long",
    notional=1_000_000.0,
    maturity=1.0,
    instrument_type="vanilla",
):
    return {
        "trade_id": trade_id,
        "instrument_type": instrument_type,
        "direction": direction,
        "params": {
            "maturity": maturity,
            "notional": notional,
            "assets": ["AAPL"],
        },
        "modifiers": [],
    }


def test_format_notional_compacts_large_values():
    assert _format_notional(1_250_000, compact=True) == "1.25M"
    assert _format_notional(15_500, compact=True) == "16K"
    assert _format_notional(875, compact=True) == "875"


def test_format_notional_handles_signed_values():
    assert _format_notional(25_000, compact=True, signed=True) == "+25K"
    assert _format_notional(-2_500_000, compact=True, signed=True) == "-2.50M"
    assert _format_notional(0, compact=True, signed=True) == "0"


def test_portfolio_summary_rows_use_directional_net_and_latest_t0_mtm():
    portfolio = [
        _trade("TRD_001", direction="long", notional=1_000_000, maturity=1.25),
        _trade("TRD_002", direction="short", notional=2_000_000, maturity=3.5),
    ]
    rows = dict(_portfolio_summary_rows(portfolio, {"per_trade_t0_mtm": [25_000.0, -1_000.0]}))

    assert rows["Trades"] == "2"
    assert rows["Gross notional"] == "3.00M"
    assert rows["Net notional"] == "-1.00M"
    assert rows["Max maturity"] == "3.50y"
    assert rows["t=0 MtM"] == "+24K"


def test_portfolio_summary_rows_marks_stale_results_when_trade_count_mismatches():
    portfolio = [
        _trade("TRD_001"),
        _trade("TRD_002"),
    ]
    rows = dict(_portfolio_summary_rows(portfolio, {"per_trade_t0_mtm": [100.0]}))

    assert rows["t=0 MtM"] == "Run stale"


def test_portfolio_summary_rows_marks_missing_results():
    rows = dict(_portfolio_summary_rows([_trade("TRD_001")], None))

    assert rows["t=0 MtM"] == "No run"


def test_resolve_selected_trade_id_keeps_existing_selection():
    portfolio = [_trade("TRD_001"), _trade("TRD_002")]

    assert _resolve_selected_trade_id(portfolio, "TRD_002") == "TRD_002"


def test_resolve_selected_trade_id_falls_back_to_first_trade():
    portfolio = [_trade("TRD_001"), _trade("TRD_002")]

    assert _resolve_selected_trade_id(portfolio, "TRD_999") == "TRD_001"


def test_resolve_selected_trade_id_returns_none_for_empty_portfolio():
    assert _resolve_selected_trade_id([], "TRD_001") is None


def test_next_clone_trade_id_uses_available_suffix():
    portfolio = [
        _trade("TRD_001"),
        _trade("TRD_001_copy"),
        _trade("TRD_001_copy_2"),
    ]

    assert _next_clone_trade_id(portfolio, "TRD_001") == "TRD_001_copy_3"
