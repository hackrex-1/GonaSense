# Crop table sources

Every crop value used in `web/data/crops.json` is listed with its source key
and evidence status. Detailed research notes and the reference list (S1-S18,
AE) are in the repository-root `crop_table_sources.md`.

Status values:

- **CONFIRMED**: within a range or supported by a retrieved source; still
  subject to local-variety review.
- **DERIVED**: calculated from retrieved source values; the calculation is in
  the research notes.
- **ESTIMATE**: no direct source value was retrieved; the dashboard labels
  inputs in this category as estimates.

The `field_status` map covers the modeled crop inputs. `family` is listed
below as supporting crop information but is not part of that status map. No
crop is fully confirmed for Gombe varieties, so each remains
`"provisional": true`. The dashboard tags the affected criteria and evidence
counts and explains the need for local review.

## Status summary

| Crop | Confirmed | Derived | Estimate |
| --- | --- | --- | --- |
| Maize | 5 | 1 | 5 |
| Sorghum | 5 | 0 | 6 |
| Millet | 3 | 1 | 7 |
| Cowpea | 3 | 2 | 6 |
| Groundnut | 5 | 1 | 5 |

## Values

| Crop | Field | Value | Source | Status |
| --- | --- | --- | --- | --- |
| maize | family | cereal | Botanical classification | CONFIRMED |
| maize | cycle_days | 110 | S1,S4 | CONFIRMED |
| maize | min_rain_mm | 500 | S1,S5 | CONFIRMED |
| maize | dry_tolerance_days | 10 | S14,S15,AE | ESTIMATE |
| maize | heat_metric | tmax | S11 | CONFIRMED |
| maize | heat_threshold_c | 35 | S11,S1 | CONFIRMED |
| maize | heat_days_limit | 5 | AE | ESTIMATE |
| maize | flower_frac | 0.45-0.60 | S4 | DERIVED |
| maize | water | 0.80 | S1,S5,AE | ESTIMATE |
| maize | n_fixing | 0 | AE | CONFIRMED |
| maize | cover | 0.50 | AE | ESTIMATE |
| maize | market | 0.70 | AE | ESTIMATE |
| sorghum | family | cereal | Botanical classification | CONFIRMED |
| sorghum | cycle_days | 115 | S2,S4 | CONFIRMED |
| sorghum | min_rain_mm | 450 | S2,S5 | CONFIRMED |
| sorghum | dry_tolerance_days | 14 | S14,AE | ESTIMATE |
| sorghum | heat_metric | tmax | S13 | CONFIRMED |
| sorghum | heat_threshold_c | 36 | S13 | CONFIRMED |
| sorghum | heat_days_limit | 5 | AE | ESTIMATE |
| sorghum | flower_frac | 0.50-0.65 | AE | ESTIMATE |
| sorghum | water | 0.45 | S2,S5,AE | ESTIMATE |
| sorghum | n_fixing | 0 | AE | CONFIRMED |
| sorghum | cover | 0.50 | AE | ESTIMATE |
| sorghum | market | 0.55 | AE | ESTIMATE |
| millet | family | cereal | Botanical classification | CONFIRMED |
| millet | cycle_days | 90 | S6,S5 | CONFIRMED |
| millet | min_rain_mm | 385 | S5 | DERIVED |
| millet | dry_tolerance_days | 14 | S14,AE | ESTIMATE |
| millet | heat_metric | tmax | S18 | CONFIRMED |
| millet | heat_threshold_c | 40 | S18,AE | ESTIMATE |
| millet | heat_days_limit | 5 | AE | ESTIMATE |
| millet | flower_frac | 0.45-0.60 | AE | ESTIMATE |
| millet | water | 0.35 | S5,AE | ESTIMATE |
| millet | n_fixing | 0 | AE | CONFIRMED |
| millet | cover | 0.45 | AE | ESTIMATE |
| millet | market | 0.50 | AE | ESTIMATE |
| cowpea | family | legume | Botanical classification | CONFIRMED |
| cowpea | cycle_days | 85 | S7,S8 | CONFIRMED |
| cowpea | min_rain_mm | 360 | S2,S3,S5 | DERIVED |
| cowpea | dry_tolerance_days | 12 | S14,AE | ESTIMATE |
| cowpea | heat_metric | tmin | S9,S10 | CONFIRMED |
| cowpea | heat_threshold_c | 25 | S9,S10 | ESTIMATE |
| cowpea | heat_days_limit | 5 | AE | ESTIMATE |
| cowpea | flower_frac | 0.50-0.70 | S7 | DERIVED |
| cowpea | water | 0.40 | AE | ESTIMATE |
| cowpea | n_fixing | 1 | S17,AE | CONFIRMED |
| cowpea | cover | 0.80 | AE | ESTIMATE |
| cowpea | market | 0.60 | AE | ESTIMATE |
| groundnut | family | legume | Botanical classification | CONFIRMED |
| groundnut | cycle_days | 110 | S3,S4 | CONFIRMED |
| groundnut | min_rain_mm | 500 | S3,S5 | CONFIRMED |
| groundnut | dry_tolerance_days | 12 | S14,AE | ESTIMATE |
| groundnut | heat_metric | tmax | S12 | CONFIRMED |
| groundnut | heat_threshold_c | 35 | S12 | CONFIRMED |
| groundnut | heat_days_limit | 5 | AE | ESTIMATE |
| groundnut | flower_frac | 0.35-0.65 | S3 | DERIVED |
| groundnut | water | 0.50 | S3,S5,AE | ESTIMATE |
| groundnut | n_fixing | 1 | AE | CONFIRMED |
| groundnut | cover | 0.70 | AE | ESTIMATE |
| groundnut | market | 0.65 | AE | ESTIMATE |

## Review steps

1. Check each cited source against the primary document and record its full
   citation in the research notes.
2. Review estimated or derived inputs with a local agronomist and farmer,
   especially variety cycles, rainfall needs, crop thresholds, market values,
   and the cowpea night-heat threshold.
3. Change a field's `field_status` to `confirmed` only when its source and
   relevance to local varieties have been checked. Set a crop's
   `"provisional"` to `false` only after every modeled field is confirmed.
4. Re-run `python -m pipeline.run_all --mode nasa` and
   `python -m pipeline.validate`.

Do not quote a source from memory. If the primary document is not at hand, keep
the field marked as an estimate or derived.
