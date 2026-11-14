"""Optional IMERG daily-rain fetcher for the satellite cross-check.

PHASE 5 (optional). Fallback rule from the plan: if this is not working by
hour 20, drop it, use POWER for rain, and say so in the limits panel.

Planned output: ``raw/imerg_<id>.csv`` with columns ``date, rain_mm``.
Requires an Earthdata login and ``earthaccess``.
"""

from __future__ import annotations


def main() -> int:
    raise SystemExit(
        "pipeline/fetch_imerg.py is optional and not implemented yet.\n"
        "See implementation plan section 4.3 for the data source and fallback rule."
    )


if __name__ == "__main__":
    raise SystemExit(main())
