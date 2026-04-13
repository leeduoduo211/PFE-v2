import numpy as np
from pfev2.instruments.base import BaseInstrument
from pfev2.core.exceptions import InstrumentError


class Digital(BaseInstrument):
    def __init__(self, *, trade_id, maturity, notional, asset_indices, strike, option_type="call"):
        super().__init__(trade_id, maturity, notional, asset_indices)
        if strike <= 0:
            raise InstrumentError(f"strike must be positive, got {strike}")
        if option_type not in ("call", "put"):
            raise InstrumentError(f"option_type must be 'call' or 'put', got '{option_type}'")
        self.strike = strike
        self.option_type = option_type

    def payoff(self, spots, path_history=None, t_grid=None):
        s = spots[:, 0]
        if self.option_type == "call":
            return (s > self.strike).astype(float)
        else:
            return (s < self.strike).astype(float)


class DualDigital(BaseInstrument):
    def __init__(self, *, trade_id, maturity, notional, asset_indices, strikes, option_types):
        super().__init__(trade_id, maturity, notional, asset_indices)
        if len(strikes) != 2 or len(option_types) != 2:
            raise InstrumentError("DualDigital requires exactly 2 strikes and 2 option_types")
        self.strikes = strikes
        self.option_types = option_types

    def payoff(self, spots, path_history=None, t_grid=None):
        conditions = np.ones(len(spots), dtype=bool)
        for i in range(2):
            s = spots[:, i]
            if self.option_types[i] == "call":
                conditions &= s > self.strikes[i]
            else:
                conditions &= s < self.strikes[i]
        return conditions.astype(float)


class TripleDigital(BaseInstrument):
    def __init__(self, *, trade_id, maturity, notional, asset_indices, strikes, option_types):
        super().__init__(trade_id, maturity, notional, asset_indices)
        if len(strikes) != 3 or len(option_types) != 3:
            raise InstrumentError("TripleDigital requires exactly 3 strikes and 3 option_types")
        self.strikes = strikes
        self.option_types = option_types

    def payoff(self, spots, path_history=None, t_grid=None):
        conditions = np.ones(len(spots), dtype=bool)
        for i in range(3):
            s = spots[:, i]
            if self.option_types[i] == "call":
                conditions &= s > self.strikes[i]
            else:
                conditions &= s < self.strikes[i]
        return conditions.astype(float)
