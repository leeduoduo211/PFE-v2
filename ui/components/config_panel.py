# ui/components/config_panel.py
"""PFE configuration panel."""

import streamlit as st


_GRID_STEPS_PER_YEAR = {"daily": 252, "weekly": 52, "monthly": 12}


def _estimate_runtime(n_outer: int, n_inner: int, grid_frequency: str,
                      n_trades: int, has_path_dependent: bool) -> float:
    """Back-of-envelope runtime estimate in seconds.

    Empirically calibrated on the numpy backend: European payoffs are
    vectorised across outer paths so effective throughput is ~60M "calls"
    per second; path-dependent loops process per-path and run ~500K/s.
    The estimate errs low on mixed-portfolio runs because the slowest trade
    dominates wall time.
    """
    if n_trades == 0:
        return 0.0
    T = _GRID_STEPS_PER_YEAR.get(grid_frequency, 52)
    calls = n_outer * T * n_inner * max(n_trades, 1)
    throughput = 500_000 if has_path_dependent else 60_000_000
    return 0.3 + calls / throughput


def _fmt_seconds(s: float) -> str:
    if s < 1:
        return "<1s"
    if s < 60:
        return f"~{int(round(s))}s"
    if s < 3600:
        m, sec = divmod(int(round(s)), 60)
        return f"~{m}m {sec}s"
    h, rem = divmod(int(round(s)), 3600)
    m = rem // 60
    return f"~{h}h {m}m"


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

    # Runtime estimate — shown as soon as there's a non-empty portfolio.
    portfolio = st.session_state.get("portfolio", [])
    if portfolio:
        has_pd = any(
            t.get("instrument_type") in {
                "DoubleNoTouch", "ForwardStartingOption", "RestrikeOption",
                "AsianOption", "Cliquet", "RangeAccrual",
                "AccumulatorDecumulator", "Autocallable", "TARF",
            } or t.get("modifiers")
            for t in portfolio
        )
        est = _estimate_runtime(
            config["n_outer"], config["n_inner"],
            config["grid_frequency"], len(portfolio), has_pd,
        )
        st.caption(
            f"Estimated runtime: **{_fmt_seconds(est)}** "
            f"({config['n_outer']:,} \u00d7 "
            f"{_GRID_STEPS_PER_YEAR.get(config['grid_frequency'], 52)} steps "
            f"\u00d7 {config['n_inner']:,} inner \u00d7 {len(portfolio)} trade"
            f"{'s' if len(portfolio) != 1 else ''})"
        )
