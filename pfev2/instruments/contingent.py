import numpy as np
from pfev2.instruments.base import BaseInstrument
from pfev2.core.exceptions import InstrumentError


class ContingentOption(BaseInstrument):
    """
    Trigger asset breaches barrier → vanilla payoff on target asset.
    """

    def __init__(
        self, *, trade_id, maturity, notional, asset_indices,
        trigger_asset_idx, trigger_barrier, trigger_direction,
        target_asset_idx, target_strike, target_type,
    ):
        super().__init__(trade_id, maturity, notional, asset_indices)
        if trigger_direction not in ("up", "down"):
            raise InstrumentError(f"trigger_direction must be 'up' or 'down'")
        if target_type not in ("call", "put"):
            raise InstrumentError(f"target_type must be 'call' or 'put'")
        self.trigger_asset_pos = list(asset_indices).index(trigger_asset_idx)
        self.target_asset_pos = list(asset_indices).index(target_asset_idx)
        self.trigger_barrier = trigger_barrier
        self.trigger_direction = trigger_direction
        self.target_strike = target_strike
        self.target_type = target_type

    def payoff(self, spots, path_history=None, t_grid=None):
        s_trigger = spots[:, self.trigger_asset_pos]
        s_target = spots[:, self.target_asset_pos]

        if self.trigger_direction == "up":
            triggered = s_trigger > self.trigger_barrier
        else:
            triggered = s_trigger < self.trigger_barrier

        if self.target_type == "call":
            vanilla = np.maximum(s_target - self.target_strike, 0.0)
        else:
            vanilla = np.maximum(self.target_strike - s_target, 0.0)

        return triggered.astype(float) * vanilla
