"""Pydantic request models for the PFE-v2 REST API.

These mirror the UI trade-spec dict format documented in CLAUDE.md
(``{trade_id, instrument_type, direction, params, modifiers}``) so the same
payloads flow through ``ui.utils.converters`` unchanged. Structural validation
happens here; deep economic validation (PSD correlation matrix, positive
strikes, max 5 underlyings, ...) stays in the converters and pfev2 classes.

Note: ``typing.Optional``/``List``/``Dict`` are used instead of PEP 604
unions because pydantic evaluates annotations at runtime and the API is
exercised on Python 3.9 in some dev environments.
"""

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class ModifierSpec(BaseModel):
    type: str
    params: Dict[str, Any] = Field(default_factory=dict)


class TradeSpec(BaseModel):
    trade_id: str
    instrument_type: str
    direction: Literal["long", "short"] = "long"
    params: Dict[str, Any]
    modifiers: List[ModifierSpec] = Field(default_factory=list)


class MarketState(BaseModel):
    spots: List[float]
    vols: List[float]
    rates: List[float]
    domestic_rate: float
    corr_matrix: List[List[float]]
    asset_names: List[str]
    asset_classes: List[str]


class ConfigState(BaseModel):
    """All fields optional — missing keys fall back to PFEConfig defaults."""

    n_outer: Optional[int] = None
    n_inner: Optional[int] = None
    confidence_level: Optional[float] = None
    grid_frequency: Optional[str] = None
    margined: Optional[bool] = None
    mpor_days: Optional[int] = None
    backend: Optional[str] = None
    n_workers: Optional[int] = None
    seed: Optional[int] = None
    antithetic: Optional[bool] = None

    def to_state(self) -> Dict[str, Any]:
        """Dict with only the explicitly-set keys, for ``build_config``."""
        return {k: v for k, v in self.model_dump().items() if v is not None}


class RunRequest(BaseModel):
    market: MarketState
    portfolio: List[TradeSpec] = Field(min_length=1)
    config: ConfigState = Field(default_factory=ConfigState)
    label: Optional[str] = None


class T0MtmRequest(BaseModel):
    market: MarketState
    portfolio: List[TradeSpec] = Field(min_length=1)
    config: ConfigState = Field(default_factory=ConfigState)
