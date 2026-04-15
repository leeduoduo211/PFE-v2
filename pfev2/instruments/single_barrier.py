import numpy as np
from pfev2.instruments.base import BaseInstrument
from pfev2.core.exceptions import InstrumentError


class SingleBarrier(BaseInstrument):
    """European-style barrier option — barrier checked at expiry only.

    Unlike KnockOut/KnockIn modifiers (which monitor the path continuously),
    this instrument checks the barrier condition only at maturity against S(T).

    Payoff (barrier_type="in"):
      Call: max(S(T) - K, 0) * 1{barrier_condition_met}
      Put:  max(K - S(T), 0) * 1{barrier_condition_met}

    Payoff (barrier_type="out"):
      Call: max(S(T) - K, 0) * 1{barrier_condition_NOT_met}
      Put:  max(K - S(T), 0) * 1{barrier_condition_NOT_met}

    where barrier_condition:
      direction="up":  S(T) > barrier
      direction="down": S(T) < barrier
    """

    def __init__(self, *, trade_id, maturity, notional, asset_indices,
                 strike, barrier, option_type, barrier_direction, barrier_type):
        super().__init__(trade_id, maturity, notional, asset_indices)
        if strike <= 0:
            raise InstrumentError(f"strike must be positive, got {strike}")
        if barrier <= 0:
            raise InstrumentError(f"barrier must be positive, got {barrier}")
        if option_type not in ("call", "put"):
            raise InstrumentError(f"option_type must be 'call' or 'put', got '{option_type}'")
        if barrier_direction not in ("up", "down"):
            raise InstrumentError(f"barrier_direction must be 'up' or 'down', got '{barrier_direction}'")
        if barrier_type not in ("in", "out"):
            raise InstrumentError(f"barrier_type must be 'in' or 'out', got '{barrier_type}'")
        self.strike = strike
        self.barrier = barrier
        self.option_type = option_type
        self.barrier_direction = barrier_direction
        self.barrier_type = barrier_type

    def payoff(self, spots, path_history=None, t_grid=None):
        s = spots[:, 0]
        if self.option_type == "call":
            vanilla = np.maximum(s - self.strike, 0.0)
        else:
            vanilla = np.maximum(self.strike - s, 0.0)
        if self.barrier_direction == "up":
            condition = s > self.barrier
        else:
            condition = s < self.barrier
        if self.barrier_type == "out":
            condition = ~condition
        return vanilla * condition.astype(float)
