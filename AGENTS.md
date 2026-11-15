# AGENTS.md

This file is the standing brief for future agent sessions. It copies the
mission, operating rules and non-negotiable rules from
`GonaSense_Agent_Implementation_Plan.md`, then adds the commands and traps
specific to this repository.

## Mission

Build **GonaSense**, a static web dashboard plus an offline Python data
pipeline. GonaSense helps a smallholder farmer or extension worker in Gombe
State, Nigeria, compare **at least three crop rotation strategies** (one of them
the user's existing rotation) using NASA satellite data, explains each
strategy, and leaves the final decision to humans.

Context: this is an entry for the NASA Space Apps Challenge 2026, challenge
"Field Shift: Adapting Farms with NASA Data". A small product that works end to
end beats a large one that is half finished.

The name stands for: *Gona* (Hausa for farm) + *Sense* (satellite sensing). The
logo is a wordmark plus a hoe with signal arcs.

## Operating rules

1. Work in the phases in section 15 of the plan, in order. After each phase run
   its checks, commit, and continue. Do not wait for approval between phases
   unless a STOP condition is hit.
2. Do not ask questions you can answer by making a reasonable choice. Make the
   choice, write it to `DECISIONS.md` (one line: decision, reason), and continue.
3. Never leave the repo in a broken state. `web/index.html` MUST open and render
   at every commit from Phase 2 onward.
4. Keep everything simple: no frontend framework, no build step, no backend, no
   database, no API keys in the browser.

## Non-negotiable rules

1. **Never invent data or citations.** Any crop threshold, score, coordinate or
   source you cannot derive from a file or API response MUST be marked
   provisional. Never write a fake reference.
2. **Synthetic data must always be labelled.** If the dashboard is showing
   synthetic data, a banner reading
   "DEMO DATA: synthetic, not real NASA observations" MUST be visible at the
   top of every view. The banner is driven by `data_mode` in `metrics.json`.
3. **Provisional values must be visibly tagged.** Any crop field whose
   `field_status` in `crops.json` is `estimate` or `derived`, and any crop with
   `"provisional": true`, must render with an "estimate" tag
   wherever it influences a displayed number.
4. **Show uncertainty as counts, never as a single precise prediction.** Write
   "12 of 24 seasons", not "50% chance".
5. **Scenario sliders are sensitivity tests, not forecasts.** Label them
   exactly: "Sensitivity test, not a forecast".
6. **Support, not replace.** Every strategy card carries this footer verbatim:
   "This is a decision aid. Your experience and your extension officer's advice
   come first."
7. **No browser storage APIs** (localStorage, sessionStorage, IndexedDB). Keep
   state in memory and in the URL hash only.
8. **Static only.** After the initial JSON fetch, the page makes no network
   requests (map tiles excepted).
9. **Relative URLs only** (`data/metrics.json`, never `/data/...`) so the site
   works under a GitHub Pages sub-path.
10. **Accessibility basics:** semantic HTML, labels on every control, visible
    focus states, WCAG AA contrast, never rely on colour alone, minimum 16 px
    body text, 44 px tap targets.
11. **Language:** plain English, short sentences, no jargon without a glossary
    link. All user-facing strings live in `web/js/strings.js`.

## Commands

```powershell
# Tests
.\.venv\Scripts\python.exe -m pytest -q
node --test "tests/*.test.mjs"      # NOT `node --test tests/` on Windows

# Real-data build from cached POWER CSVs (no network)
.\.venv\Scripts\python.exe -m pipeline.run_all --mode nasa

# Synthetic demo build
.\.venv\Scripts\python.exe -m pipeline.run_all --mode synthetic --refresh

# Local site (ES modules need HTTP)
python -m http.server 8080 --directory web
```

`python -m pipeline.run_all` writes all five JSON files and then validates the
contracts. `--refresh` regenerates synthetic data; nasa mode reuses
`raw/power_<id>.csv` and downloads only if a file is missing.

## Repository notes

- Keep the frozen JSON contracts in `web/data/` exactly as the plan defines
  them. The validator is the source of truth.
- `web/data/metrics.json` currently holds the real-data (`nasa`) build. Do not
  replace it with synthetic output for the final submission.
- `web/vendor/chart.umd.min.js` and `web/vendor/leaflet/` are committed; do not
  reintroduce CDN links.
- `raw/` is git-ignored except `.gitkeep`. The POWER CSVs live there; preserve
  them or re-download.
- The layout has three column wrappers (`.column-controls`, `.column-centre`,
  `.column-cards`). Mobile order is set with CSS `order`; desktop order uses
  grid areas. Do not go back to a single spanning cards cell.
- Browser caching can hide a rebuilt stylesheet or module. Use a hard reload or
  a fresh port while testing.
