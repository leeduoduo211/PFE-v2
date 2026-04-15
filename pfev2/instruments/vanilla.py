import numpy as np
from pfev2.instruments.base import BaseInstrument
from pfev2.core.exceptions import InstrumentError


class VanillaCall(BaseInstrument):
    """European vanilla call option.

    Category: European
    Path required: No

    Payoff: max(S(T) - K, 0)

    Parameters
    ----------
    strike : float
        Option strike price. Must be positive.
    """

    def __init__(self, *, trade_id, maturity, notional, asset_indices, strike):
        super().__init__(trade_id, maturity, notional, asset_indices)
        if strike <= 0:
            raise InstrumentError(f"strike must be positive, got {strike}")
        self.strike = strike

    def payoff(self, spots, path_history=None, t_grid=None):
        s = spots[:, 0]
        return np.maximum(s - self.strike, 0.0)


class VanillaPut(BaseInstrument):
    """European vanilla put option.

    Category: European
    Path required: No

    Payoff: max(K - S(T), 0)

    Parameters
    ----------
    strike : float
        Option strike price. Must be positive.
    """

    def __init__(self, *, trade_id, maturity, notional, asset_indices, strike):
        super().__init__(trade_id, maturity, notional, asset_indices)
        if strike <= 0:
            raise InstrumentError(f"strike must be positive, got {strike}")
        self.strike = strike

    def payoff(self, spots, path_history=None, t_grid=None):
        s = spots[:, 0]
        return np.maximum(self.strike - s, 0.0)
