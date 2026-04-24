from __future__ import annotations

from abc import abstractmethod

import numpy as np


class BaseModifier:
    """Abstract base class for all payoff modifiers.

    Group: Base

    Wraps an existing instrument (or another modifier) and transforms the
    raw payoff returned by the inner instrument's ``payoff`` method.
    Attributes such as ``trade_id``, ``maturity``, ``notional``, and
    ``asset_indices`` are delegated transparently to the inner instrument.

    Subclasses implement ``_apply`` to perform the actual transformation.

    Parameters
    ----------
    inner : BaseInstrument or BaseModifier
        The instrument (or modifier chain) whose payoff will be transformed.
    """

    def __init__(self, inner, **kwargs):
        self._inner = inner

    @property
    def trade_id(self):
        return self._inner.trade_id

    @property
    def maturity(self):
        return self._inner.maturity

    @property
    def notional(self):
        return self._inner.notional

    @property
    def asset_indices(self):
        return self._inner.asset_indices

    @property
    def requires_full_path(self) -> bool:
        """Whether this modifier needs the full simulated path.

        The default returns ``True`` — safe for any modifier that observes
        prices along the path (barriers, knock-in/out, realized-vol, schedule,
        target-profit). Payoff-only modifiers (``PayoffCap``, ``PayoffFloor``,
        ``LeverageModifier``) override this to delegate to
        ``self._inner.requires_full_path`` so wrapping an otherwise-European
        trade doesn't force path-dependent pricing.
        """
        return True

    def is_alive(self, t: float) -> bool:
        return self._inner.is_alive(t)

    def observation_dates(self) -> np.ndarray | None:
        return self._inner.observation_dates()

    def payoff(self, spots, path_history, t_grid=None):
        raw_payoff = self._inner.payoff(spots, path_history, t_grid)
        return self._apply(raw_payoff, spots, path_history, t_grid)

    @abstractmethod
    def _apply(self, raw_payoff, spots, path_history, t_grid=None) -> np.ndarray:
        ...
