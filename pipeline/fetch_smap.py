"""Optional SMAP surface-soil-moisture fetcher.

PHASE 5 (optional). SMAP starts in 2015 and has coarse resolution; both
limits must be stated in the limits panel if this is used.

Planned output: ``raw/smap_<id>.csv`` with columns ``date, sm``.
"""

from __future__ import annotations


def main() -> int:
    raise SystemExit(
        "pipeline/fetch_smap.py is optional and not implemented yet.\n"
        "See implementation plan section 4.3 for the data source and fallback rule."
    )


if __name__ == "__main__":
    raise SystemExit(main())
