# Polla World Cup 2026 — Prediction Model

A statistical model for the **Polla World Cup 2026** prediction pool (~415 entrants, winner-take-most).
Built to optimize **expected value against the contest scoring + the field**, not just to pick likely winners.

**▶ Live report:** https://simonro.github.io/polla2026/

## Method
- **Strength:** current World Football **Elo**, blended with a **Massey common-opponent** rating and the
  **betting market** (the 3-source model). Calibrated on **5,651 internationals since 2021** (through 2026-06-07).
- **Scorelines:** **Dixon-Coles** bivariate-Poisson per match (Belgium 1.61 xG, etc.).
- **Tournament:** **Monte Carlo** (30k sims) over the *real* verified 2026 bracket
  (12 groups of 4 → top 2 + 8 best thirds → R32 → Final).
- **Injuries:** documented Elo adjustments from the ESPN tracker (2026-06-06) — Brazil gutted, etc.
- **Field model:** casual champion-pick distribution for this **Miami / NY / Bogotá (Latino-heavy) pool**,
  which over-picks Argentina / Brazil / Colombia / Mexico — the core leverage edge.

All foundational data was read from raw page text or parsed by code — no trusted LLM extraction
(a hallucinated FIFA-page draw was caught and discarded; the draw was verified verbatim vs Wikipedia).

## Three entries (distinct champions, to cover the prize space)
| Entry | Champion | Idea |
|---|---|---|
| A | **England** | European value, wins the right half |
| B | **France** | contrarian + Portugal pushed to the semis |
| C | **Spain** | 3-source best model — **2.6× field leverage** (best single entry) |

All three **fade Brazil** (2.7% to win, but ~13% of this field picks it → 0.21× leverage).

## Files
- `index.html` — the interactive report (bracket tracker, group grids, edge panel).
- `output/entry_A.csv` / `entry_B.csv` / `entry_C.csv` — copy-down sheets for manual entry.
- `engine.py` → `blend.py` → `picks.py` → `make_infographic.py` → `make_csv.py` — the pipeline.
- `data/` — verified draw, current Elo, results, fixtures, market odds, injury adjustments.

*Not betting advice. Built with Claude Code.*
