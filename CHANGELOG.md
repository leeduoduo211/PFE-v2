# Changelog

All notable changes to this project are logged here (reverse chronological).
See [`/Users/xuefeng/.claude/CLAUDE.md`](file:///Users/xuefeng/.claude/CLAUDE.md) for the logging convention.

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
