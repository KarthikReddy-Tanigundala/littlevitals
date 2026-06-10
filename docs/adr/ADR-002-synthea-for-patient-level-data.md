# ADR-002 — Synthea for patient-level data

- **Status:** Accepted
- **Date:** 2026-06
- **Deciders:** Karthik Reddy Tanigundala

## Context

Patient-level analytics (length of stay, readmission, diagnosis mix, paediatric
segmentation) need encounter-grain data. The real Victorian microdata sources —
**VAED**, **VEMD**, **ESIS** — are access-controlled behind a data-request and
ethics process that cannot be satisfied for a public portfolio. AIHW public data
is aggregate (hospital × financial year) and annual only.

## Decision

Split the problem by data grain:

- **Aggregate hospital performance** → real **AIHW MyHospitals** public data.
- **Patient-level / monthly analytics** → **Synthea** synthetic patients
  (MITRE Corp), configured for Victorian demographics, and clearly labelled
  synthetic everywhere it appears.

## Consequences

- **+** Demonstrates patient-grain modelling (the work I'd do on VAED in a real
  role) without touching restricted data.
- **+** Defensible and standard practice — Synthea is used by CSIRO and AU health
  IT vendors.
- **−** Synthea encodes largely US-derived disease prevalence; it is illustrative,
  not epidemiologically accurate for Victoria. **Never present Synthea figures as
  real Australian health facts** (also recorded in CLAUDE.md §25).
- **−** Two grains/sources to reconcile in the model; handled by keeping them in
  separate facts.

## Interview line

> "Patient-level Victorian data sits behind a data-request and ethics process I
> can't satisfy publicly, so I used real aggregate AIHW data and Synthea for the
> patient grain — the standard approach when microdata can't be shared."
