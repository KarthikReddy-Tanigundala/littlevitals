# Security & Governance — LittleVitals

This project models a governance posture appropriate to a hospital decision-support
environment, even though all patient-level data is synthetic. Demonstrating the
*capability* is the point.

## 1. The Five Safes

| Safe | How LittleVitals addresses it |
|---|---|
| **Safe projects** | Public, educational benchmarking analytics; purpose stated in README. |
| **Safe people** | Least-privilege RBAC roles separating engineer / analyst / executive / readonly. |
| **Safe settings** | No real patient data; secrets via env vars / GitHub Secrets, never committed. |
| **Safe data** | Patient-level = **synthetic (Synthea)**; aggregate = AIHW public, de-identified. |
| **Safe outputs** | Small-number suppression (n<5); patient-level pages not Publish-to-Web (screenshots only). |

## 2. RBAC (Snowflake) — `sql/00_snowflake_setup.sql`

| Role | Access |
|---|---|
| `LITTLEVITALS_ENGINEER` | All schemas, read/write (dbt service role). |
| `LITTLEVITALS_ANALYST` | Read `SILVER` + `GOLD`. |
| `LITTLEVITALS_EXECUTIVE` | Read `GOLD` only. |
| `LITTLEVITALS_READONLY` | Public-facing: `GOLD` aggregate views only. |

Roles form a hierarchy (engineer ⊃ analyst ⊃ executive ⊃ readonly) so grants flow
down without duplication.

## 3. Data classification & masking

- **Object tag** `data_classification` with values `PUBLIC` / `INTERNAL` /
  `SENSITIVE_SYNTHETIC`, applied to patient-level dimensions when built.
- **Dynamic masking policy** `mask_postcode` coarsens geography (`3000` → `30XX`)
  for non-privileged roles — demonstrated even on synthetic quasi-identifiers.

| Data | Classification | Notes |
|---|---|---|
| AIHW aggregate ED/elective | PUBLIC | De-identified by AIHW before release. |
| Hospital master, geography | PUBLIC | Public reference data. |
| Synthea patient demographics | SENSITIVE_SYNTHETIC | Synthetic, but treated as PII for capability demo. |

## 4. Row-Level Security (Power BI — planned)

Dynamic RLS via `USERPRINCIPALNAME()` joined to a security-mapping table, so a
LHN manager sees only their hospitals while a state executive sees all VIC data.
Roles: `HOSPITAL_ANALYST`, `LHN_MANAGER`, `STATE_EXECUTIVE`. (See CLAUDE.md §5.4.)

## 5. Secrets handling

- `.env`, `profiles.yml` secrets, and `.streamlit/secrets.toml` are git-ignored.
- The committed `littlevitals_dbt/profiles.yml` is safe — it references credentials
  only via `env_var()`, never literals.
- CI runs on DuckDB with **no secrets**; only the optional production docs build
  uses Snowflake GitHub Secrets.
- `detect-secrets` runs as a pre-commit hook to block accidental credential commits.

## 6. Limitations

This is an analytics-engineering & BI portfolio, not a clinical or production
security system. No real patient data is used; no clinical decisions should be
based on it. See CLAUDE.md §25 for the full limitations statement.
