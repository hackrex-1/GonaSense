# Data sources

Record versions, access dates and licences here. Update this file whenever a
fetcher changes product or date range.

## In use

### NASA POWER - Daily point API

- Endpoint: `https://power.larc.nasa.gov/api/temporal/daily/point`
- Community: `AG` (agroclimatology)
- Parameters: `T2M_MAX`, `T2M_MIN`, `PRECTOTCORR`, `GWETROOT`
- Period: 2001-01-01 to 2024-12-31
- Spatial unit: LGA centroid (one point per LGA)
- Missing value sentinel: `-999`, replaced with NaN by `fetch_power.py`
- Access: no login; accessed 2026-11-14
- Licence: NASA open data (see the POWER data policy)
- Notes: modelled reanalysis, not ground observations. Root-zone wetness
  (`GWETROOT`) is a model estimate and is described as such in the limits
  panel.
- Resolution caveat: the POWER grid is coarser than a Gombe LGA, so several
  neighbouring LGAs receive identical series. Akko, Billiri and Kaltungo
  match exactly; Gombe and Kwami match; Funakaye and Nafada match. This is
  documented in the page's limits panel and must not be presented as
  field-level variation.

### geoBoundaries - Nigeria ADM2 (LGA boundaries)

- Product: `geoBoundaries-NGA-ADM2_simplified.geojson`
- Release: gbOpen, 2022 boundaries; source GRID3
- API record: `https://www.geoboundaries.org/api/current/gbOpen/NGA/ADM2/`
- Licence: CC BY 4.0
- Use: area-weighted centroids for the 11 Gombe State LGAs in
  `pipeline/config.py`. Access date 2026-11-14.
- Note: Guyuk appears near the Gombe border in the simplified geometry but is
  an Adamawa LGA, so it is excluded.

### GADM - Nigeria level 2 (state mask only)

- Product: `gadm41_NGA_2.json` (v4.1)
- Source: `https://geodata.ucdavis.edu/gadm/gadm4.1/json/gadm41_NGA_2.json.zip`
- Use: point-in-polygon mask to keep only LGA centroids inside Gombe State.
  It is not used for coordinates in the app.
- Licence: GADM is free for academic and non-commercial use; check the GADM
  licence before redistributing derived boundary files.
- Access date: 2026-11-14.

## Optional (Phase 5)

### GPM IMERG - Final Run daily precipitation

- Use: independent rain series to cross-check POWER and set confidence labels.
- Planned output: `raw/imerg_<id>.csv` with `date, rain_mm`.
- Access: NASA Earthdata login via `earthaccess`.
- Status: not fetched yet. Fallback is POWER-only plus an honest limits note.

### SMAP - surface soil moisture (SPL3SMP)

- Use: independent soil-moisture check; record starts in 2015.
- Planned output: `raw/smap_<id>.csv` with `date, sm`.
- Limitation: coarse footprint, so it cannot resolve a field.
- Status: not fetched yet.

### MODIS MOD13Q1 - 16-day NDVI via AppEEARS

- Use: bare-field share and the shaded NDVI chart.
- Planned output: `raw/ndvi_<id>.csv` with `date, ndvi`.
- Processing: apply quality flags, scale per product documentation, linearly
  interpolate to daily, then average per dekad.
- Status: not requested yet. If unavailable, `bare_share` is `null` and the
  page states the limitation.

## How the LGA centroids were derived

1. Download the geoBoundaries Nigeria ADM2 simplified GeoJSON (api record
   above).
2. Download GADM Nigeria level 2 and keep only features with
   `NAME_1 == "Gombe"`; dissolve their outer rings into a state mask.
3. For each ADM2 feature, compute the area-weighted centroid of all polygon
   parts.
4. Keep features whose centroid falls inside the Gombe state mask.
5. Drop Guyuk (Adamawa) and round coordinates to 4 decimal places.

The run used Python's standard library only (`json`, `zipfile`); no manual
coordinate typing. If a boundary release changes, rerun this and update
`pipeline/config.py`, then refresh `web/data/locations.json`.

## Citation block for the README

> NASA POWER (NASA Langley Research Center), accessed 2026-11-14.
> geoBoundaries gbOpen NGA ADM2, GRID3 (2022), CC BY 4.0.
> GADM v4.1 used for state masking only.
