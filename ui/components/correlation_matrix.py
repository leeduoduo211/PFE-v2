"""Interactive N×N correlation matrix editor with PSD validation."""

import numpy as np
import streamlit as st


def _is_positive_semidefinite(matrix: np.ndarray) -> bool:
    """Check if matrix is positive semi-definite via eigenvalues."""
    try:
        eigenvalues = np.linalg.eigvalsh(matrix)
        return bool(np.all(eigenvalues >= -1e-10))
    except np.linalg.LinAlgError:
        return False


def _nearest_psd(matrix: np.ndarray) -> np.ndarray:
    """Find nearest positive semi-definite matrix (simplified Higham)."""
    eigvals, eigvecs = np.linalg.eigh(matrix)
    eigvals = np.maximum(eigvals, 1e-8)
    result = eigvecs @ np.diag(eigvals) @ eigvecs.T
    d = np.sqrt(np.diag(result))
    result = result / np.outer(d, d)
    return result


def render_correlation_matrix(asset_names: list[str], key_prefix: str = "corr"):
    """Render an editable correlation matrix.

    Reads/writes st.session_state["market"]["corr_matrix"].
    Returns True if matrix is valid PSD, False otherwise.
    """
    n = len(asset_names)
    if n == 0:
        st.info("Add assets first to edit the correlation matrix.")
        return True

    market = st.session_state["market"]

    # Initialize or resize correlation matrix
    current = market.get("corr_matrix", [])
    if len(current) != n or (n > 0 and len(current[0]) != n):
        market["corr_matrix"] = [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]

    corr = market["corr_matrix"]

    st.subheader("Correlation Matrix")

    # Render as a grid of number inputs
    cols = st.columns([1] + [1] * n)
    cols[0].write("")
    for j, name in enumerate(asset_names):
        cols[j + 1].write(f"**{name}**")

    for i in range(n):
        cols = st.columns([1] + [1] * n)
        cols[0].write(f"**{asset_names[i]}**")
        for j in range(n):
            if i == j:
                cols[j + 1].text_input(
                    f"{asset_names[i]}-{asset_names[j]}",
                    value="1.0",
                    disabled=True,
                    key=f"{key_prefix}_{i}_{j}",
                    label_visibility="collapsed",
                )
            elif j > i:
                val = cols[j + 1].number_input(
                    f"{asset_names[i]}-{asset_names[j]}",
                    min_value=-1.0,
                    max_value=1.0,
                    value=float(corr[i][j]),
                    step=0.05,
                    key=f"{key_prefix}_{i}_{j}",
                    label_visibility="collapsed",
                )
                corr[i][j] = val
                corr[j][i] = val
            else:
                cols[j + 1].text_input(
                    f"{asset_names[i]}-{asset_names[j]}",
                    value=f"{corr[i][j]:.2f}",
                    disabled=True,
                    key=f"{key_prefix}_{i}_{j}",
                    label_visibility="collapsed",
                )

    market["corr_matrix"] = corr

    # PSD validation
    matrix = np.array(corr, dtype=float)
    is_valid = _is_positive_semidefinite(matrix)

    if not is_valid:
        st.error("Correlation matrix is NOT positive semi-definite!")
        if st.button("Fix: use nearest PSD matrix", key=f"{key_prefix}_fix"):
            fixed = _nearest_psd(matrix)
            market["corr_matrix"] = fixed.tolist()
            st.rerun()

    return is_valid
