"""Ingest AIHW MyHospitals data → Snowflake BRONZE.

Resilience pattern (CLAUDE.md §16.3): the AIHW API is not a stable contract, so
every fetch can run in `--source live` (hit the API, save a raw snapshot) or
`--source snapshot` (read the committed sample/snapshot, no network). Downstream
dbt/BI always read Snowflake, never the API — so a source outage never breaks the
build, and CI is fully offline.

Run:
    python ingestion/ingest_aihw_api.py --source snapshot --dry-run   # offline, no load
    python ingestion/ingest_aihw_api.py --source live                 # API -> Snowflake
"""

from __future__ import annotations

import argparse
import io
import logging
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config  # noqa: E402
import snowflake_loader  # noqa: E402

logger = logging.getLogger(__name__)
TIMEOUT = 120


def parse_csv(text: str) -> pd.DataFrame:
    """Parse a CSV response body into a DataFrame."""
    return pd.read_csv(io.StringIO(text))


def _save_snapshot(text: str, name: str) -> None:
    config.RAW_SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    (config.RAW_SNAPSHOT_DIR / name).write_text(text, encoding="utf-8")
    logger.info("Saved raw snapshot: %s", name)


def _load_snapshot_csv(name: str) -> pd.DataFrame:
    """Read a snapshot CSV, falling back to the committed fixture directories."""
    for directory in config.SNAPSHOT_SEARCH_DIRS:
        path = directory / name
        if path.exists():
            return pd.read_csv(path)
    raise FileNotFoundError(
        f"No snapshot or fixture for '{name}'. Run with --source live, or "
        f"generate fixtures via data/sample/generate_sample_data.py.")


def _fetch_csv_endpoint(path: str, snapshot_name: str, source: str) -> pd.DataFrame:
    if source == "live":  # pragma: no cover - network
        import requests

        resp = requests.get(f"{config.AIHW_BASE_URL}/{path}",
                            headers={"Accept": "text/csv"}, timeout=TIMEOUT)
        resp.raise_for_status()
        _save_snapshot(resp.text, snapshot_name)
        return parse_csv(resp.text)
    return _load_snapshot_csv(snapshot_name)


def fetch_reporting_units(source: str = "snapshot") -> pd.DataFrame:
    """Hospital master (name, code, state, LHN, peer group, lat/lon)."""
    if source == "live":  # pragma: no cover - network
        import requests

        resp = requests.get(f"{config.AIHW_BASE_URL}/reporting-units", timeout=30)
        resp.raise_for_status()
        df = pd.json_normalize(resp.json())
        _save_snapshot(df.to_csv(index=False), "raw_aihw_reporting_units.csv")
        return df
    return _load_snapshot_csv("raw_aihw_reporting_units.csv")


def fetch_ed_data(source: str = "snapshot") -> pd.DataFrame:
    """ED presentations (hospital × financial_year × triage_category)."""
    return _fetch_csv_endpoint("measure-downloads/myh-ed",
                               "raw_aihw_ed_presentations.csv", source)


def main(source: str = "snapshot", load: bool = True) -> dict[str, int]:
    units = fetch_reporting_units(source)
    ed = fetch_ed_data(source)
    logger.info("Fetched %s reporting units, %s ED rows (source=%s)",
                len(units), len(ed), source)
    if load:  # pragma: no cover - requires Snowflake
        snowflake_loader.load_dataframe_to_snowflake(units, "RAW_AIHW_REPORTING_UNITS")
        snowflake_loader.load_dataframe_to_snowflake(ed, "RAW_AIHW_ED_PRESENTATIONS")
    return {"reporting_units": len(units), "ed": len(ed)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", choices=["live", "snapshot"], default="snapshot")
    parser.add_argument("--dry-run", action="store_true",
                        help="Fetch/parse only; do not load to Snowflake.")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    result = main(source=args.source, load=not args.dry_run)
    logger.info("Done: %s", result)
