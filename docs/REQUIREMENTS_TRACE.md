# Requirements trace

Each row maps a requirement from section 1 of the implementation plan to the
code that satisfies it. "Verified" means the behaviour was checked in the
running page, not only read in source. See `docs/QA.md` for the checks.

| ID | Requirement | Where it is satisfied | Status |
| --- | --- | --- | --- |
| R1 | Combine NASA data with local agricultural information (crop knowledge table) in a decision-support tool | `pipeline/` computes POWER-based season checks; `web/data/crops.json` holds the crop table; `web/js/scoring.js` combines them; `web/js/ui.js` renders cards | DONE |
| R2 | Compare at least three rotation strategies, including the farmer's existing one | `web/js/main.js` builds strategy A from `state.existing` plus strategies B/C/D from `strategies.json`; `web/js/ui.js` renders four cards | DONE |
| R3 | Each strategy card has five labelled sections: Why suggested, Evidence, Benefits, Information gaps, Risks needing local review | `renderCard` in `web/js/ui.js` appends all five `section()` blocks in order | DONE |
| R4 | Farmer can enter priorities or constraints, and the ranking changes live | six sliders in `renderPriorities` (`ui.js`); `rank()` in `scoring.js`; verified 67 -> 66 when Save water moved to 5 | DONE |
| R5 | Uncertainty is explained: counts of past years, confidence label per location, data-limits panel, "ask a local expert" lines | `evidenceLine` in `text.js`; `confidence`/`confidence_reason` in `metrics.json`; `renderLimits` and `ask-expert` line in `ui.js` | DONE |
| R6 | Satellite versus ground data is explained, including that no ground stations were used | `strings.limitsSatellite`, rendered by `renderLimits` in `ui.js` | DONE |
| R7 | Datasets of different resolution are harmonized to one grid (location x 10-day period) | `pipeline/harmonize.py` builds 36 dekads per location-year; tested by `tests/test_metrics.py` | DONE |
| R8 | Bare-field periods and seasonal vulnerability are highlighted | `web/js/charts.js` has the `bareShade` plugin and shaded-dekad logic; `harmonize.bare_share_from_means` computes flags. **This build has no NDVI source**, so the chart shows the required "Greenness data not loaded for this build" note and the 30% default instead of shading | PARTIAL (explained) |
| R9 | Interpretable by farmers with limited technical experience: plain language, traffic-light scores, glossary | `web/js/strings.js` copy; `trafficLight()` in `scoring.js`; `renderGlossary` in `ui.js` | DONE |
| R10 | Visible message on every card that the tool supports, not replaces, farmer judgment | `strings.support`, appended to every card in `renderCard` | DONE |
| R11 | Optional: map, timeline, scenario sliders | Leaflet map in `web/js/map.js`; onset chart in `charts.js`; rain/temperature radio groups in `ui.js` | DONE (optional items implemented) |

## Why R8 is partial

The chart code and the shading plugin are complete and tested against the
`bare_flags` contract. The current environment has no reachable NDVI product
(MODIS/AppEEARS and GIBS were unavailable), and the project rule forbids
inventing values. The page therefore degrades as specified: the canvas is
hidden, the wrapper collapses, and the note says the score uses the documented
30% default. Supplying `raw/ndvi_<id>.csv` and re-running the pipeline enables
the shading without a front-end change.
