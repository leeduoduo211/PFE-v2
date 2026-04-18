# Design Tokens

Source of truth for `ui/theme.py`. Any value used in production Python code must appear here.

## Color

### Surfaces
| Token           | Hex       | Use                                |
| --------------- | --------- | ---------------------------------- |
| `bg_page`       | `#f8fafc` | App background (slate-50)          |
| `bg_card`       | `#ffffff` | Cards, KPIs, inputs, sidebar       |
| `bg_surface`    | `#f1f5f9` | Recessed regions, toggle track     |
| `bg_hover`      | `#f8fafc` | Row hover                          |
| `border`        | `#e2e8f0` | All 1px borders                    |
| `border_strong` | `#cbd5e1` | Hover border                       |
| `border_focus`  | `#3b82f6` | Input focus ring                   |

### Text
| Token             | Hex       | Use                           |
| ----------------- | --------- | ----------------------------- |
| `text_primary`    | `#1e293b` | Headings, KPI values          |
| `text_body`       | `#475569` | Body copy, secondary buttons  |
| `text_secondary`  | `#64748b` | Chart labels, table headers   |
| `text_muted`      | `#94a3b8` | Subtitles, tab labels         |

### Semantic
| Token    | Hex       | Use                                |
| -------- | --------- | ---------------------------------- |
| `blue`   | `#3b82f6` | Primary action, EPE trace, accent  |
| `red`    | `#ef4444` | PFE trace, danger, loss            |
| `green`  | `#22c55e` | Gain, long tag, success            |
| `amber`  | `#f59e0b` | Median trace, warning, barrier mod |
| `purple` | `#8b5cf6` | Structural modifier                |
| `cyan`   | `#06b6d4` | 6th colorway slot                  |

### Product categories
| Kind              | Hex       |
| ----------------- | --------- |
| European          | `#2563eb` |
| Path-dependent    | `#d97706` |
| Multi-asset       | `#be185d` |
| Periodic          | `#7c3aed` |

## Type
- **Inter** 400/500/600/700 — UI.
- **JetBrains Mono** 400/500/600 — all numbers (`font-variant-numeric: tabular-nums`).

Ramp (used in mocks; Streamlit stMetric uses two of these):

| Role         | Size     | Weight | Font   |
| ------------ | -------- | ------ | ------ |
| Section lbl  | 10.4px   | 600    | Inter  |
| Body / input | 12–13px  | 400–500| Inter  |
| KPI label    | 9.9px UC | 600    | Inter  |
| KPI value    | 24px     | 700    | Mono   |
| H3 / card    | 14px     | 600    | Inter  |
| H2 / tab ttl | 17px     | 600    | Inter  |

## Spacing & radius
- Base unit: 4px. Common: `8 · 12 · 16 · 24`.
- Radii: `4px` (badges) · `6px` (inputs) · `7px` (buttons) · `10px` (cards, KPIs).
- Shadow: `0 1px 3px rgba(0,0,0,0.04)` on all cards.

## Chart palette (Plotly)
- PFE: `#ef4444` line + `rgba(239,68,68,0.10)` fill
- EPE: `#3b82f6` line + `rgba(59,130,246,0.10)` fill
- Median: `#f59e0b`
- Per-trade colorway: `#3b82f6 · #ef4444 · #22c55e · #f59e0b · #8b5cf6 · #06b6d4 · #ec4899 · #14b8a6 · #f97316 · #a855f7`
- Grid: `#f1f5f9`. Axes: `#e2e8f0`. Tick labels: `#94a3b8`.
