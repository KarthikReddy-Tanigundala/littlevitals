"""
Data access for the LittleVitals Streamlit app.

Reads the Gold tables from the DuckDB warehouse built by dbt (`dev.duckdb` at the
repo root). For a Streamlit Community Cloud deployment, point at Snowflake instead
by providing st.secrets["snowflake"] — the same Gold table names apply.

All queries are cached; the connection is opened read-only so it can run while
dbt holds the file.
"""

from __future__ import annotations

import os
from pathlib import Path

import duckdb
import pandas as pd
import streamlit as st

REPO_ROOT = Path(__file__).resolve().parents[2]
DUCKDB_PATH = os.environ.get("LITTLEVITALS_DUCKDB", str(REPO_ROOT / "dev.duckdb"))


def warehouse_ready() -> bool:
    """True when the DuckDB file exists and has the Gold fact table."""
    if not Path(DUCKDB_PATH).exists():
        return False
    try:
        con = duckdb.connect(DUCKDB_PATH, read_only=True)
        con.execute("select 1 from GOLD.fct_ed_presentations limit 1")
        return True
    except Exception:
        return False
    finally:
        try:
            con.close()
        except Exception:
            pass


@st.cache_resource(show_spinner=False)
def _connection() -> duckdb.DuckDBPyConnection:
    return duckdb.connect(DUCKDB_PATH, read_only=True)


@st.cache_data(ttl=3600, show_spinner=False)
def query(sql: str) -> pd.DataFrame:
    return _connection().execute(sql).fetch_df()


# ---- Convenience loaders ----------------------------------------------------
@st.cache_data(ttl=3600, show_spinner=False)
def load_scorecard() -> pd.DataFrame:
    return query("select * from GOLD.mart_hospital_scorecard")


@st.cache_data(ttl=3600, show_spinner=False)
def load_fact() -> pd.DataFrame:
    return query(
        """
        select f.*, h.hospital_name, h.lhn_name, h.peer_group,
               h.state_code, h.state_name, h.latitude, h.longitude, h.is_paediatric
        from GOLD.fct_ed_presentations f
        join GOLD.dim_hospital h on f.hospital_key = h.hospital_key
        """
    )


@st.cache_data(ttl=3600, show_spinner=False)
def load_paediatric_summary() -> pd.DataFrame:
    return query("select * from GOLD.mart_paediatric_summary order by encounters desc")


@st.cache_data(ttl=3600, show_spinner=False)
def load_encounters() -> pd.DataFrame:
    return query(
        """
        select f.patient_id, f.age_band, f.is_paediatric, f.encounter_class,
               f.los_hours, f.is_readmission_30d, f.had_readmission_30d,
               g.seifa_irsd_quintile, d.body_system, d.condition_description
        from GOLD.fct_patient_encounters f
        join GOLD.dim_geography g on f.geography_key = g.geography_key
        join GOLD.dim_diagnosis d on f.diagnosis_key = d.diagnosis_key
        """
    )


@st.cache_data(ttl=3600, show_spinner=False)
def load_elective_episodes() -> pd.DataFrame:
    return query(
        """
        select f.wait_days, f.is_admitted, f.is_overdue, f.financial_year,
               u.urgency_code, u.urgency_name, u.recommended_max_wait_days,
               s.specialty_name
        from GOLD.fct_elective_surgery f
        join GOLD.dim_urgency_category u on f.urgency_key = u.urgency_key
        join GOLD.dim_surgical_specialty s on f.specialty_key = s.specialty_key
        """
    )


@st.cache_data(ttl=3600, show_spinner=False)
def load_monthly_paediatric() -> pd.DataFrame:
    return pd.read_csv(REPO_ROOT / "data" / "sample" / "monthly_paediatric_ed.csv",
                       parse_dates=["month_date"])


@st.cache_data(ttl=3600, show_spinner=False)
def financial_years() -> list[str]:
    df = query("select distinct financial_year from GOLD.fct_ed_presentations order by 1")
    return df["financial_year"].tolist()


def latest_financial_year() -> str:
    return financial_years()[-1]
