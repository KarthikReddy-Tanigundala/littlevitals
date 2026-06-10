"""Cross-platform ingestion orchestrator (canonical entrypoint — CLAUDE.md §16.5).

Sequences: AIHW API → Synthea → ABS geography. dbt owns the transform DAG; this
only sequences ingest → (then run `dbt build`). Idempotent and safe to re-run.

Run:
    python ingestion/run_all_ingestion.py --source snapshot --dry-run   # offline check
    python ingestion/run_all_ingestion.py --source live                 # → Snowflake
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ingest_abs_geography  # noqa: E402
import ingest_aihw_api  # noqa: E402
import ingest_synthea  # noqa: E402

logger = logging.getLogger(__name__)


def main(source: str = "snapshot", load: bool = True) -> dict[str, dict]:
    summary = {
        "aihw_api": ingest_aihw_api.main(source=source, load=load),
        "synthea": ingest_synthea.main(load=load),
        "abs_geography": ingest_abs_geography.main(load=load),
    }
    logger.info("Ingestion summary: %s", summary)
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", choices=["live", "snapshot"], default="snapshot")
    parser.add_argument("--dry-run", action="store_true",
                        help="Fetch/parse only; do not load to Snowflake.")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    main(source=args.source, load=not args.dry_run)
