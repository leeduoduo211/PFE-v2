# Changelog

All notable changes to this project are logged here (reverse chronological).
See [`/Users/xuefeng/.claude/CLAUDE.md`](file:///Users/xuefeng/.claude/CLAUDE.md) for the logging convention.

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
