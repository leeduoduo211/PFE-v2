from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np

from pfev2.core.exceptions import InstrumentError


class BaseInstrument(ABC):
    """Abstract base class for all PFE instruments.

    Category: Base

    Defines the common interface every instrument must implement. Subclasses
    provide a ``payoff`` method that maps simulated spot prices (and optionally
    the full path history) to a per-path payoff vector.

    Parameters
    ----------
    trade_id : str
        Unique identifier for the trade.
    maturity : float
        Time to maturity in years. Must be positive.
    notional : float
        Notional amount. Must be non-zero.
    asset_indices : tuple of int
        Indices into the global asset array. At most 5 underlyings allowed.
    """

    def __init__(
        self,
        trade_id: str,
        maturity: float,
        notional: float,
        asset_indices: tuple[int, ...],
    ):
        if maturity <= 0:
            raise InstrumentError(f"maturity must be positive, got {maturity}")
        if notional == 0:
            raise InstrumentError(f"notional must be non-zero, got {notional}")
        if not asset_indices:
            raise InstrumentError("asset_indices must not be empty")
        if len(asset_indices) > 5:
            raise InstrumentError(f"max 5 underlyings per trade, got {len(asset_indices)}")

        self.trade_id = trade_id
        self.maturity = maturity
        self.notional = notional
        self.asset_indices = tuple(asset_indices)

    @abstractmethod
    def payoff(
        self,
        spots: np.ndarray,
        path_history: np.ndarray | None,
        t_grid: np.ndarray | None = None,
    ) -> np.ndarray:
        ...

    @property
    def requires_full_path(self) -> bool:
        return False

    def is_alive(self, t: float) -> bool:
        return t < self.maturity

    def observation_dates(self) -> np.ndarray | None:
        return None

    # ------------------------------------------------------------------
    # Shared helpers for subclasses
    # ------------------------------------------------------------------

    def _resolve_obs_indices(
        self,
        schedule: np.ndarray,
        n_steps: int,
        t_grid: np.ndarray | None,
        *,
        include_past: bool = True,
    ) -> np.ndarray:
        """Convert observation times in ``schedule`` to path indices.

        Common helper for Asian / Cliquet / RangeAccrual / Accumulator /
        Autocallable / TARF. Replaces the ~8 lines of identical
        ``np.searchsorted + np.clip`` logic previously duplicated in each
        payoff implementation.

        Parameters
        ----------
        schedule : np.ndarray
            Absolute observation times (in years).
        n_steps : int
            Number of time points in the simulated path (``path_history.shape[1]``).
        t_grid : np.ndarray or None
            Explicit simulation time grid (passed from nested pricing). When
            ``None`` a uniform grid from ``0`` to ``self.maturity`` is assumed.
        include_past : bool
            Whether observations on or before the valuation time should be
            included when the path contains realized history.

        Returns
        -------
        obs_indices : np.ndarray[int]
            Path-history indices at which to read spot prices, clipped to
            ``[0, n_steps - 1]``.
        """
        schedule = np.asarray(schedule, dtype=float)
        if schedule.size == 0:
            return np.array([], dtype=int)

        if t_grid is not None:
            valuation_time = self._valuation_time_from_grid(t_grid)
            has_explicit_valuation = hasattr(t_grid, "valuation_time")
            grid = np.asarray(t_grid, dtype=float)
            if grid.size == 0:
                return np.array([], dtype=int)

            # Full conditional paths are passed with an absolute grid from
            # inception. Legacy single-node pricing may pass only the remaining
            # relative grid; in that case convert absolute schedule dates to
            # times relative to the valuation node and drop already-past dates.
            is_relative_remaining = (
                not has_explicit_valuation
                and abs(float(grid[0])) <= 1e-12
                and float(grid[-1]) < self.maturity - 1e-12
            )
            if is_relative_remaining:
                valuation_time = self.maturity - float(grid[-1])
                schedule = schedule - valuation_time
                schedule = schedule[schedule > 1e-12]
                if schedule.size == 0:
                    return np.array([], dtype=int)
            elif not include_past:
                schedule = schedule[schedule > valuation_time + 1e-12]
                if schedule.size == 0:
                    return np.array([], dtype=int)

            obs_indices = np.searchsorted(grid, schedule, side="right") - 1
        else:
            t_grid_full = np.linspace(0.0, self.maturity, n_steps)
            obs_indices = np.searchsorted(t_grid_full, schedule, side="right") - 1
        return np.clip(obs_indices, 0, n_steps - 1)

    def _resolve_event_index(
        self,
        event_time: float,
        n_steps: int,
        t_grid: np.ndarray | None,
        *,
        exclude_terminal: bool = True,
    ) -> int:
        """Resolve a single absolute event date to a path-history index."""
        max_idx = n_steps - 2 if exclude_terminal and n_steps > 1 else n_steps - 1
        max_idx = max(0, max_idx)

        if t_grid is not None:
            has_explicit_valuation = hasattr(t_grid, "valuation_time")
            grid = np.asarray(t_grid, dtype=float)
            if grid.size == 0:
                return 0

            is_relative_remaining = (
                not has_explicit_valuation
                and abs(float(grid[0])) <= 1e-12
                and float(grid[-1]) < self.maturity - 1e-12
            )
            if is_relative_remaining:
                valuation_time = self.maturity - float(grid[-1])
                lookup_time = event_time - valuation_time
                if lookup_time <= 0.0:
                    return 0
            else:
                lookup_time = event_time

            idx = int(np.searchsorted(grid, lookup_time, side="right")) - 1
            return max(0, min(idx, max_idx))

        t_grid_full = np.linspace(0.0, self.maturity, n_steps)
        idx = int(np.searchsorted(t_grid_full, event_time, side="right")) - 1
        return max(1 if n_steps > 1 else 0, min(idx, max_idx))

    @staticmethod
    def _valuation_time_from_grid(t_grid: np.ndarray | None) -> float:
        if t_grid is None:
            return 0.0
        return float(getattr(t_grid, "valuation_time", 0.0))

    @staticmethod
    def _validate_schedule(schedule, maturity: float, name: str = "schedule") -> None:
        """Validate that no scheduled observation date exceeds ``maturity``.

        Called from ``__init__`` of path-scheduled instruments. Prevents
        silent clipping at the path's final index when the user supplies
        out-of-range dates.
        """
        arr = np.asarray(schedule, dtype=float)
        if arr.size == 0:
            return
        if np.any(arr < 0):
            raise InstrumentError(f"{name} must be non-negative; got min={arr.min():.4f}")
        if np.any(arr > maturity + 1e-12):
            raise InstrumentError(
                f"{name} dates must be <= maturity ({maturity}); "
                f"got max={arr.max():.4f}"
            )
