# Method (draft)

This mirrors sections 4-7 of the implementation plan. Update it when the code
changes, not afterwards.

## 1. Harmonization

Daily series are aggregated to 36 dekads per year: days 1-10, 11-20 and
21-end of month. Rain is summed; temperature and root-zone wetness are
averaged. NDVI (16-day) is linearly interpolated to daily, then averaged per
dekad. Every derived series is keyed by `(location, year, dekad)`.

## 2. Rainfall onset

Search from 1 April to 31 October. Onset is the first day on which:

- the 3-day rainfall total is at least 20 mm, and
- no run of 7 consecutive dry days (< 1 mm/day) follows within the next 30
  days (a false-start guard).

If nothing qualifies, onset is `None`. Those years are counted as failed
seasons for every crop, never skipped; otherwise reliability is overstated.
Years with more than 5% missing rain inside the search window are excluded
from onset detection and counted as failures.

Onset is stored as a day-of-year integer.

## 3. Per crop, per season

Starting at onset, the crop window runs for `cycle_days`. Flowering is the
fractional slice `flower_frac` of that cycle (for example 0.4 to 0.6).

A season passes for a crop when:

| Check | Pass rule |
| --- | --- |
| Rain | season total >= `min_rain_mm` |
| Dry spell | longest run < `DRY_DAY_MM` <= `dry_tolerance_days` days |
| Heat | days with Tmax > `heat_threshold_c` during flowering <= `heat_days_limit` |

Counts are aggregated over all years: `n_total`, `n_valid`, `rain_ok`,
`dry_ok`, `heat_ok`, `all_ok`. Reliability is `all_ok / n_total`.

## 4. Scenarios

The 12 cases are the product of rain multipliers (0.8, 0.9, 1.0, 1.1) and
temperature deltas (0, +1, +2 °C). Each case copies the daily frame, scales
rain, adds the delta to Tmax and Tmin, and reruns onset and crop checks.
Onset may shift under scaled rain; say so in the page.

## 5. Bare-field share

For each location, average NDVI per dekad across years. `bare_share` is the
share of the 24 dekads from 1 April to 30 November whose mean NDVI is below
`NDVI_BARE_THRESHOLD`. Store the 36 per-dekad means and 36 `bare_flags` for
chart shading. If NDVI is missing, store `null` and let scoring use the
neutral 0.3 default with a visible note.

## 6. Scoring

```js
climate = avg((rain_ok + dry_ok + heat_ok) / (3 * n_total))
water   = avg(1 - crop.water)
soil    = avg(crop.n_fixing)
erosion = avg(crop.cover) * (1 - bare_share)
pests   = family changes / sequence length   // wraps around the cycle
income  = avg(crop.market)

total = sum(weight[k] * part[k]) / sum(weight[k])
```

The climate bar uses the average of the three pass rates. The evidence
sentence uses the stricter `all_ok` count, because "all conditions held in
the same season" is the honest claim. Weights come from the six priority
sliders (1-5). All-zero weights return 0, never NaN.

Top-strategy colour thresholds: green at >= 0.65, amber 0.45-0.65, red below
0.45. Always pair colour with a text label and icon.

## 7. Confidence

If IMERG is available, correlate POWER and IMERG seasonal rainfall totals
across years:

- High: r >= 0.7 and at least 15 valid years
- Medium: r 0.4-0.7
- Low: r < 0.4, or fewer than 10 valid years

Without IMERG, every location is "Medium (single source)" and the limits
panel explains why. This is a heuristic, not a validation study.
