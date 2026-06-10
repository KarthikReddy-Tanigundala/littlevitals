"""Hospital scorecard — one row per hospital per FY with ratings + YoY deltas."""

import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import streamlit as st  # noqa: E402

from utils import data  # noqa: E402
from utils.charts import STATUS_COLORS  # noqa: E402

st.set_page_config(page_title="Scorecard · LittleVitals", page_icon="🗂️", layout="wide")
st.title("🗂️ Hospital Scorecard")

if not data.warehouse_ready():
    st.error("Build the DuckDB warehouse first (`dbt build`).")
    st.stop()

sc = data.load_scorecard()
fys = data.financial_years()

col1, col2 = st.columns(2)
fy = col1.selectbox("Financial year", fys, index=len(fys) - 1)
ratings = col2.multiselect("Rating", list(STATUS_COLORS), default=list(STATUS_COLORS))

view = sc[(sc["state_code"] == "VIC") & (sc["financial_year"] == fy)
          & (sc["scorecard_overall_rating"].isin(ratings))].copy()
view = view.sort_values("total_ed_presentations", ascending=False)

display = view[[
    "hospital_name", "lhn_name", "total_ed_presentations", "median_ed_wait_all_triage",
    "pct_ed_seen_on_time_cat2", "pct_ed_seen_on_time_cat3", "four_hour_rule_pct",
    "scorecard_overall_rating", "yoy_ed_presentations_growth_pct",
]].rename(columns={
    "hospital_name": "Hospital", "lhn_name": "LHN",
    "total_ed_presentations": "ED presentations", "median_ed_wait_all_triage": "Median wait (min)",
    "pct_ed_seen_on_time_cat2": "Cat 2 on-time", "pct_ed_seen_on_time_cat3": "Cat 3 on-time",
    "four_hour_rule_pct": "4-hour rule", "scorecard_overall_rating": "Rating",
    "yoy_ed_presentations_growth_pct": "YoY growth %",
})


def colour_rating(val: str) -> str:
    return f"background-color: {STATUS_COLORS.get(val, '#eee')}; color: white;"


styled = (display.style
          .format({"ED presentations": "{:,}", "Cat 2 on-time": "{:.0%}",
                   "Cat 3 on-time": "{:.0%}", "4-hour rule": "{:.0%}",
                   "YoY growth %": "{:+.1f}%", "Median wait (min)": "{:.0f}"})
          .map(colour_rating, subset=["Rating"]))

st.dataframe(styled, width="stretch", hide_index=True)

n = len(view)
meets = (view["scorecard_overall_rating"] == "Meets Benchmark").sum()
st.caption(f"{meets} of {n} Victorian hospitals meet the Cat 2 benchmark in {fy}.")
