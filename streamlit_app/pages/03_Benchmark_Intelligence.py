"""Benchmark Intelligence — Spiegelhalter funnel plot for fair comparison."""

import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import streamlit as st  # noqa: E402

from utils import data  # noqa: E402
from utils.charts import funnel_plot  # noqa: E402

st.set_page_config(page_title="Benchmark Intelligence · LittleVitals", page_icon="🎯", layout="wide")
st.title("🎯 Benchmark Intelligence")

if not data.warehouse_ready():
    st.error("Build the DuckDB warehouse first (`dbt build`).")
    st.stop()

fact = data.load_fact()
fys = data.financial_years()
fy = st.selectbox("Financial year", fys, index=len(fys) - 1)

# Cat 2 funnel: volume = Cat 2 presentations, indicator = Cat 2 on-time.
cat2 = fact[(fact["state_code"] == "VIC") & (fact["triage_code"] == 2)
            & (fact["financial_year"] == fy)].copy()
cat2 = cat2.rename(columns={"total_presentations": "presentations"})

st.plotly_chart(funnel_plot(cat2), width="stretch")

st.markdown(
    """
    **Why a funnel plot, not a league table?** Small hospitals have noisier rates,
    so a simple ranking unfairly punishes them. The funnel plots each hospital's
    on-time rate against its volume, with control limits that *widen* where volume
    is low. Only hospitals **outside the 99.8% limits** are genuine ("special-cause")
    outliers worth investigating — the standard fair-comparison method in health
    services research (Spiegelhalter, 2005).
    """
)

# Best / worst callouts.
best = cat2.loc[cat2["pct_seen_on_time"].idxmax()]
worst = cat2.loc[cat2["pct_seen_on_time"].idxmin()]
c1, c2 = st.columns(2)
c1.metric("Best Cat 2 on-time", best["hospital_name"], f"{best['pct_seen_on_time']:.0%}")
c2.metric("Lowest Cat 2 on-time", worst["hospital_name"], f"{worst['pct_seen_on_time']:.0%}")
