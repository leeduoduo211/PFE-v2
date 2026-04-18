# UI Kit — PFE-v2 web app

React recreation of the Streamlit app at `ui/app.py`. Pixel-intent match (Streamlit HTML can't be replicated exactly; tokens come from `ui/theme.py`).

## Files
- `index.html` — app shell + routing between 4 steps.
- `styles.css` — imports the root `colors_and_type.css` tokens.
- `Sidebar.jsx` — brand, portfolio summary, trade rows, run history.
- `StepTabs.jsx` — numbered workflow tabs with ● ▸ ○ glyphs.
- `MarketDataTab.jsx` — assets table + correlation matrix (PSD badge).
- `PortfolioTab.jsx` — trade detail with stacked modifier sections.
- `ConfigTab.jsx` — sampling + variance-reduction controls + run banner.
- `ResultsTab.jsx` — 4 KPI cards, live Plotly PFE/EPE chart, per-trade table.

## Interactions
- Click tabs to move between steps (all 4 render).
- Sidebar trade selection updates the Portfolio tab's active trade.
- Config → **Run PFE** button jumps to Results (fake run; data is canned).
- Results' **No results yet** empty state appears if `hasResults=false`.

## Notes
- Plotly is the chart library (matching app's stack). Template matches `pfe_light` from `ui/theme.py`.
- Numbers all use JetBrains Mono, comma-grouped, no currency prefix.
- No real backend; all data is inline constants.
