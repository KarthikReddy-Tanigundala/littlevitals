"""Data loaders for the analytics layer (Gold warehouse + synthetic monthly series)."""

from __future__ import annotations

from pathlib import Path

import duckdb
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
DUCKDB_PATH = REPO_ROOT / "dev.duckdb"
MONTHLY_CSV = REPO_ROOT / "data" / "sample" / "monthly_paediatric_ed.csv"


def _con() -> duckdb.DuckDBPyConnection:
    return duckdb.connect(str(DUCKDB_PATH), read_only=True)


def load_scorecard() -> pd.DataFrame:
    """Gold executive scorecard (one row per hospital per FY)."""
    return _con().execute("select * from GOLD.mart_hospital_scorecard").fetch_df()


def load_fact() -> pd.DataFrame:
    """ED fact joined to the hospital dimension."""
    return _con().execute(
        """
        select f.*, h.hospital_name, h.lhn_name, h.peer_group, h.state_code
        from GOLD.fct_ed_presentations f
        join GOLD.dim_hospital h on f.hospital_key = h.hospital_key
        """
    ).fetch_df()


def load_monthly_paediatric() -> pd.Series:
    """
    Synthetic monthly paediatric ED presentations as a time-indexed Series
    (month-start frequency). SYNTHETIC — see generator docstring.
    """
    df = pd.read_csv(MONTHLY_CSV, parse_dates=["month_date"])
    s = df.set_index("month_date")["presentations"].astype(float)
    return s.asfreq("MS")
