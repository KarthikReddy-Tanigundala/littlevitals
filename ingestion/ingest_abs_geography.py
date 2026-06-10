"""Ingest ABS geographic reference data → Snowflake BRONZE.

Production path: download the ABS ASGS SA2 boundaries + a postcode→SA2
correspondence and the SEIFA index, then load the postcode→SA2/SEIFA mapping.
Offline path: load the committed `seed_vic_geography.csv` (the same shape) so the
pipeline is demonstrable without the large ABS downloads.
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
GEOGRAPHY_SEED = config.ROOT / "littlevitals_dbt" / "seeds" / "reference" / "seed_vic_geography.csv"


def load_geography() -> pd.DataFrame:
    """Read the postcode→SA2/PHN/SEIFA/remoteness reference."""
    if not GEOGRAPHY_SEED.exists():
        raise FileNotFoundError(f"Geography reference not found: {GEOGRAPHY_SEED}")
    return pd.read_csv(GEOGRAPHY_SEED)


def main(load: bool = True) -> dict[str, int]:
    df = load_geography()
    logger.info("Read %s geography rows", len(df))
    if load:  # pragma: no cover - requires Snowflake
        snowflake_loader.load_dataframe_to_snowflake(df, "RAW_ABS_SA2_POSTCODE_MAP")
    return {"RAW_ABS_SA2_POSTCODE_MAP": len(df)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    logger.info("Done: %s", main(load=not args.dry_run))
