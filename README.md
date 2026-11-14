# Gombe Rotation Advisor

A no-server decision aid for rain-fed farmers in Gombe State, Nigeria. Pick
your local government area and your current rotation, move the priority
sliders, and see climate-tested alternatives re-rank live. Every strategy
card answers the same five questions: why it was suggested, what the evidence
is, what it could add, what information is missing, and what needs local
review.

Built for the **NASA Space Apps Challenge 2026 (Field Shift)**.

> **Status: Phase 0 complete.** The repository, data contracts, POWER fetcher
> and front-end shell are in place. `web/data/metrics.json` is currently
> synthetic mock data with the final shape, so the front end can be built in
> parallel with the metrics pipeline. Do not read its numbers as findings yet.

## Problem

Smallholder farmers in Gombe start the season on a guess. The rains arrive
late or stall after a false start, soils are losing fertility under
continuous cereal cropping, and the advice available often assumes a season
that no longer looks like the last 24. A rotation that ignores dry spells,
heat during flowering, or soil nitrogen can fail even in a "normal" year.

## What it does

- Compares a farmer's existing rotation with three or more alternatives.
- Scores each rotation on climate reliability, water demand, soil building,
  erosion cover, pest-cycle break and market income, weighted by the user's
  own priorities.
- Shows the evidence as counts of seasons, not just a score: "in 12 of 24
  seasons, rainfall, dry spells and heat all stayed within maize limits".
- Tests sensitivity to 20% less rain or 2 °C more heat, clearly labelled as a
  test and not a forecast.
- States its limits: satellite estimates, one point per LGA, no ground
  stations, crop thresholds still awaiting local review.

## Live site

Pending. The deployed site will be the contents of `web/` on GitHub Pages.

## Repository layout

```
gombe-rotation-advisor/
  pipeline/     offline Python: fetch, metrics, export, validate
  raw/          cached downloads, git-ignored
  web/          the deployed site (HTML, CSS, ES modules, JSON)
  docs/         sources, method, crop table citations
  tests/        pytest for the pipeline, node tests for scoring
  README.md
```

## Quick start

```powershell
# 1. Python dependencies
pip install -r requirements.txt

# 2. Download POWER data for one LGA (all LGAs if you omit --locations)
python pipeline/fetch_power.py --locations gombe

# 3. Check the exported JSON contracts
python pipeline/validate.py

# 4. JavaScript scoring tests
npm test

# 5. Open the site (a local server is needed for ES modules)
python -m http.server 8080 --directory web
# then visit http://localhost:8080
```

`python pipeline/fetch_power.py` without arguments downloads all 11 LGAs,
pausing between calls, and caches each response in `raw/power_<id>.csv`.
Later runs reuse the cache; pass `--force` to refresh.

Phase 2 commands (`python pipeline/metrics.py`, `python pipeline/export_json.py`)
are stubs until the metrics core lands.

## Data sources

| Dataset | Product / version | Period | Use |
| --- | --- | --- | --- |
| NASA POWER | Daily point API, community `AG` | 2001-2024 | Rain, Tmax, Tmin, root-zone wetness |
| geoBoundaries | NGA ADM2, gbOpen, GRID3 (2022) | 2022 boundary | LGA centroids |
| GADM | NGA level 2, v4.1 | 2022 boundary | State mask to exclude border LGAs |
| GPM IMERG | Final Run daily | optional | Rain cross-check and confidence |
| SMAP | SPL3SMP | optional | Surface soil moisture |
| MODIS | MOD13Q1 16-day NDVI via AppEEARS | optional | Bare-field share |

Details, access dates and licences: [`docs/sources.md`](docs/sources.md).

## Method

Onset, crop windows, counts and the scoring formula are written up in
[`docs/method.md`](docs/method.md). In short:

- Onset is the first 3-day total of at least 20 mm that is not followed by a
  7-day dry spell, searched from 1 April to 31 October.
- A crop passes a year when season rain, the longest dry spell and heat days
  during flowering all stay inside its limits.
- Reliability is the share of **all** years in which all three pass, with
  years that never had an onset counted as failures.
- The web page scores rotations with weights from the priority sliders.

## Limitations and uncertainty

- NASA POWER is a modelled product, not a weather station. Every location is
  labelled "Medium (single source)" until IMERG is added.
- One centroid represents a whole LGA; soil, slope and variety vary within it.
- Crop thresholds marked `"verify"` are literature-based estimates awaiting
  local expert review. The page must show that tag.
- Scenarios are sensitivity tests, not forecasts.
- This is a decision aid. Farmers' experience and extension officers' advice
  come first.

## Team

_(Fill in names, roles and affiliations before submission.)_

## AI-use disclosure

_(Complete if the challenge requires it. Record which tools were used for
code, copy and analysis, and what was reviewed by a human.)_

## Licence

- Code: MIT.
- Written content and figures: CC BY 4.0.
- Data: follow each provider's licence (POWER: open; geoBoundaries/GRID3:
  CC BY 4.0; GADM: non-commercial; NASA satellite products: open).
