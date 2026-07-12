# Product

## Register

product

> The public landing page (`/`) is a **brand**-register surface; every authenticated screen
> (`/signup`, `/login`, `/dashboard`) is **product**. The default register is product because
> the app is the core deliverable and the landing exists to funnel into it.

## Users

Two audiences on one platform (Insight Forge — an AI decision-intelligence backend for the
education sector):

- **Prospects** land on `/` deciding whether this tool is worth signing up for. Context:
  evaluating quickly, skimming, comparing to spreadsheets and BI tools they already tolerate.
- **Institution operators** (Admins, Deans, Faculty) inside the app. Context: they have a CSV
  of student/academic data and want it turned into a decision — risk cohorts, KPIs, recommended
  actions — without writing SQL or waiting on a data team. Primary task per screen: upload data,
  read the report, act.

## Product Purpose

Turn a raw educational dataset into decisions. A user uploads a CSV/JSON; the backend's
deterministic multi-agent pipeline (Data Engineer → Analyst → Business Analyst → Executive
Report) profiles it, computes real statistics, and returns KPIs, insights, anomalies, ranked
recommendations, and a health score. The frontend's job: make that upload → analyze → decide
loop feel fast, legible, and trustworthy. Success = a user uploads and understands what to do
next within one screen, without a manual.

## Brand Personality

Precise, calm, and quietly confident — a high-precision instrument, not a hype machine.
Monochrome-utility voice (Linear / Vercel / Cal.com lane): the data is the color. Three words:
**disciplined, legible, unshowy**. It should feel like a tool an operator trusts, where nothing
is decorative and every number is defensible.

## Anti-references

- Generic "AI SaaS" landing pages: gradient-mesh heroes, glassmorphism, purple-to-pink gradients,
  the big-number/hero-metric template repeated down the page.
- Rainbow BI dashboards where every chart is a different saturated hue and color means nothing.
- The mock the old frontend shipped: fake "Corporate Health Index / C-Suite" corporate cosplay
  and a hardcoded auth token. Removed entirely.

## Design Principles

- **The data is the color.** UI stays monochrome (ink/graphite/slate/paper); the single Action
  Blue and chart marks are the only saturated elements, reserved for meaning and state.
- **Show the real pipeline.** Every number on screen traces to a real backend field
  (health_score, KPIs, insights, recommendations) — no invented metrics, no placeholder charts.
- **Motion conveys, never decorates.** Landing motion choreographs the story once on load/scroll;
  app motion is fast (150–250ms) and only signals state (upload progress, chart draw, reveal).
- **Earned familiarity in the app.** Standard affordances — top nav, forms, dropzone, cards used
  only where they're the right container. The tool disappears into the task.
- **One loop, obvious.** Upload → analyze → decide is the spine of the app; the dashboard makes
  the next action unmistakable.

## Accessibility & Inclusion

- WCAG 2.1 AA. Body text ≥4.5:1 on paper/white (use Graphite `#242424`, never light gray for
  body). Chart marks carry non-color encodings (labels, position, shape), not hue alone.
- Full `prefers-reduced-motion` alternatives on every animation (line-draw, reveals, count-ups
  become instant/crossfade).
- Keyboard-operable auth forms and dropzone; visible focus rings; inputs 8px radius with clear
  states (default/focus/error).

## Visual System

See `design.md` (Cal.com monochrome reference) at the project root — it is the committed
DESIGN.md for this project. Tokens: Paper `#f4f4f4` page, White cards, Graphite text, Ink CTAs,
Silver borders, Action Blue `#0099ff` accent; Cal Sans (Poppins substitute) headings + Inter
body; pill CTAs, 12px cards, subtle diffuse shadows, no card borders, no gradients.
