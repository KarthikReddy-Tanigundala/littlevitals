# ADR-001 — Medallion architecture (Bronze / Silver / Gold)

- **Status:** Accepted
- **Date:** 2026-06
- **Deciders:** Karthik Reddy Tanigundala

## Context

We ingest several heterogeneous public sources (AIHW API + XLSX, Synthea, ABS)
with differing shapes and refresh cadences, and must serve a clean star schema to
Power BI, Streamlit, and a data-science layer. We need clear separation between
"what the source said" and "what the business consumes", plus an audit trail —
important in a healthcare context.

## Decision

Adopt a three-layer **medallion** architecture, implemented as Snowflake/DuckDB
schemas and dbt model folders:

- **Bronze** (`stg_`) — raw, immutable, 1:1 with source; rename + type-cast only.
- **Silver** (`int_`) — cleaned, typed, deduplicated; joins and business logic.
- **Gold** (`dim_`/`fct_`/`mart_`) — conformed Kimball star schema, optimised for
  query/BI consumption.

## Consequences

- **+** Source fidelity is preserved in Bronze, so we can always reprocess.
- **+** Business logic is centralised in Silver/Gold, not duplicated in BI tools.
- **+** Layer boundaries map cleanly to dbt model folders and tests, and to a
  readable lineage graph.
- **−** More models/boilerplate than a single-layer transform; mitigated by dbt's
  `ref()` graph and naming conventions.

## Interview line

> "Bronze preserves source fidelity for audit and reprocessing; Silver handles
> type-casting and dedupe once; Gold is optimised purely for query performance.
> In healthcare you specifically want Bronze immutability for the audit trail."
