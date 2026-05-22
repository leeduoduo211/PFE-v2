from ui.utils.formatting import confidence_percentile_label


def test_confidence_percentile_label_uses_configured_level():
    assert confidence_percentile_label(0.99) == "99th percentile"
