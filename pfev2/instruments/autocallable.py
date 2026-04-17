import numpy as np
from pfev2.instruments.base import BaseInstrument
from pfev2.core.exceptions import InstrumentError


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

    @property
    def requires_full_path(self) -> bool:
        return True

    def observation_dates(self) -> np.ndarray:
        return self.schedule

    def payoff(self, spots, path_history, t_grid=None):
        n_paths = path_history.shape[0]
        n_steps = path_history.shape[1]
        initial_prices = path_history[:, 0, :]  # (n_paths, n_assets)

        if t_grid is not None:
            obs_indices = np.searchsorted(t_grid, self.schedule, side="right") - 1
            obs_indices = np.clip(obs_indices, 0, n_steps - 1)
        else:
            t_grid_full = np.linspace(0.0, self.maturity, n_steps)
            obs_indices = np.searchsorted(t_grid_full, self.schedule, side="right") - 1
            obs_indices = np.clip(obs_indices, 0, n_steps - 1)

        result = np.zeros(n_paths)
        called = np.zeros(n_paths, dtype=bool)

        for i, idx in enumerate(obs_indices):
            obs_prices = path_history[:, idx, :]
            performances = obs_prices / initial_prices
            worst_perf = np.min(performances, axis=1)

            newly_called = (~called) & (worst_perf >= self.autocall_trigger)
            result[newly_called] = self.coupon_rate * (i + 1)
            called |= newly_called

        # At maturity for uncalled paths
        terminal_prices = path_history[:, -1, :]
        terminal_perf = terminal_prices / initial_prices
        worst_terminal = np.min(terminal_perf, axis=1)

        uncalled = ~called
        put_loss = uncalled & (worst_terminal < self.put_strike)
        result[put_loss] = worst_terminal[put_loss] - 1.0

        return result
