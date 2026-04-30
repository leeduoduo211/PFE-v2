import numpy as np

from pfev2.core.exceptions import InstrumentError
from pfev2.instruments.base import BaseInstrument


class RestrikeOption(BaseInstrument):
    """Restrike (cliquet-style) option whose strike resets at a fixed date.

    Category: Path-dependent
    Path required: Yes

    The strike is locked in at the spot price observed on ``reset_time``.
    Payoff at maturity (in spot units, not performance-normalised):

        Call: max(S(T) - S(t_reset), 0)
        Put:  max(S(t_reset) - S(T), 0)

    Parameters
    ----------
    reset_time : float
        Date (in years) at which the strike resets to the prevailing spot.
        Must satisfy 0 < reset_time < maturity.
    option_type : str
        "call" or "put". Defaults to "call".
    """

    def __init__(self, *, trade_id, maturity, notional, asset_indices, reset_time, option_type="call"):
        super().__init__(trade_id, maturity, notional, asset_indices)
        if reset_time <= 0 or reset_time >= maturity:
            raise InstrumentError(f"reset_time must be in (0, maturity), got {reset_time}")
        if option_type not in ("call", "put"):
            raise InstrumentError("option_type must be 'call' or 'put'")
        self.reset_time = reset_time
        self.option_type = option_type

    @property
    def requires_full_path(self) -> bool:
        return True

    def payoff(self, spots, path_history, t_grid=None):
        prices = path_history[:, :, 0]
        n_paths, n_steps = prices.shape

        reset_idx = self._resolve_event_index(self.reset_time, n_steps, t_grid)

        s_reset = prices[:, reset_idx]
        s_terminal = prices[:, -1]

        if self.option_type == "call":
            return np.maximum(s_terminal - s_reset, 0.0)
        else:
            return np.maximum(s_reset - s_terminal, 0.0)
