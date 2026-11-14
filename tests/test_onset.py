"""Onset detection tests using synthetic rainfall (implementation plan 8)."""

import pandas as pd

from pipeline import metrics


def test_known_onset_is_found(make_daily):
    events = {f"2001-05-{day}": 10.0 for day in (20, 21, 22)}
    for date in pd.date_range("2001-05-23", "2001-09-30", freq="3D"):
        events[date] = 5.0

    daily = make_daily(events=events)

    # Earliest 3-day window reaching 20 mm starts on 19 May (day 139).
    assert metrics.onset(daily) == 139


def test_false_start_is_rejected(make_daily):
    # A 30 mm burst on 10-12 April, then nothing until 1 July.
    events = {f"2001-04-{day}": 10.0 for day in (10, 11, 12)}
    events.update({f"2001-07-{day}": 10.0 for day in (1, 2, 3)})
    for date in pd.date_range("2001-07-04", "2001-10-15", freq="3D"):
        events[date] = 5.0

    daily = make_daily(events=events)

    # The April burst fails the dry-spell guard; the July window starts on
    # 30 June (day 181), the day before the rain arrives.
    assert metrics.onset(daily) == 181


def test_no_onset_returns_none(make_daily):
    assert metrics.onset(make_daily()) is None


def test_year_with_too_much_missing_rain_is_skipped(make_daily):
    events = {}
    for date in pd.date_range("2001-05-20", "2001-09-30", freq="3D"):
        events[date] = 5.0
    daily = make_daily(events=events)

    # Blank out every sixth day from April to October: about 17% missing.
    search = daily.loc["2001-04-01":"2001-10-31"].index[::6]
    daily.loc[search, "PRECTOTCORR"] = float("nan")

    assert metrics.onset(daily) is None


def test_onsets_are_detected_per_year(make_daily):
    def season(year):
        events = {f"{year}-06-{day:02d}": 10.0 for day in (1, 2, 3)}
        for date in pd.date_range(f"{year}-06-04", f"{year}-09-30", freq="3D"):
            events[date] = 5.0
        return make_daily(year=year, events=events)

    daily = pd.concat([season(2001), season(2002)])
    onsets = metrics.onsets_by_year(daily)

    assert list(onsets) == ["2001", "2002"]
    assert onsets["2001"] == 151
    assert onsets["2002"] == 151
