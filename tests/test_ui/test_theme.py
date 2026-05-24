from ui.theme import _CSS


def _css_block(selector):
    start = _CSS.index(selector)
    open_brace = _CSS.index("{", start)
    close_brace = _CSS.index("}", open_brace)
    return _CSS[open_brace:close_brace]


def test_streamlit_button_tiers_keep_actions_compact_without_shrinking_tabs():
    primary = _css_block("button[kind=\"primary\"]")
    assert "min-height: 32px !important;" in primary
    assert "height: 32px !important;" in primary

    assert "button[kind=\"secondary\"]:not([role=\"tab\"])" in _CSS
    assert ".stButton > button:not([kind=\"primary\"]):not([role=\"tab\"])" in _CSS
    utility = _css_block("button[kind=\"secondary\"]:not([role=\"tab\"])")
    assert "min-height: 30px !important;" in utility
    assert "height: 30px !important;" in utility


def test_sampling_config_labels_use_consistent_height():
    assert "st-key-tab_cfg_sampling_controls" in _CSS
    assert "st-key-tab-cfg-sampling-controls" in _CSS
    sampling_label_block = _css_block(
        "div[class*=\"st-key-tab_cfg_sampling_controls\"] [data-testid=\"stWidgetLabel\"]"
    )

    assert "min-height: 36px !important;" in sampling_label_block
