{% docs __overview__ %}

# LittleVitals — dbt Documentation

**Melbourne Health-System Analytics Platform** · Bronze → Silver → Gold (Kimball star schema).

This site is the live data dictionary and lineage graph for the LittleVitals
warehouse. Use the **lineage graph** (bottom-right) to trace any column from the
AIHW source through to the Power BI marts.

## Layers
- **Staging (`stg_`, schema `BRONZE`)** — 1:1 with source: rename + type-cast only.
- **Intermediate (`int_`, schema `SILVER`)** — joins, enrichment, derived business logic.
- **Marts / core (`dim_`, `fct_`, schema `GOLD`)** — conformed Kimball star schema.
- **Marts / reporting (`mart_`, schema `GOLD`)** — BI-ready aggregates.

## Key models
- `fct_ed_presentations` — ED fact, grain = hospital × financial year × triage (annual).
- `dim_hospital`, `dim_triage_category`, `dim_date` — conformed dimensions.
- `mart_hospital_scorecard` — one row per hospital per FY for the executive scorecard.

## Data sources & honesty
Aggregate hospital performance derives from **AIHW MyHospitals** public data. The
sample/CI build uses **synthetic fixtures** (seed = 42) so the pipeline runs offline
on DuckDB. Patient-level analytics (not in this slice) use **Synthea** synthetic
patients. See the repository README for the full limitations section.

{% enddocs %}
