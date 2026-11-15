# GonaSense: Agent Implementation Plan

**Audience: a coding agent.** Read this whole file before writing any code. It is your build specification. Follow it literally. Where it says MUST, there is no discretion.

---

## 0. Mission

Build **GonaSense**, a static web dashboard plus an offline Python data pipeline. GonaSense helps a smallholder farmer or extension worker in Gombe State, Nigeria, compare **at least three crop rotation strategies** (one of them the user's existing rotation) using NASA satellite data, explains each strategy, and leaves the final decision to humans.

Context: this is an entry for the NASA Space Apps Challenge 2026, challenge "Field Shift: Adapting Farms with NASA Data". Judges score against the challenge requirements in section 1. A small product that works end to end beats a large one that is half finished.

The name stands for: *Gona* (Hausa for farm) + *Sense* (satellite sensing). The logo is a wordmark plus a hoe with signal arcs (SVG in section 13).

### Operating rules

1. Work in the phases in section 15, in order. After each phase run its checks, commit, and continue. Do not wait for approval between phases unless a STOP condition in section 15 is hit.
2. Do not ask questions you can answer by making a reasonable choice. Make the choice, write it to `DECISIONS.md` (one line: decision, reason), and continue.
3. Never leave the repo in a broken state. `web/index.html` MUST open and render at every commit from Phase 2 onward.
4. Keep everything simple: no frontend framework, no build step, no backend, no database, no API keys in the browser.

---

## 1. Requirements the product must satisfy (acceptance checklist)

Create `docs/REQUIREMENTS_TRACE.md` as a table mapping each row to the file and function that satisfies it. Mark each row DONE only when you have verified it in the running page.

| ID | Requirement | Where it is satisfied |
| --- | --- | --- |
| R1 | Combine NASA data with local agricultural information (crop knowledge table) in a decision-support tool | pipeline + `crops.json` + dashboard |
| R2 | Compare at least three rotation strategies, including the farmer's existing one | strategy cards |
| R3 | Each strategy card has five labelled sections: Why suggested, Evidence, Benefits, Information gaps, Risks needing local review | `ui.js` cards |
| R4 | Farmer can enter priorities or constraints, and the ranking changes live | six priority sliders |
| R5 | Uncertainty is explained: results as counts of past years, confidence label per location, data-limits panel, "ask a local expert" lines | cards + limits panel |
| R6 | Satellite versus ground data is explained, including that no ground stations were used | limits panel |
| R7 | Datasets of different resolution are harmonized to one grid (location x 10-day period) | `pipeline/harmonize.py` |
| R8 | Bare-field periods and seasonal vulnerability are highlighted | NDVI chart with shaded periods |
| R9 | Interpretable by farmers with limited technical experience: plain language, traffic-light scores, glossary | UI copy |
| R10 | Visible message on every card that the tool supports, not replaces, farmer judgment | card footer |
| R11 | Optional: map, timeline, scenario sliders | Leaflet map, onset chart, rain/temp sensitivity sliders |

---

## 2. Non-negotiable rules

1. **Never invent data or citations.** Any crop threshold, score, coordinate or source you cannot derive from a file or API response MUST be marked provisional (see 2.2). Never write a fake reference.
2. **Synthetic data must always be labelled.** If the dashboard is showing synthetic data, a banner reading "DEMO DATA: synthetic, not real NASA observations" MUST be visible at the top of every view. The banner is driven by `data_mode` in `metrics.json` (`"synthetic"` or `"nasa"`).
3. **Provisional values must be visibly tagged.** Any value with `"provisional": true` in `crops.json` renders with a small "unverified estimate" tag wherever it influences a displayed number.
4. **Show uncertainty as counts, never as a single precise prediction.** Write "12 of 24 seasons", not "50% chance".
5. **Scenario sliders are sensitivity tests, not forecasts.** Label them exactly: "Sensitivity test, not a forecast".
6. **Support, not replace.** Every strategy card carries this footer verbatim: "This is a decision aid. Your experience and your extension officer's advice come first."
7. **No browser storage APIs** (localStorage, sessionStorage, IndexedDB). Keep state in memory and in the URL hash only.
8. **Static only.** After the initial JSON fetch, the page makes no network requests (map tiles excepted, see 12.5).
9. **Relative URLs only** (`data/metrics.json`, never `/data/...`) so the site works under a GitHub Pages sub-path.
10. **Accessibility basics:** semantic HTML, labels on every control, visible focus states, text contrast at WCAG AA, never rely on colour alone, minimum 16 px body text, 44 px tap targets.
11. **Language:** plain English, short sentences, no jargon without a glossary link. All user-facing strings live in `web/js/strings.js` so another language can be added later.

---

## 3. Tech stack

| Layer | Choice |
| --- | --- |
| Pipeline | Python 3.11+, `pandas`, `numpy`, `requests`, `pytest`. Optional: `earthaccess`, `geopandas`, `shapely`, `pyarrow` |
| Front end | Plain HTML, CSS, ES modules. Leaflet 1.9.x for the map. Chart.js 4.x for charts. Vendor both into `web/vendor/` (download once, commit the files) |
| Tests | `pytest` for the pipeline, Node built-in test runner (`node --test`) for `scoring.js` |
| Hosting | GitHub Pages serving `web/`, deployed by a GitHub Actions workflow |

---

## 4. Repository layout (create exactly this)

```
gonasense/
  README.md
  AGENTS.md                  # copy of section 0 and section 2 for future agent sessions
  DECISIONS.md
  HUMAN_TODO.md              # see section 16
  .gitignore                 # raw/, __pycache__/, .venv/, node_modules/
  .github/workflows/pages.yml
  pipeline/
    __init__.py
    config.py
    locations.py
    fetch_power.py
    fetch_imerg.py           # optional, graceful if no credentials
    fetch_smap.py            # optional
    fetch_ndvi.py            # optional (AppEEARS CSV reader)
    synth.py                 # synthetic data generator
    harmonize.py
    metrics.py
    export_json.py
    validate.py
    run_all.py               # CLI: --mode synthetic|nasa
  raw/                       # downloaded or generated source files, git-ignored
  web/
    index.html
    css/style.css
    js/ main.js state.js data.js scoring.js text.js charts.js map.js ui.js strings.js
    data/ locations.json crops.json strategies.json metrics.json glossary.json
    img/ logo.svg favicon.svg
    vendor/ leaflet/ chart.umd.min.js
  docs/
    REQUIREMENTS_TRACE.md
    method.md                # plain description of every metric and threshold
    sources.md               # every data source, product, version, date range
    crop_table_sources.md    # one row per crop value: value, source, status
  tests/
    test_onset.py test_metrics.py test_validate.py scoring.test.mjs
```

---

## 5. Data modes

The pipeline MUST support two modes selected by `python -m pipeline.run_all --mode synthetic|nasa`.

- **`synthetic` (build this first).** `synth.py` generates a realistic daily weather series for each location so the whole product runs end to end with no network and no credentials. Output files are identical in shape to nasa mode and carry `"data_mode": "synthetic"`. This is the default so the project always runs.
- **`nasa` (real data).** `fetch_power.py` downloads NASA POWER. IMERG, SMAP and NDVI are optional add-ons that are used only when their raw files exist in `raw/`. If a fetcher cannot run (no network, no credentials, service error), log a clear warning, skip it, and continue with what is available. Never crash the whole run for an optional source. Output carries `"data_mode": "nasa"` and a `sources_used` list.

### 5.1 Synthetic generator requirements (`synth.py`)

- Fixed random seed per location so output is reproducible.
- Years 2001 to 2024, daily, columns `T2M_MAX, T2M_MIN, PRECTOTCORR, GWETROOT` (the same names POWER uses).
- Rain: dry season Nov to Mar near zero; a monsoon season with onset that varies by year (roughly late April to early June), wet-day frequency rising to a peak in August, occasional dry spells of 5 to 15 days inside the season, gamma-distributed wet-day amounts. A few years MUST have a false start and a few MUST have a late onset, so the onset logic is exercised.
- Tmax: seasonal curve with a hot peak around March to May (about 38 to 40 C) and cooler wet season (about 30 to 33 C), plus noise. Tmin follows.
- GWETROOT: 0 to 1, driven by a decaying sum of recent rain.
- Synthetic NDVI per dekad: low in the dry season, rising after onset, peaking Aug to Sep.
- Add small per-location offsets so locations differ.
- Write a header comment stating the output is fake and must never be presented as observations.

---

## 6. Configuration (`pipeline/config.py`)

All tunables live here. No magic numbers elsewhere.

```python
YEARS = (2001, 2024)
DATA_DIR = "web/data"
RAW_DIR = "raw"

ONSET = dict(amount_mm=20.0, window_days=3, dry_days=7, lookahead_days=30,
             earliest="04-01", latest="10-31")   # PROVISIONAL: confirm and cite a West African onset definition
DRY_DAY_MM = 1.0
MAX_MISSING_FRAC = 0.05          # years with more missing rain than this in the search window are excluded
RAIN_MULTS = [0.8, 0.9, 1.0, 1.1]
TEMP_DELTAS = [0, 1, 2]          # degrees C added to Tmax and Tmin
NDVI_BARE_THRESHOLD = 0.25       # PROVISIONAL: tune from data
BARE_SEASON = ("04-01", "11-30") # window for bare_share
DEFAULT_BARE_SHARE = 0.30        # used only if NDVI is missing; UI must note this
```

Scenario key format (use everywhere): `f"rain{pct:+d}_temp{dt:+d}"` where `pct = round((mult - 1) * 100)`. Examples: `rain+0_temp+0` (the base case), `rain-10_temp+1`. Also write `"base"` as an alias in the exported JSON for the base case.

---

## 7. Locations (`pipeline/locations.py`)

Target 6 to 8 Local Government Areas (LGAs) of Gombe State, one point per LGA.

1. First try to build centroids from a boundary file: download Nigeria admin level 2 boundaries (geoBoundaries `NGA` ADM2 or GADM), filter to Gombe State, compute `geometry.centroid` with geopandas. Record the source and URL in `docs/sources.md`.
2. If that fails (no network or no geopandas), use the fallback seed below and set `"coords_status": "approximate seed, replace with boundary centroids"` on each location.

```python
FALLBACK_LOCATIONS = {
  "gombe":   ("Gombe",    10.29, 11.17),
  "akko":    ("Akko",     10.28, 10.95),
  "kaltungo":("Kaltungo",  9.81, 11.31),
  "dukku":   ("Dukku",    10.82, 10.77),
  "nafada":  ("Nafada",   11.10, 11.33),
  "kwami":   ("Kwami",    10.45, 10.97),
}
```

These coordinates are approximate and MUST be flagged as such. Never present them as surveyed.

---

## 8. Pipeline specification

### 8.1 `fetch_power.py`

- Endpoint: `https://power.larc.nasa.gov/api/temporal/daily/point`
- Parameters: `parameters=T2M_MAX,T2M_MIN,PRECTOTCORR,GWETROOT`, `community=AG`, `latitude`, `longitude`, `start=YYYYMMDD`, `end=YYYYMMDD`, `format=JSON`.
- Parse `response["properties"]["parameter"]` into a DataFrame indexed by date. Replace `-999` with NaN.
- One request per location for the whole period. Sleep 1 to 2 s between requests. Retry up to 3 times with backoff. Timeout 120 s.
- Cache to `raw/power_<id>.csv`. Skip download if the file exists unless `--refresh` is passed.
- After loading, log the missing-value share per variable and warn above 2 percent.
- Before relying on parameter names, read the POWER API documentation response or error message; if a parameter is rejected, report it in the log and in `HUMAN_TODO.md` instead of guessing.

### 8.2 Optional fetchers

- `fetch_imerg.py`: if `earthaccess` is installed and Earthdata credentials exist (env `EARTHDATA_USERNAME` and `EARTHDATA_PASSWORD`, or `~/.netrc`), download the daily GPM IMERG Final precipitation for a small box around each location and write `raw/imerg_<id>.csv` with `date,rain_mm`. Otherwise print "IMERG skipped: no credentials" and return.
- `fetch_smap.py`: same pattern, surface soil moisture, writes `raw/smap_<id>.csv` with `date,sm`. Record starts around 2015.
- `fetch_ndvi.py`: do not call AppEEARS automatically. Read user-supplied CSVs at `raw/ndvi_<id>.csv` with columns `date,ndvi` (the human exports these from AppEEARS). If absent, skip silently and use the default bare share.
- Every optional fetcher MUST be importable and runnable without its optional dependency installed (guard imports).

### 8.3 `harmonize.py` (requirement R7)

- Define the dekad: days 1 to 10, 11 to 20, and 21 to end of month, giving 36 per year. Provide `dekad_index(date) -> int (1..36)`.
- Sum rain, average temperature and soil series per dekad. Interpolate 16-day NDVI to daily, then average per dekad.
- Output a tidy table keyed by `(location, year, dekad)`. Persist as `raw/harmonized_<id>.csv`. The cross-dataset comparison and the `ndvi_dekad` series are built from it.

### 8.4 `metrics.py`

Implement exactly the logic below. Write the unit tests in section 14 alongside it.

```python
def longest_run(mask) -> int:
    best = cur = 0
    for v in mask:
        cur = cur + 1 if bool(v) else 0
        best = max(best, cur)
    return best

def find_onset(rain: "pd.Series", year: int, cfg) -> tuple["pd.Timestamp | None", str]:
    """Return (onset_date, status). status is 'ok', 'no_onset' or 'bad_data'."""
    r = rain[f"{year}-{cfg['earliest']}":f"{year}-{cfg['latest']}"]
    if len(r) == 0 or r.isna().mean() > MAX_MISSING_FRAC:
        return None, "bad_data"
    roll = r.rolling(cfg["window_days"], min_periods=cfg["window_days"]).sum()
    for d in roll.index:
        if roll[d] >= cfg["amount_mm"]:           # NaN compares False
            nxt = r[d + pd.Timedelta(days=1): d + pd.Timedelta(days=cfg["lookahead_days"])]
            if longest_run((nxt < DRY_DAY_MM).fillna(False)) <= cfg["dry_days"]:
                return d, "ok"
    return None, "no_onset"
```

Semantics: `bad_data` years are excluded from every count (they reduce `n_total`). `no_onset` years COUNT as failed seasons for every crop (they stay in `n_total` and contribute zero passes). This prevents reliability from being overstated.

Per crop, per year (full daily frame `df` is used so windows may extend into the next calendar year; truncate at the end of the data and note it in `docs/method.md`):

```python
def crop_year(df, onset, crop):
    cyc = int(crop["cycle_days"])
    end = onset + pd.Timedelta(days=cyc)
    w = df.loc[onset:end]
    f0 = onset + pd.Timedelta(days=round(crop["flower_frac"][0] * cyc))
    f1 = onset + pd.Timedelta(days=round(crop["flower_frac"][1] * cyc))
    fl = df.loc[f0:f1]
    rain = float(w["PRECTOTCORR"].sum())
    dry = longest_run(w["PRECTOTCORR"] < DRY_DAY_MM)
    heat = int((fl["T2M_MAX"] > crop["heat_threshold_c"]).sum())
    return dict(rain_ok=rain >= crop["min_rain_mm"],
                dry_ok=dry <= crop["dry_tolerance_days"],
                heat_ok=heat <= crop["heat_days_limit"])
```

Aggregation per location, scenario and crop into **counts**:

`{"rain_ok": int, "dry_ok": int, "heat_ok": int, "all_ok": int, "n_total": int}` where `all_ok` counts years in which all three pass in the same year, and a `no_onset` year adds 0 to every count but 1 to `n_total`.

Scenarios: for every combination in `RAIN_MULTS x TEMP_DELTAS`, copy the daily frame, multiply `PRECTOTCORR` by the multiplier, add the delta to `T2M_MAX` and `T2M_MIN`, rerun onset detection and every crop. Onset may shift under scaled rain; that is expected.

Per location also compute:

- `onset_by_year`: day-of-year integer per year (omit `no_onset`/`bad_data` years, and list them under `no_onset_years` and `bad_data_years`).
- `ndvi_dekad`: 36 values (mean NDVI per dekad across years) or `null` if NDVI is unavailable.
- `bare_flags`: 36 booleans, true where `ndvi_dekad < NDVI_BARE_THRESHOLD` (all false and `bare_share` null if NDVI unavailable).
- `bare_share`: share of dekads inside `BARE_SEASON` that are flagged bare, or `null`.
- `confidence`: see 8.5.

### 8.5 Confidence label per location

- If IMERG exists: compute the correlation across years between POWER and IMERG seasonal rainfall totals over the main rainy season.
  - `High`: correlation >= 0.7 and at least 15 usable years.
  - `Medium`: correlation from 0.4 to below 0.7.
  - `Low`: correlation below 0.4, or fewer than 10 usable years.
- If IMERG does not exist: `Medium (single source)`.
- In synthetic mode: `Not applicable (demo data)`.
Write the label and a one-sentence `confidence_reason` to `metrics.json`. Document the rule in `docs/method.md` as a heuristic.

### 8.6 `export_json.py` and `validate.py`

`export_json.py` writes `web/data/*.json` (shapes in section 9). `validate.py` runs automatically at the end of `run_all.py` and exits non-zero on any failure. It MUST check:

- every crop referenced in `strategies.json` exists in `crops.json`
- every location has every scenario key (12 keys plus the `base` alias)
- every count satisfies `0 <= x <= n_total` and `all_ok <= min(rain_ok, dry_ok, heat_ok)`
- no NaN or Infinity anywhere in any JSON
- `ndvi_dekad` and `bare_flags` have length 36 when present
- `data_mode` is `synthetic` or `nasa`
- total size of `web/data/` is under 5 MB

---

## 9. JSON contracts (frozen: do not change shapes without writing a line in `DECISIONS.md`)

```jsonc
// locations.json
[{"id":"gombe","name":"Gombe","lat":10.29,"lon":11.17,
  "coords_status":"approximate seed, replace with boundary centroids"}]

// metrics.json
{"data_mode":"synthetic",
 "generated":"YYYY-MM-DD",
 "years":[2001,2024],
 "sources_used":["NASA POWER (synthetic stand-in)"],
 "locations":{
  "gombe":{
   "n_total":24,"no_onset_years":[2007],"bad_data_years":[],
   "confidence":"Medium (single source)","confidence_reason":"Only NASA POWER rainfall was available.",
   "bare_share":0.31,"ndvi_dekad":[0.18,0.17],"bare_flags":[true,true],
   "onset_by_year":{"2001":134,"2002":122},
   "scenarios":{
     "rain+0_temp+0":{"maize":{"rain_ok":19,"dry_ok":15,"heat_ok":20,"all_ok":12,"n_total":24}},
     "base":"rain+0_temp+0"}}}}
```

(Numbers above are illustrative only. `ndvi_dekad` and `bare_flags` are shortened here; real arrays have 36 entries. The `base` entry is a string alias to another key. Make the front end resolve it.)

```jsonc
// strategies.json  (alternatives only; the existing rotation is created in the UI)
[{"id":"B","name":"Cereal, then legume","sequence":["maize","cowpea"],
  "benefits":["Legumes fix nitrogen","Breaks pest and disease cycles","Adds a second income crop"],
  "gaps":["Soil type and fertility","Local cowpea or groundnut market","Variety and seed access"],
  "risks":["Check pest pressure on the legume","Confirm planting dates with your extension officer"]},
 {"id":"C","name":"Drought-tolerant mix","sequence":["sorghum","cowpea"],
  "benefits":["Lower water demand","Better fit for dry or variable seasons"],
  "gaps":["Local sorghum and millet market","Variety choice","Bird and pest pressure"],
  "risks":["Lower yield potential in good years","Confirm varieties with an agronomist"]}]
```

Also provide a third alternative `D` "Millet, then groundnut" (`["millet","groundnut"]`) so the UI shows the existing rotation plus three alternatives. Write benefits, gaps and risks in the same style.

```jsonc
// crops.json : see section 10.1 for the seed
// glossary.json : [{"term":"NDVI","plain":"A satellite measure of how green and healthy plants are."}]
```

---

## 10. Seed content

### 10.1 `crops.json` seed (ALL PROVISIONAL)

Use these values so the product runs. Every crop gets `"provisional": true` and `"source_status": "PROVISIONAL: not yet verified against IITA or FAO"`. The human will verify and replace them. Do not present them as facts anywhere; the UI shows the "unverified estimate" tag (rule 2.3).

Scores `water, n_fixing, cover, market` are on a 0 to 1 scale.

| crop | family | cycle_days | min_rain_mm | dry_tolerance_days | heat_threshold_c | heat_days_limit | flower_frac | water | n_fixing | cover | market |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| maize | cereal | 110 | 500 | 10 | 35 | 5 | [0.45, 0.60] | 0.80 | 0 | 0.50 | 0.70 |
| sorghum | cereal | 115 | 450 | 14 | 38 | 5 | [0.50, 0.65] | 0.45 | 0 | 0.50 | 0.55 |
| millet | cereal | 90 | 350 | 14 | 40 | 5 | [0.45, 0.60] | 0.35 | 0 | 0.45 | 0.50 |
| cowpea | legume | 85 | 350 | 12 | 35 | 5 | [0.40, 0.60] | 0.40 | 1 | 0.80 | 0.60 |
| groundnut | legume | 110 | 450 | 12 | 35 | 5 | [0.30, 0.55] | 0.50 | 1 | 0.70 | 0.65 |

Also create `docs/crop_table_sources.md` with one row per value and the columns: crop, field, value, source, status. Set every status to `UNVERIFIED` and every source to `TODO: cite IITA or FAO`. The human fills these in.

### 10.2 `glossary.json`

Write plain-language entries (one or two short sentences each, written for a farmer) for: rainfall onset, dry spell, dekad (10-day period), NDVI, soil moisture, bare field, reliability, crop rotation, nitrogen fixing, legume, cereal, sensitivity test, confidence label, extension officer.

---

## 11. Scoring logic (`web/js/scoring.js`)

Pure functions, no DOM access, ES module, testable in Node. Implement exactly:

```js
const frac = (c, key) => c[key] / c.n_total;

export function scoreStrategy(seq, loc, scen, crops, w) {
  const avg = f => seq.reduce((s, c) => s + f(c), 0) / seq.length;
  const m = c => loc.scenarios[scen][c];
  const bare = loc.bare_share ?? 0.3;                    // mirror DEFAULT_BARE_SHARE
  const changes = seq.filter((c, i) =>
    crops[c].family !== crops[seq[(i + 1) % seq.length]].family).length;
  const parts = {
    climate: avg(c => (frac(m(c), "rain_ok") + frac(m(c), "dry_ok") + frac(m(c), "heat_ok")) / 3),
    water:   avg(c => 1 - crops[c].water),
    soil:    avg(c => crops[c].n_fixing),
    erosion: avg(c => crops[c].cover) * (1 - bare),
    pests:   seq.length > 1 ? changes / seq.length : 0,
    income:  avg(c => crops[c].market),
  };
  let num = 0, den = 0;
  for (const k in parts) { num += w[k] * parts[k]; den += w[k]; }
  return { total: den ? num / den : 0, parts };
}

export function rank(strategies, loc, scen, crops, w) {
  return strategies
    .map(s => ({ s, r: scoreStrategy(s.sequence, loc, scen, crops, w) }))
    .sort((a, b) => b.r.total - a.r.total);
}

export const scenarioKey = (rainMult, tempDelta) =>
  `rain${Math.round((rainMult - 1) * 100) >= 0 ? "+" : ""}${Math.round((rainMult - 1) * 100)}_temp${tempDelta >= 0 ? "+" : ""}${tempDelta}`;
```

Notes: `scenarioKey` MUST produce the same strings as the Python key format in section 6 (`rain+0_temp+0`, `rain-10_temp+1`). Add a test that asserts this. The `climate` part is the average of the three pass rates; the Evidence sentence on cards uses `all_ok` (stricter: all conditions met in the same season).

Traffic light for the total score: green >= 0.65, amber from 0.45 to below 0.65, red below 0.45. Always pair colour with a text label ("Strong fit", "Mixed fit", "Weak fit") and an icon.

---

## 12. Front-end specification

### 12.1 State (`state.js`)

```js
export const state = {
  location: "gombe",
  existing: ["maize", "maize"],     // user-editable, length 2 or 3
  weights: { climate:3, water:3, soil:3, erosion:3, pests:3, income:3 },   // 1..5
  rain: 1.0, temp: 0
};
```

`setState(patch)` merges, writes `location.hash` as `#<locationId>` (plain id only, no other hash content), then calls `update()`. On load and on `hashchange`, read the hash and select that location if valid.

### 12.2 `main.js`

`init()`: fetch the five JSON files once, resolve the `base` alias, build the controls, call `update()`. If any fetch fails, show a plain error panel with a retry button; never a blank page.

`update()`: read state; pick the location's metrics; build the strategy list `[{id:"A", name:"Your current rotation", sequence: state.existing}, ...DATA.strategies]`; call `rank`; then `drawMap`, `drawCharts`, `drawCards`, `drawLimits`. No network calls.

### 12.3 Layout and components

Desktop (>= 1000 px): left control column, centre map and charts, right strategy cards. Mobile (< 700 px): single column in this order: demo banner, location and rotation, priorities (collapsible), cards, charts, map, limits, glossary. Test at 360 px width.

| Component | Behaviour |
| --- | --- |
| Demo banner | Shown when `data_mode == "synthetic"`. Amber background, bold text, cannot be dismissed |
| Location select | Lists locations; changing it updates everything and the URL hash |
| Existing rotation | One select per year slot (2 slots default, button to add a third, max 3). Crops come from `crops.json` |
| Priority sliders | Six sliders, 1 to 5, labelled in plain words: "Save water" (water), "Earn income" (income), "Improve soil" (soil), "Reduce erosion" (erosion), "Fewer pests" (pests), "Reliable harvest" (climate). Live update on `input` |
| Scenario selects | Rainfall (-20, -10, 0, +10 percent) and temperature (0, +1, +2 C) as snapping sliders or radio groups, under the label "Sensitivity test, not a forecast" |
| Map | Leaflet, one marker per location, colour by that location's top strategy traffic light (plus text in the popup). Click selects the location. If tiles fail to load, the markers still render on a plain background |
| Onset chart | Chart.js scatter or dot plot of onset day-of-year by year with a median line and a note "Each dot is one year" |
| NDVI chart | Chart.js line over the 36 dekads with bare dekads shaded (use a plugin or a second dataset). If `ndvi_dekad` is null, show "Greenness data not loaded for this build" and the default-bare-share note |
| Strategy cards | See 12.4 |
| Limits panel | See 12.6 |
| Glossary | Accordion from `glossary.json`; technical terms elsewhere link to their entry |

### 12.4 Strategy card (requirements R2, R3, R10)

Each card, in this order, with visible headings:

1. Header: rank number, strategy name, sequence as chips ("Maize, then Cowpea"), traffic-light badge with text, total score as a bar (no raw decimal as the headline).
2. Six small bars for the criteria (climate, water, soil, erosion, pests, income) with plain labels.
3. **Why suggested**: one or two sentences from `text.js` templates using the two highest and the lowest criterion scores.
4. **Evidence**: one line per crop in the sequence, for example "Maize: in 12 of 24 seasons, rainfall, dry spells and heat all stayed within its limits." If the location has `no_onset_years`, append "In N years the rains did not start reliably."
5. **Benefits**: list from `strategies.json`.
6. **Information gaps**: list from `strategies.json`.
7. **Risks needing local review**: list from `strategies.json`, then a line "Ask a local expert about: variety, soil type, local market, pests."
8. Provisional tag next to any score influenced by a provisional crop value.
9. Footer (verbatim from rule 2.6).

For the existing rotation (id "A") use these fixed texts: benefits = ["A baseline you already know"], gaps = ["Soil condition and yield history on your farm"], risks = ["If the same crop family repeats, pests and disease can build up"].

`text.js` MUST generate sentences from templates filled with real numbers and criterion names. Example why-template: "Suggested because it scores well on {top1} and {top2}, but lower on {lowest}." Keep every template in `strings.js`.

### 12.5 Map details

Use OpenStreetMap tiles with the required attribution. Centre on Gombe State (about lat 10.3, lon 11.2, zoom 8). Fit bounds to the markers.

### 12.6 Data-and-limits panel (requirements R5, R6)

Static text plus values from `metrics.json`. MUST include, in plain language:

- Data sources used, product names, and date range (from `sources_used` and `years`).
- Resolution statement: results are per local government area point and per 10-day period; soil moisture from satellites is coarse (about 9 km or more) and cannot see a single field.
- Satellite versus ground: satellites give a consistent long record everywhere but are estimates; rain gauges and soil tests are more accurate locally; **no ground stations were used in this tool**; what ground validation would add.
- The confidence label for the selected location and its reason.
- The scenario-slider disclaimer.
- The support-not-replace message.
- A short respectful note that security conditions in parts of the northeast can limit farming.

### 12.7 Visual design

- Palette (CSS variables on `:root`): `--forest:#1F4D33; --leaf:#2E7D4F; --sun:#F2A93B; --mint:#EAF3EC; --ink:#14281D; --soil:#9A4F12; --sage:#8DB48E`.
- Headings: `font-family: Cambria, Georgia, serif`. Body: `Calibri, "Segoe UI", system-ui, sans-serif`.
- Header: dark forest bar with the GonaSense logo lockup (logo SVG plus wordmark "Gona" in white and "Sense" in `--sun`).
- Cards on mint backgrounds with soft shadow and rounded corners (about 12 px). No decorative side stripes under titles.
- Support light and dark: define colours as variables and override under `@media (prefers-color-scheme: dark)`.
- Viewport meta: `width=device-width, initial-scale=1`.

---

## 13. Logo (`web/img/logo.svg`, `web/img/favicon.svg`)

Create the logo exactly as follows (wordmark is rendered in HTML text next to it, not inside the SVG). Hoe handle, hoe blade, and three signal arcs.

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="2 -4 120 120">
  <line x1="24" y1="108" x2="76" y2="34" stroke="#1F4D33" stroke-width="8" stroke-linecap="round"/>
  <polygon points="72.7,31.8 104.2,53.0 86.4,65.2 69.3,44.0" fill="#F2A93B" stroke="#F2A93B" stroke-width="5" stroke-linejoin="round"/>
  <path d="M78.8,26.1 A14 14 0 0 1 94.0,38.8" fill="none" stroke="#2E7D4F" stroke-width="5" stroke-linecap="round"/>
  <path d="M78.0,17.1 A23 23 0 0 1 102.9,38.0" fill="none" stroke="#2E7D4F" stroke-width="5" stroke-linecap="round"/>
  <path d="M77.2,8.1 A32 32 0 0 1 111.9,37.2" fill="none" stroke="#2E7D4F" stroke-width="5" stroke-linecap="round"/>
</svg>
```

This is the light-background version. For the dark header, produce a variant with handle `#FFFFFF` and arcs `#F2A93B`. The favicon is the same icon on a transparent background.

---

## 14. Tests

Create and run these. All MUST pass before the final commit.

**pytest**
- `test_onset.py`: (a) synthetic rain with a known onset is found on the expected date; (b) a false start (20 mm in 3 days followed by a 10-day dry spell inside the lookahead window) is rejected and a later true onset is found; (c) a year with no qualifying rain returns `no_onset`; (d) a year with more than 5 percent missing rain returns `bad_data`.
- `test_metrics.py`: (a) `longest_run` on known masks; (b) `crop_year` pass/fail on a hand-built frame with a known dry spell and known heat days; (c) a `no_onset` year adds 0 to all counts and 1 to `n_total`; (d) scenario key format equals `rain+0_temp+0` for multiplier 1.0 and delta 0, and `rain-10_temp+1` for 0.9 and 1.
- `test_validate.py`: `validate.py` fails on a deliberately broken JSON (count above `n_total`, missing scenario key, NaN).

**Node (`scoring.test.mjs`, run with `node --test tests/`)**
- Continuous maize (`["maize","maize"]`) has `parts.pests === 0`; `["maize","cowpea"]` has `parts.pests === 1`.
- All-zero weights return `total === 0` and no NaN.
- Raising only the water weight moves a sorghum/millet-based strategy above maize-based ones on the seed data.
- `scenarioKey(0.9, 1)` equals `"rain-10_temp+1"` and `scenarioKey(1.0, 0)` equals `"rain+0_temp+0"`.

**Manual or scripted UI checks (document results in `docs/QA.md`)**
- Changing each control updates map, charts and cards with no network request after load.
- Page is usable at 360 px width with no horizontal scrolling.
- With the NDVI file missing, the page degrades gracefully.
- With a scenario key deliberately removed from a copy of the data, the page shows a clear message rather than a blank screen.

---

## 15. Build order, definitions of done, and STOP conditions

### Phase 0: Scaffold
Create the repo layout (section 4), `.gitignore`, `DECISIONS.md`, `HUMAN_TODO.md`, `AGENTS.md`, and an empty-but-valid `web/index.html`. Set up a Python venv and install pipeline dependencies. **Done when** `pytest` runs (even with no tests yet) and `web/index.html` opens.

### Phase 1: Synthetic end-to-end data
Implement `config.py`, `locations.py`, `synth.py`, `harmonize.py`, `metrics.py`, `export_json.py`, `validate.py`, `run_all.py`, and the pipeline tests. **Done when** `python -m pipeline.run_all --mode synthetic` writes all five JSON files into `web/data/`, `validate.py` passes, and `pytest` passes.

### Phase 2: Front end on the synthetic data
Implement all `web/js` modules, `index.html`, `style.css`, logo, vendored libraries, scoring tests. **Done when** the page loads from a local static server (`python -m http.server -d web`), the demo banner shows, three or more strategy cards render with all five sections, and moving a priority slider re-ranks strategies.

### Phase 3: Charts, map, scenarios, limits, glossary
Add the onset chart, NDVI chart with shaded bare periods, Leaflet map, scenario controls, the limits panel and glossary. **Done when** every row in section 1 is DONE in `docs/REQUIREMENTS_TRACE.md`.

### Phase 4: Real NASA mode
Implement `fetch_power.py` and the optional fetchers, then run `python -m pipeline.run_all --mode nasa`. **If the sandbox has no network access, do not fake it.** Leave the code complete and tested against a mocked response, record this in `HUMAN_TODO.md`, and continue. **Done when** either the real run succeeds (and the banner disappears because `data_mode` is `nasa`), or the code is complete, mock-tested and the limitation is recorded.

### Phase 5: Documentation and deployment
Write `README.md` (sections: what it is, live link placeholder, screenshots placeholder, how to run both modes, data sources, method, limitations, uncertainty handling, where local expertise is required, credits, AI-use disclosure placeholder), `docs/method.md`, `docs/sources.md`, `docs/QA.md`. Create `.github/workflows/pages.yml` that uploads `web/` as the Pages artifact and deploys it on push to `main`. **Done when** all docs exist and contain no unexplained placeholders beyond those listed in `HUMAN_TODO.md`.

### Phase 6: Final verification and report
Run every test, run the full pipeline in synthetic mode from a clean checkout, open the site, and walk the checklist in section 1. Produce the final report (section 17).

### STOP conditions (halt and report instead of improvising)
- A required library cannot be installed and there is no reasonable fallback.
- Any test cannot be made to pass without weakening it.
- You are tempted to invent a value to make progress: use a provisional placeholder instead (rule 2.1) and log it.

---

## 16. Things only a human can do (write `HUMAN_TODO.md`)

Create this file and keep it current. Each item states what is needed and where in the repo it goes. Include at least:

1. Verify every crop value in `web/data/crops.json` against IITA and FAO sources, fill `docs/crop_table_sources.md`, then set `"provisional": false` per value.
2. Confirm and cite the rainfall onset definition used in `config.py`, and the dry-spell and heat thresholds.
3. Replace fallback LGA coordinates with boundary centroids if section 7 step 1 did not succeed.
4. Create a free NASA Earthdata login; provide credentials via environment variables to enable IMERG and SMAP.
5. Export MODIS NDVI for the locations from AppEEARS as `raw/ndvi_<id>.csv`, then tune `NDVI_BARE_THRESHOLD`.
6. Run `python -m pipeline.run_all --mode nasa` on a machine with internet access if Phase 4 could not.
7. Hand-check one location and one year of onset against the raw daily rain and against NiMet seasonal information or farmer experience.
8. Replace the synthetic example texts with reviewed gaps and risks for each strategy (agronomist review), and confirm strategies B, C and D with IITA or a local agronomist.
9. Add the farmer or extension-worker conversation notes to `docs/`.
10. Enable GitHub Pages in the repository settings (source: GitHub Actions) and add the live URL to the README.
11. Fill the AI-use disclosure in the README if the challenge rules require it.
12. Re-run the pipeline in `nasa` mode, confirm the demo banner is gone, and capture screenshots.

---

## 17. Final report (print when finished)

Return a short report containing: what was built per phase; the result of each test suite; the contents of `HUMAN_TODO.md`; every entry in `DECISIONS.md`; any requirement in section 1 not marked DONE and why; the exact commands to run the project locally in both modes.
