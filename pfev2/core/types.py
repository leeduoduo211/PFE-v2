from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

import numpy as np

from pfev2.core.exceptions import (
    ConfigError,
    CorrelationMatrixError,
    MarketDataError,
)


class AssetClass(Enum):
    FX = "FX"
    EQUITY = "EQUITY"


@dataclass
class TimeGrid:
    dates: np.ndarray
    dt: np.ndarray

    @classmethod
    def from_maturity(cls, maturity: float, frequency: str = "weekly") -> TimeGrid:
        freq_map = {"daily": 252, "weekly": 52, "monthly": 12}
        steps_per_year = freq_map.get(frequency)
        if steps_per_year is None:
            raise ConfigError(f"Unknown frequency: {frequency}. Use daily/weekly/monthly.")
        n_steps = max(1, int(round(maturity * steps_per_year)))
        dates = np.linspace(0.0, maturity, n_steps + 1)
        dt = np.diff(dates)
        return cls(dates=dates, dt=dt)

    def remaining_grid(self, from_idx: int) -> TimeGrid:
        remaining_dates = self.dates[from_idx:] - self.dates[from_idx]
        return TimeGrid(dates=remaining_dates, dt=np.diff(remaining_dates))


class PayoffTimeGrid(np.ndarray):
    """Numpy time grid carrying the valuation time used to build a path."""

    def __new__(cls, dates, valuation_time: float = 0.0):
        obj = np.asarray(dates, dtype=float).view(cls)
        obj.valuation_time = float(valuation_time)
        return obj

    def __array_finalize__(self, obj):
        if obj is not None:
            self.valuation_time = getattr(obj, "valuation_time", 0.0)


@dataclass(frozen=True)
class MarketData:
    spots: np.ndarray
    vols: np.ndarray
    rates: np.ndarray
    domestic_rate: float
    corr_matrix: np.ndarray
    asset_names: list[str]
    asset_classes: list[str]

    def __post_init__(self):
        n = len(self.spots)
        for name, arr in [("vols", self.vols), ("rates", self.rates)]:
            if arr.shape != (n,):
                raise MarketDataError(
                    f"{name} shape {arr.shape} doesn't match spots shape ({n},)"
                )
        if self.corr_matrix.shape != (n, n):
            raise MarketDataError(
                f"corr_matrix shape {self.corr_matrix.shape} doesn't match ({n},{n})"
            )
        if len(self.asset_names) != n or len(self.asset_classes) != n:
            raise MarketDataError(
                f"asset_names/asset_classes length doesn't match spots shape ({n},)"
            )
        for name, arr in [("spots", self.spots), ("vols", self.vols), ("rates", self.rates)]:
            if np.any(np.isnan(arr)):
                raise MarketDataError(f"NaN detected in {name}")
        if np.any(self.vols <= 0):
            raise MarketDataError(f"All vol values must be positive, got min={self.vols.min()}")
        corr = self.corr_matrix
        if not np.allclose(corr, corr.T, atol=1e-8):
            raise CorrelationMatrixError("Correlation matrix is not symmetric")
        if not np.allclose(np.diag(corr), 1.0):
            raise CorrelationMatrixError("Correlation matrix diagonal must be 1.0")
        if np.any(np.abs(corr) > 1.0 + 1e-8):
            raise CorrelationMatrixError("Correlation values must be in [-1, 1]")
        eigvals = np.linalg.eigvalsh(corr)
        if np.any(eigvals < -1e-8):
            raise CorrelationMatrixError(
                f"Correlation matrix is not positive semi-definite (min eigenvalue={eigvals.min():.6f})"
            )

    def index_of(self, name: str) -> int:
        try:
            return self.asset_names.index(name)
        except ValueError as e:
            raise MarketDataError(
                f"Asset '{name}' not found in {self.asset_names}"
            ) from e

    def evolve(self, new_spots: np.ndarray, t: float) -> MarketData:
        return MarketData(
            spots=new_spots,
            vols=self.vols,
            rates=self.rates,
            domestic_rate=self.domestic_rate,
            corr_matrix=self.corr_matrix,
            asset_names=self.asset_names,
            asset_classes=self.asset_classes,
        )


@dataclass
class PFEConfig:
    n_outer: int = 5000
    n_inner: int = 2000
    confidence_level: float = 0.95
    grid_frequency: str = "weekly"
    margined: bool = False
    mpor_days: int = 10
    backend: str = "numpy"
    n_workers: int = 1
    seed: int = 42
    antithetic: bool = False

    def __post_init__(self):
        if self.n_outer <= 0:
            raise ConfigError(f"n_outer must be positive, got {self.n_outer}")
        if self.n_inner <= 0:
            raise ConfigError(f"n_inner must be positive, got {self.n_inner}")
        if not (0.0 < self.confidence_level < 1.0):
            raise ConfigError(
                f"confidence_level must be in (0, 1), got {self.confidence_level}"
            )
        if self.backend not in ("numpy", "numba"):
            raise ConfigError(f"backend must be 'numpy' or 'numba', got '{self.backend}'")
