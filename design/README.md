# PFE-v2 Design System

Visual reference for the Clean Finance Light theme used by the Streamlit app.

- **`preview/`** — live HTML/React mock of every screen (Dashboard, Market Data, Portfolio, Config, Results). Open `preview/index.html` in any browser, or view online via GitHub Pages at `https://leeduoduo211.github.io/PFE-v2/preview/`.
- **`tokens.md`** — the canonical color, type, and spacing tokens. Source of truth for `ui/theme.py`.

## When to edit what

| If you're changing…                              | Edit…                                  |
| ------------------------------------------------ | -------------------------------------- |
| A color, font size, or spacing value used at runtime | `ui/theme.py` → then update `design/tokens.md` |
| The visual spec only (not shipped code)          | `design/tokens.md` + `design/preview/` |
| A screen layout mock                              | `design/preview/*.jsx`                 |

The mock is a **reference**, not a dependency — Streamlit never loads it.
