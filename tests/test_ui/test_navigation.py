from ui.utils.navigation import tab_switch_script


def test_tab_switch_script_targets_requested_tab_with_retry():
    script = tab_switch_script(tab_index=1, minimum_tabs=2)

    assert "tabs[1].click()" in script
    assert "tabs.length >= 2" in script
    assert "setInterval" in script
    assert "clearInterval" in script
