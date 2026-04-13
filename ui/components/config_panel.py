# ui/components/config_panel.py
"""PFE configuration panel."""

import streamlit as st


def render_config_panel(key_prefix: str = "cfg"):
    """Render PFEConfig controls. Reads/writes st.session_state['config']."""
    config = st.session_state["config"]

    col1, col2, col3, col4 = st.columns(4)
    config["n_outer"] = col1.number_input(
        "Outer Paths", value=config["n_outer"],
        min_value=100, max_value=50000, step=500,
        key=f"{key_prefix}_n_outer",
        help="Number of outer Monte Carlo scenarios",
    )
    config["n_inner"] = col2.number_input(
        "Inner Paths", value=config["n_inner"],
        min_value=100, max_value=20000, step=500,
        key=f"{key_prefix}_n_inner",
        help="Number of inner Monte Carlo paths per node",
    )
    config["confidence_level"] = col3.number_input(
        "Confidence", value=config["confidence_level"],
        min_value=0.5, max_value=0.999, step=0.01, format="%.3f",
        key=f"{key_prefix}_conf",
    )
    freq_options = ["daily", "weekly", "monthly"]
    config["grid_frequency"] = col4.selectbox(
        "Grid Freq", freq_options,
        index=freq_options.index(config["grid_frequency"]),
        key=f"{key_prefix}_freq",
    )

    col1, col2, col3, col4 = st.columns(4)
    config["seed"] = col1.number_input(
        "Seed", value=config["seed"],
        min_value=0, max_value=999999, step=1,
        key=f"{key_prefix}_seed",
    )
    import os
    config["n_workers"] = col2.number_input(
        "Threads", value=config.get("n_workers", 1),
        min_value=1, max_value=os.cpu_count() or 8, step=1,
        key=f"{key_prefix}_n_workers",
        help="Parallel threads for inner MC pricing (1 = sequential)",
    )
    config["antithetic"] = col3.checkbox(
        "Antithetic", value=config.get("antithetic", False),
        key=f"{key_prefix}_antithetic",
        help="Antithetic variates: pair Z and -Z for variance reduction",
    )
    config["margined"] = col4.checkbox(
        "Margined", value=config["margined"],
        key=f"{key_prefix}_margined",
    )
    if config["margined"]:
        config["mpor_days"] = st.number_input(
            "MPoR Days", value=config["mpor_days"],
            min_value=1, max_value=30, step=1,
            key=f"{key_prefix}_mpor",
        )
