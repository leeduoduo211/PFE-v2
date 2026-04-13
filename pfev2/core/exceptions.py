class PFEv2Error(Exception):
    """Base exception for all PFE-v2 errors."""


class MarketDataError(PFEv2Error):
    """Invalid market data (spots, vols, rates dimensions, NaN values)."""


class CorrelationMatrixError(PFEv2Error):
    """Correlation matrix is not PSD, not symmetric, or values outside [-1,1]."""


class InstrumentError(PFEv2Error):
    """Invalid instrument configuration."""


class ModifierError(PFEv2Error):
    """Incompatible or invalid modifier configuration."""


class SimulationError(PFEv2Error):
    """Path generation failure."""


class PricingError(PFEv2Error):
    """Inner MC pricing failure."""


class ConfigError(PFEv2Error):
    """Invalid PFEConfig values."""
