import pytest

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


def test_hierarchy():
    """All exceptions inherit from PFEv2Error."""
    for exc_class in [
        MarketDataError, CorrelationMatrixError, InstrumentError,
        ModifierError, SimulationError, PricingError, ConfigError,
    ]:
        assert issubclass(exc_class, PFEv2Error)
        assert issubclass(exc_class, Exception)


def test_can_catch_by_base():
    with pytest.raises(PFEv2Error):
        raise MarketDataError("bad data")


def test_message_preserved():
    err = InstrumentError("strike must be positive, got -1.0")
    assert "-1.0" in str(err)
