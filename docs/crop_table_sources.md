# Crop table sources

Every value in `web/data/crops.json` needs a citation before submission.
Rows marked **verify** are literature-based estimates that a local expert
must review. Until then the page must show the "unverified estimate" tag.

## Crops in the first release

Maize, sorghum, millet, cowpea and groundnut. Soybean is optional.

## Values

| Crop | cycle_days | min_rain_mm | dry_tolerance_days | heat_threshold_c | heat_days_limit | flower_frac | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Maize | 100 | 450 | 10 | 35 | 4 | 0.40-0.60 | verify |
| Sorghum | 120 | 300 | 15 | 38 | 6 | 0.45-0.65 | verify |
| Millet | 90 | 250 | 18 | 40 | 6 | 0.40-0.60 | verify |
| Cowpea | 80 | 250 | 14 | 36 | 5 | 0.35-0.60 | verify |
| Groundnut | 110 | 350 | 12 | 35 | 4 | 0.40-0.65 | verify |

## Scores (0 to 1)

| Crop | family | water demand | n_fixing | cover | market |
| --- | --- | --- | --- | --- | --- |
| Maize | cereal | 0.75 | 0.05 | 0.45 | 0.80 |
| Sorghum | cereal | 0.35 | 0.05 | 0.55 | 0.60 |
| Millet | cereal | 0.20 | 0.05 | 0.40 | 0.45 |
| Cowpea | legume | 0.30 | 0.85 | 0.60 | 0.70 |
| Groundnut | legume | 0.40 | 0.75 | 0.65 | 0.75 |

## Citation checklist

Fill one line per crop. Suggested sources, to be checked against the actual
documents rather than quoted from memory:

1. IITA crop guides (maize, cowpea, soybean) - cycle length, spacing, pests.
2. FAO crop water information (maize, sorghum, millet, groundnut, cowpea) -
   seasonal water requirement and drought sensitivity.
3. FAO ECOCROP - temperature and rainfall envelopes.
4. NiMet agro-meteorological bulletins - local season timing context.
5. One conversation with a Gombe extension officer or farmer - variety
   maturity, market demand, local practice. Record permission to quote.

## Open questions for the research lead

- Which maize and cowpea varieties are actually grown around each LGA?
- Is groundnut rosette or aflatoxin the bigger constraint locally?
- What price seasonality should the market score reflect?
- Should `heat_days_limit` differ between early and late maturing varieties?
