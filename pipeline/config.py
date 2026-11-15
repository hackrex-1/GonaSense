"""Central configuration for the GonaSense pipeline.

Every tunable value lives here so thresholds can change without touching
logic. Values that still need a citation are marked PROVISIONAL and are
tracked in ``docs/crop_table_sources.md`` and ``HUMAN_TODO.md``.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

# --------------------------------------------------------------------------
# Paths
# --------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "raw"
DATA_DIR = BASE_DIR / "web" / "data"
WEB_DATA_DIR = DATA_DIR
DOCS_DIR = BASE_DIR / "docs"

# --------------------------------------------------------------------------
# Time span
# --------------------------------------------------------------------------
YEARS = (2001, 2024)

# --------------------------------------------------------------------------
# Rainfall onset
# PROVISIONAL: confirm and cite a West African onset definition.
# --------------------------------------------------------------------------
ONSET = dict(
    amount_mm=20.0,
    window_days=3,
    dry_days=7,
    lookahead_days=30,
    earliest="04-01",
    latest="10-31",
)

DRY_DAY_MM = 1.0
MAX_MISSING_FRAC = 0.05  # years with more missing rain than this are excluded
# Kept for the older module names; both refer to the same rule.
ONSET_MAX_MISSING_SHARE = MAX_MISSING_FRAC
WINDOW_MAX_MISSING_SHARE = MAX_MISSING_FRAC

# --------------------------------------------------------------------------
# Scenario grid (sensitivity tests, never forecasts)
# --------------------------------------------------------------------------
RAIN_MULTS = [0.8, 0.9, 1.0, 1.1]
TEMP_DELTAS = [0, 1, 2]  # degrees Celsius added to Tmax and Tmin
BASE_SCENARIO = "rain+0_temp+0"

# --------------------------------------------------------------------------
# Bare-field detection from NDVI
# PROVISIONAL: tune from data once real NDVI is available.
# --------------------------------------------------------------------------
NDVI_BARE_THRESHOLD = 0.25
BARE_SEASON = ("04-01", "11-30")  # window for bare_share
DEFAULT_BARE_SHARE = 0.30  # only when NDVI is missing; the UI must say so

# --------------------------------------------------------------------------
# Synthetic generator
# --------------------------------------------------------------------------
SYNTH_SEED = 2026

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
POWER_TIMEOUT_SECONDS = 120

# --------------------------------------------------------------------------
# Exports
# --------------------------------------------------------------------------
MAX_DATA_BYTES = 5 * 1024 * 1024


def dekads() -> list[str]:
    """The 36 dekad labels (MM-DD) used in every exported series."""
    return [
        f"{month:02d}-{start:02d}"
        for month in range(1, 13)
        for start in (1, 11, 21)
    ]


def scenario_key(rain_mult: float, temp_delta: int) -> str:
    """Canonical scenario key shared with ``web/js/scoring.js``."""
    percent = round((rain_mult - 1) * 100)
    return f"rain{percent:+d}_temp{temp_delta:+d}"


def all_scenarios() -> list[str]:
    """Scenario keys for the rain x temperature grid, in stable order."""
    return [scenario_key(mult, delta) for mult in RAIN_MULTS for delta in TEMP_DELTAS]


def data_years() -> list[int]:
    """Every calendar year in the study period, inclusive."""
    return list(range(YEARS[0], YEARS[1] + 1))


def year_span_text() -> str:
    return f"{YEARS[0]}-01-01 to {YEARS[1]}-12-31"


def today_iso() -> str:
    return date.today().isoformat()


if __name__ == "__main__":
    print(f"Years: {YEARS[0]}-{YEARS[1]} ({len(data_years())} seasons)")
    print(f"Scenarios: {len(all_scenarios())}: {', '.join(all_scenarios())}")
    print(f"Dekads: {len(dekads())} -> {', '.join(dekads()[:3])} ...")
