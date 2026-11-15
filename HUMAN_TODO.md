# Human TODO

Items a person must complete before this can be presented as validated advice.
Each item says where the work goes.

## Data and thresholds

- [ ] **Verify every crop value** in `web/data/crops.json` against IITA and
      FAO sources, fill `docs/crop_table_sources.md`, then set
      `"provisional": false` per crop. The page currently tags every score
      containing these crops as an estimate.
- [ ] **Confirm and cite the onset definition**, the 7-day dry-spell guard and
      the heat thresholds in `pipeline/config.py`. The current values are
      provisional: 20 mm over 3 days, 7 dry days within 30, search 1 April to
      31 October.
- [ ] **Calibrate the cowpea night-heat threshold** (Tmin > 25 C during
      flowering). In the current 2001-2024 NASA POWER build, all 24 seasons at
      all 11 LGAs passed this check, so it does not distinguish seasons yet.
      Review the threshold with a local agronomist before treating it as useful
      risk evidence.
- [ ] **Replace the remaining synthetic strategy copy** in
      `web/data/strategies.json` with reviewed gaps and risks, and confirm
      strategies B, C and D with IITA or a local agronomist.
- [ ] **Tune `NDVI_BARE_THRESHOLD`** (currently 0.25) after real NDVI arrives.
- [ ] **Update the year range** if POWER is refreshed beyond 2024.

## Satellite data

- [ ] **Create a free NASA Earthdata login** and provide credentials through
      environment variables to enable IMERG and SMAP. Add `raw/imerg_<id>.csv`
      and `raw/smap_<id>.csv`; the confidence label then stops saying
      "Medium (single source)".
- [ ] **Export MODIS NDVI for the 11 locations from AppEEARS** as
      `raw/ndvi_<id>.csv` with columns `date,ndvi`, then re-run the pipeline.
      This is the only missing piece for requirement R8.
- [ ] **Run `python -m pipeline.run_all --mode nasa --refresh` on a machine
      with internet access.** The current nasa build used cached
      `raw/power_<id>.csv` files because `power.larc.nasa.gov` was unreachable
      from the build environment. The cached files are real, complete POWER
      data (8,766 rows per LGA, 2001-2024), but they were not re-downloaded in
      this session.

## Verification and content

- [ ] **Hand-check one location and one year of onset** against the raw daily
      rain and against NiMet seasonal information or farmer experience. The
      Gombe 2001 spot check in `docs/method.md` is a start, not validation.
- [ ] **Add farmer or extension-worker conversation notes** to `docs/`. This
      is the local knowledge the tool is meant to support.
- [ ] **Replace the live-link and screenshot placeholders** in `README.md`.
- [ ] **Fill the Team section** in `README.md`.

## Deployment

- [ ] **Enable GitHub Pages** in the repository settings (source: GitHub
      Actions), push to `main`, and add the live URL to `README.md`. The
      workflow is `.github/workflows/pages.yml`.
- [ ] **Confirm the deployed sub-path works.** All asset URLs are relative, but
      this must be seen on the real Pages URL.
- [ ] **Re-run the nasa build, confirm the demo banner is gone, and capture
      fresh screenshots** of desktop and 360 px layouts.

## Known environment limits

- No network access to `power.larc.nasa.gov`, `modis.ornl.gov` or
  `gibs.earthdata.nasa.gov` from the build machine. Cached POWER CSVs make the
  nasa build possible; NDVI and IMERG are not.
- The build machine's browser can cache old CSS/JS after a rebuild. Use a hard
  reload or a fresh port when reviewing.
