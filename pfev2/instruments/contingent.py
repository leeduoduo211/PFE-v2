import numpy as np
from pfev2.instruments.base import BaseInstrument
from pfev2.core.exceptions import InstrumentError


class ContingentOption(BaseInstrument):
    """Contingent option: vanilla payoff on a target asset, gated by a trigger asset.

    Category: European
    Path required: No

    If the trigger asset breaches its barrier at maturity, the holder receives
    a vanilla call or put payoff on the target asset; otherwise zero.

    Payoff:
        trigger_met * max(sign * (S_target(T) - K_target), 0)

    where trigger_met = 1 if:
        direction="up":   S_trigger(T) > barrier
        direction="down": S_trigger(T) < barrier

    Parameters
    ----------
    trigger_asset_idx : int
        Global asset index of the trigger underlying.
    trigger_barrier : float
        Barrier level for the trigger asset.
    trigger_direction : str
        "up" — trigger fires when S_trigger > barrier.
        "down" — trigger fires when S_trigger < barrier.
    target_asset_idx : int
        Global asset index of the target underlying whose payoff is paid.
    target_strike : float
        Strike of the vanilla option on the target asset.
    target_type : str
        "call" or "put" for the target asset's payoff.
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
