import numpy as np

from pfev2.engine.cholesky import CholeskyDecomposer


def test_identity():
    L = CholeskyDecomposer.decompose(np.eye(3))
    np.testing.assert_allclose(L, np.eye(3))


def test_reconstruct():
    corr = np.array([[1.0, 0.5, 0.3], [0.5, 1.0, 0.4], [0.3, 0.4, 1.0]])
    L = CholeskyDecomposer.decompose(corr)
    np.testing.assert_allclose(L @ L.T, corr, atol=1e-10)


def test_correlate_normals():
    corr = np.array([[1.0, 0.8], [0.8, 1.0]])
    L = CholeskyDecomposer.decompose(corr)
    rng = np.random.default_rng(42)
    z = rng.standard_normal((50000, 2))
    w = z @ L.T
    empirical_corr = np.corrcoef(w.T)
    np.testing.assert_allclose(empirical_corr, corr, atol=0.02)


def test_single_asset():
    L = CholeskyDecomposer.decompose(np.array([[1.0]]))
    np.testing.assert_allclose(L, np.array([[1.0]]))


def test_near_singular():
    corr = np.array([[1.0, 0.9999], [0.9999, 1.0]])
    L = CholeskyDecomposer.decompose(corr)
    reconstructed = L @ L.T
    np.testing.assert_allclose(np.diag(reconstructed), [1.0, 1.0], atol=1e-6)
