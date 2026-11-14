"""Central configuration for the Gombe Rotation Advisor pipeline.

Every tunable value lives here so thresholds can change without touching
logic. Anything that still needs a citation is flagged in
``docs/crop_table_sources.md``.

Run order (see README):
    python pipeline/fetch_power.py
    python pipeline/metrics.py
    python pipeline/export_json.py
"""

from pathlib import Path

# --------------------------------------------------------------------------
# Paths
# --------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "raw"
WEB_DATA_DIR = BASE_DIR / "web" / "data"
DOCS_DIR = BASE_DIR / "docs"

# --------------------------------------------------------------------------
# Time span
# --------------------------------------------------------------------------
YEARS = (2001, 2024)

# --------------------------------------------------------------------------
# Locations: one centroid per LGA in Gombe State.
#
# Derived from geoBoundaries gbOpen NGA ADM2 (GRID3, 2022, CC BY 4.0),
# filtered to Gombe State. Centroids are area-weighted polygon centroids,
# not guessed coordinates. Guyuk (Adamawa) is excluded even though the
# simplified boundary touches the state edge. See docs/sources.md.
#
# Format: id: (display name, latitude, longitude)
# --------------------------------------------------------------------------
LOCATIONS = {
    "akko":         ("Akko",         10.1077, 11.0378),
    "balanga":      ("Balanga",       9.8380, 11.6511),
    "billiri":      ("Billiri",       9.8308, 11.1233),
    "dukku":        ("Dukku",        10.7864, 10.8613),
    "funakaye":     ("Funakaye",     10.7862, 11.3751),
    "gombe":        ("Gombe",        10.3028, 11.1857),
    "kaltungo":     ("Kaltungo",      9.8546, 11.4188),
    "kwami":        ("Kwami",        10.4949, 11.1835),
    "nafada":       ("Nafada",       11.0364, 11.2091),
    "shongom":      ("Shongom",       9.6604, 11.2006),
    "yamaltu-deba": ("Yamaltu/Deba", 10.2626, 11.4726),
}

# --------------------------------------------------------------------------
# Rainfall onset (verify and cite before submission)
# --------------------------------------------------------------------------
ONSET = dict(
    amount_mm=20,        # cumulative rain that can start the season
    window_days=3,       # ... measured over this many days
    dry_days=7,          # a false start is followed by this many dry days
    lookahead_days=30,   # give up searching after this long
    earliest="04-01",    # search window start (MM-DD)
    latest="10-31",      # search window end (MM-DD)
)

DRY_DAY_MM = 1.0
ONSET_MAX_MISSING_SHARE = 0.05    # skip a year if more of the search window is missing
WINDOW_MAX_MISSING_SHARE = 0.05   # reject a crop season above this missing share

# --------------------------------------------------------------------------
# Scenario grid (sensitivity test, not a forecast)
# --------------------------------------------------------------------------
RAIN_MULTS = [0.8, 0.9, 1.0, 1.1]
TEMP_DELTAS = [0, 1, 2]   # degrees Celsius added to Tmax and Tmin
BASE_SCENARIO = "rain+0_temp+0"

# --------------------------------------------------------------------------
# Bare-field detection from NDVI
# --------------------------------------------------------------------------
NDVI_BARE_THRESHOLD = 0.25   # tune from the data, then document
NDVI_BARE_MONTHS = (4, 11)   # 1 April - 30 November

# --------------------------------------------------------------------------
# NASA POWER
# --------------------------------------------------------------------------
POWER_API = "https://power.larc.nasa.gov/api/temporal/daily/point"
POWER_PARAMS = ("T2M_MAX", "T2M_MIN", "PRECTOTCORR", "GWETROOT")
POWER_COMMUNITY = "AG"
POWER_FILL_VALUE = -999.0
POWER_RETRIES = 3
POWER_PAUSE_SECONDS = 1.5
POWER_MAX_MISSING_SHARE = 0.02


def dekads():
    """Return the 36 dekad labels used in every exported series."""
    return [
        f"{month:02d}-{start:02d}"
        for month in range(1, 13)
        for start in (1, 11, 21)
    ]


def all_scenarios():
    """Scenario keys for the rain x temperature grid, base case first."""
    keys = []
    for mult in RAIN_MULTS:
        for delta in TEMP_DELTAS:
            pct = round((mult - 1) * 100)
            keys.append(f"rain{pct:+d}_temp{delta:+d}")
    return keys


if __name__ == "__main__":
    print(f"Locations: {len(LOCATIONS)}")
    print(f"Scenarios: {len(all_scenarios())} -> {', '.join(all_scenarios())}")
    print(f"Dekads: {len(dekads())} -> {', '.join(dekads()[:3])} ...")
