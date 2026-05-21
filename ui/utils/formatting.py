"""Small UI formatting helpers shared across result views."""


def confidence_percentile_label(confidence_level: float) -> str:
    """Return a display label such as ``95th percentile``."""
    percent = float(confidence_level) * 100.0
    if abs(percent - round(percent)) < 1e-9:
        text = str(int(round(percent)))
    else:
        text = f"{percent:.1f}".rstrip("0").rstrip(".")
    return f"{text}th percentile"
