# Changelog

All notable changes to this project are logged here (reverse chronological).

---

## 2026-06-12 — React frontend (Phase 2 of the SPA migration)

**Type**: Feature
**Summary**: New `frontend/` package — a Vite + React + TypeScript SPA over the Phase-1 REST API, with the visual design ported from `design/preview/` (same tokens, same `pfe_light` chart styling). Streamlit app unaffected. Verified end-to-end in the browser: market editing → registry-driven trade builder → T0 MtM preview → run submission with live progress → KPI cards + Plotly exposure profile + per-trade table.

- `frontend/src/api/` **(new)** — `types.ts` mirrors `api/schemas.py` and the result/run-summary payloads; `client.ts` is a small typed fetch wrapper with an `ApiError` carrying the server's 422 detail.
- `frontend/src/components/TradeForm.tsx` **(new)** — registry-driven form builder: renders all 18 instruments and 9 modifiers from `GET /registry` with renderers for every field type (float, select, float_list, select_list, schedule, asset_select, asset_select_optional), variable asset counts ("1-5"/"2-5"), modifier stacking with group badges, and the wrap-chain display.
- `frontend/src/components/` **(new)** — Sidebar (portfolio summary, trade list with T0 MtM, run history), MarketTab (editable assets + symmetric correlation editor with heatmap shading), ConfigTab (sampling, antithetic, margined/MPoR), ResultsTab (progress bar → KPI cards, lazy-loaded Plotly PFE/EPE chart, per-trade table, CSV export).
- `frontend/src/App.tsx` **(new)** — wizard state + run polling (400ms while running, result fetch on completion); per-run trade-id snapshots so the per-trade table stays correct if the portfolio is edited mid-run.
- `frontend/src/styles/tokens.css` — design tokens verbatim from `design/preview/tokens.css` (font paths adjusted); `app.css` ported from the UI-kit stylesheet with live-app additions (progress bar, error banner).
- Plotly (~4.5MB) is code-split via `React.lazy` — the app shell is a 168KB chunk.
- `.github/workflows/ci.yml` — new `frontend` job: `npm ci` + `npm run build` (tsc type-check + Vite build) on Node 22.
- `README.md`, `CLAUDE.md`, `frontend/README.md` — run instructions and architecture notes.

---

## 2026-06-10 — REST API service (Phase 1 of the SPA migration)

**Type**: Feature
**Summary**: New `api/` package — a FastAPI layer over the engine intended as the backend for a future React frontend. The Streamlit app is untouched. 330 tests pass; ruff clean.

- `api/schemas.py` **(new)** — Pydantic request models mirroring the UI trade-spec dict format (`{trade_id, instrument_type, direction, params, modifiers}`); structural validation only, deep validation stays in converters/pfev2. Uses `typing.List`/`Optional` instead of PEP 604 unions so pydantic can evaluate annotations on Python 3.9 dev machines (ruff per-file-ignore added).
- `api/jobs.py` **(new)** — `RunStore`: in-process thread-pool job execution for `compute_pfe` with live progress (wired to the existing `on_progress` callback), status lifecycle (queued/running/completed/failed), and run history. Designed as the seam to swap for Celery/Redis if multi-user concurrency ever matters.
- `api/serializers.py` **(new)** — registry → JSON schema (drives dynamic frontend forms the same way it drives Streamlit forms); `PFEResult` → JSON (curves + scalars; MtM matrix opt-in via `?include_mtm=true`).
- `api/app.py` **(new)** — endpoints: `GET /health`, `GET /registry`, `POST /t0-mtm`, `POST /runs` (202 + run id), `GET /runs`, `GET /runs/{id}`, `GET /runs/{id}/result`. Inputs validated synchronously at submission via `ui/utils/converters.py`, with `PFEv2Error`/`KeyError`/`TypeError` mapped to specific 422s. CORS open for Phase-1 dev (restrict before shared deployment).
- `tests/test_api/test_endpoints.py` **(new)** — 9 tests: registry schema (18 instruments / 9 modifiers, no `cls` leakage), T0 MtM preview + validation errors, full run lifecycle (submit → poll → result, including `include_mtm` and run-history listing), rejection paths (empty portfolio, unknown instrument, bad config), 404s.
- `pyproject.toml` — new `api` extra (`fastapi`, `uvicorn`); `fastapi` + `httpx` added to dev extras so CI exercises the API tests; `api*` added to packages.
- `.github/workflows/ci.yml` — ruff now lints `api/`.
- `README.md` — REST API section with endpoint table; test badge 321 → 330.

---

## 2026-06-10 — Payment-time discounting for periodic instruments + housekeeping

**Type**: Fix
**Summary**: Cashflows of periodic instruments are now discounted from their own payment dates instead of the trade's maturity, the inner-MC memory budget accounts for the full normals allocation, and several repo-hygiene gaps are closed (missing LICENSE, leaked local path, stale Python hints, undocumented modeling assumptions). 321 tests pass; ruff clean.

**Engine**
- `pfev2/instruments/{autocallable,tarf,accumulator}.py` — added `pv_payoff(spots, path_history, t_grid, rate)` and `pays_before_maturity=True`. An autocall coupon is discounted from its call date, and each TARF/Accumulator period PnL from its fixing date, rather than the whole payoff at `exp(-r*tau)`. `payoff()` semantics are unchanged (raw, undiscounted cashflow sum).
- `pfev2/instruments/base.py` — `_resolve_obs_indices` gained `return_times=True` (observation times measured from the valuation node, aligned with indices); new `_time_to_maturity_from_grid` helper; `pays_before_maturity` property (default False).
- `pfev2/pricing/inner_mc.py` — `price_trade` and `batch_price_path_dependent` call `pv_payoff` for `pays_before_maturity` trades and skip the blanket maturity discount.
- `pfev2/modifiers/base.py` — explicit `pays_before_maturity=False`: modifiers transform the aggregate payoff, which doesn't commute with per-cashflow discounting, so wrapped trades keep the at-maturity convention.
- `pfev2/pricing/inner_mc.py` — memory-budget chunking now sizes by `n_assets` instead of `n_trade_assets`: the correlated-normals array spans all market assets (correlation is applied before trade-asset selection), so the old estimate under-counted by `n_assets / n_trade_assets`.
- `tests/test_pricing/test_payment_time_discounting.py` **(new)** — 11 tests: hand-computed PV checks per instrument, `rate=0` equivalence with raw payoff, and pricer-level checks that a deterministic always-calls autocallable is discounted from its call date through both `batch_price_path_dependent` and `price_trade`.

**Housekeeping**
- `LICENSE` **(new)** — MIT license text; README and pyproject already declared MIT but the file was missing.
- `README.md` — new "Modeling assumptions" section (GBM with flat parameters, risk-neutral outer measure, discounting and settlement conventions); test badge 310 → 321.
- `CHANGELOG.md` — removed a `file://` link to a machine-local path.
- `CLAUDE.md` — removed machine-specific Windows conda commands.
- `run_windows.bat` — Python version hint corrected to 3.10+ to match `requires-python`.

---

## 2026-04-24 — Structural review cleanup: 20+ refactors across packaging, UI, core

**Type**: Refactor + Feature
**Summary**: Full-repo review on master identified 20+ structural issues. Fixed all actionable items in one pass: unified color tokens, split the monolithic registry, added CI, factored out duplicated observation-index logic, tightened package metadata, added ruff linting, and removed dead code. 310 tests still pass; ruff check clean.

**Packaging & infrastructure**
- `pyproject.toml` — added `readme`, `license`, `authors`, `keywords`, `classifiers`, `project.urls`. Added `ruff` as a dev dep, `[tool.ruff]` + `[tool.ruff.lint]` config with pragmatic rule set + per-file ignores.
- Deleted `setup.cfg`, `setup.py`, `requirements.txt` — redundant with pyproject.
- `.gitignore` — added `.DS_Store`, `.idea/`, `.vscode/`, `.ruff_cache/`, `.mypy_cache/`, `.claire/`, `Thumbs.db`.
- `run_windows.bat` — corrected Python version hint (3.10+ → 3.9+) to match pyproject declaration.
- `.github/workflows/ci.yml` **(new)** — ruff lint + pytest on Python 3.9/3.10/3.11/3.12.
- `examples/README.md` **(new)** — gallery index with per-script summary.

**Core library**
- `pfev2/{core,risk,pricing,utils,engine/backends}/__init__.py` — populated previously-empty subpackage inits with proper exports (Instrument, compute_pfe, PFEResult, cantor_pair, InnerMCPricer, NumpyBackend). `from pfev2.risk import compute_pfe` now works.
- `pfev2/instruments/base.py` — added `_resolve_obs_indices()` and `_validate_schedule()` helpers on `BaseInstrument`. The former eliminates ~8 lines of duplicated searchsorted/clip logic from 5 instruments (Asian, Cliquet, RangeAccrual, Autocallable, TARF). The latter prevents silent clipping when user supplies schedule dates past maturity.
- `pfev2/modifiers/base.py` — documented the `requires_full_path` default + override pattern (barriers/schedule/target_profit accept default `True`; payoff-only modifiers override to delegate).
- `pfev2/core/types.py`, `pfev2/engine/cholesky.py` — added `from err` exception chaining (ruff B904).

**UI**
- `ui/utils/product_content.py` — aliased all color constants to `ui.theme.COLORS`. Category colors, form-section accents, and modifier-group accents now derive from a single source of truth.
- `ui/utils/registries/` **(new package)** — split 911-line `registry.py` into 5 category files (european, path_dependent, multi_asset, periodic, modifiers) plus an aggregator `__init__.py`. `registry.py` reduced to a 34-line thin re-export; all call sites unchanged.
- `ui/utils/session_keys.py` **(new)** — central registry of `st.session_state` key names as a `SK` class, replacing scattered magic strings.
- `ui/components/__init__.py` — cleaned exports; removed three stale stubs (`render_pfe_epe_chart`, `render_fan_chart`, `render_per_trade_breakdown`) that were all `pass`.
- `ui/components/results_viewer.py` — dropped redundant per-chart `legend=dict(...)` overrides; the pfe_light Plotly template already provides them.

**Auto-fixes (ruff --fix across 19 files)**
- Import reordering (isort), pyupgrade modernisations (list[X] over List[X] where safe), dead imports removed.

**Known intentionally-skipped items**
- `DualDigital`/`TripleDigital` generalisation into `MultiDigital` — deferred (breaking API change, modest benefit).
- `trade_builder.py` / `trade_economics.py` / `registry.py` further sub-splitting — deferred (high churn, low ROI at current size).
- Comprehensive UI rendering test harness — deferred (needs Streamlit test infrastructure).

**Verification**: `python3 -m pytest tests/ -v` → 310 passed, 4 skipped. `python3 -m ruff check pfev2/ ui/ tests/` → clean.

---

## 2026-04-17 — UI design overhaul: 15 improvements across layout, flow, and features

**Type**: Feature + Refactor
**Summary**: Walked through the Streamlit UI in a browser preview, catalogued 15 improvements, then implemented all of them (except dark mode, which the user explicitly skipped). Covers layout chrome, onboarding presets, discoverability hints, runtime estimation, result export, session snapshots, and live portfolio summary. 310 tests pass.

**Files**:
- `ui/theme.py` — hide Streamlit "Deploy" button and other default chrome; add inline-SVG `ICON_*` glyphs for KPI cards; extend `kpi_card()` with optional icon parameter.
- `ui/app.py` — page title + subtitle; step-numbered tabs with `●/▸/○` state glyphs driven by `has_market` / `n_trades` / `has_results`; live sidebar portfolio summary (gross/net notional, max maturity); preset launcher expander on Market Data tab; unified snapshot expander (market-only vs full-session save); wire new `render_result_exports`; generation counter for widget key prefix so presets actually reset widget state.
- `ui/components/config_panel.py` — runtime estimate below the config grid (path-dependent vs vectorised-European throughput), re-calibrated against empirical 1-second run.
- `ui/components/correlation_matrix.py` — skip rendering entirely for `n == 1` (no correlation to edit).
- `ui/components/trade_builder.py` — modifier discoverability hint card with link to wiki, shown only when no modifiers are attached.
- `ui/components/results_viewer.py` — KPI cards now carry icons; legend moved to upper-right with transparent background; `render_result_exports()` adds CSV + Python-snippet downloads; `render_run_comparison()` enriched with Peak PFE / EEPE deltas and percentage changes above the overlay chart.
- `ui/utils/presets.py` **(new)** — three canonical quick-start bundles: Equity 2-asset, FX accumulator, 3-asset basket.
- `ui/utils/snapshots.py` — added `serialize_session()` / `deserialize_session()` for v2 market+portfolio+config bundles (backwards-compatible with legacy v1 market-only envelopes).

**Notes**:
- Preset loading needed a generation-counter trick because Streamlit widgets cache values under their keys; purging `session_state["tab_mkt_*"]` alone wasn't enough. Bumping the key prefix forces a fresh widget tree.
- Margined/unmargined overlay on results chart was already implemented in `results_viewer.py:136`; verified working.
- Dark mode intentionally skipped per user request.

---

## 2026-04-17 — Documentation revamp: illustrative README + wiki

**Type**: Docs
**Summary**: Rewrote README and all wiki pages in a less spec-heavy, more illustrative tone. Added real PFE/EPE profile PNG as the hero image, replaced ASCII-art diagrams with Mermaid, added two new wiki pages (Mathematical Foundations, FAQ), fixed stale parameter names left over from the instrument merge.

**Files**:
- `README.md` — added TOC, badges, hero PNG, Mermaid architecture + instrument-tree + decision diagrams. Trimmed parameter tables, pushed detail to wiki.
- `docs/assets/pfe_profile.png` — real PFE/EPE profile generated from `basic_pfe.py` (2000 outer × 1000 inner paths, peak PFE ≈ $4.37M).
- `docs/assets/make_pfe_profile.py` — reproducible matplotlib script.
- Wiki pages (in separate `PFE-v2.wiki.git` repo):
  - `Home.md` — navigation-first home page with hero image.
  - `Getting-Started.md` — corrected attribute names (`time_points`/`pfe_curve`/`epe_curve`, not `time_grid`/`pfe_profile`/`epe_profile`).
  - `Architecture.md` — Mermaid diagrams for outer/inner MC, Cholesky flow, and modifier chain.
  - `Instruments.md` — full rewrite with narrative-first tone; fixed stale params (`ContingentOption` → correct 6-param schema, `SingleBarrier` → `barrier_direction` + `barrier_type`, `Cliquet` removed non-existent `global_cap`, `Accumulator` → `AccumulatorDecumulator`, `Autocallable` → correct `autocall_trigger`/`put_strike`, no `ki_barrier`).
  - `Modifiers.md` — added missing `LeverageModifier.threshold` param, `TargetProfit.partial_fill` param, and realized-vol modifier details.
  - `Streamlit-UI.md` — refocused on user workflow rather than data-flow internals.
  - `Examples.md` — updated to post-merge API (`AccumulatorDecumulator` + `side`, attribute name fixes).
  - `Mathematical-Foundations.md` **(new)** — GBM SDE, Cholesky derivation, quantile standard error, why we don't use Black–Scholes.
  - `FAQ.md` **(new)** — 20+ common pitfalls and questions grouped by topic.
  - `_Sidebar.md` — cleaner nested nav.

**Notes**:
- Wiki lives in a separate git repo (`git@github.com:leeduoduo211/PFE-v2.wiki.git`); pushed independently.
- PNG reproducible via `PYTHONPATH=. python3 docs/assets/make_pfe_profile.py`.

---

## 2026-04-17 — Post-merge review: 5 fixes across core, UI, and docs

**Type**: Fix + Docs
**Summary**: Thorough code review after the VanillaCall/Put → VanillaOption merge surfaced five issues; all fixed with `310 passed, 4 skipped` on the full test suite.

**Files**:
- `pfev2/pricing/inner_mc.py:77,157` — Cholesky cache now inserts (`cache[id] = L`) instead of replacing the whole dict (`cache = {id: L}`). Prevents silent cache loss if `corr_matrix` rebinds across calls.
- `ui/utils/registry.py:119,140` — `ContingentOption.trigger_asset_idx` and `.target_asset_idx` now carry `"default": 0` / `"default": 1` for schema consistency with every other registry field.
- `pfev2/instruments/{tarf,accumulator,autocallable,range_accrual,asian,cliquet}.py` — Standardized `obs_indices` clip lower bound to `0` across all six path-dependent instruments. Previously the `t_grid is None` and `t_grid is not None` branches disagreed (`1` vs `0`), causing identical schedules to behave differently between outer and nested pricing.
- `ui/components/trade_economics.py:299+` — Replaced 6 lambda stubs with real term-sheet builders for `SingleBarrier`, `AsianOption`, `Cliquet`, `RangeAccrual`, `Autocallable`, `TARF`. Term-sheet UI now shows full economic narrative for all 18 instruments.
- `docs/product-catalog.md`, `docs/specs/2026-04-15-*.md`, `docs/plans/2026-04-15-*.md` — Added deprecation banners pointing readers at the post-merge `README.md` as the authoritative taxonomy source. Body prose left intact as historical record.

**Notes**:
- Did not change: `BaseModifier.requires_full_path = True` default (verified that delegation modifiers like `cap_floor`, `leverage` correctly override). `Dispersion.component_types` field name (verified consistent across class/registry/tests). `Autocallable` coupon indexing (docstring ambiguous, behavior matches standard convention).
- Review was driven by parallel Explore agents; several agent-flagged issues were rejected after spot-checks — filtering was important.
