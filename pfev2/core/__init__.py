"""Core dataclasses, protocols, and exceptions shared across the engine."""

from pfev2.core.exceptions import (
    ConfigError,
    CorrelationMatrixError,
    InstrumentError,
    MarketDataError,
    ModifierError,
    PFEv2Error,
    PricingError,
    SimulationError,
)
from pfev2.core.protocols import Instrument, SimulationBackend
from pfev2.core.types import AssetClass, MarketData, PFEConfig, TimeGrid

__all__ = [
    # types
    "AssetClass",
    "MarketData",
    "PFEConfig",
    "TimeGrid",
    # protocols
    "Instrument",
    "SimulationBackend",
    # exceptions
    "PFEv2Error",
    "ConfigError",
    "CorrelationMatrixError",
    "InstrumentError",
    "MarketDataError",
    "ModifierError",
    "PricingError",
    "SimulationError",
]
