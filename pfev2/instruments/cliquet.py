import numpy as np
from pfev2.instruments.base import BaseInstrument


class Cliquet(BaseInstrument):
    """Periodic reset option summing clipped local returns.

    return_i = clip(S(t_i) / S(t_{i-1}) - 1, local_floor, local_cap)
    Payoff = max(sum(return_i), global_floor)
    """

    def __init__(self, *, trade_id, maturity, notional, asset_indices,
                 local_cap, local_floor, global_floor, schedule):
        super().__init__(trade_id, maturity, notional, asset_indices)
        self.local_cap = local_cap
        self.local_floor = local_floor
        self.global_floor = global_floor
        self.schedule = np.asarray(schedule)

    @property
    def requires_full_path(self) -> bool:
        return True

    def observation_dates(self) -> np.ndarray:
        return self.schedule

    def payoff(self, spots, path_history, t_grid=None):
        prices = path_history[:, :, 0]
        n_paths, n_steps = prices.shape

        if t_grid is not None:
            obs_indices = np.searchsorted(t_grid, self.schedule, side="right") - 1
            obs_indices = np.clip(obs_indices, 0, n_steps - 1)
        else:
            t_grid_full = np.linspace(0.0, self.maturity, n_steps)
            obs_indices = np.searchsorted(t_grid_full, self.schedule, side="right") - 1
            obs_indices = np.clip(obs_indices, 0, n_steps - 1)

        # Prepend index 0 as the initial reference price
        all_indices = np.concatenate([[0], obs_indices])
        total_return = np.zeros(n_paths)

        for i in range(1, len(all_indices)):
            s_prev = prices[:, all_indices[i - 1]]
            s_curr = prices[:, all_indices[i]]
            local_ret = s_curr / s_prev - 1.0
            clipped = np.clip(local_ret, self.local_floor, self.local_cap)
            total_return += clipped

        return np.maximum(total_return, self.global_floor)
