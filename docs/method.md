# Method

This file describes what the pipeline actually computes. It mirrors the code in
`pipeline/`, not an aspiration. Thresholds marked provisional are listed in
`HUMAN_TODO.md`.

## 1. Inputs and harmonization

- **Weather:** NASA POWER daily point data for 2001-01-01 to 2024-12-31, 8,766
  days per location, columns `T2M_MAX`, `T2M_MIN`, `PRECTOTCORR`, `GWETROOT`.
  Missing values (`-999`) become NaN.
- **Locations:** 11 Gombe State LGAs, one boundary-derived centroid each (see
  `docs/sources.md`).
- **NDVI (optional):** a user-supplied `raw/ndvi_<id>.csv` with `date,ndvi`.
  No NDVI product is fetched automatically.

Daily series are aggregated to 36 dekads per year: days 1-10, 11-20 and
21-end of month. Rain is summed; temperature and root-zone wetness are
averaged. NDVI, when present, is linearly interpolated from its 16-day
samples to daily values and then averaged per dekad. Every derived series is
keyed by `(location, year, dekad)` and written to `raw/harmonized_<id>.csv`.

## 2. Rainfall onset

The search runs from **1 April to 31 October**. Onset is the end date of the
first 3-day window whose total is at least **20 mm**, provided that no run of
**7 consecutive dry days** (each below 1 mm) occurs within the next **30
days**. The dry-run guard rejects false starts.

- If no window qualifies, the year is `no_onset`.
- If more than **5%** of rain values in the search window are missing, the year
  is `bad_data` and is excluded from `n_total`.
- Onset is stored as a day-of-year integer. Because the returned date is the
  end of the window, a 20 mm total on 29-31 May is stored as day 151.

`no_onset` years stay in `n_total` and count as failures for every crop. They
are never silently dropped; dropping them would overstate reliability.

## 3. Per crop, per season

Starting at onset, the crop window covers `cycle_days` days, inclusive. The
flowering window is the slice from `round(flower_frac[0] * cycle_days)` to
`round(flower_frac[1] * cycle_days)` days after onset, inclusive. Dry spells
are checked within this flowering window, not across the whole crop cycle.

A season passes for a crop only when all three checks pass:

| Check | Pass rule |
| --- | --- |
| Rain | season total >= `min_rain_mm` |
| Dry spell | longest run of flowering-window days below 1 mm <= `dry_tolerance_days` |
| Heat | days above `heat_threshold_c` during flowering <= `heat_days_limit`, using Tmax or Tmin as selected by `heat_metric` |

`dry_tolerance_days` and `heat_days_limit` are provisional risk-screening
thresholds, not established biological limits. `min_rain_mm` represents a
crop water requirement and is not a guaranteed crop-failure point. See
`docs/crop_table_sources.md` and the detailed research notes in
`../crop_table_sources.md`.

The pipeline reports `rain_ok`, `dry_ok`, `heat_ok`, `all_ok` and `n_total`.
Reliability is not reported as a single probability; the page shows counts such
as "19 of 24 seasons".

## 4. Sensitivity scenarios

Twelve cases are the product of rain multipliers (0.8, 0.9, 1.0, 1.1) and
temperature deltas (0, +1, +2 °C). Each case copies the daily frame, scales
rain, adds the delta to Tmax and Tmin, recomputes onset and reruns the crop
checks. Onset can move under scaled rain, so scenario results are sensitivity
tests, not forecasts. The key format is `rain-10_temp+1`; the base key is
`rain+0_temp+0`, with `"base"` stored as a string alias.

## 5. Bare-field share and NDVI

When NDVI is available, the pipeline averages NDVI per dekad across years.
`bare_flags` marks the 36 dekads whose mean is below **0.25**. `bare_share` is
the share of the 24 dekads from **1 April to 30 November** (dekads 10-33) that
are flagged. The chart shades flagged dekads.

When NDVI is unavailable, `ndvi_dekad` and `bare_flags` are `null`,
`bare_share` is `null`, the chart says "Greenness data not loaded for this
build", and scoring uses the documented **0.30** default. This is the case in
the current real-data build.

## 6. Scoring (front end)

```js
climate = avg((rain_ok + dry_ok + heat_ok) / (3 * n_total))
water   = avg(1 - crop.water)
soil    = avg(crop.n_fixing)
erosion = avg(crop.cover) * (1 - bare_share)   // bare_share ?? 0.30
pests   = family changes / sequence length      // wraps around the cycle
income  = avg(crop.market)

total = sum(weight[k] * part[k]) / sum(weight[k])
```

The climate bar uses the average of the three pass rates. The evidence sentence
uses the stricter `all_ok` count because "all conditions held in the same
season" is the honest claim. Weights come from the six priority sliders (1-5).
All-zero weights return 0, never NaN.

Traffic lights: strong at >= 0.65, mixed at 0.45 to below 0.65, weak below
0.45. Colour is always paired with a text label and an icon.

## 7. Confidence

Confidence is a heuristic, not a validation study.

- Synthetic mode: "Not applicable (demo data)".
- NASA mode without a second rainfall source: "Medium (single source)", because
  only POWER rainfall is available to cross-check.
- If IMERG is supplied: correlate POWER and IMERG June-September totals across
  years. High at r >= 0.7 with at least 15 valid years; Medium at r 0.4-0.7;
  Low below 0.4 or with fewer than 10 usable years.

The current real-data build uses cached POWER only, so every location is
"Medium (single source)". Some neighbouring LGAs share an identical POWER
series because the model grid is coarser than an LGA: Akko/Billiri/Kaltungo,
Funakaye/Nafada, and Gombe/Kwami/Yamaltu-Deba. This is stated in the page's
limits panel.

## 8. Hand check (Gombe, 2001)

Running the pipeline on `raw/power_gombe.csv` gives onset day **151**
(31 May 2001). Checking the raw daily rain by eye:

- The 3-day window 29-31 May totals **20.32 mm**.
- The earlier 6-8 May window totals more than 31 mm but is followed by a
  7-day dry run, so the false-start guard rejects it.
- The longest dry run in the following 30 days is 4 days, below the 7-day
  threshold.

The next window (30 May-1 June) also exceeds 20 mm, so the result is stable
within one day. This is a spot check, not a validation against gauges or NiMet
records.
