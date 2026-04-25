import numpy as np

from pfev2.core.exceptions import InstrumentError
from pfev2.instruments.base import BaseInstrument


class TARF(BaseInstrument):
    """Target Accrual Redemption Forward.

    Like an Accumulator but terminates when cumulative profit hits target.
    Partial fill on the final fixing: if cumulative would exceed target,
    only the residual amount is taken.

    At each observation (while cumulative < target):
      Buy side:  units = 1 if S >= K, else leverage
      Sell side: units = 1 if S <= K, else leverage
      period_pnl = units * (S - K) * sign  (sign = +1 buy, -1 sell)
    """

    def __init__(self, *, trade_id, maturity, notional, asset_indices,
                 strike, target, leverage, side, schedule):
        super().__init__(trade_id, maturity, notional, asset_indices)
        if strike <= 0:
            raise InstrumentError(f"strike must be positive, got {strike}")
        if target <= 0:
            raise InstrumentError(f"target must be positive, got {target}")
        if leverage <= 0:
            raise InstrumentError(f"leverage must be positive, got {leverage}")
        if side not in ("buy", "sell"):
            raise InstrumentError(f"side must be 'buy' or 'sell', got '{side}'")
        self.strike = strike
        self.target = target
        self.leverage = leverage
        self.side = side
        self.schedule = np.asarray(schedule)
        self._validate_schedule(self.schedule, maturity)

    @property
    def requires_full_path(self) -> bool:
        return True

    def observation_dates(self) -> np.ndarray:
        return self.schedule

    def payoff(self, spots, path_history, t_grid=None):
        prices = path_history[:, :, 0]
        n_paths, n_steps = prices.shape

        obs_indices = self._resolve_obs_indices(self.schedule, n_steps, t_grid)

        sign = 1.0 if self.side == "buy" else -1.0
        cumulative = np.zeros(n_paths)
        terminated = np.zeros(n_paths, dtype=bool)
        result = np.zeros(n_paths)

        for idx in obs_indices:
            s_obs = prices[:, idx]
            if self.side == "buy":
                units = np.where(s_obs >= self.strike, 1.0, self.leverage)
            else:
                units = np.where(s_obs <= self.strike, 1.0, self.leverage)

            period_pnl = units * (s_obs - self.strike) * sign
            new_cumulative = cumulative + period_pnl

            # Check target hit (only for non-terminated paths)
            hits_target = (~terminated) & (new_cumulative >= self.target)
            result[hits_target] = self.target  # partial fill: cap at target
            terminated |= hits_target

            # Update cumulative for non-terminated paths
            active = ~terminated
            cumulative[active] = new_cumulative[active]

        # Paths that never hit target
        still_active = ~terminated
        result[still_active] = cumulative[still_active]

        return result
