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

    @property
    def pays_before_maturity(self) -> bool:
        return True

    def observation_dates(self) -> np.ndarray:
        return self.schedule

    def payoff(self, spots, path_history, t_grid=None):
        return self._payoff_impl(spots, path_history, t_grid, rate=None)

    def pv_payoff(self, spots, path_history, t_grid, rate):
        """Payoff with each period's PnL discounted from its fixing date."""
        return self._payoff_impl(spots, path_history, t_grid, rate=rate)

    def _payoff_impl(self, spots, path_history, t_grid, rate):
        prices = path_history[:, :, 0]
        n_paths, n_steps = prices.shape

        obs_indices, obs_times = self._resolve_obs_indices(
            self.schedule, n_steps, t_grid, return_times=True
        )

        # Past observations relative to the valuation node: paths that hit
        # the target in the past had their cashflow paid at termination —
        # MtM at any later node must be zero. (The accrued PnL of surviving
        # paths is left unchanged here; that's a related but separate
        # accrual-accounting question outside the scope of this fix.)
        is_past_obs = obs_times <= 1e-12

        if rate is None:
            obs_dfs = np.ones(obs_indices.size)
        else:
            obs_dfs = np.exp(-rate * np.maximum(obs_times, 0.0))

        sign = 1.0 if self.side == "buy" else -1.0
        cumulative = np.zeros(n_paths)
        terminated = np.zeros(n_paths, dtype=bool)
        result = np.zeros(n_paths)

        for i, idx in enumerate(obs_indices):
            s_obs = prices[:, idx]
            if self.side == "buy":
                units = np.where(s_obs >= self.strike, 1.0, self.leverage)
            else:
                units = np.where(s_obs <= self.strike, 1.0, self.leverage)

            period_pnl = units * (s_obs - self.strike) * sign
            new_cumulative = cumulative + period_pnl

            # Check target hit (only for non-terminated paths)
            hits_target = (~terminated) & (new_cumulative >= self.target)
            active = ~terminated
            if is_past_obs[i]:
                # Past cashflows are settled. They affect target capacity and
                # termination state, but are not part of remaining MtM.
                terminated |= hits_target
            else:
                non_hit = active & ~hits_target
                result[non_hit] += period_pnl[non_hit] * obs_dfs[i]
                # Partial fill: only the residual target amount is still paid
                # at the hit fixing, not the full target again.
                residual = np.maximum(self.target - cumulative, 0.0)
                result[hits_target] += residual[hits_target] * obs_dfs[i]
                terminated |= hits_target

            # Update cumulative for non-terminated paths
            active = ~terminated
            cumulative[active] = new_cumulative[active]

        return result
