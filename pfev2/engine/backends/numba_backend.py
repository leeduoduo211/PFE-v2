import numpy as np

from pfev2.utils.seeds import cantor_pair

try:
    from numba import njit, prange
    HAS_NUMBA = True
except ImportError:
    HAS_NUMBA = False


def _per_path_seeds(base_seed: int, n_paths: int) -> np.ndarray:
    """Derive ``n_paths`` distinct uint32 seeds from a single base seed.

    ``np.random.seed`` (and numba's port of it) requires the seed to fit in
    ``uint32``, i.e. ``[0, 2**32)``. The previous scheme computed
    ``base_seed + p * 1000003`` directly inside the @njit kernel and
    overflowed for ``n_paths > ~4295`` at the default base seed — so the
    default ``PFEConfig(n_outer=5000)`` silently broke (or became backend-
    dependent) when ``backend="numba"``.

    Build the per-path seeds in Python using ``SeedSequence``, which mixes
    its entropy through a high-quality hash and produces uniformly-
    distributed uint32 values regardless of the base seed magnitude.
    """
    ss = np.random.SeedSequence(int(base_seed))
    # generate_state returns uint32 by default — exactly what np.random.seed
    # accepts inside @njit.
    return ss.generate_state(int(n_paths), dtype=np.uint32)


if HAS_NUMBA:
    @njit(cache=True, parallel=True)
    def _randn_parallel(per_path_seeds, n_steps, n_assets):
        n_paths = per_path_seeds.shape[0]
        result = np.empty((n_paths, n_steps, n_assets))
        for p in prange(n_paths):
            np.random.seed(per_path_seeds[p])
            for t in range(n_steps):
                for a in range(n_assets):
                    result[p, t, a] = np.random.randn()
        return result


class NumbaBackend:
    def __init__(self):
        if not HAS_NUMBA:
            raise ImportError("numba >= 0.59 required for NumbaBackend")

    def randn(self, shape: tuple, seed: int) -> np.ndarray:
        if len(shape) == 3:
            seeds = _per_path_seeds(seed, shape[0])
            return _randn_parallel(seeds, shape[1], shape[2])
        rng = np.random.Generator(np.random.PCG64(seed))
        return rng.standard_normal(shape)

    def matmul(self, a: np.ndarray, b: np.ndarray) -> np.ndarray:
        return np.matmul(a, b)

    def exp(self, x: np.ndarray) -> np.ndarray:
        return np.exp(x)

    def maximum(self, a: np.ndarray, b: np.ndarray) -> np.ndarray:
        return np.maximum(a, b)

    def derive_seed(self, base_seed: int, idx1: int, idx2: int) -> int:
        return base_seed + cantor_pair(idx1, idx2)
