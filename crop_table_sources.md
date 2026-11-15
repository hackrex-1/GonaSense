# Crop table: values, sources and status

Companion to `web/data/crops.json`. Prepared 15 November 2026. Every value has a status:

- **CONFIRMED**: taken from, or inside a range given by, a source we retrieved (references below).
- **DERIVED**: calculated by us from retrieved source values; the calculation is in the note.
- **ESTIMATE**: no source retrieved. Deduced from related evidence and general agronomic knowledge. Needs expert review. The UI marks these as an estimate.

The retrieved pages were read as web pages in one session. Some are secondary summaries or search snippets (noted in the reference list). Trace those to the primary paper before citing them in the README.

## Changes from the provisional seed

| Crop | Field | Seed | Now | Why |
| --- | --- | --- | --- | --- |
| sorghum | heat_threshold_c | 38 | 36 | Floret fertility falls above 36 C daytime maximum (S13) |
| millet | min_rain_mm | 350 | 385 | Scaled from FAO's 450-650 mm sorghum/millet range (S5) |
| cowpea | min_rain_mm | 350 | 360 | Scaled by cycle length from sorghum and groundnut figures |
| cowpea | heat_metric / threshold | Tmax 35 | Tmin 25 | Night temperature drives cowpea pod-set loss (S9, S10) |
| cowpea | flower_frac | [0.40, 0.60] | [0.50, 0.70] | Trial flowering days vs maturity days (S7) |
| groundnut | min_rain_mm | 450 | 500 | FAO: 500-700 mm reliable rainfall (S3) |
| groundnut | flower_frac | [0.30, 0.55] | [0.35, 0.65] | FAO stage lengths (S3) |

## Pipeline and method changes this implies

1. **`heat_metric` field (new).** `metrics.py` must test `T2M_MIN` when `heat_metric` is `tmin` (cowpea) and `T2M_MAX` otherwise.
2. **Calibrate the cowpea Tmin threshold.** Run POWER Tmin for the flowering window at each location. If almost every year exceeds 25 C, the threshold carries no information and needs revisiting with an agronomist or a heat-tolerant-variety note.
3. **Dry spells in the flowering window.** FAO identifies flowering as the most sensitive stage for maize and groundnut (S1, S3). Compute `dry_tolerance_days` inside the `flower_frac` window, not across the whole cycle.
4. **Onset rule.** The 20 mm / 3 d / 7 d-in-30 rule matches the published one, which starts counting on 1 May (S16). Your `earliest="04-01"` is a Gombe adaptation. Document it as such.
5. **Meaning of `min_rain_mm`.** Values come from FAO crop water needs. They are requirements, not guaranteed failure points, and effective rainfall is lower than total rainfall.
6. **`dry_tolerance_days` and `heat_days_limit`.** Neither has a per-crop published value. Call them risk thresholds in the UI, not biological limits.

## Value-by-value table

| crop | field | value | source | status | note |
| --- | --- | --- | --- | --- | --- |
| maize | cycle_days | 110 | S1,S4 | CONFIRMED | Early 80-110 d, medium 110-140 d (S1); 125 d for Nigeria (S4). 110 is the early/medium edge. Use 125 for later varieties. |
| maize | min_rain_mm | 500 | S1,S5 | CONFIRMED | Lower bound of the 500-800 mm seasonal water need. A water need, not a crop-failure point. |
| maize | dry_tolerance_days | 10 | S14,S15,AE | ESTIMATE | Middle of the 7/10/15 d classes used in the literature. Flowering is the most sensitive stage (S1). |
| maize | heat_metric | tmax | S11 | CONFIRMED | Tmax. |
| maize | heat_threshold_c | 35 | S11,S1 | CONFIRMED | Tmax above 35 C counts as heat stress. |
| maize | heat_days_limit | 5 | AE | ESTIMATE | Design parameter: flowering-window days over threshold that count as failure. No published day-count. |
| maize | flower_frac | [0.45, 0.6] | S4 | DERIVED | Nigeria stages 20/35/40/30 d: mid-season starts at day 55 of 125 = 0.44. Window covers silking to early grain fill. |
| maize | water | 0.8 | S1,S5,AE | ESTIMATE | Ordinal only: maize has the highest FAO water need of the five. |
| maize | n_fixing | 0 | AE | CONFIRMED | Non-legume. |
| maize | cover | 0.5 | AE | ESTIMATE | Moderate canopy. |
| maize | market | 0.7 | AE | ESTIMATE | Cannot be derived from data. Needs farmer or market input. |
| sorghum | cycle_days | 115 | S2,S4 | CONFIRMED | FAO page covers 110-130 d crops; FAO-56 lists 130-140 d. Photoperiod-sensitive local types run longer. |
| sorghum | min_rain_mm | 450 | S2,S5 | CONFIRMED | Lower bound of 450-650 mm for 110-130 d sorghum. |
| sorghum | dry_tolerance_days | 14 | S14,AE | ESTIMATE | Near the 15 d class; sorghum is more drought tolerant than maize. |
| sorghum | heat_metric | tmax | S13 | CONFIRMED | Tmax. |
| sorghum | heat_threshold_c | 36 | S13 | CONFIRMED | Changed from 38 to 36: daytime maxima above 36 C reduce floret fertility. |
| sorghum | heat_days_limit | 5 | AE | ESTIMATE | Design parameter. |
| sorghum | flower_frac | [0.5, 0.65] | AE | ESTIMATE | Anthesis typically falls around 55-65% of cycle. Not confirmed against a source. |
| sorghum | water | 0.45 | S2,S5,AE | ESTIMATE | Ordinal: below maize and groundnut in FAO water need. |
| sorghum | n_fixing | 0 | AE | CONFIRMED | Non-legume. |
| sorghum | cover | 0.5 | AE | ESTIMATE | Moderate canopy. |
| sorghum | market | 0.55 | AE | ESTIMATE | Needs farmer or market input. |
| millet | cycle_days | 90 | S6,S5 | CONFIRMED | Inside the 80-100 d class (S6). FAO's guide lists 105-140 d (S5), so this is an early variety. Local late millets run longer. |
| millet | min_rain_mm | 385 | S5 | DERIVED | 450 mm (lower bound for sorghum/millet) x 90/105 d = 386, rounded to 385. Crude scaling by cycle length. |
| millet | dry_tolerance_days | 14 | S14,AE | ESTIMATE | Near the 15 d class; millet is the most drought tolerant of the five. |
| millet | heat_metric | tmax | S18 | CONFIRMED | Tmax. |
| millet | heat_threshold_c | 40 | S18,AE | ESTIMATE | Weak support only (Tmax 40, Topt 34 in a modelling table). Millet is the most heat tolerant of the five. |
| millet | heat_days_limit | 5 | AE | ESTIMATE | Design parameter. |
| millet | flower_frac | [0.45, 0.6] | AE | ESTIMATE | Panicle emergence and flowering typically around 50-60% of a ~90 d cycle. Not confirmed against a source. |
| millet | water | 0.35 | S5,AE | ESTIMATE | Ordinal: lowest water use. |
| millet | n_fixing | 0 | AE | CONFIRMED | Non-legume. |
| millet | cover | 0.45 | AE | ESTIMATE | Sparser canopy than the other crops. |
| millet | market | 0.5 | AE | ESTIMATE | Needs farmer or market input. |
| cowpea | cycle_days | 85 | S7,S8 | CONFIRMED | Improved lines mature in 68-85 d (S7), extra-early in 60-65 d (S8). 85 is the conservative top of the range. Landraces run longer. FAO-56's 110 d is Mediterranean and not used. |
| cowpea | min_rain_mm | 360 | S2,S3,S5 | DERIVED | Scaled by cycle length: 450 x 85/115 = 333 (sorghum basis) and 500 x 85/110 = 386 (groundnut basis); mean ~360. No cowpea-specific seasonal figure found. |
| cowpea | dry_tolerance_days | 12 | S14,AE | ESTIMATE | Between the 10 d and 15 d classes. Cowpea is fairly drought tolerant. |
| cowpea | heat_metric | tmin | S9,S10 | CONFIRMED | CHANGED from Tmax to Tmin: night temperature drives pod-set loss. |
| cowpea | heat_threshold_c | 25 | S9,S10 | ESTIMATE | Night temperature: no damage at 20 C, strong bud suppression at 30 C (S10). 25 C is the midpoint, a deduction. Calibrate against POWER Tmin; Gombe rainy-season nights may sit near 20-23 C. |
| cowpea | heat_days_limit | 5 | AE | ESTIMATE | Design parameter. |
| cowpea | flower_frac | [0.5, 0.7] | S7 | DERIVED | Flowering began at 41-52 d of 68-85 d = 0.48-0.76 of the cycle. Window set to 0.50-0.70. |
| cowpea | water | 0.4 | AE | ESTIMATE | Ordinal. No FAO cowpea water figure retrieved. |
| cowpea | n_fixing | 1 | S17,AE | CONFIRMED | Legume; cowpea left more residual N than soybean in the Ibadan trial (S17). |
| cowpea | cover | 0.8 | AE | ESTIMATE | Spreading types give dense ground cover. |
| cowpea | market | 0.6 | AE | ESTIMATE | Needs farmer or market input. |
| groundnut | cycle_days | 110 | S3,S4 | CONFIRMED | 90-115 d for sequential types, 120-140 d for alternate types (S3); 130 d in West Africa (S4). 110 suits short types. |
| groundnut | min_rain_mm | 500 | S3,S5 | CONFIRMED | CHANGED from 450 to 500: FAO says a rainfed crop needs about 500-700 mm of reliable rainfall. |
| groundnut | dry_tolerance_days | 12 | S14,AE | ESTIMATE | Near the 10 d class. Flowering and pod formation are most sensitive (S3). |
| groundnut | heat_metric | tmax | S12 | CONFIRMED | Tmax. |
| groundnut | heat_threshold_c | 35 | S12 | CONFIRMED | Flowering highly sensitive at 35 C and above. |
| groundnut | heat_days_limit | 5 | AE | ESTIMATE | Design parameter. |
| groundnut | flower_frac | [0.35, 0.65] | S3 | DERIVED | FAO stages: establishment 10-20 d, vegetative 25-35 d, flowering 30-40 d, total about 105-140 d. Flowering runs from about day 45 to 80 of ~127 = 0.35-0.63. |
| groundnut | water | 0.5 | S3,S5,AE | ESTIMATE | Ordinal: mid-range FAO water need. |
| groundnut | n_fixing | 1 | AE | CONFIRMED | Legume. |
| groundnut | cover | 0.7 | AE | ESTIMATE | Fairly dense, low canopy. |
| groundnut | market | 0.65 | AE | ESTIMATE | Needs farmer or market input. FAO chapter (S17) notes groundnut is commonly a sold crop. |

## References

- **S1**: FAO Land & Water, Crop information: Maize (fao.org/land-water/databases-and-software/crop-information/maize)
- **S2**: FAO Land & Water, Crop information: Sorghum (same site, /sorghum)
- **S3**: FAO Land & Water, Crop information: Groundnut (same site, /groundnut)
- **S4**: Allen et al. 1998, FAO Irrigation and Drainage Paper 56, ch. 6, Table 11 (fao.org/4/x0490e/x0490e0b.htm). The table says its values are indicative only
- **S5**: FAO seasonal crop water needs table (fao.org/3/u3160E/u3160e04.htm): maize 500-800, groundnut 500-700, sorghum/millet 450-650 mm; millet cycle 105-140 d
- **S6**: FAO agro-ecological zones Table A4.1 (fao.org/4/t0742e/T0742E11.htm): pearl millet cycle classes 60-80 and 80-100 d
- **S7**: Cowpea variety trials, Nigeria/Niger (core.ac.uk/download/478323334.pdf): flowering 41-52 d, maturity 68-85 d
- **S8**: Cowpea breeding paper (isgpb.org/journal/index.php/IJGPB/article/download/2541/953): extra-early lines mature in 60-65 d
- **S9**: A. E. Hall, 'Heat Stress and its Impact' (plantstress.com/?p=176): cowpea pod set damaged by high night temperature, not by much hotter days
- **S10**: 'Heat Injury during Early Floral Bud Development in Cowpea' (scilit.com/publications/dfa413c87eeda76c86933e252e0d2c55): 30 C nights suppress floral buds, 20 C normal. Secondary summary seen at encyclopedia.pub: yield falls per degree of night temperature above ~16.5 C
- **S11**: Maize heat-tolerance paper, EJ Plant Breeding (ejplantbreeding.org/index.php/EJPB/article/view/1448/1047): heat stress = Tmax above 35 C (and Tmin above 23 C)
- **S12**: Groundnut heat review, Agronomy 7(2):30 (mdpi.com/2073-4395/7/2/30): flowering highly sensitive at 35 C and above
- **S13**: Sorghum floret fertility paper (typeset.io/pdf/impact-of-high-temperature-stress-on-floret-fertility-and-2x62lmctwl.pdf): daytime maxima above 36 C reduce fertility
- **S14**: ICRISAT dry-spell analysis for West Africa (oar.icrisat.org/3054/1/JA_1222.pdf): probabilities of spells over 7, 10, 15 d
- **S15**: Adimassu et al., Intra-seasonal rainfall variability and crop yield, Upper East Ghana (agris.fao.org/search/en/records/67235fd58aa2fad1ce4701b2): 7, 10, 14, 21 d classes
- **S16**: Onset rule as described in arXiv 2106.12571 (Segou, Mali), attributed to Sivakumar 1988: from 1 May, 20 mm in 3 d, no spell over 7 d in next 30 d
- **S17**: FAO, Integrating crops and livestock in West Africa, ch. III (fao.org/4/x6543e/x6543e03.htm): cowpea left more residual N than soybean in ILCA Ibadan rotation
- **S18**: Ramirez-Villegas-type crop temperature table, PMC7581754 Table 3, seen only as a search snippet (page blocked): millet Topt 34, Tmax 40
- **AE**: Analyst estimate (no source retrieved); deduced from related evidence and general agronomic knowledge. Needs expert review

## Still needed from a human

- Local variety cycle lengths and farmer-preferred varieties for Gombe (extension officer or ADP).
- Market scores for all five crops (farmer or market-survey input).
- Expert review of every ESTIMATE, especially dry-spell tolerance and the cowpea Tmin threshold.
- Primary-source check of S10 (summary seen) and S18 (snippet only).
- Not retrieved: EcoCrop sheets for sorghum, millet and groundnut; FAO pages for millet and cowpea; IITA's cowpea farmer guide.
