# GonaSense

A static decision aid for rain-fed farmers in Gombe State, Nigeria. Pick your
local government area and current rotation, move the priority sliders, and see
climate-tested alternatives re-rank live. Every strategy card answers the same
five questions: why it was suggested, what the evidence is, what it could add,
what information is missing, and what needs local review.

Built for the **NASA Space Apps Challenge 2026 (Field Shift)**.

> **Status: build complete.** The site runs on real NASA POWER data for 11
> Gombe LGAs, 2001-2024. The demo banner is hidden in `nasa` mode. NDVI is the
> one missing input: no NDVI source was reachable, so the chart says so and
> scoring uses the documented 30% default. Crop thresholds remain provisional
> until a human verifies them. See `HUMAN_TODO.md`.

## What it does

- Compares the farmer's existing rotation with three alternatives.
- Scores each rotation on climate reliability, water demand, soil building,
  erosion cover, pest-cycle break and market income, weighted by the user's
  priorities.
- Shows evidence as counts of seasons, not a single probability: "in 21 of 24
  seasons, rainfall, dry spells and heat stayed within maize screening
  thresholds".
- Tests sensitivity to 20% less rain or 2 °C more heat, labelled as a test and
  not a forecast.
- States its limits: satellite estimates, one point per LGA, no ground
  stations, provisional crop thresholds.

## Live site

Pending. The deployed site is the contents of `web/` on GitHub Pages. Add the
URL here after enabling Pages (see `HUMAN_TODO.md`).

## Screenshots

Pending. Placeholder for:

- desktop three-column view
- 360 px mobile view
- a strategy card close-up

## Repository layout

```
gombe-rotation-advisor/
  pipeline/     offline Python: fetch, metrics, export, validate
  raw/          cached downloads, git-ignored
  web/          the deployed site (HTML, CSS, ES modules, JSON)
  docs/         requirements trace, method, sources, crop citations, QA
  tests/        pytest for the pipeline, node tests for scoring
  AGENTS.md     standing brief for future agent sessions
  DECISIONS.md  one-line decisions and reasons
  HUMAN_TODO.md what still needs a person
```

## Quick start

```powershell
# 1. Python dependencies
python -m venv .venv --system-site-packages
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

# 2. Real-data build from cached POWER CSVs (no network needed)
.\.venv\Scripts\python.exe -m pipeline.run_all --mode nasa

# 3. Or a labelled synthetic demo
.\.venv\Scripts\python.exe -m pipeline.run_all --mode synthetic --refresh

# 4. Tests
.\.venv\Scripts\python.exe -m pytest -q
node --test "tests/*.test.mjs"

# 5. Serve the site (ES modules need HTTP, not file://)
python -m http.server 8080 --directory web
# visit http://localhost:8080
```

Both `run_all` modes write all five JSON files into `web/data/` and then run
the contract validator. `--refresh` re-downloads POWER when network is
available; otherwise the cached `raw/power_<id>.csv` files are reused.

To refresh POWER explicitly:

```powershell
.\.venv\Scripts\python.exe -m pipeline.fetch_power
```

## Tests

- `pytest`: 30 passing. Covers onset, false starts, missing data, crop checks,
  scenario keys, harmonization, bare-share window and contract validation.
- `node --test "tests/*.test.mjs"`: 8 passing. Covers the scoring formula,
  scenario-key parity with Python, NDVI fallback, ranking and traffic lights.
- `docs/QA.md` records the manual UI checks: 360 px layout, control updates,
  no post-load network, accessibility audit and graceful degradation.

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

Onset, crop windows, counts and the scoring formula are in
[`docs/method.md`](docs/method.md). In short:

- Onset is the end of the first 3-day total of at least 20 mm that is not
  followed by a 7-day dry spell, searched from 1 April to 31 October.
- A crop passes a year when season rain, the longest dry spell during
  flowering, and heat days during flowering all stay inside its screening
  thresholds.
- Reliability is the share of **all** years in which all three pass, with years
  that never had an onset counted as failures.
- The web page scores rotations with weights from the priority sliders.

## Limitations and uncertainty

- NASA POWER is a modelled product, not a weather station. Every location is
  labelled "Medium (single source)" until a second rainfall source is added.
- POWER's grid is coarser than an LGA, so some neighbouring LGAs share an
  identical modelled series: Akko/Billiri/Kaltungo, Funakaye/Nafada, and
  Gombe/Kwami/Yamaltu-Deba. This is stated in the limits panel.
- One centroid represents a whole LGA; soil, slope and variety vary within it.
- NDVI is not available in this build, so `bare_share` is `null` and scoring
  uses the neutral 0.30 default with a visible note. The NDVI chart is hidden,
  not fabricated.
- Crop values are provisional (`"provisional": true`). Each field carries a
  `field_status` of confirmed, derived or estimate, and the cards tag every
  scored criterion and evidence line that depends on a non-confirmed field.
- Scenario pass rates can move when scaled rain shifts the detected onset. They
  are sensitivity tests, not forecasts.
- No ground stations were used. Rain gauges, soil tests and NiMet records would
  let us validate onset dates and crop limits locally.
- This is a decision aid. Farmers' experience and extension officers' advice
  come first.

## Where local expertise is required

- Confirming crop cycle lengths, water needs, dry-spell tolerance and heat
  thresholds for Gombe varieties.
- Confirming the onset definition used by local extension services.
- Reviewing the benefits, gaps and risks on strategies B, C and D.
- Checking onset dates against NiMet bulletins and farmer recollection.
- Advising on security and access conditions in parts of the north-east.

## Credits

- NASA POWER (NASA Langley Research Center), accessed 2026-11-14.
- geoBoundaries gbOpen NGA ADM2, GRID3 (2022), CC BY 4.0.
- GADM v4.1, used for state masking only.
- Chart.js 4.4.7 and Leaflet 1.9.4, vendored.
- OpenStreetMap contributors for map tiles.

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
