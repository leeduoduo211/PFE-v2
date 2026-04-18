# ui/utils/runner.py
"""Execute PFE computation with progress bar and result storage."""

import traceback
import threading
import numpy as np
import streamlit as st
from pfev2.risk.pfe import compute_pfe
from ui.utils.converters import build_market_data, build_portfolio, build_config
from ui.utils.session import add_run


def run_pfe_calculation():
    """Run PFE computation using current session state.
    Shows progress bar, stores result in session state runs history.
    Returns the PFEResult or None on error.
    """
    market_state = st.session_state["market"]
    portfolio_specs = st.session_state["portfolio"]
    config_state = st.session_state["config"]

    if not portfolio_specs:
        st.error("Portfolio is empty. Add at least one trade.")
        return None

    try:
        market = build_market_data(market_state)
        portfolio = build_portfolio(portfolio_specs, market)
        config = build_config(config_state)
    except Exception as e:
        st.error(f"Configuration error: {e}")
        return None

    progress_value = [0.0]  # mutable container for thread-safe progress
    result_container = {}
    error_container = {}

    def _update_progress(p):
        progress_value[0] = p

    def worker():
        try:
            result_container["result"] = compute_pfe(
                portfolio, market, config,
                on_progress=_update_progress,
                per_trade_detail=True,
            )
        except Exception as e:
            error_container["error"] = e
            error_container["tb"] = traceback.format_exc()

    import time

    status = st.status("Running PFE calculation...", expanded=True)
    with status:
        progress_bar = st.progress(0, text="Initializing...")
        info_text = st.empty()
        info_text.caption(
            f"Config: {config.n_outer:,} outer \u00d7 {config.n_inner:,} inner"
            f" | {'Antithetic' if config.antithetic else 'Standard'}"
            f" | {config.n_workers} thread{'s' if config.n_workers > 1 else ''}"
        )

        thread = threading.Thread(target=worker)
        thread.start()

        # Poll progress from main thread (Streamlit widgets aren't thread-safe)
        while thread.is_alive():
            p = progress_value[0]
            progress_bar.progress(min(p, 1.0), text=f"Time steps: {p:.0%}")
            time.sleep(0.15)

        thread.join()
        progress_bar.progress(1.0, text="Done!")

    if "error" not in error_container:
        elapsed = result_container["result"].computation_time
        status.update(label=f"PFE complete in {elapsed:.1f}s", state="complete", expanded=False)
    else:
        status.update(label="PFE computation failed", state="error", expanded=True)

    if "error" in error_container:
        err = error_container["error"]
        tb = error_container.get("tb", "")
        st.error(f"PFE computation failed: {type(err).__name__}: {err}")
        with st.expander("Full traceback"):
            st.code(tb)
        return None

    pfe_result = result_container["result"]

    # Compute exposure matrix for fan chart
    if config.margined:
        freq_map = {"daily": 252, "weekly": 52, "monthly": 12}
        steps_per_year = freq_map.get(config.grid_frequency, 52)
        mpor_steps = max(1, int(round(config.mpor_days / 252 * steps_per_year)))
        exposure = np.zeros_like(pfe_result.mtm_matrix)
        for t in range(pfe_result.mtm_matrix.shape[1]):
            lookback = max(t - mpor_steps, 0)
            exposure[:, t] = np.maximum(
                pfe_result.mtm_matrix[:, t] - pfe_result.mtm_matrix[:, lookback], 0.0
            )
    else:
        exposure = np.maximum(pfe_result.mtm_matrix, 0.0)

    # Build per-trade PFE curves
    per_trade_pfe = None
    per_trade_mtm_matrix = pfe_result.per_trade_mtm  # shape (n_trades, n_outer, n_steps)
    if per_trade_mtm_matrix is not None:
        per_trade_exposure = np.maximum(per_trade_mtm_matrix, 0.0)
        per_trade_pfe = np.quantile(per_trade_exposure, config.confidence_level, axis=1)

    # Compute per-trade t=0 MtM (mean across outer paths at time step 0)
    n_trades = len(portfolio_specs)
    if per_trade_mtm_matrix is not None:
        per_trade_t0_mtm = [float(np.mean(per_trade_mtm_matrix[i, :, 0])) for i in range(n_trades)]
    else:
        per_trade_t0_mtm = []

    # Store summary for run comparison (only curves, not full matrices)
    run_summary = {
        "time_points": pfe_result.time_points.tolist(),
        "pfe_curve": pfe_result.pfe_curve.tolist(),
        "epe_curve": pfe_result.epe_curve.tolist(),
        "peak_pfe": pfe_result.peak_pfe,
        "eepe": pfe_result.eepe,
        "config": {
            "n_outer": config.n_outer,
            "n_inner": config.n_inner,
            "confidence_level": config.confidence_level,
            "grid_frequency": config.grid_frequency,
            "margined": config.margined,
            "seed": getattr(config, "seed", None),
            "antithetic": getattr(config, "antithetic", False),
        },
        "unmargined_pfe_curve": pfe_result.unmargined_pfe_curve.tolist(),
        "unmargined_epe_curve": pfe_result.unmargined_epe_curve.tolist(),
        "computation_time": pfe_result.computation_time,
        "n_trades": len(portfolio_specs),
        "n_assets": len(market_state["asset_names"]),
        "per_trade_t0_mtm": per_trade_t0_mtm,
    }

    add_run(run_summary)

    # Store latest full result for display (includes heavy matrices for fan chart)
    latest = dict(run_summary)
    latest["exposure_matrix"] = exposure.tolist()
    if per_trade_pfe is not None:
        latest["per_trade_pfe"] = per_trade_pfe.tolist()
    latest["per_trade_t0_mtm"] = per_trade_t0_mtm
    st.session_state["latest_result"] = latest

    return pfe_result
