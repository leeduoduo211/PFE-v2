import numpy as np
from pfev2.core.exceptions import CorrelationMatrixError


class CholeskyDecomposer:
    EPSILON = 1e-8

    @staticmethod
    def decompose(corr_matrix: np.ndarray) -> np.ndarray:
        regularized = corr_matrix + CholeskyDecomposer.EPSILON * np.eye(len(corr_matrix))
        try:
            return np.linalg.cholesky(regularized)
        except np.linalg.LinAlgError:
            raise CorrelationMatrixError(
                "Cholesky decomposition failed — matrix is not positive semi-definite"
            )
