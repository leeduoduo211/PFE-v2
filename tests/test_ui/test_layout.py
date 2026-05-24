from ui.components import config_panel, trade_builder


def test_sampling_controls_use_even_columns_with_bottom_aligned_second_row():
    assert hasattr(config_panel, "_sampling_control_layout")
    layout = config_panel._sampling_control_layout()

    assert layout["columns"] == [1, 1, 1, 1]
    assert layout["top_row_alignment"] == "top"
    assert layout["bottom_row_alignment"] == "bottom"


def test_portfolio_submit_button_uses_add_trade_alignment():
    assert hasattr(trade_builder, "_portfolio_submit_column_widths")
    widths = trade_builder._portfolio_submit_column_widths()

    assert widths == [0.78, 0.22]
