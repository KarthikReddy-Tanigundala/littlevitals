"""Elective Surgery Tracker — waiting times by urgency and specialty."""

import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import plotly.express as px  # noqa: E402
import plotly.graph_objects as go  # noqa: E402
import streamlit as st  # noqa: E402

from utils import data  # noqa: E402
from utils.charts import TEAL, AMBER, CORAL, INK  # noqa: E402

st.set_page_config(page_title="Elective Surgery · LittleVitals", page_icon="🔪", layout="wide")
st.title("🔪 Elective Surgery Tracker")

if not data.warehouse_ready():
    st.error("Build the DuckDB warehouse first (`dbt build`).")
    st.stop()

st.info("📌 Synthetic elective-surgery waitlist episodes (seed=42). Wait statistics "
        "use admitted episodes; episodes still waiting are censored.", icon="⚠️")

ep = data.load_elective_episodes()
fy = sorted(ep["financial_year"].unique())[-1]
URG_COLOR = {1: CORAL, 2: AMBER, 3: TEAL}

cur = ep[ep["financial_year"] == fy]
adm = cur[cur["is_admitted"]]

# ---- KPI tiles --------------------------------------------------------------
st.subheader(f"Financial Year {fy}")
c1, c2, c3, c4, c5 = st.columns(5)
for col, code in zip((c1, c2, c3), (1, 2, 3)):
    med = adm.loc[adm["urgency_code"] == code, "wait_days"].median()
    rec = int(cur.loc[cur["urgency_code"] == code, "recommended_max_wait_days"].iloc[0])
    col.metric(f"Median wait — Cat {code}", f"{med:.0f} d", delta=f"target ≤ {rec}d",
               delta_color="off")
on_time = (adm["wait_days"] <= adm["recommended_max_wait_days"]).mean()
c4.metric("% seen on time", f"{on_time:.0%}")
c5.metric("Overdue episodes", f"{int(cur['is_overdue'].sum()):,}")

# ---- Median wait by urgency over time --------------------------------------
left, right = st.columns(2)
with left:
    st.markdown("##### Median wait (days) by urgency over time")
    adm_all = ep[ep["is_admitted"]]
    trend = (adm_all.groupby(["financial_year", "urgency_code"])["wait_days"]
             .median().reset_index())
    fig = go.Figure()
    for code in [1, 2, 3]:
        d = trend[trend["urgency_code"] == code]
        fig.add_trace(go.Scatter(x=d["financial_year"], y=d["wait_days"],
                                 mode="lines+markers", name=f"Cat {code}",
                                 line=dict(color=URG_COLOR[code], width=2.5)))
    fig.update_layout(template="plotly_white", height=380, font=dict(color=INK),
                      margin=dict(l=10, r=10, t=10, b=10), yaxis_title="Median wait (days)")
    st.plotly_chart(fig, width="stretch")

with right:
    st.markdown(f"##### Median wait (days) by specialty — {fy}")
    spec = (adm.groupby("specialty_name")["wait_days"].median()
            .sort_values().reset_index())
    fig2 = go.Figure(go.Bar(x=spec["wait_days"], y=spec["specialty_name"],
                            orientation="h", marker_color=TEAL))
    fig2.update_layout(template="plotly_white", height=380, font=dict(color=INK),
                       margin=dict(l=10, r=10, t=10, b=10), xaxis_title="Median wait (days)")
    st.plotly_chart(fig2, width="stretch")

# ---- % within recommended time by urgency ----------------------------------
st.markdown("##### % seen within clinically recommended time, by urgency category")
ot = (adm.assign(on_time=adm["wait_days"] <= adm["recommended_max_wait_days"])
      .groupby("urgency_name")["on_time"].mean().reset_index())
fig3 = px.bar(ot, x="urgency_name", y="on_time", color_discrete_sequence=[TEAL])
fig3.update_yaxes(tickformat=".0%", title="% on time")
fig3.update_layout(template="plotly_white", height=320, font=dict(color=INK),
                   margin=dict(l=10, r=10, t=10, b=10), xaxis_title=None)
st.plotly_chart(fig3, width="stretch")
st.caption("Kaplan–Meier time-to-admission curves for these episodes: see analytics/06_waitlist_survival.py.")
