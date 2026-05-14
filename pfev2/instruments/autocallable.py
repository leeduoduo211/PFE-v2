import numpy as np

from pfev2.core.exceptions import InstrumentError
from pfev2.instruments.base import BaseInstrument


class Autocallable(BaseInstrument):
    """Autocallable structured note.

    At each observation date, if worst-of performance >= autocall_trigger,
    the note is called and pays accrued coupons. If never called, at maturity:
    - If worst performance >= put_strike: no loss (principal returned)
    - If worst performance < put_strike: loss = worst_performance - 1.0

    For single-asset trades, "worst-of" reduces to the single asset's performance.
    """

    def __init__(self, *, trade_id, maturity, notional, asset_indices,
                 autocall_trigger, coupon_rate, put_strike, schedule):
        super().__init__(trade_id, maturity, notional, asset_indices)
        if autocall_trigger <= 0:
            raise InstrumentError(f"autocall_trigger must be positive, got {autocall_trigger}")
        if put_strike <= 0:
            raise InstrumentError(f"put_strike must be positive, got {put_strike}")
        self.autocall_trigger = autocall_trigger
        self.coupon_rate = coupon_rate
        self.put_strike = put_strike
        self.schedule = np.asarray(schedule)
        self._validate_schedule(self.schedule, maturity)

    @property
    def requires_full_path(self) -> bool:
        return True

    def observation_dates(self) -> np.ndarray:
        return self.schedule

    def payoff(self, spots, path_history, t_grid=None):
        n_paths = path_history.shape[0]
        n_steps = path_history.shape[1]
        initial_prices = path_history[:, 0, :]  # (n_paths, n_assets)

        obs_indices = self._resolve_obs_indices(self.schedule, n_steps, t_grid)

        # Identify observation dates that have already happened relative to
        # the valuation node. A path that autocalled in the past has no
        # future cashflow — the coupon was paid at the call date, not at
        # maturity — so its MtM at any later node must be zero. The "called"
        # flag still propagates so future observations don't re-trigger and
        # the put-strike maturity check doesn't fire.
        valuation_time = self._valuation_time_from_grid(t_grid)
        schedule_arr = np.asarray(self.schedule, dtype=float)
        if obs_indices.size == schedule_arr.size:
            is_past_obs = schedule_arr < valuation_time - 1e-12
        else:
            # Legacy relative-grid path: helper already filtered past dates.
            is_past_obs = np.zeros(obs_indices.size, dtype=bool)

        result = np.zeros(n_paths)
        called = np.zeros(n_paths, dtype=bool)

        for i, idx in enumerate(obs_indices):
            obs_prices = path_history[:, idx, :]
            performances = obs_prices / initial_prices
            worst_perf = np.min(performances, axis=1)

            newly_called = (~called) & (worst_perf >= self.autocall_trigger)
            if not is_past_obs[i]:
                result[newly_called] = self.coupon_rate * (i + 1)
            # else: past call — cashflow already paid at the call date, no MtM
            called |= newly_called

        # At maturity for uncalled paths
        terminal_prices = path_history[:, -1, :]
        terminal_perf = terminal_prices / initial_prices
        worst_terminal = np.min(terminal_perf, axis=1)

        uncalled = ~called
        put_loss = uncalled & (worst_terminal < self.put_strike)
        result[put_loss] = worst_terminal[put_loss] - 1.0

        return result
