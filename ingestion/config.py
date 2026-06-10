"""Central configuration for the ingestion layer (reads .env if present)."""

from __future__ import annotations

import os
from pathlib import Path

try:  # optional — only needed for local .env loading
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
except ImportError:  # pragma: no cover
    pass

ROOT = Path(__file__).resolve().parents[1]
DATA_SAMPLE_DIR = ROOT / "data" / "sample"
RAW_SNAPSHOT_DIR = ROOT / "data" / "raw_snapshots"
# Committed offline fixtures (also consumed by dbt seeds) used as the snapshot
# fallback when no live API snapshot exists.
FIXTURES_DIR = ROOT / "littlevitals_dbt" / "seeds" / "fixtures"

# Search order for snapshot reads: a fresh live snapshot, then committed fixtures.
SNAPSHOT_SEARCH_DIRS = [RAW_SNAPSHOT_DIR, FIXTURES_DIR, DATA_SAMPLE_DIR]

# AIHW MyHospitals API (best-effort; the pipeline falls back to snapshots — §16.3).
AIHW_BASE_URL = os.getenv("AIHW_BASE_URL", "https://myhospitalsapi.aihw.gov.au/api/v1")

# Snowflake connection parameters (only used when actually loading to Snowflake).
SNOWFLAKE = {
    "account": os.getenv("SNOWFLAKE_ACCOUNT"),
    "user": os.getenv("SNOWFLAKE_USER"),
    "password": os.getenv("SNOWFLAKE_PASSWORD"),
    "database": os.getenv("SNOWFLAKE_DATABASE", "LITTLEVITALS_DB"),
    "warehouse": os.getenv("SNOWFLAKE_WAREHOUSE", "COMPUTE_WH"),
    "role": os.getenv("SNOWFLAKE_ROLE", "LITTLEVITALS_ENGINEER"),
}
