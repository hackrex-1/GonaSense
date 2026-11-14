"""Write the frozen JSON contracts into ``web/data/``.

PHASE 2 - NOT IMPLEMENTED YET.

Planned flow:
  1. Load cached raw/ series and the crop table.
  2. Run metrics (onset, crops, scenarios, bare share) per location.
  3. Write locations.json, crops.json, strategies.json, metrics.json,
     glossary.json into web/data/.
  4. Call pipeline.validate.validate_all() and exit non-zero on errors.

Until then, web/data/ contains hand-written mock files with the same shape
so the front end can be built against real contracts.
"""

from __future__ import annotations

try:
    from . import config, validate
except ImportError:  # pragma: no cover - script mode
    import config
    import validate


def main() -> int:
    raise SystemExit(
        "pipeline/export_json.py is a Phase 2 module and is not implemented yet.\n"
        "Run `python pipeline/validate.py` to check the current mock contracts."
    )


if __name__ == "__main__":
    raise SystemExit(main())
