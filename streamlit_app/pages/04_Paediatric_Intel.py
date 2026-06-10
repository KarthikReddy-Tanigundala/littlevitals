"""Paediatric Health Intelligence — Synthea synthetic patient layer."""

import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import plotly.express as px  # noqa: E402
import plotly.graph_objects as go  # noqa: E402
import streamlit as st  # noqa: E402

from utils import data  # noqa: E402
from utils.charts import TEAL, INK, GREY  # noqa: E402

st.set_page_config(page_title="Paediatric · LittleVitals", page_icon="🧒", layout="wide")
st.title("🧒 Paediatric Health Intelligence")

if not data.warehouse_ready():
    st.error("Build the DuckDB warehouse first (`dbt build`).")
    st.stop()

st.warning("🧪 **Synthetic data (Synthea-style, seed=42).** Patient-level figures are "
           "fully synthetic and must not be read as real Victorian health facts.", icon="🧪")

enc = data.load_encounters()
paed = enc[enc["is_paediatric"]].copy()
summary = data.load_paediatric_summary()

# ---- KPI tiles --------------------------------------------------------------
c1, c2, c3, c4 = st.columns(4)
c1.metric("Paediatric encounters", f"{len(paed):,}")
c2.metric("Distinct patients", f"{paed['patient_id'].nunique():,}")
c3.metric("Avg length of stay", f"{paed['los_hours'].mean():.1f} h")
c4.metric("30-day readmission", f"{paed['had_readmission_30d'].mean():.1%}")

# ---- Top diagnoses + age bands ---------------------------------------------
left, right = st.columns(2)
with left:
    st.markdown("##### Top 10 paediatric diagnoses")
    top = summary.head(10).sort_values("encounters")
    fig = go.Figure(go.Bar(x=top["encounters"], y=top["condition_description"],
                           orientation="h", marker_color=TEAL))
    fig.update_layout(template="plotly_white", height=400, font=dict(color=INK),
                      margin=dict(l=10, r=10, t=10, b=10), xaxis_title="Encounters")
    st.plotly_chart(fig, width="stretch")

with right:
    st.markdown("##### Encounters by age band")
    order = ["Neonate (0–28d)", "Infant (1–12m)", "Toddler (1–3y)",
             "Child (4–12y)", "Adolescent (13–17y)"]
    band = (paed.groupby("age_band").size().reindex(order).fillna(0).reset_index())
    band.columns = ["age_band", "encounters"]
    fig2 = px.bar(band, x="age_band", y="encounters", color_discrete_sequence=[TEAL])
    fig2.update_layout(template="plotly_white", height=400, font=dict(color=INK),
                       margin=dict(l=10, r=10, t=10, b=10),
                       xaxis_title=None, yaxis_title="Encounters")
    st.plotly_chart(fig2, width="stretch")

# ---- Readmission equity + seasonality --------------------------------------
left2, right2 = st.columns(2)
with left2:
    st.markdown("##### 30-day readmission by SEIFA quintile (equity)")
    eq = (paed.groupby("seifa_irsd_quintile")["had_readmission_30d"]
          .mean().reset_index())
    fig3 = px.bar(eq, x="seifa_irsd_quintile", y="had_readmission_30d",
                  color_discrete_sequence=[TEAL])
    fig3.update_layout(template="plotly_white", height=380, font=dict(color=INK),
                       margin=dict(l=10, r=10, t=10, b=10),
                       xaxis_title="SEIFA IRSD quintile (1 = most disadvantaged)",
                       yaxis_title="Readmission rate")
    fig3.update_yaxes(tickformat=".0%")
    fig3.update_xaxes(tickvals=[1, 2, 3, 4, 5])
    st.plotly_chart(fig3, width="stretch")
    st.caption("Disadvantaged areas (quintiles 1–2) show higher readmission. Synthetic.")

with right2:
    st.markdown("##### Monthly paediatric ED — winter surge")
    monthly = data.load_monthly_paediatric()
    fig4 = go.Figure(go.Scatter(x=monthly["month_date"], y=monthly["presentations"],
                                mode="lines", line=dict(color=TEAL, width=2)))
    # Shade Australian winters (Jun–Aug).
    for yr in monthly["year"].unique():
        fig4.add_vrect(x0=f"{yr}-06-01", x1=f"{yr}-08-31", fillcolor=GREY,
                       opacity=0.12, line_width=0)
    fig4.update_layout(template="plotly_white", height=380, font=dict(color=INK),
                       margin=dict(l=10, r=10, t=10, b=10),
                       yaxis_title="ED presentations / month")
    st.plotly_chart(fig4, width="stretch")
    st.caption("Shaded = Jun–Aug (Australian winter). Synthetic monthly series.")
