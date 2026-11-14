"""Optional MODIS NDVI loader for the bare-field analysis.

PHASE 5 (optional). Submit a point request in AppEEARS for a MODIS 16-day
NDVI product (for example MOD13Q1) for all centroids, download the CSV,
apply the quality flags, and scale values as the product documentation says.

Planned output: ``raw/ndvi_<id>.csv`` with columns ``date, ndvi``.
"""

from __future__ import annotations


def main() -> int:
    raise SystemExit(
        "pipeline/fetch_ndvi.py is optional and not implemented yet.\n"
        "It expects an AppEEARS export; see implementation plan section 4.3."
    )


if __name__ == "__main__":
    raise SystemExit(main())
