"""Ingest Synthea synthetic patient data → Snowflake BRONZE.

Production path: run the Synthea generator (Java) for Victorian demographics,
then point this script at its CSV output. Offline path: read the committed
synthetic fixtures (Synthea-style schema). Either way the BRONZE tables are the
same shape. See ingestion/README.md for the Synthea install + run command.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config  # noqa: E402
import snowflake_loader  # noqa: E402

logger = logging.getLogger(__name__)

# Synthea fixture file -> BRONZE table.
TABLES = {
    "raw_synthea_patients.csv": "RAW_SYNTHEA_PATIENTS",
    "raw_synthea_encounters.csv": "RAW_SYNTHEA_ENCOUNTERS",
    "raw_synthea_conditions.csv": "RAW_SYNTHEA_CONDITIONS",
}


def _read_fixture(name: str, source_dir: Path | None) -> pd.DataFrame:
    dirs = [source_dir] if source_dir else config.SNAPSHOT_SEARCH_DIRS
    for directory in dirs:
        path = directory / name
        if path.exists():
            return pd.read_csv(path)
    raise FileNotFoundError(f"Synthea file not found: {name}")


def main(source_dir: str | None = None, load: bool = True) -> dict[str, int]:
    """Load Synthea tables. `source_dir` overrides the fixture search (live export)."""
    src = Path(source_dir) if source_dir else None
    counts: dict[str, int] = {}
    for filename, table in TABLES.items():
        df = _read_fixture(filename, src)
        counts[table] = len(df)
        logger.info("Read %s rows for %s", len(df), table)
        if load:  # pragma: no cover - requires Snowflake
            snowflake_loader.load_dataframe_to_snowflake(df, table)
    return counts


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--synthea-output", help="Path to a real Synthea CSV output dir.")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    logger.info("Done: %s", main(source_dir=args.synthea_output, load=not args.dry_run))
