# ADR-003 — DuckDB for CI, and Power BI Import (not DirectQuery)

- **Status:** Accepted
- **Date:** 2026-06
- **Deciders:** Karthik Reddy Tanigundala

## Context

Two related questions: (1) how to run CI cheaply and reproducibly without leaking
Snowflake credentials or burning trial credits, and (2) how Power BI should
connect to Snowflake for a portfolio demo.

## Decision

**1. CI runs on DuckDB, production on Snowflake.** The dbt project is engine-
portable via `target.type`; CI builds the full DAG + all tests on `dbt-duckdb`
with committed synthetic fixtures — no secrets, no network, no cost. Snowflake is
reserved for production (and an optional production docs catalog).

**2. Power BI uses Import mode, not DirectQuery.** The trial warehouse auto-
suspends to protect credits, so DirectQuery would cold-start on every interaction
and look broken in a demo. The dataset is tiny, so Import is instant and keeps
Publish-to-Web fast and free. One DirectQuery page is kept as a capability proof.

## Consequences

- **+** A fresh clone builds and passes CI with zero setup; repo stays runnable
  after cloud trials expire (DuckDB is also the permanent fallback engine).
- **+** Fast, reliable demo; no warehouse cold-starts mid-presentation.
- **−** SQL must stay reasonably portable across DuckDB/Snowflake (handled with
  `target`-type branching where needed).
- **−** Import data is as fresh as the last scheduled refresh, not live — an
  acceptable trade-off at this data volume.

## Interview line

> "I run CI on DuckDB so it's free, fast, and needs no secrets, and keep Snowflake
> for prod. For Power BI I chose Import because with an auto-suspending trial
> warehouse DirectQuery's cold-start would wreck the demo — I'd switch to
> DirectQuery the moment freshness or volume justified keeping the warehouse warm."
