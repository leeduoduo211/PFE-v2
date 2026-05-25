"""Interactive N x N correlation matrix editor with PSD validation."""

from __future__ import annotations

from html import escape

import numpy as np
import streamlit as st

from ui.theme import card_title, corr_cell_html


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


def _parse_corr_value(raw_value: str) -> float | None:
    """Parse a correlation input and enforce [-1, 1]."""
    try:
        value = float(raw_value)
    except (TypeError, ValueError):
        return None
    if value < -1.0 or value > 1.0:
        return None
    return value


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

    # Initialize or resize correlation matrix.
    current = market.get("corr_matrix", [])
    if len(current) != n or (n > 0 and len(current[0]) != n):
        market["corr_matrix"] = [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]

    if n == 1:
        return True

    corr = market["corr_matrix"]
    safe_names = [escape(str(name), quote=True) for name in asset_names]

    card_title("Correlation matrix", "Must be positive semi-definite. Validated on save.")

    grid = st.container(border=True)
    invalid_pairs = []
    with grid:
        header_cols = st.columns([1.1] + [1] * n, gap="small")
        header_cols[0].markdown("&nbsp;", unsafe_allow_html=True)
        for i, name in enumerate(safe_names):
            header_cols[i + 1].markdown(
                f"<div style=\"padding:6px 0 2px;text-align:center;font-size:11px;"
                f"font-weight:600;color:#94a3b8;text-transform:uppercase;"
                f"letter-spacing:0.06em;font-family:'JetBrains Mono',monospace;\">"
                f"{name}</div>",
                unsafe_allow_html=True,
            )

        for i, row_name in enumerate(safe_names):
            row_cols = st.columns([1.1] + [1] * n, gap="small")
            row_cols[0].markdown(
                f'<div style="min-height:38px;display:flex;align-items:center;'
                f'font-weight:600;color:#1e293b;font-size:13px;white-space:nowrap;">'
                f"{row_name}</div>",
                unsafe_allow_html=True,
            )
            for j in range(n):
                if j > i:
                    row_cols[j + 1].markdown(
                        '<div style="min-height:38px;"></div>',
                        unsafe_allow_html=True,
                    )
                elif i == j:
                    row_cols[j + 1].markdown(
                        corr_cell_html(corr[i][j], is_diag=True),
                        unsafe_allow_html=True,
                    )
                else:
                    input_key = f"{key_prefix}_{j}_{i}_text"
                    source_key = f"{input_key}_source"
                    source_value = f"{float(corr[i][j]):.2f}"
                    if (
                        source_key not in st.session_state
                        or st.session_state[source_key] != source_value
                    ):
                        st.session_state[input_key] = source_value
                        st.session_state[source_key] = source_value

                    raw_value = row_cols[j + 1].text_input(
                        f"{asset_names[i]}-{asset_names[j]} correlation",
                        key=input_key,
                        label_visibility="collapsed",
                    )
                    val = _parse_corr_value(raw_value)
                    if val is None:
                        invalid_pairs.append(f"{asset_names[i]}-{asset_names[j]}")
                    else:
                        corr[i][j] = val
                        corr[j][i] = val
                        st.session_state[source_key] = f"{val:.2f}"

    market["corr_matrix"] = corr

    if invalid_pairs:
        st.warning(
            "Correlation values must be numbers between -1.00 and 1.00: "
            + ", ".join(invalid_pairs)
        )

    matrix = np.array(corr, dtype=float)
    is_valid = _is_positive_semidefinite(matrix)
    try:
        min_eig = float(np.linalg.eigvalsh(matrix).min())
    except np.linalg.LinAlgError:
        min_eig = float("nan")

    if is_valid:
        st.markdown(
            f'<div style="font-size:12px;color:#64748b;">PSD check: '
            f'<span style="color:#22c55e;">passes</span> '
            f'<span style="color:#94a3b8;">(min eigenvalue {min_eig:.3f})</span></div>',
            unsafe_allow_html=True,
        )
    else:
        st.error("Correlation matrix is NOT positive semi-definite!")
        st.caption(f"Min eigenvalue: {min_eig:.4f}")
        if st.button("Fix: use nearest PSD matrix", key=f"{key_prefix}_fix"):
            fixed = _nearest_psd(matrix)
            market["corr_matrix"] = fixed.tolist()
            st.rerun()

    return is_valid
