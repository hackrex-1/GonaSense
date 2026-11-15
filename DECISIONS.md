# Decisions

Format: decision - reason.

- Reuse the existing `gombe-rotation-advisor` repository instead of creating a nested `gonasense/` directory - the plan's layout already matched, and nesting would have duplicated the documented paths.
- Keep 11 Gombe State LGAs and exclude Guyuk - Guyuk is in Adamawa, even though it appears near the Gombe border in simplified geometry.
- Derive LGA coordinates from geoBoundaries NGA ADM2 (GRID3 2022) centroids inside the GADM 4.1 Gombe mask - this satisfies the "no invented coordinates" rule; `coords_status` records the provenance.
- Keep a six-LGA fallback seed for missing boundary files - the pipeline should still run if a boundary download is unavailable, without pretending the fallback is surveyed.
- Store onset as the end date of the qualifying 3-day window - the rolling sum is only complete on the third day; tests assert day 141 and day 183 for the hand-built cases.
- Count `no_onset` years in `n_total` and give them zero passes - dropping them would overstate reliability.
- Exclude `bad_data` years from `n_total` - missing data cannot support a pass or a fail; the count is reported separately.
- Use 24 dekads (10-33, 1 April-30 November) for `bare_share` - matches `BARE_SEASON`; the earlier 9-32 window was a bug.
- Leave `ndvi_dekad`, `bare_flags` and `bare_share` null when NDVI is absent - the rule forbids inventing NDVI; the UI must explain the 0.30 default.
- Run the final build in `nasa` mode from cached POWER CSVs - the real 2001-2024 data is already on disk and verifiable, so a synthetic final build would be misleading.
- Keep confidence "Medium (single source)" in NASA mode - no second rainfall source (IMERG) is available to cross-check.
- Vendor Chart.js 4.4.7 and Leaflet 1.9.4 into `web/vendor/` - the page must not depend on a CDN at runtime.
- Keep all state in memory and the URL hash, using only the location id - satisfies the no-storage rule and the plan's exact hash format.
- Resolve the `base` string alias in the front end - the frozen contract stores `"base"` as an alias, not a duplicated block.
- Put every user-facing string in `web/js/strings.js` - including ARIA labels, traffic-light labels and the "then" join in rotation names.
- Wrap the layout in three column containers for desktop - a single spanning cards cell stretched the map row and pushed charts ~2,000 px down.
- Keep the existing rotation card first in DOM but last in rank when it scores lowest - the card always exists, and rank is by score, not by identity.
- Mark every crop value provisional and every source `TODO: cite IITA or FAO` - no citation was available to verify against.
- Use `node --test "tests/*.test.mjs"` on Windows - bare `tests/` triggers MODULE_NOT_FOUND with this Node setup.
- Add `?v=` cache-busters only during QA, not in the shipped HTML - the static site relies on normal HTTP revalidation; the deployed first load has no stale cache.

## Superseded decisions

- An earlier version stored `no_onset_years` as a count; it is now the list of years required by the contract.
- An earlier version used `cycle_days` inclusively plus one day; the window now covers exactly `cycle_days` days.
