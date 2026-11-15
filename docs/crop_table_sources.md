# Crop table sources

Every value in `web/data/crops.json` needs a citation before submission.
**All values are currently provisional.** The UI shows an "unverified
estimate" tag on every card whose sequence includes one of these crops.

Status values: `UNVERIFIED` means no citation has been checked yet and
`crops.json` has `"provisional": true`.

## Values (one row per value)

| Crop | Field | Value | Source | Status |
| --- | --- | --- | --- | --- |
| maize | family | cereal | TODO: cite IITA or FAO | UNVERIFIED |
| maize | cycle_days | 110 | TODO: cite IITA or FAO | UNVERIFIED |
| maize | min_rain_mm | 500 | TODO: cite IITA or FAO | UNVERIFIED |
| maize | dry_tolerance_days | 10 | TODO: cite IITA or FAO | UNVERIFIED |
| maize | heat_threshold_c | 35 | TODO: cite IITA or FAO | UNVERIFIED |
| maize | heat_days_limit | 5 | TODO: cite IITA or FAO | UNVERIFIED |
| maize | flower_frac | 0.45-0.60 | TODO: cite IITA or FAO | UNVERIFIED |
| maize | water | 0.80 | TODO: cite IITA or FAO | UNVERIFIED |
| maize | n_fixing | 0 | TODO: cite IITA or FAO | UNVERIFIED |
| maize | cover | 0.50 | TODO: cite IITA or FAO | UNVERIFIED |
| maize | market | 0.70 | TODO: cite IITA or FAO | UNVERIFIED |
| sorghum | family | cereal | TODO: cite IITA or FAO | UNVERIFIED |
| sorghum | cycle_days | 115 | TODO: cite IITA or FAO | UNVERIFIED |
| sorghum | min_rain_mm | 450 | TODO: cite IITA or FAO | UNVERIFIED |
| sorghum | dry_tolerance_days | 14 | TODO: cite IITA or FAO | UNVERIFIED |
| sorghum | heat_threshold_c | 38 | TODO: cite IITA or FAO | UNVERIFIED |
| sorghum | heat_days_limit | 5 | TODO: cite IITA or FAO | UNVERIFIED |
| sorghum | flower_frac | 0.50-0.65 | TODO: cite IITA or FAO | UNVERIFIED |
| sorghum | water | 0.45 | TODO: cite IITA or FAO | UNVERIFIED |
| sorghum | n_fixing | 0 | TODO: cite IITA or FAO | UNVERIFIED |
| sorghum | cover | 0.50 | TODO: cite IITA or FAO | UNVERIFIED |
| sorghum | market | 0.55 | TODO: cite IITA or FAO | UNVERIFIED |
| millet | family | cereal | TODO: cite IITA or FAO | UNVERIFIED |
| millet | cycle_days | 90 | TODO: cite IITA or FAO | UNVERIFIED |
| millet | min_rain_mm | 350 | TODO: cite IITA or FAO | UNVERIFIED |
| millet | dry_tolerance_days | 14 | TODO: cite IITA or FAO | UNVERIFIED |
| millet | heat_threshold_c | 40 | TODO: cite IITA or FAO | UNVERIFIED |
| millet | heat_days_limit | 5 | TODO: cite IITA or FAO | UNVERIFIED |
| millet | flower_frac | 0.45-0.60 | TODO: cite IITA or FAO | UNVERIFIED |
| millet | water | 0.35 | TODO: cite IITA or FAO | UNVERIFIED |
| millet | n_fixing | 0 | TODO: cite IITA or FAO | UNVERIFIED |
| millet | cover | 0.45 | TODO: cite IITA or FAO | UNVERIFIED |
| millet | market | 0.50 | TODO: cite IITA or FAO | UNVERIFIED |
| cowpea | family | legume | TODO: cite IITA or FAO | UNVERIFIED |
| cowpea | cycle_days | 85 | TODO: cite IITA or FAO | UNVERIFIED |
| cowpea | min_rain_mm | 350 | TODO: cite IITA or FAO | UNVERIFIED |
| cowpea | dry_tolerance_days | 12 | TODO: cite IITA or FAO | UNVERIFIED |
| cowpea | heat_threshold_c | 35 | TODO: cite IITA or FAO | UNVERIFIED |
| cowpea | heat_days_limit | 5 | TODO: cite IITA or FAO | UNVERIFIED |
| cowpea | flower_frac | 0.40-0.60 | TODO: cite IITA or FAO | UNVERIFIED |
| cowpea | water | 0.40 | TODO: cite IITA or FAO | UNVERIFIED |
| cowpea | n_fixing | 1 | TODO: cite IITA or FAO | UNVERIFIED |
| cowpea | cover | 0.80 | TODO: cite IITA or FAO | UNVERIFIED |
| cowpea | market | 0.60 | TODO: cite IITA or FAO | UNVERIFIED |
| groundnut | family | legume | TODO: cite IITA or FAO | UNVERIFIED |
| groundnut | cycle_days | 110 | TODO: cite IITA or FAO | UNVERIFIED |
| groundnut | min_rain_mm | 450 | TODO: cite IITA or FAO | UNVERIFIED |
| groundnut | dry_tolerance_days | 12 | TODO: cite IITA or FAO | UNVERIFIED |
| groundnut | heat_threshold_c | 35 | TODO: cite IITA or FAO | UNVERIFIED |
| groundnut | heat_days_limit | 5 | TODO: cite IITA or FAO | UNVERIFIED |
| groundnut | flower_frac | 0.30-0.55 | TODO: cite IITA or FAO | UNVERIFIED |
| groundnut | water | 0.50 | TODO: cite IITA or FAO | UNVERIFIED |
| groundnut | n_fixing | 1 | TODO: cite IITA or FAO | UNVERIFIED |
| groundnut | cover | 0.70 | TODO: cite IITA or FAO | UNVERIFIED |
| groundnut | market | 0.65 | TODO: cite IITA or FAO | UNVERIFIED |

## How to clear a row

1. Find the value in an IITA, FAO or peer-reviewed source and write the exact
   citation (author, year, title, page or table).
2. Put the citation in the Source column and change Status to `VERIFIED`.
3. Change the matching `"provisional": true` to `false` in
   `web/data/crops.json` only when every value for that crop is verified.
4. Re-run `python -m pipeline.run_all --mode nasa` and
   `python -m pipeline.validate` so the page and contracts stay consistent.

Do not quote a source from memory. If the document is not at hand, leave the
row as `UNVERIFIED`.
