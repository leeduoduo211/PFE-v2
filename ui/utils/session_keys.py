"""Central registry of ``st.session_state`` keys used across the UI.

Magic strings kept in one place so the whole UI has a single source of
truth for what session_state keys exist and what they mean. Prefer
``from ui.utils.session_keys import SK`` and reference ``SK.MARKET`` etc.
in new code; plain string access still works for legacy call sites.
"""

from __future__ import annotations


class SK:
    """Named session_state keys. String values must NEVER be changed without
    also deleting any snapshots / test fixtures that reference the old name."""

    # --- Core state ---
    MARKET = "market"
    PORTFOLIO = "portfolio"
    CONFIG = "config"
    RUNS = "runs"
    LATEST_RESULT = "latest_result"

    # --- Trade editing ---
    EDITING_TRADE = "editing_trade"
    PENDING_EDIT_TRADE = "_pending_edit_trade"
    PENDING_NEXT_TRADE_ID = "_pending_next_trade_id"

    # --- View / navigation flags ---
    VIEW_MODE = "view_mode"            # "wizard" | "dashboard"
    SWITCH_TO_PORTFOLIO = "_switch_to_portfolio"
    SWITCH_TO_RESULTS = "_switch_to_results"

    # --- Widget state generation counters ---
    # Bumped when a preset loads to force widget reinitialisation.
    MARKET_FORM_GEN = "_market_form_gen"


def all_keys() -> list[str]:
    """Return every key defined on SK. Useful for sanity tests."""
    return [v for k, v in vars(SK).items() if not k.startswith("_") and isinstance(v, str)]
