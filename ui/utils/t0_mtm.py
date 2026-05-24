"""Fast t=0 MtM preview for portfolio UI display.

The full PFE run already stores per-trade t=0 MtM in ``latest_result``.  This
module provides the lighter pre-run estimate used by the Portfolio tab and
sidebar before a full nested grid calculation has been run.
"""

from __future__ import annotations

import json
from typing import Any

import numpy as np

from pfev2.core.types import TimeGrid
from pfev2.engine.backends.numpy_backend import NumpyBackend
from pfev2.engine.gbm import MultivariateGBM
from pfev2.pricing.inner_mc import InnerMCPricer
from pfev2.utils.seeds import make_inner_mc_seed_sequence
from ui.utils.converters import build_config, build_market_data, build_portfolio


def _json_ready(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, dict):
        return {str(k): _json_ready(v) for k, v in sorted(value.items())}
    if isinstance(value, (list, tuple)):
        return [_json_ready(v) for v in value]
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    return value


def _build_backend(config):
    if config.backend == "numba":
        try:
            from pfev2.engine.backends.numba_backend import NumbaBackend

            return NumbaBackend()
        except ImportError:
            return NumpyBackend()
    return NumpyBackend()


def t0_mtm_preview_signature(
    market_state: dict,
    portfolio_specs: list[dict],
    config_state: dict,
) -> str:
    """Stable cache key for the inputs that affect preview t=0 MtM."""
    config_subset = {
        "n_inner": config_state.get("n_inner"),
        "grid_frequency": config_state.get("grid_frequency"),
        "backend": config_state.get("backend"),
        "seed": config_state.get("seed"),
        "antithetic": config_state.get("antithetic"),
    }
    payload = {
        "market": market_state,
        "portfolio": portfolio_specs,
        "config": config_subset,
    }
    return json.dumps(_json_ready(payload), sort_keys=True, separators=(",", ":"))


def compute_t0_mtm_preview(
    market_state: dict,
    portfolio_specs: list[dict],
    config_state: dict,
) -> list[float]:
    """Price each trade at t=0 without running the full PFE time grid."""
    if not portfolio_specs:
        return []

    market = build_market_data(market_state)
    portfolio = build_portfolio(portfolio_specs, market)
    config = build_config(config_state)

    engine = MultivariateGBM(backend=_build_backend(config))
    pricer = InnerMCPricer(
        engine=engine,
        antithetic=config.antithetic,
        n_workers=1,
    )
    pricer.set_market(market)

    all_node_spots = market.spots[np.newaxis, :]
    realized_paths = all_node_spots[:, np.newaxis, :]
    realized_grid = np.array([0.0])

    values: list[float] = []
    for trade_idx, trade in enumerate(portfolio):
        remaining_grid = TimeGrid.from_maturity(trade.maturity, config.grid_frequency)
        seed_seq = make_inner_mc_seed_sequence(config.seed, 0, trade_idx)

        if trade.requires_full_path:
            mtm = pricer.batch_price_path_dependent(
                trade,
                market,
                all_node_spots,
                remaining_grid,
                config.n_inner,
                seed_seq,
                realized_paths=realized_paths,
                realized_grid=realized_grid,
            )
        else:
            mtm = pricer.batch_price_european(
                trade,
                market,
                all_node_spots,
                remaining_grid,
                config.n_inner,
                seed_seq,
            )
        values.append(float(mtm[0]))

    return values


def get_cached_t0_mtm_preview(session_state) -> dict:
    """Return current preview values, recomputing only when inputs change."""
    market_state = session_state.get("market", {})
    portfolio_specs = session_state.get("portfolio", [])
    config_state = session_state.get("config", {})

    if not portfolio_specs or not market_state.get("asset_names"):
        return {}

    signature = t0_mtm_preview_signature(market_state, portfolio_specs, config_state)
    cached = session_state.get("t0_mtm_preview")
    if cached and cached.get("signature") == signature:
        return cached

    try:
        values = compute_t0_mtm_preview(market_state, portfolio_specs, config_state)
        preview = {
            "signature": signature,
            "per_trade_t0_mtm": values,
            "source": "preview",
        }
    except Exception as exc:
        preview = {
            "signature": signature,
            "per_trade_t0_mtm": [],
            "source": "preview",
            "error": f"{type(exc).__name__}: {exc}",
        }

    session_state["t0_mtm_preview"] = preview
    return preview


def resolve_t0_mtm_values(
    portfolio: list[dict],
    latest_result: dict | None = None,
    t0_preview: dict | None = None,
) -> tuple[list[float], str | None]:
    """Choose display t=0 MtM values, preferring full-run values."""
    n_trades = len(portfolio)
    latest_values = (latest_result or {}).get("per_trade_t0_mtm", []) or []
    if n_trades and len(latest_values) == n_trades:
        return [float(v) for v in latest_values], "run"

    preview_values = (t0_preview or {}).get("per_trade_t0_mtm", []) or []
    if n_trades and len(preview_values) == n_trades:
        return [float(v) for v in preview_values], "preview"

    return [], None
