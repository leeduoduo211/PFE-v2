"""Simulation backends: NumPy (default) and Numba (optional JIT)."""

from pfev2.engine.backends.numpy_backend import NumpyBackend

__all__ = ["NumpyBackend"]

# Numba backend is imported lazily because numba is an optional dependency.
try:
    from pfev2.engine.backends.numba_backend import NumbaBackend  # noqa: F401
    __all__.append("NumbaBackend")
except ImportError:  # numba not installed
    pass
