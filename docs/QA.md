# QA record

Manual and scripted checks against the real-data build (`data_mode: "nasa"`)
served from `web/`. Run on 2026-11-15 with Node 24.18.0, Python 3.13
(`.venv`), Chromium via the desktop browser tools.

## Automated tests

| Suite | Command | Result |
| --- | --- | --- |
| Pipeline | `.\.venv\Scripts\python.exe -m pytest -q` | 27 passed |
| Scoring | `node --test "tests/*.test.mjs"` | 8 passed |
| Contracts | `python -m pipeline.run_all --mode nasa` (runs validate) | 11 locations exported, all contracts pass |

Note: `node --test tests/` fails to resolve on this Windows setup; use the
quoted glob `node --test "tests/*.test.mjs"`.

## Page load

- `http://localhost:8080` loads with **no console errors**.
- 4 strategy cards render: Drought-tolerant mix, Millet then groundnut,
  Cereal then legume, Your current rotation.
- 11 Leaflet markers render.
- The onset chart is 270 px high at >= 700 px width; the NDVI canvas is hidden
  because this build has no NDVI.
- The demo banner is hidden in `nasa` mode; `data-badge` reads
  "11 LGAs · 12 sensitivity cases · NASA data".

## Controls

| Check | Result |
| --- | --- |
| Location select changes cards, charts, map, title and hash | Pass: Gombe -> Akko updates hash to `#akko`, title to "Akko · GonaSense", median onset to 1 June |
| Add a third year | Pass: adds a third crop select and a "Remove year 3" button |
| Remove the third year | Pass: returns to two selects |
| Priority slider updates cards live | Pass: moving Save water to 5 changed the top score from 67 to 66 |
| Scenario radios update counts | Pass: 20% less rain and +2 °C changed the four scores (66/65/63/34 to 64/63/59/29 in the synthetic run; real data also updates) |
| Missing scenario key | Pass: a copy with `rain-20_temp+2` removed shows "This sensitivity case is missing" and a plain explanation, not a blank page |
| No network after load | Pass: request list unchanged after slider and location changes (40 requests before and after) |

## Layout

- **360 px:** `documentElement.scrollWidth` 345 < 360; no horizontal
  scrolling. Single column. Visual order is controls, cards, charts, map,
  limits, glossary, as required.
- **414 px, 768 px:** no horizontal overflow.
- **1280 px:** three columns. Controls 256 px, centre 625 px, cards 320 px.
  Map starts at the top of the centre column and charts follow 16 px below it;
  cards sit in their own column. No overflow.
- The earlier grid used one spanning cards cell, which stretched the map row
  and pushed charts ~2,000 px down. Fixed by wrapping each column and using
  explicit grid areas.

## Accessibility

Lighthouse (desktop audit, real-data build):

| Category | Score |
| --- | --- |
| Accessibility | 1.00 |
| Best practices | 1.00 |
| SEO | 1.00 |

- Every form control has an accessible name.
- Focus styles are visible (`:focus-visible` outline).
- Colour is never the only signal: traffic lights pair colour with a text
  label and icon.
- All app-owned buttons, selects and sliders are at least 44 px high. The
  native radio input is 17 px inside a 44 px label, so the tap target is the
  label. Leaflet's zoom buttons are vendor controls at 30 px; inline glossary
  and attribution links are text links, not standalone tap targets.
- The "ask a local expert" paragraph was previously appended inside a `<ul>`,
  which failed the Lighthouse list rule. It now follows the list inside the
  section.

## Graceful degradation

Tested on a copy of `web/` on a separate local port, with the original data
untouched.

1. **NDVI missing** (`ndvi_dekad` and `bare_flags` set to `null`):
   cards still render, the NDVI canvas and its 270 px wrapper are hidden, and
   the note reads "Greenness data not loaded for this build. The score uses a
   default bare-field share of 30%. Ask a local expert about your field."
2. **Scenario key missing** (deleted `rain-20_temp+2`):
   choosing 20% less rain and +2 °C shows an alert with the key name and a
   recovery instruction. Choosing another case restores the cards.
3. **metrics.json missing** (renamed to `.bak`):
   the page shows "The data could not be loaded", the HTTP error detail and a
   "Try again" button. The header badge also changes. The only console entry is
   the expected 404, with no uncaught JavaScript error.

## Data spot check

- 11 locations, 24 seasons each, 0 no-onset years and 0 bad-data years in the
  current POWER build.
- Gombe 2001 onset is day 151 (31 May). The raw 29-31 May total is 20.32 mm;
  the earlier 6-8 May candidate is rejected because a 7-day dry run follows.
  See `docs/method.md` section 8.
- Neighbouring LGAs that share an identical POWER series are documented in the
  limits panel: Akko/Billiri/Kaltungo, Funakaye/Nafada, and
  Gombe/Kwami/Yamaltu-Deba.

## Known limitations

- No NDVI in this build, so the NDVI chart is a plain explanatory note and
  erosion uses the 0.30 default.
- IMERG and SMAP are not available, so confidence stays "Medium (single
  source)".
- POWER is a modelled product; the LGA point is not a field measurement.
- Crop values are provisional. See `docs/crop_table_sources.md`.
- Browser caching can serve an older CSS/JS file after a rebuild. Use a hard
  reload or a fresh port while reviewing.
