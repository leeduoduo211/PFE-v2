"""JSON serialization for registry entries and PFEResult objects."""

from __future__ import annotations

from dataclasses import asdict

from ui.utils.registry import INSTRUMENT_REGISTRY, MODIFIER_REGISTRY


def _strip_cls(entry: dict) -> dict:
    """Registry entry minus the (non-serializable) constructor class."""
    return {k: v for k, v in entry.items() if k != "cls"}


def registry_payload() -> dict:
    """The instrument/modifier registries as a JSON-safe schema.

    This is the same data that drives the Streamlit trade-builder forms;
    a frontend can generate its forms from it the same way.
    """
    return {
        "instruments": {k: _strip_cls(v) for k, v in INSTRUMENT_REGISTRY.items()},
        "modifiers": {k: _strip_cls(v) for k, v in MODIFIER_REGISTRY.items()},
    }


def serialize_result(result, include_mtm_matrix: bool = False) -> dict:
    """PFEResult → JSON-safe dict.

    The full MtM matrix (n_outer × T_steps) is excluded unless requested —
    at production scale it is tens of MB as JSON.
    """
    payload = {
        "time_points": result.time_points.tolist(),
        "time_points_in_periods": result.time_points_in_periods().tolist(),
        "period_label": result.period_label(),
        "pfe_curve": result.pfe_curve.tolist(),
        "epe_curve": result.epe_curve.tolist(),
        "unmargined_pfe_curve": (
            result.unmargined_pfe_curve.tolist()
            if result.unmargined_pfe_curve is not None else None
        ),
        "unmargined_epe_curve": (
            result.unmargined_epe_curve.tolist()
            if result.unmargined_epe_curve is not None else None
        ),
        "peak_pfe": result.peak_pfe,
        "eepe": result.eepe,
        "computation_time": result.computation_time,
        "config": asdict(result.config),
    }
    if result.per_trade_mtm is not None:
        # (n_trades, n_outer, T) → per-trade t=0 MtM, averaged over outer paths
        payload["per_trade_t0_mtm"] = (
            result.per_trade_mtm[:, :, 0].mean(axis=1).tolist()
        )
    if include_mtm_matrix:
        payload["mtm_matrix"] = result.mtm_matrix.tolist()
    return payload
