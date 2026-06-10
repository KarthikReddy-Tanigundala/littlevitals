"""Ingest AIHW static XLSX data tables → Snowflake BRONZE.

These direct XLSX downloads are durable (unlike the API) and serve as the
fallback source per CLAUDE.md §16.2/§16.3. In `--source live` the workbook is
downloaded and snapshotted; parsing is via pandas + openpyxl. All relevant
sheets are loaded.
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

# Durable AIHW XLSX endpoints (CLAUDE.md §2.2).
ELECTIVE_2324_URL = (
    "https://www.aihw.gov.au/getmedia/d1f39fa7-644f-4b46-95a0-a4d04360f2b1/"
    "Elective-surgery-waiting-times-2023-24.xlsx")


def parse_workbook(path_or_buffer) -> dict[str, pd.DataFrame]:
    """Parse every sheet of an XLSX workbook into a dict of DataFrames."""
    book = pd.read_excel(path_or_buffer, sheet_name=None, engine="openpyxl")
    return {sheet: df for sheet, df in book.items() if not df.empty}


def fetch_workbook(url: str, snapshot_name: str, source: str):
    if source == "live":  # pragma: no cover - network
        import requests

        resp = requests.get(url, timeout=180)
        resp.raise_for_status()
        config.RAW_SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
        snap = config.RAW_SNAPSHOT_DIR / snapshot_name
        snap.write_bytes(resp.content)
        return snap
    snap = config.RAW_SNAPSHOT_DIR / snapshot_name
    if not snap.exists():
        raise FileNotFoundError(
            f"No XLSX snapshot '{snapshot_name}'. Run once with --source live.")
    return snap


def main(source: str = "snapshot", load: bool = True) -> dict[str, int]:  # pragma: no cover
    path = fetch_workbook(ELECTIVE_2324_URL, "elective_surgery_2023_24.xlsx", source)
    sheets = parse_workbook(path)
    counts = {}
    for sheet, df in sheets.items():
        table = "RAW_AIHW_ELECTIVE_XLSX_" + snowflake_loader.normalize_column(sheet)[:40]
        counts[table] = len(df)
        if load:
            snowflake_loader.load_dataframe_to_snowflake(df, table)
    return counts


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", choices=["live", "snapshot"], default="snapshot")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    logger.info("Done: %s", main(source=args.source, load=not args.dry_run))
