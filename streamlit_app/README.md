# LittleVitals — Streamlit companion app

Interactive companion to the Power BI dashboard. Reads the **Gold** tables from
the dbt-built warehouse and renders KPI tiles, trends, a hospital map, an
executive scorecard, and a **funnel plot** for fair hospital comparison.

## Pages
| Page | Content |
|---|---|
| Overview | KPI tiles (Vic, latest FY), Cat 2 on-time trend vs benchmark, hospital map, top-10 bar |
| ED Performance | Hospital × triage wait heatmap, wait-vs-on-time scatter |
| Hospital Scorecard | Rated scorecard table with YoY deltas |
| Benchmark Intelligence | Spiegelhalter funnel plot (special-cause outliers) |
| Paediatric Intel | Synthea layer: top diagnoses, age bands, readmission-by-SEIFA, winter surge |

## Run locally
From the repo root, after `dbt build` has created `dev.duckdb`:

```powershell
.\.venv\Scripts\Activate.ps1
streamlit run streamlit_app\app.py
```

The app reads `dev.duckdb` at the repo root (override with the `LITTLEVITALS_DUCKDB`
environment variable).

## Deploy to Streamlit Community Cloud
1. Point the app at **Snowflake** (Gold schema) instead of the local DuckDB file —
   add `st.secrets["snowflake"]` and swap the connection in `utils/data.py`.
2. Set the app entrypoint to `streamlit_app/app.py` and the requirements file to
   `streamlit_app/requirements.txt`.
3. Add Snowflake credentials via the Streamlit **Secrets** UI (never commit them).

> ⚠️ Sample build figures are synthetic (seed=42), not real AIHW data.
