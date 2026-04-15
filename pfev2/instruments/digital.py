import numpy as np
from pfev2.instruments.base import BaseInstrument
from pfev2.core.exceptions import InstrumentError


class Digital(BaseInstrument):
    """European binary (cash-or-nothing) digital option on a single asset.

    Category: European
    Path required: No

    Payoff:
        Call: 1 if S(T) > K, else 0
        Put:  1 if S(T) < K, else 0

    Parameters
    ----------
    strike : float
        Barrier strike level. Must be positive.
    option_type : str
        "call" or "put". Defaults to "call".
    """

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
    """Binary digital option contingent on two assets simultaneously meeting their conditions.

    Category: Multi-asset
    Path required: No

    Payoff: 1 if both conditions satisfied simultaneously, else 0

    Conditions per asset i:
        call: S_i(T) > K_i
        put:  S_i(T) < K_i

    Parameters
    ----------
    strikes : list of float
        Strike levels for each of the two assets. Length must be 2.
    option_types : list of str
        "call" or "put" for each of the two assets. Length must be 2.
    """

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
    """Binary digital option contingent on three assets simultaneously meeting their conditions.

    Category: Multi-asset
    Path required: No

    Payoff: 1 if all three conditions satisfied simultaneously, else 0

    Conditions per asset i:
        call: S_i(T) > K_i
        put:  S_i(T) < K_i

    Parameters
    ----------
    strikes : list of float
        Strike levels for each of the three assets. Length must be 3.
    option_types : list of str
        "call" or "put" for each of the three assets. Length must be 3.
    """

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
