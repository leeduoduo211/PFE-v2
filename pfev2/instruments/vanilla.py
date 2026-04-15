import numpy as np
from pfev2.instruments.base import BaseInstrument
from pfev2.core.exceptions import InstrumentError


class VanillaOption(BaseInstrument):
    """European vanilla option (call or put).

    Category: European
    Path required: No

    Payoff:
        call: max(S(T) - K, 0)
        put:  max(K - S(T), 0)

    Parameters
    ----------
    strike : float
        Option strike price. Must be positive.
    option_type : str
        ``"call"`` or ``"put"``.
    """

    def __init__(self, *, trade_id, maturity, notional, asset_indices, strike, option_type):
        super().__init__(trade_id, maturity, notional, asset_indices)
        if strike <= 0:
            raise InstrumentError(f"strike must be positive, got {strike}")
        if option_type not in ("call", "put"):
            raise InstrumentError(
                f"option_type must be 'call' or 'put', got '{option_type}'"
            )
        self.strike = strike
        self.option_type = option_type

    def payoff(self, spots, path_history=None, t_grid=None):
        s = spots[:, 0]
        if self.option_type == "call":
            return np.maximum(s - self.strike, 0.0)
        return np.maximum(self.strike - s, 0.0)
