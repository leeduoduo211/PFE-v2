import numpy as np

from pfev2.core.exceptions import InstrumentError
from pfev2.instruments.base import BaseInstrument


class ForwardStartingOption(BaseInstrument):
    """Forward-starting option whose strike is set at a future date.

    Category: Path-dependent
    Path required: Yes

    The effective strike is fixed to the spot price at ``start_time``.
    Payoff at maturity (performance-normalised):

        Call: max(S(T) / S(t_start) - 1, 0)
        Put:  max(1 - S(T) / S(t_start), 0)

    Parameters
    ----------
    start_time : float
        Date (in years) at which the strike is set. Must satisfy
        0 < start_time < maturity.
    option_type : str
        "call" or "put". Defaults to "call".
    """

    def __init__(self, *, trade_id, maturity, notional, asset_indices, start_time, option_type="call"):
        super().__init__(trade_id, maturity, notional, asset_indices)
        if start_time <= 0 or start_time >= maturity:
            raise InstrumentError(f"start_time must be in (0, maturity), got {start_time}")
        if option_type not in ("call", "put"):
            raise InstrumentError(f"option_type must be 'call' or 'put', got '{option_type}'")
        self.start_time = start_time
        self.option_type = option_type

    @property
    def requires_full_path(self) -> bool:
        return True

    def payoff(self, spots, path_history, t_grid=None):
        prices = path_history[:, :, 0]
        n_paths, n_steps = prices.shape

        start_idx = self._resolve_event_index(self.start_time, n_steps, t_grid)

        s_start = prices[:, start_idx]
        s_terminal = prices[:, -1]
        performance = s_terminal / s_start

        if self.option_type == "call":
            return np.maximum(performance - 1.0, 0.0)
        else:
            return np.maximum(1.0 - performance, 0.0)
