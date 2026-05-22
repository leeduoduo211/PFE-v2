# Portfolio Tab Redesign Design

Date: 2026-05-22

## Goal

Redesign the Streamlit Portfolio tab so it reads as a portfolio review and
management workspace first, with trade creation/editing as a secondary action.
The current tab puts the trade builder before the portfolio list, so the most
important review surface is visually buried once a user has trades.

## Chosen Direction

Use the B1 structure from the visual mockups: **Summary -> Table -> Detail**.

The Portfolio tab should present information in this order:

1. Portfolio summary strip.
2. Portfolio table.
3. Selected trade detail panel.
4. Collapsed or clearly separated add/edit trade builder.

## User Experience

At the top of the tab, keep the existing `Portfolio` section heading, then show
a compact summary strip with the key portfolio-level facts:

- trade count
- gross notional
- net notional
- max maturity
- latest t=0 MtM or result status when available

Below the summary, show the portfolio table as the primary object on the page.
Rows should be scan-friendly and use the existing compact finance styling:
trade ID, direction, product/category, maturity, notional, t=0 MtM when
available, and row actions grouped at the right.

Below the table, show a focused detail area for one selected trade. This panel
replaces the current repeated per-row term-sheet expanders. It should contain
the same important information, but only for the selected trade:

- term sheet
- payoff/economic summary where available
- modifiers
- structural/scenario notes

Trade creation should move below the review surface into a secondary
`Add / edit trade` area. It can start collapsed when the portfolio already has
trades, and expand automatically when:

- the portfolio is empty
- the user clicks `Add Trade`
- the user clicks `Edit` on a row

## Component Boundaries

Keep the existing Streamlit architecture and avoid a rewrite.

Recommended component responsibilities:

- `ui/app.py`: arrange the Portfolio tab in the new order.
- `ui/components/portfolio_table.py`: render the summary/table surface and row
  actions; return or persist selected trade state.
- `ui/components/trade_builder.py`: remain the canonical add/edit form.
- `ui/components/term_sheet.py`: remain the canonical detail renderer.
- `ui/theme.py`: provide reusable summary/detail/table styling classes.

This preserves the existing registry-driven product model and avoids duplicating
instrument logic.

## State Model

Use Streamlit session state for lightweight UI state:

- selected portfolio row index or trade ID
- whether the add/edit builder is expanded
- pending edit trade, reusing the existing `_pending_edit_trade` mechanism

Selection should survive reruns when possible. If the selected trade is deleted,
fall back to the first remaining trade or no selection.

## Error Handling

The redesign should preserve current behavior:

- If there are no trades, show a clear empty state and expand the builder.
- If market data is missing, keep term-sheet/detail warnings as they are.
- If edit/delete/clone actions change the portfolio, invalidate results.
- Do not remove existing validation from the trade builder.

## Testing And Verification

Manual/browser checks should cover:

- empty portfolio state
- portfolio with one trade
- portfolio with multiple trades
- selecting a trade and viewing details
- add trade flow
- edit existing trade flow
- clone/delete actions
- layout at the current desktop viewport

Code checks should include at minimum:

- `python3 -m compileall ui/app.py ui/components/portfolio_table.py ui/components/trade_builder.py ui/components/term_sheet.py ui/theme.py`

If existing UI tests cover portfolio behavior, run the relevant test file as
well.

## Non-Goals

- No pricing-engine changes.
- No product registry changes.
- No conversion away from Streamlit.
- No full dashboard redesign.
- No new JavaScript frontend.

## Open Implementation Notes

The selected trade detail can be implemented as a button-driven selection first,
using `View` or row-click-like actions. If Streamlit row-level click behavior is
too awkward, explicit `View`, `Edit`, `Clone`, and `Del` buttons are acceptable
and consistent with the existing app.
