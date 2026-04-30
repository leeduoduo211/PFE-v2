"""Market data input component: manual entry."""

import streamlit as st

from ui.components.correlation_matrix import render_correlation_matrix
from ui.theme import card_title

_ASSET_CAP = 10


def _table_header(labels_widths: list[tuple[str, float]]):
    """Render an overline-styled column header row."""
    cols = st.columns([w for _, w in labels_widths])
    for col, (label, _) in zip(cols, labels_widths):
        col.markdown(
            f'<div style="font-size:10px;font-weight:600;color:#94a3b8;'
            f'text-transform:uppercase;letter-spacing:0.08em;'
            f'padding:0 0 4px 2px;">{label}</div>',
            unsafe_allow_html=True,
        )


def render_market_data_input(key_prefix: str = "mkt"):
    """Render the full market data input section.
    Reads/writes st.session_state["market"].
    Returns True if correlation matrix is valid PSD.
    """
    market = st.session_state["market"]

    card_title("Assets", "Tickers are free-form. Match the pricer lookup.")

    n_assets = st.number_input(
        "Number of assets",
        min_value=1, max_value=_ASSET_CAP,
        value=max(1, len(market["asset_names"])),
        key=f"{key_prefix}_n_assets",
    )

    # Resize arrays if needed
    current_n = len(market["asset_names"])
    if n_assets != current_n:
        _resize_market(market, int(n_assets))

    _COL_WIDTHS = [(("Ticker", 2)), (("Class", 1.5)), (("Spot", 1.5)),
                   (("Vol (ann.)", 1.5)), (("Drift", 1.5))]
    _table_header(_COL_WIDTHS)

    for i in range(int(n_assets)):
        cols = st.columns([w for _, w in _COL_WIDTHS])
        market["asset_names"][i] = cols[0].text_input(
            f"Asset {i+1} Name", value=market["asset_names"][i],
            key=f"{key_prefix}_name_{i}", label_visibility="collapsed",
        )
        market["asset_classes"][i] = cols[1].selectbox(
            f"Class {i+1}", ["EQUITY", "FX"],
            index=0 if market["asset_classes"][i] == "EQUITY" else 1,
            key=f"{key_prefix}_class_{i}", label_visibility="collapsed",
        )
        market["spots"][i] = cols[2].number_input(
            f"Spot {i+1}", value=float(market["spots"][i]),
            min_value=0.0001, format="%.4f",
            key=f"{key_prefix}_spot_{i}", label_visibility="collapsed",
        )
        market["vols"][i] = cols[3].number_input(
            f"Vol {i+1}", value=float(market["vols"][i]),
            min_value=0.001, max_value=5.0, step=0.01, format="%.4f",
            key=f"{key_prefix}_vol_{i}", label_visibility="collapsed",
        )
        market["rates"][i] = cols[4].number_input(
            f"Rate {i+1}", value=float(market["rates"][i]),
            min_value=-0.5, max_value=1.0, step=0.005, format="%.4f",
            key=f"{key_prefix}_rate_{i}", label_visibility="collapsed",
        )

    st.caption(f"{int(n_assets)} of {_ASSET_CAP} asset cap.")

    market["domestic_rate"] = st.number_input(
        "Domestic Rate", value=float(market["domestic_rate"]),
        min_value=-0.5, max_value=1.0, step=0.005, format="%.4f",
        key=f"{key_prefix}_dom_rate",
    )

    is_psd = render_correlation_matrix(market["asset_names"], key_prefix=f"{key_prefix}_corr")
    return is_psd


def _resize_market(market: dict, n: int):
    """Resize all market arrays to n assets, preserving existing values."""
    for key, default in [
        ("asset_names", "Asset"),
        ("asset_classes", "EQUITY"),
        ("spots", 100.0),
        ("vols", 0.20),
        ("rates", 0.03),
    ]:
        current = market[key]
        if len(current) < n:
            if isinstance(default, str):
                current.extend([f"{default}_{i+1}" for i in range(len(current), n)])
            else:
                current.extend([default] * (n - len(current)))
        elif len(current) > n:
            market[key] = current[:n]

    # Resize correlation matrix
    old_n = len(market.get("corr_matrix", []))
    if old_n != n:
        new_corr = [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]
        for i in range(min(old_n, n)):
            for j in range(min(old_n, n)):
                new_corr[i][j] = market["corr_matrix"][i][j] if old_n > 0 else (1.0 if i == j else 0.0)
        market["corr_matrix"] = new_corr
