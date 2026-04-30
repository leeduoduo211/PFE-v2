"""Interactive N x N correlation matrix editor with PSD validation."""

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

    # Editable upper-triangle inputs.
    with st.expander("Edit correlations", expanded=False):
        for i in range(n):
            for j in range(i + 1, n):
                col_label, col_input = st.columns([2, 1])
                col_label.markdown(
                    f'<div style="padding-top:8px;font-size:13px;color:#475569;">'
                    f"{safe_names[i]} -> {safe_names[j]}</div>",
                    unsafe_allow_html=True,
                )
                val = col_input.number_input(
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

    market["corr_matrix"] = corr

    header_cells = (
        '<th style="padding:6px 8px;"></th>'
        + "".join(
            f'<th style="padding:6px 8px;text-align:right;font-size:11px;'
            f"font-weight:600;color:#94a3b8;text-transform:uppercase;"
            f"letter-spacing:0.06em;font-family:'JetBrains Mono',monospace;\">{name}</th>"
            for name in safe_names
        )
    )
    body_rows = []
    for i in range(n):
        row_cells = (
            f'<td style="padding:6px 10px 6px 0;font-weight:500;color:#1e293b;'
            f'font-size:13px;white-space:nowrap;">{safe_names[i]}</td>'
        )
        for j in range(n):
            row_cells += (
                f'<td style="padding:2px;">{corr_cell_html(corr[i][j], is_diag=(i == j))}</td>'
            )
        body_rows.append(f"<tr>{row_cells}</tr>")

    st.markdown(
        '<table style="border-collapse:separate;border-spacing:2px;'
        "background:#ffffff;border:1px solid #e2e8f0;border-radius:8px;"
        "padding:8px 12px;box-shadow:0 1px 3px rgba(0,0,0,0.04);"
        'margin:4px 0 8px 0;">'
        f"<thead><tr>{header_cells}</tr></thead>"
        f'<tbody>{"".join(body_rows)}</tbody>'
        "</table>",
        unsafe_allow_html=True,
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
