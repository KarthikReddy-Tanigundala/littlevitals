"""ED Performance deep dive — triage matrix + wait-vs-on-time scatter."""

import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import pandas as pd  # noqa: E402
import plotly.express as px  # noqa: E402
import streamlit as st  # noqa: E402

from utils import data  # noqa: E402
from utils.charts import TEAL, INK  # noqa: E402

st.set_page_config(page_title="ED Performance · LittleVitals", page_icon="📈", layout="wide")
st.title("📈 ED Performance Deep Dive")

if not data.warehouse_ready():
    st.error("Build the DuckDB warehouse first (`dbt build`).")
    st.stop()

fact = data.load_fact()
fys = data.financial_years()
fy = st.selectbox("Financial year", fys, index=len(fys) - 1)
vic = fact[(fact["state_code"] == "VIC") & (fact["financial_year"] == fy)]

# ---- Median wait matrix: hospital x triage ---------------------------------
st.subheader("Median wait (minutes) by hospital × triage category")
matrix = (vic.pivot_table(index="hospital_name", columns="triage_code",
                          values="median_wait_minutes", aggfunc="mean")
          .sort_index())
fig_m = px.imshow(
    matrix, color_continuous_scale="YlOrRd", aspect="auto", text_auto=".0f",
    labels=dict(x="Triage category", y="Hospital", color="Median wait (min)"),
)
fig_m.update_xaxes(tickvals=list(matrix.columns), ticktext=[f"Cat {c}" for c in matrix.columns])
fig_m.update_layout(template="plotly_white", height=460, font=dict(color=INK))
st.plotly_chart(fig_m, width="stretch")

# ---- Scatter: median wait vs on-time, per hospital (Cat 2 + Cat 3) ---------
st.subheader("Wait time vs on-time performance")
sub = vic[vic["triage_code"].isin([2, 3])].copy()
sub["Triage"] = "Cat " + sub["triage_code"].astype(str)
fig = px.scatter(
    sub, x="median_wait_minutes", y="pct_seen_on_time",
    color="Triage", size="total_presentations", hover_name="hospital_name",
    color_discrete_sequence=[TEAL, "#e0a32e"],
    labels={"median_wait_minutes": "Median wait (min)", "pct_seen_on_time": "Seen on time"},
)
fig.update_yaxes(tickformat=".0%")
fig.update_layout(template="plotly_white", height=460, font=dict(color=INK))
st.plotly_chart(fig, width="stretch")

st.caption("Each point is one hospital. Up-and-left is better (faster waits, higher on-time).")
