# PFE-v2 frontend

React + TypeScript single-page app over the REST API (`api/`). Phase 2 of the
Streamlit-to-SPA migration — the visual design is ported from the UI kit in
`design/preview/` and uses the same design tokens (`src/styles/tokens.css`).

## Run

```bash
# Terminal 1 — backend
pip3 install -e ".[api]"
python3 -m uvicorn api.app:app

# Terminal 2 — frontend (proxies /api → 127.0.0.1:8000)
cd frontend
npm install
npm run dev          # http://localhost:5173
```

`npm run build` type-checks (`tsc -b`) and emits a production bundle to
`dist/` — CI runs this on every push.

## How it works

- **Registry-driven forms** — `GET /api/registry` returns the same instrument and
  modifier field schemas that drive the Streamlit trade builder.
  `src/components/TradeForm.tsx` renders all 18 instruments and 9 modifiers
  from that schema; new instruments added to the Python registry appear here
  with no frontend change.
- **Trade specs on the wire** — the app state *is* the API payload format
  (`{trade_id, instrument_type, direction, params, modifiers}`); there is no
  mapping layer.
- **Runs** — `POST /api/runs` queues a computation; the app streams live
  progress from `GET /api/runs/{id}/events` via `EventSource` (wired to the
  engine's `on_progress` callback) and renders curves, KPI cards, and the
  per-trade table from `GET /api/runs/{id}/result`.
- **Plotly** is lazy-loaded (it dominates bundle size) only when a result is
  first displayed; the chart layout matches the `pfe_light` template from
  `ui/theme.py`.

## Layout

```
src/
  api/         types.ts (wire types) · client.ts (typed fetch)
  components/  Sidebar · StepTabs · MarketTab · PortfolioTab · TradeForm
               ConfigTab · ResultsTab · PfeChart · inputs (NumInput etc.)
  styles/      tokens.css (design system, verbatim) · app.css
  App.tsx      state + run polling · main.tsx entry
```
