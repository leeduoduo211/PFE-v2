"""Session state initialization and management."""

import streamlit as st

MAX_RUNS = 5


def init_session_state():
    """Initialize all session state keys with defaults if not present."""
    defaults = {
        "market": {
            "asset_names": [],
            "asset_classes": [],
            "spots": [],
            "vols": [],
            "rates": [],
            "domestic_rate": 0.03,
            "corr_matrix": [],
        },
        "portfolio": [],
        "editing_trade": None,
        "config": {
            "n_outer": 1000,
            "n_inner": 1000,
            "confidence_level": 0.95,
            "grid_frequency": "weekly",
            "margined": False,
            "mpor_days": 10,
            "backend": "numpy",
            "n_workers": 4,
            "seed": 42,
            "antithetic": False,
        },
        "runs": [],
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


def add_run(result_summary: dict):
    """Add a PFE run to history, evicting oldest if at capacity."""
    runs = st.session_state["runs"]
    label = f"Run #{len(runs) + 1}"
    result_summary["label"] = label
    runs.append(result_summary)
    if len(runs) > MAX_RUNS:
        runs.pop(0)


def get_asset_names():
    """Get current asset names from session state."""
    return st.session_state["market"]["asset_names"]
