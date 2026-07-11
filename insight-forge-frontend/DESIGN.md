# Design

Visual system for the Insight Forge frontend. Register: **product** (dashboards, admin, tools — design serves the data).

## Direction

Off-white editorial workspace. Calm paper background, deep ink text, one confident
accent, and semantic status colors for academic risk. Reads as a considered
institutional tool — not a dark glassmorphic SaaS template.

Deliberately avoided (the "AI made this" tells that were in the old build):
gradient text, glassmorphism/blur cards, cyan→indigo gradients, dark radial hero.

## Color (OKLCH tokens — see `globals.css :root`)

- `--bg` cool paper off-white (near chroma 0, not cream/sand)
- `--surface` / `--surface-2` white cards, subtle raised fills
- `--ink` deep near-black text · `--ink-soft` secondary · `--muted` tertiary (all ≥4.5:1 on paper)
- `--border` hairline · `--border-strong` dividers
- `--brand` deep teal-blue (primary, sparing) · `--brand-ink` text-safe brand
- `--accent` warm amber (rare highlight / focus energy)
- Status: `--safe` green · `--warn` amber · `--critical` rose — used for risk tiers and KPIs

## Type

- Display / brand / page titles / big numbers: **Fraunces** (serif, optical size) — carries the editorial, human character.
- UI / body / tables / labels: **Inter** (sans) in 400/500/600/700.
- Never gradient-filled. Emphasis via weight, size, and the serif.

## Surfaces & shape

- Cards: solid `--surface`, `1px --border`, soft low-opacity shadow, radius 14px. No blur.
- Hairline dividers, generous padding, varied vertical rhythm.
- Status badges: tinted background of the status hue + darker text of the same hue (no side-stripes).

## Motion

- Ease-out (quart/expo), 160–260ms. Subtle lifts on hover, staggered list reveals.
- Full `prefers-reduced-motion` fallbacks (crossfade/instant).

## Accessibility

- Body text ≥4.5:1, large text ≥3:1. Visible focus ring (`--accent`).
- Status never encoded by color alone (label + color).
