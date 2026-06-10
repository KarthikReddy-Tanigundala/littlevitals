# Architecture — LittleVitals

## 1. Overview

LittleVitals is an end-to-end modern data stack over Australian public hospital
performance data, with a paediatric lens. It is **engine-portable**: the identical
dbt project runs on **DuckDB** (local development + CI, zero infrastructure) and
**Snowflake** (production), selected by `target.type`.

```
SOURCES → INGESTION → BRONZE → SILVER → GOLD (star schema) → SERVING
 AIHW      Python      raw      cleaned   dims + facts + marts   Power BI
 Synthea   loaders                                              Streamlit
 ABS                                                            dbt docs
                                                                analytics/ (DS)
```

## 2. Layers

| Layer | Schema | dbt prefix | Materialisation | Purpose |
|---|---|---|---|---|
| Landing | `RAW` / `BRONZE` | (seed / source) | — | Raw ingested data, immutable |
| Staging | `BRONZE` | `stg_` | view | 1:1 with source — rename + type-cast only |
| Intermediate | `SILVER` | `int_` | view | Joins, enrichment, derived business logic |
| Dimensions / facts | `GOLD` | `dim_` / `fct_` | table | Conformed Kimball star schema |
| Marts | `GOLD` | `mart_` | table | BI-ready aggregates |

## 3. Star schema (current ED slice)

```
        dim_date ──┐
                   │
 dim_hospital ──── fct_ed_presentations ──── dim_triage_category
                   │
        (degenerate: financial_year, triage_code)
                   │
            mart_hospital_scorecard   (hospital × FY)
```

- **Grain of `fct_ed_presentations`:** hospital × financial_year × triage_category
  (**annual** — AIHW public data is published per financial year; see CLAUDE.md §16.1).
- **Surrogate keys** via `dbt_utils.generate_surrogate_key`; every dimension carries
  a `-1` Unknown member so referential-integrity tests never silently drop fact rows.

## 4. Engine strategy (key design decision)

| Concern | Local / CI | Production |
|---|---|---|
| Engine | DuckDB (`dbt-duckdb`) | Snowflake (`dbt-snowflake`) |
| Source data | Committed synthetic fixtures (seed=42) | Live AIHW ingestion → `BRONZE` |
| Secrets | none | env vars / GitHub Secrets |
| Cost | free | XS warehouse, auto-suspend, resource monitor |

This means a fresh `git clone` builds and tests the **entire** warehouse with no
accounts, and the project stays runnable forever even after cloud trials lapse.
See [ADR-003](docs/adr/ADR-003-duckdb-ci-and-power-bi-import.md).

## 5. Data quality & governance

- **Enforced dbt contracts** on every Gold model (schema drift fails the build).
- **dbt unit test** on transformation logic; **reconciliation test** ties Gold VIC
  totals back to source within tolerance; **FY-macro boundary test**.
- **48 data tests** (uniqueness, not-null, relationships, accepted ranges/values).
- Five Safes framing + RBAC + classification tags/masking — see [SECURITY.md](SECURITY.md).

## 6. Serving

- **Power BI** (Import mode) — executive dashboard; see [ADR-003](docs/adr/ADR-003-duckdb-ci-and-power-bi-import.md).
- **Streamlit** ([streamlit_app/](streamlit_app/README.md)) — interactive companion incl. funnel plot.
- **dbt docs** — lineage site (GitHub Pages).
- **analytics/** ([analytics/](analytics/README.md)) — SARIMA forecast, STL seasonality,
  clustering, proportion tests.

## 7. CI/CD

- `dbt_ci.yml` — every PR/push: build + test on DuckDB (no secrets).
- `dbt_docs_deploy.yml` — push to `main`: build + publish docs to GitHub Pages.

## 8. Repository map

See the tree in [README.md](README.md#-repository-structure). The master spec is
[CLAUDE.md](CLAUDE.md).
