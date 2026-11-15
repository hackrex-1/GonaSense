"""Crop-year, aggregation, scenario and harmonization tests."""

import pandas as pd
import pytest

from pipeline import config, harmonize, metrics


def season_rain(daily, start, end, amount=8.0):
    for date in pd.date_range(start, end, freq="D"):
        daily.loc[date, "PRECTOTCORR"] = amount
    return daily


def test_longest_run_on_known_masks():
    assert metrics.longest_run([True, True, False, True, True, True]) == 3
    assert metrics.longest_run([False, False]) == 0
    assert metrics.longest_run([]) == 0


def test_crop_year_passes_when_limits_are_met(make_daily, crop):
    daily = season_rain(make_daily(), "2001-05-01", "2001-08-20")
    result = metrics.crop_year(daily, pd.Timestamp("2001-05-01"), crop)

    assert result["valid"] is True
    assert result["rain_ok"] and result["dry_ok"] and result["heat_ok"]
    assert result["all_ok"] is True
    assert result["rain_mm"] >= crop["min_rain_mm"]


def test_crop_year_fails_on_a_known_dry_spell(make_daily, crop):
    daily = make_daily()
    for date in pd.date_range("2001-05-01", "2001-08-08", freq="15D"):
        daily.loc[date, "PRECTOTCORR"] = 80.0

    result = metrics.crop_year(daily, pd.Timestamp("2001-05-01"), crop)

    assert result["valid"] is True
    assert result["dry_ok"] is False
    assert result["dry_days"] > crop["dry_tolerance_days"]
    assert result["all_ok"] is False


def test_crop_year_fails_on_known_heat_days(make_daily, crop):
    daily = season_rain(make_daily(tmax=40.0), "2001-05-01", "2001-08-20")
    result = metrics.crop_year(daily, pd.Timestamp("2001-05-01"), crop)

    assert result["valid"] is True
    assert result["heat_days"] > crop["heat_days_limit"]
    assert result["heat_ok"] is False


def test_crop_year_fails_on_season_rain(make_daily, crop):
    daily = season_rain(make_daily(), "2001-05-01", "2001-08-20", amount=1.0)
    result = metrics.crop_year(daily, pd.Timestamp("2001-05-01"), crop)
    assert result["rain_ok"] is False
    assert result["rain_mm"] < crop["min_rain_mm"]


def test_no_onset_year_adds_zero_counts_and_one_to_n_total(make_daily, crop):
    def season(year):
        frame = make_daily(year=year)
        if year != 2003:
            season_rain(frame, f"{year}-05-01", f"{year}-08-20")
        return frame

    daily = pd.concat([season(2001), season(2002), season(2003)])
    result = metrics.compute_location(
        daily, {"maize": crop}, harmonize.harmonize(daily), "synthetic",
        years=[2001, 2002, 2003],
    )
    counts = result["scenarios"][config.BASE_SCENARIO]["maize"]

    assert result["n_total"] == 3
    assert result["no_onset_years"] == [2003]
    assert counts["n_total"] == 3
    assert counts["all_ok"] == 2
    assert counts["rain_ok"] == 2


def test_scenario_key_format_matches_the_spec():
    assert config.scenario_key(1.0, 0) == "rain+0_temp+0"
    assert config.scenario_key(0.9, 1) == "rain-10_temp+1"
    assert config.scenario_key(1.1, 2) == "rain+10_temp+2"
    assert config.scenario_key(0.8, 0) == "rain-20_temp+0"


def test_every_scenario_is_written(make_daily, crop):
    daily = season_rain(make_daily(), "2001-05-01", "2001-08-20")
    result = metrics.compute_scenarios(daily, {"maize": crop}, [2001])

    assert len(config.all_scenarios()) == 12
    assert set(result["scenarios"]) == set(config.all_scenarios()) | {"base"}
    assert result["scenarios"]["base"] == "rain+0_temp+0"


def test_rain_scenario_scales_the_pass_counts(make_daily, crop):
    # One season with 470 mm: below the 500 mm limit, above it at +10% rain,
    # and further below at -10%. This proves the multiplier reaches the check.
    daily = make_daily()
    for date in pd.date_range("2001-05-01", "2001-05-03", freq="D"):
        daily.loc[date, "PRECTOTCORR"] = 10.0
    for date in pd.date_range("2001-05-04", "2001-08-09", freq="D"):
        daily.loc[date, "PRECTOTCORR"] = 390.0 / 98.0

    result = metrics.compute_scenarios(daily, {"maize": crop}, [2001])

    assert result["n_total"] == 1
    assert result["scenarios"]["rain+0_temp+0"]["maize"]["rain_ok"] == 0
    assert result["scenarios"]["rain+10_temp+0"]["maize"]["rain_ok"] == 1
    assert result["scenarios"]["rain-10_temp+0"]["maize"]["rain_ok"] == 0


def test_harmonize_produces_36_dekads_per_year(make_daily):
    daily = make_daily()
    table = harmonize.harmonize(daily, None)

    assert len(table) == 36
    assert table["dekad"].tolist() == list(range(1, 37))
    assert pd.isna(table["ndvi"]).all()


def test_harmonize_sums_rain_and_averages_temperature(make_daily):
    daily = make_daily()
    season_rain(daily, "2001-01-01", "2001-01-31", amount=1.0)
    daily = daily.loc["2001-01-01":"2001-01-31"]
    table = harmonize.harmonize_daily(daily)

    assert table["rain_mm"].tolist() == [10.0, 10.0, 11.0]
    assert table["tmax"].tolist() == [32.0, 32.0, 32.0]


def test_dekad_index_maps_month_ends():
    assert harmonize.dekad_index("2001-01-01") == 1
    assert harmonize.dekad_index("2001-01-31") == 3
    assert harmonize.dekad_index("2001-12-31") == 36
    assert len(harmonize.bare_dekads()) == 24


def test_bare_share_flags_only_the_april_to_november_window():
    means = [0.6] * 36
    for index in range(10, 16):  # six bare dekads inside the window
        means[index - 1] = 0.2
    share, flags = harmonize.bare_share_from_means(means)

    assert len(flags) == 36
    assert sum(flags) == 6
    assert share == pytest.approx(6 / 24, abs=0.001)


def test_bare_share_is_null_without_ndvi():
    assert harmonize.bare_share_from_means(None) == (None, None)
    assert harmonize.ndvi_dekad_means(None) is None
