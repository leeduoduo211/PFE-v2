import numpy as np
import pytest

try:
    from pfev2.engine.backends.numba_backend import (
        HAS_NUMBA,
        NumbaBackend,
        _per_path_seeds,
    )
except ImportError:
    HAS_NUMBA = False
    _per_path_seeds = None

# Seed-derivation tests run without numba; everything else requires it.
numba_required = pytest.mark.skipif(not HAS_NUMBA, reason="numba not installed")


@numba_required
def test_randn_shape():
    backend = NumbaBackend()
    z = backend.randn((100, 10, 3), seed=42)
    assert z.shape == (100, 10, 3)


@numba_required
def test_randn_deterministic():
    backend = NumbaBackend()
    z1 = backend.randn((50, 5, 2), seed=123)
    z2 = backend.randn((50, 5, 2), seed=123)
    np.testing.assert_array_equal(z1, z2)


@numba_required
def test_matmul():
    backend = NumbaBackend()
    a = np.random.randn(100, 3, 4)
    b = np.random.randn(4, 2)
    result = backend.matmul(a, b)
    expected = a @ b
    np.testing.assert_allclose(result, expected, rtol=1e-10)


@numba_required
def test_matches_numpy_backend():
    from pfev2.engine.backends.numpy_backend import NumpyBackend
    nb = NumbaBackend()
    npb = NumpyBackend()
    z_nb = nb.randn((100, 10, 3), seed=42)
    z_np = npb.randn((100, 10, 3), seed=42)
    assert z_nb.shape == z_np.shape
    np.testing.assert_allclose(z_nb.mean(), 0.0, atol=0.1)
    np.testing.assert_allclose(z_nb.std(), 1.0, atol=0.1)


# ── seed-derivation regression: per-path seeds must fit in uint32 ───────────
# np.random.seed (and numba's port of it) rejects seeds outside [0, 2^32).
# The previous scheme computed `seed + p * 1000003`, which overflowed for
# n_outer ≥ ~4296 with the default base seed — silently breaking the
# numba backend at the default PFEConfig(n_outer=5000).


@pytest.mark.skipif(_per_path_seeds is None, reason="numba backend module not importable")
def test_per_path_seeds_in_uint32_range_at_default_n_outer():
    seeds = _per_path_seeds(base_seed=42, n_paths=5000)
    assert seeds.dtype == np.uint32
    assert seeds.min() >= 0
    assert seeds.max() < 2**32


@pytest.mark.skipif(_per_path_seeds is None, reason="numba backend module not importable")
def test_per_path_seeds_unique():
    seeds = _per_path_seeds(base_seed=42, n_paths=10_000)
    assert len(np.unique(seeds)) == len(seeds)


@pytest.mark.skipif(_per_path_seeds is None, reason="numba backend module not importable")
def test_per_path_seeds_deterministic():
    a = _per_path_seeds(base_seed=42, n_paths=100)
    b = _per_path_seeds(base_seed=42, n_paths=100)
    np.testing.assert_array_equal(a, b)


@pytest.mark.skipif(_per_path_seeds is None, reason="numba backend module not importable")
def test_per_path_seeds_varies_with_base_seed():
    a = _per_path_seeds(base_seed=42, n_paths=100)
    b = _per_path_seeds(base_seed=43, n_paths=100)
    assert not np.array_equal(a, b)
