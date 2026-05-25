"""Session state initialization and management."""

import streamlit as st

from ui.utils.session_keys import SK

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
        "run_counter": 0,
        "run_scenario_name": "",
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


def _unique_run_label(base_label: str, runs: list[dict]) -> str:
    """Return a label that is unique within the current run history."""
    existing = {run.get("label") for run in runs}
    if base_label not in existing:
        return base_label

    suffix = 2
    while f"{base_label} ({suffix})" in existing:
        suffix += 1
    return f"{base_label} ({suffix})"


def add_run(result_summary: dict, label=None) -> dict:
    """Add a PFE run snapshot to history, evicting oldest if at capacity."""
    runs = st.session_state["runs"]
    st.session_state["run_counter"] = st.session_state.get("run_counter", len(runs)) + 1

    default_label = f"Run #{st.session_state['run_counter']}"
    base_label = (label or "").strip() or default_label

    stored_run = dict(result_summary)
    stored_run["label"] = _unique_run_label(base_label, runs)
    runs.append(stored_run)
    if len(runs) > MAX_RUNS:
        runs.pop(0)
    return stored_run


def select_run(label: str) -> bool:
    """Select a stored run as the active result shown in the main body."""
    for run in st.session_state.get("runs", []):
        if run.get("label") == label:
            st.session_state["latest_result"] = run
            return True
    return False


def invalidate_results(clear_runs: bool = True):
    """Clear run outputs after market, portfolio, or config inputs change."""
    st.session_state.pop("latest_result", None)
    if clear_runs and "runs" in st.session_state:
        st.session_state["runs"] = []
        st.session_state["run_counter"] = 0


def request_portfolio_tab():
    """Request switching back to the Portfolio tab after Streamlit reruns."""
    st.session_state[SK.SWITCH_TO_PORTFOLIO] = True


def get_asset_names():
    """Get current asset names from session state."""
    return st.session_state["market"]["asset_names"]
