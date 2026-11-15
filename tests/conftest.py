import json
from pathlib import Path

import pandas as pd
import pytest

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "web" / "data"


@pytest.fixture
def make_daily():
    """Build a synthetic daily POWER-shaped frame for one or more years."""

    def _make(year=2001, events=None, tmax=32.0, tmin=22.0, soil=0.4):
        index = pd.date_range(f"{year}-01-01", f"{year}-12-31", freq="D")
        frame = pd.DataFrame({
            "PRECTOTCORR": 0.0,
            "T2M_MAX": float(tmax),
            "T2M_MIN": float(tmin),
            "GWETROOT": float(soil),
        }, index=index)
        for date, amount in (events or {}).items():
            frame.loc[pd.Timestamp(date), "PRECTOTCORR"] = float(amount)
        return frame

    return _make


@pytest.fixture
def crop():
    """A local crop definition, independent of the researched crop table."""
    return {
        "cycle_days": 100,
        "min_rain_mm": 450,
        "dry_tolerance_days": 10,
        "heat_metric": "tmax",
        "heat_threshold_c": 35,
        "heat_days_limit": 4,
        "flower_frac": [0.4, 0.6],
    }


@pytest.fixture
def dataset(tmp_path):
    """Write a minimal valid set of five contracts and return the directory."""
    crops = json.loads((DATA / "crops.json").read_text(encoding="utf-8"))
    strategies = json.loads((DATA / "strategies.json").read_text(encoding="utf-8"))
    glossary = json.loads((DATA / "glossary.json").read_text(encoding="utf-8"))

    crops = dict(list(crops.items())[:2])
    strategies = [{
        "id": "B", "name": "Test mix", "sequence": list(crops),
        "benefits": ["x"], "gaps": ["y"], "risks": ["z"],
    }]

    counts = {"rain_ok": 5, "dry_ok": 5, "heat_ok": 5, "all_ok": 5, "n_total": 10}
    scenarios = {
        key: {crop_id: dict(counts) for crop_id in crops}
        for key in [
            f"rain{pct:+d}_temp{temp:+d}"
            for pct in (-20, -10, 0, 10)
            for temp in (0, 1, 2)
        ]
    }
    scenarios["base"] = "rain+0_temp+0"
    metrics = {
        "data_mode": "synthetic",
        "generated": "2026-01-01",
        "years": [2001, 2024],
        "sources_used": ["test"],
        "locations": {
            "gombe": {
                "n_total": 10,
                "no_onset_years": [],
                "bad_data_years": [],
                "confidence": "Not applicable (demo data)",
                "confidence_reason": "Test data.",
                "bare_share": None,
                "ndvi_dekad": None,
                "bare_flags": None,
                "onset_by_year": {"2001": 140},
                "scenarios": scenarios,
            },
        },
    }
    locations = [{
        "id": "gombe", "name": "Gombe", "lat": 10.3, "lon": 11.18,
        "coords_status": "test centroid",
    }]

    for name, payload in (
        ("crops.json", crops),
        ("strategies.json", strategies),
        ("glossary.json", glossary),
        ("locations.json", locations),
        ("metrics.json", metrics),
    ):
        (tmp_path / name).write_text(json.dumps(payload), encoding="utf-8")
    return tmp_path
