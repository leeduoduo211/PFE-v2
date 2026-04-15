import pytest
from unittest.mock import patch, MagicMock
from ui.utils.registry import INSTRUMENT_REGISTRY


def _make_trade_spec(inst_type):
    """Build a minimal trade spec for testing."""
    spec = INSTRUMENT_REGISTRY[inst_type]
    params = {"maturity": 1.0, "notional": 1_000_000, "assets": ["AAPL"]}
    for field in spec["fields"]:
        if field.get("default") is not None:
            params[field["name"]] = field["default"]
        elif field["type"] == "schedule":
            params[field["name"]] = [0.25, 0.5, 0.75, 1.0]
        elif field["type"] == "float":
            params[field["name"]] = 100.0
        elif field["type"] == "select":
            params[field["name"]] = field.get("choices", ["call"])[0]
        elif field["type"] == "float_list":
            params[field["name"]] = [100.0, 100.0]
        elif field["type"] == "select_list":
            params[field["name"]] = [field.get("choices", ["call"])[0]] * 2
        elif field["type"] in ("asset_select", "asset_select_optional"):
            params[field["name"]] = 0
    n_assets = spec.get("n_assets", 1)
    if isinstance(n_assets, str):
        n_assets = int(n_assets.split("-")[0])
    if n_assets > 1:
        params["assets"] = [f"ASSET_{i}" for i in range(n_assets)]
    return {
        "trade_id": f"TEST_{inst_type}",
        "instrument_type": inst_type,
        "direction": "long",
        "params": params,
        "modifiers": [],
    }


@pytest.fixture
def mock_streamlit():
    with patch("ui.components.term_sheet.st") as mock_st, \
         patch("ui.components.trade_economics.st") as mock_econ_st:
        mock_st.markdown = MagicMock()
        mock_st.caption = MagicMock()
        mock_st.plotly_chart = MagicMock()
        mock_econ_st.markdown = MagicMock()
        mock_econ_st.caption = MagicMock()
        yield mock_st


class TestTermSheetRenderer:
    @pytest.mark.parametrize("inst_type", list(INSTRUMENT_REGISTRY.keys()))
    def test_render_does_not_raise(self, mock_streamlit, inst_type):
        from ui.components.term_sheet import render_term_sheet
        trade = _make_trade_spec(inst_type)
        asset_names = trade["params"]["assets"]
        market_spots = [100.0] * len(asset_names)
        render_term_sheet(trade, asset_names, market_spots)
        assert mock_streamlit.markdown.call_count > 0

    def test_render_with_modifier(self, mock_streamlit):
        from ui.components.term_sheet import render_term_sheet
        trade = _make_trade_spec("VanillaOption")
        trade["modifiers"] = [
            {"type": "KnockOut", "params": {"barrier": 120.0, "direction": "up",
                                            "asset_idx": None, "observation_style": "continuous",
                                            "observation_dates": [], "window_start": 0.0,
                                            "window_end": 1.0, "rebate": 0.0}},
        ]
        render_term_sheet(trade, ["AAPL"], [100.0])
        assert mock_streamlit.markdown.call_count > 0
