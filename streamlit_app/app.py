"""LittleVitals — Streamlit companion app. Overview / hero page."""

import sys
import pathlib

APP_DIR = pathlib.Path(__file__).resolve().parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

import streamlit as st  # noqa: E402

from utils import data  # noqa: E402
from utils.charts import on_time_trend, top_hospitals, hospital_map  # noqa: E402

st.set_page_config(page_title="LittleVitals", page_icon="🏥", layout="wide")


def main() -> None:
    st.title("🏥 LittleVitals")
    st.caption("Melbourne Health-System Analytics — Victorian ED performance")

    if not data.warehouse_ready():
        st.error(
            "DuckDB warehouse not found. Build it first:\n\n"
            "```\ndbt build --project-dir littlevitals_dbt --profiles-dir littlevitals_dbt\n```"
        )
        st.stop()

    st.info("📌 Sample build — figures use synthetic fixtures (seed=42), not real AIHW data.",
            icon="⚠️")

    scorecard = data.load_scorecard()
    fact = data.load_fact()
    fy = data.latest_financial_year()

    vic = scorecard[(scorecard["state_code"] == "VIC") & (scorecard["financial_year"] == fy)]
    vic_prev = scorecard[(scorecard["state_code"] == "VIC")
                         & (scorecard["financial_year"] == _prev_fy(fy))]

    # ---- KPI tiles ----------------------------------------------------------
    total = int(vic["total_ed_presentations"].sum())
    total_prev = int(vic_prev["total_ed_presentations"].sum()) if not vic_prev.empty else None
    cat2 = _wavg(vic, "pct_ed_seen_on_time_cat2", "total_ed_presentations")
    wait = _wavg(vic, "median_ed_wait_all_triage", "total_ed_presentations")
    four_hr = _wavg(vic, "four_hour_rule_pct", "total_ed_presentations")

    st.subheader(f"Victoria — Financial Year {fy}")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total ED presentations", f"{total:,}",
              delta=(f"{(total/total_prev-1):+.1%} YoY" if total_prev else None))
    c2.metric("Cat 2 seen on time", f"{cat2:.0%}",
              delta=f"{(cat2-0.80):+.0%} vs 80% target", delta_color="normal")
    c3.metric("Median ED wait", f"{wait:.0f} min")
    c4.metric("4-hour rule (NEAT)", f"{four_hr:.0%}")

    # ---- Trend + map --------------------------------------------------------
    left, right = st.columns([1.1, 1])
    with left:
        st.plotly_chart(on_time_trend(_trend(fact)), width="stretch")
    with right:
        st.plotly_chart(hospital_map(vic), width="stretch")

    st.markdown("##### Top Victorian hospitals by ED presentations")
    st.plotly_chart(top_hospitals(vic.nlargest(10, "total_ed_presentations")),
                    width="stretch")


def _prev_fy(fy: str) -> str:
    start = int(fy[:4]) - 1
    return f"{start}-{str(start + 1)[2:]}"


def _wavg(df, value_col, weight_col) -> float:
    w = df[weight_col]
    return float((df[value_col] * w).sum() / w.sum()) if w.sum() else 0.0


def _trend(fact):
    cat2 = fact[(fact["state_code"] == "VIC") & (fact["triage_code"] == 2)]
    rows = []
    for fy, grp in cat2.groupby("financial_year"):
        rows.append({
            "financial_year": fy,
            "vic_on_time": (grp["pct_seen_on_time"] * grp["total_presentations"]).sum()
                           / grp["total_presentations"].sum(),
            "national_on_time": grp["national_on_time_pct"].iloc[0],
        })
    import pandas as pd
    return pd.DataFrame(rows).sort_values("financial_year")


if __name__ == "__main__":
    main()
