"""
Converter layer: bridges UI session state dicts to pfev2 library objects.

Functions
---------
build_market_data  – dict → MarketData
build_instrument   – spec dict → instrument instance (with optional modifiers)
build_portfolio    – list[spec dict] + MarketData → list[instrument]
build_config       – dict → PFEConfig
"""

import numpy as np

from pfev2.core.types import MarketData, PFEConfig
from ui.utils.registry import INSTRUMENT_REGISTRY, MODIFIER_REGISTRY


def _coerce_modifier_params(mod_type: str, params: dict) -> dict:
    """Normalize UI widget values before constructing modifier objects."""
    coerced = dict(params)
    if mod_type == "TargetProfit" and isinstance(coerced.get("partial_fill"), str):
        coerced["partial_fill"] = coerced["partial_fill"].strip().lower() == "true"
    return coerced


def build_market_data(state: dict) -> MarketData:
    """Construct a MarketData from a flat UI state dict."""
    return MarketData(
        spots=np.array(state["spots"], dtype=float),
        vols=np.array(state["vols"], dtype=float),
        rates=np.array(state["rates"], dtype=float),
        domestic_rate=float(state["domestic_rate"]),
        corr_matrix=np.array(state["corr_matrix"], dtype=float),
        asset_names=list(state["asset_names"]),
        asset_classes=list(state["asset_classes"]),
    )


def build_instrument(spec: dict, name_to_idx: dict):
    """
    Construct an instrument (possibly wrapped by modifiers) from a spec dict.

    Parameters
    ----------
    spec : dict
        {
            "trade_id":        str,
            "instrument_type": str,          # key in INSTRUMENT_REGISTRY
            "params":          dict,         # constructor kwargs (excluding trade_id)
            "modifiers":       list[dict],   # [{type, params}, ...]
        }
    name_to_idx : dict
        Mapping from asset name to positional index (unused by converters directly,
        available for callers that build specs from asset names).

    Returns
    -------
    instrument instance, optionally wrapped by modifier chain
    """
    inst_type = spec["instrument_type"]
    reg = INSTRUMENT_REGISTRY[inst_type]
    cls = reg["cls"]

    params = dict(spec["params"])
    params["trade_id"] = spec["trade_id"]

    # Apply direction: short = negate notional
    direction = spec.get("direction", "long")
    if direction == "short":
        params["notional"] = -params["notional"]

    # Convert asset names to integer indices
    if "assets" in params:
        asset_names = params.pop("assets")
        params["asset_indices"] = tuple(name_to_idx[n] for n in asset_names)

    # Ensure asset_indices is a tuple (pfev2 instruments expect tuple, not list)
    if "asset_indices" in params:
        params["asset_indices"] = tuple(params["asset_indices"])

    base = cls(**params)

    # Apply modifiers in order (each wraps the previous)
    wrapped = base
    for mod_spec in spec.get("modifiers", []):
        mod_reg = MODIFIER_REGISTRY[mod_spec["type"]]
        mod_cls = mod_reg["cls"]
        mod_params = _coerce_modifier_params(
            mod_spec["type"], mod_spec.get("params", {})
        )
        wrapped = mod_cls(wrapped, **mod_params)

    return wrapped


def build_portfolio(specs: list, market: MarketData) -> list:
    """
    Construct a list of instruments from a list of spec dicts.

    Parameters
    ----------
    specs  : list of spec dicts (see build_instrument)
    market : MarketData – used to derive the name→index mapping

    Returns
    -------
    list of instrument instances, in the same order as specs
    """
    name_to_idx = {name: i for i, name in enumerate(market.asset_names)}
    return [build_instrument(spec, name_to_idx) for spec in specs]


def build_config(state: dict) -> PFEConfig:
    """
    Construct a PFEConfig from a UI state dict.

    Only keys present in state override the dataclass defaults; missing keys
    fall back to PFEConfig field defaults.
    """
    field_map = {
        "n_outer": int,
        "n_inner": int,
        "confidence_level": float,
        "grid_frequency": str,
        "margined": bool,
        "mpor_days": int,
        "backend": str,
        "n_workers": int,
        "seed": int,
        "antithetic": bool,
    }
    kwargs = {key: cast(state[key]) for key, cast in field_map.items() if key in state}
    return PFEConfig(**kwargs)
