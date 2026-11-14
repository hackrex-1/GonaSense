"""Onset detection tests.

Phase 2. The three cases from the implementation plan are staged as skips so
the test runner stays green until pipeline/metrics.py is implemented.
"""

import pytest


@pytest.mark.skip(reason="Phase 2: pipeline/metrics.py onset() not implemented")
def test_known_onset_is_found():
    """A synthetic series with a clear start returns that day-of-year."""


@pytest.mark.skip(reason="Phase 2: pipeline/metrics.py onset() not implemented")
def test_false_start_is_rejected():
    """Rain followed by a 10-day dry spell must not count as onset."""


@pytest.mark.skip(reason="Phase 2: pipeline/metrics.py onset() not implemented")
def test_no_onset_returns_none():
    """A dry search window returns None, which later counts as a failed season."""
