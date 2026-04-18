# PFE-v2 Design System

High-fidelity design system for **PFE-v2**, a Python engine with a Streamlit UI for computing **Potential Future Exposure (PFE)** on exotic derivatives via nested Monte Carlo.

Source of truth: [github.com/leeduoduo211/PFE-v2](https://github.com/leeduoduo211/PFE-v2) (branch `master`).
All tokens, components, and content in this system are lifted directly from `ui/theme.py`, `ui/components/*.py`, and `.streamlit/config.toml`.

---

## What PFE-v2 does

Banks and brokerages selling exotic derivatives need to know: *if things go badly for our client, how much could they owe us?* Potential Future Exposure is the industry answer — the 95th-percentile of positive mark-to-market across every plausible future market scenario.

PFE-v2 is a clean, hackable Python alternative to Murex / Calypso / Numerix. It ships with **18 instruments** (vanilla, digital, barrier, Asian, cliquet, worst-of, autocallable, TARF, accumulator…), **9 composable modifiers** (knock-in/out, payoff caps/floors, realized-vol knocks, target profit…), and a **4-step Streamlit wizard** (Market → Portfolio → Config → Results).

### Audience
Quant analysts, risk managers, and trading-desk users at a specific financial institution. Interface is data-dense, scientific, light-mode, chart-forward — **Bloomberg-meets-LaTeX** in intent, Stripe-clean in execution.

### Products covered
1. **Streamlit web app** (`ui/app.py`) — the primary surface. Tab-based workflow, sidebar with portfolio summary + run history, Plotly charts with a custom `pfe_light` template.
2. **Internal tooling / reports** — CSV + Python-snippet exports from the Results tab.

Note: no marketing site or mobile app exists in the source. This design system covers the one product that exists.

---

## Index

| Path | What's in it |
|---|---|
| `README.md` | You are here. Context + content + visual + iconography sections. |
| `colors_and_type.css` | All design tokens as CSS variables (colors, type, radii, elevation). Single source of truth for derivative work. |
| `SKILL.md` | Agent-skill manifest (usable in Claude Code). |
| `preview/` | HTML cards that populate the **Design System** review tab. |
| `ui_kits/pfe_app/` | React recreation of the Streamlit app — `index.html` plus JSX component modules. |
| `assets/` | Logo mark, icon set, chart reference screenshot. |

---

## Content fundamentals

### Voice
**Precise, quant-fluent, quietly authoritative.** Assumes the reader knows what a 95th-percentile quantile, a Cholesky decomposition, and MPoR days are. Never baby-talks the concepts; when a term could be ambiguous, the copy defines it in-line and moves on.

Key examples (all from the live app):

- Page subtitle: *"Nested Monte Carlo Potential Future Exposure on exotic derivative portfolios."*
- Tab caption: *"Define assets, spot prices, volatilities, and correlation structure."*
- Empty state: *"No results yet. Configure and run PFE in the Configuration tab."*
- Error: *"Correlation matrix is NOT positive semi-definite!"*
- Sidebar help: *"Antithetic variates: pair Z and −Z for variance reduction."*

### Tone rules
- **Third person, imperative mood** for instructions. "Define assets" not "Let's define your assets". No "we", no "you", no apologies.
- **Sentence case** for headings, tabs, buttons — never Title Case. ("Market Data" is the one exception, and only because it's a proper workflow name.)
- **UPPERCASE + letterspacing** reserved for overlines / section dividers: `PORTFOLIO (4 TRADES)`, `RUN HISTORY`, `SAVE & LOAD`.
- **Numbers are sacred.** Always in JetBrains Mono, always tabular, always comma-grouped. Currency is implicit (no `$` prefix in the core UI).
- **No exclamations** except for the one validation error (`… is NOT positive semi-definite!`). That single emphasis is the whole exclamation budget.
- **No emoji.** Anywhere. A single `◈` (lozenge) appears as the browser favicon/page icon. Unicode arrows (`→ ▸ ● ○`) stand in for state glyphs.

### Jargon is fine
"EEPE", "MPoR", "Antithetic", "PSD matrix", "Cholesky", "TARF", "Autocallable", "Restrike" all appear unexplained. If a user doesn't recognize them they're not the target user.

### Microcopy examples
- Runtime estimate: *"Estimated runtime: ~42s (5,000 × 52 steps × 2,000 inner × 3 trades)"*
- Disabled-button help: *"Disabled until the portfolio has at least one trade."*
- Preset description: *"One click loads a realistic market + portfolio. Safe to use even mid-session — overwrites current market and portfolio."*

---

## Visual foundations

### Aesthetic summary
**Clean Finance Light.** Named in `ui/theme.py`. A light-mode quantitative finance aesthetic with slate neutrals, a single blue action color, red/green semantic pair, amber for timing, and aggressively tabular numerics. Every surface is white or slate-50; shadows are whisper-quiet; borders are one pixel of slate-200.

### Color
- **Background pair**: `#f8fafc` page · `#ffffff` card. No deep colors anywhere in chrome.
- **Borders**: `#e2e8f0` default, `#cbd5e1` on hover/open, `#3b82f6` on focus.
- **Text ramp**: `#1e293b` → `#475569` → `#64748b` → `#94a3b8`. Four stops, no more.
- **Semantic**: blue `#3b82f6` action / EPE / run-A, red `#ef4444` PFE / short / warning, green `#22c55e` gain / long, amber `#f59e0b` median / peak-time, purple `#8b5cf6` run-B.
- **Fan-chart percentile bands**: stacked red transparencies `0.05 / 0.12 / 0.22`.
- **No gradients.** Exactly one exists in the whole app: the 32px sidebar logo mark (`linear-gradient(135deg, #3b82f6, #6366f1)`). Avoid introducing more.

### Type
- **Inter** for everything that isn't a number. 400 / 500 / 600 / 700.
- **JetBrains Mono** for every number, every code sample, every input field value. Tabular, 400 / 500 / 600.
- Scale runs `0.62rem` (overline) → `0.70rem` (caption) → `0.75rem` (sidebar) → `0.85rem` (body) → `1.3rem` (metric) → `1.5rem` (KPI) → `24px` (page title).

### Spacing / radii
- Radii: `4 / 6 / 7 / 8 / 10px`. Cards are `10px`, inputs `6px`, buttons `7px`, tags `4px`.
- Page content max-width `1200px`. Sidebar `chrome + text`, no images.

### Elevation
- One shadow: `0 1px 3px rgba(0,0,0,0.04)`. Cards, metrics, KPIs, Plotly container. Nothing else gets elevation.
- Focus ring: `0 0 0 3px rgba(59,130,246,0.10)` inside plus blue border.

### Backgrounds
- No photography, no illustration, no repeating patterns, no grain, no noise. The one image is `docs/assets/pfe_profile.png` (a Plotly chart screenshot) used in the README only.
- Plotly charts are the *entire* visual identity. Treat them as full-bleed imagery: grid `#f1f5f9`, zero-line `#e2e8f0`, tick font 10px `#94a3b8`.

### Motion
- One transition: `all 0.15s ease` on buttons only. No bounces, no spring, no easing library. Page state changes are instant reruns (Streamlit).
- Tab auto-switch after a run uses a synthetic click — no animated transition.

### Interaction states
- **Button hover**: primary darkens `#3b82f6 → #2563eb`; secondary adds `#f8fafc` fill and `#cbd5e1` border.
- **Metric hover**: border goes `#e2e8f0 → #cbd5e1`. No elevation change.
- **Input focus**: border `#3b82f6` + 3px `rgba(59,130,246,0.10)` halo.
- **No press/active states defined.** Click feedback is the rerun itself.

### Borders vs fills
- **Borders do the talking.** Cards, inputs, expanders, tab underline, KPI accent stripes are all 1px borders. Fills are used only for semantic tags (`.pfe-tag-long` has `#dcfce7/#16a34a`; `.pfe-tag-short` has `#fef2f2/#ef4444`) and category badges.
- **Left-border accent stripes** mark KPI cards: `pfe-kpi-red / accent / green / amber` = 3px left-border in the semantic color. This is the one "left-border accent" convention worth keeping — it's used intentionally and consistently.

### Cards
White fill, 1px slate-200 border, 10px radius, quiet shadow, 16px padding. That's the whole recipe.

### Transparency & blur
None. No backdrop-filter anywhere. The single use of `rgba(255,255,255,0.9)` on Plotly legend bg is the only translucent surface.

### Imagery vibe
If imagery is added later, keep it cool, flat, grainless, under-saturated — match the slate-cool palette. Preferred: chart screenshots, schematic diagrams, Mermaid-style flowcharts (the repo README uses blue `#dbeafe`, red `#fee2e2`, green `#dcfce7`, purple `#e9d5ff` flowchart fills).

### Scrollbars
Custom 6px, `#cbd5e1` thumb on `#f1f5f9` track — thin, visible, unfussy.

---

## Iconography

### Approach
**Hand-rolled inline SVG, slate-500 stroke, 1.6px stroke-width, round-cap/round-join, 14×14 viewBox.** The entire icon set lives in `ui/theme.py` as four constants: `ICON_PEAK`, `ICON_SCALE`, `ICON_MONEY`, `ICON_CLOCK`. Every icon in the UI is one of these four.

Key traits:
- Stroke, not fill. The one fill exception is the red dot (`#ef4444`) in `ICON_PEAK` that marks the peak point.
- Stroke color `#64748b` (fg3) so icons read as secondary chrome, not content.
- Always 14×14 inline next to KPI labels, never at large sizes, never as decoration.

### Unicode icons
The app uses Unicode glyphs liberally for small state markers where an SVG would be overkill:
- `●` (U+25CF) — complete step / active run
- `○` (U+25CB) — pending step
- `▸` (U+25B8) — next step
- `→` (U+2192) — modifier-chain composition arrow (`KnockOut → VanillaOption`)
- `◈` (U+25C8) — page icon / favicon (`st.set_page_config(page_icon="◈")`)
- `+` / `-` — button prefixes for "Add modifier" / "Remove last"

### No icon font, no emoji
- No FontAwesome, Lucide, Heroicons, Material Icons, Feather, Phosphor, etc. are imported. Don't add them.
- **No emoji anywhere.** The brand depends on it.
- Logos are copied into `assets/logo-mark.svg` (a reconstruction of the gradient-blue lozenge mark from the sidebar) and `assets/icons.svg` (the four KPI icons bundled as a symbol sprite).

### Substitution flag
None needed — the icon system is small enough to lift verbatim. The four SVG icons were copied directly from `ui/theme.py`; the four Unicode glyphs are standard code points.

---

## Fonts — substitution flag

The repo specifies **Inter** and **JetBrains Mono** via Google Fonts CDN (`https://fonts.googleapis.com/css2?...`). We inherit the same CDN import — no local `.ttf` or `.woff2` files needed for this system. If you want to ship offline, download Inter 400/500/600/700 and JetBrains Mono 400/500/600 and drop them into `fonts/`, then swap the `@import` in `colors_and_type.css` for `@font-face` rules.

---

## How to use this system

- **For a new HTML artifact**: link `colors_and_type.css`, use CSS variables from `:root`, follow the content rules above.
- **For a React recreation of a PFE surface**: start from `ui_kits/pfe_app/index.html` and reuse the JSX component modules there.
- **For Claude Code**: read `SKILL.md`.

## Caveats

- Streamlit's DOM is not the React DOM — when recreating, we preserve visual result, not exact HTML structure.
- No dark mode exists upstream. The design system is light-only by design.
- The "Dashboard mode" mentioned in the repo README (`ui/app.py` single-page version) is not recreated — all visual vocabulary is shared with the tabbed surface.
