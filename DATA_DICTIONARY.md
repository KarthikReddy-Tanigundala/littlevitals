# Data Dictionary — Gold layer

Field-level definitions for the business-ready `GOLD` schema. Authoritative source
is the dbt schema YAML (with enforced contracts); this is the human-readable copy.
Browse the live, lineage-linked version via `dbt docs serve`.

> ⚠️ Sample-build values are synthetic (seed=42), not real AIHW data.

## `fct_ed_presentations` (fact)
Grain: **hospital × financial_year × triage_category** (annual).

| Column | Type | Description |
|---|---|---|
| `ed_presentation_key` | varchar | Surrogate PK (hash of hospital_code + FY + triage). |
| `hospital_key` | varchar | FK → `dim_hospital`. |
| `triage_key` | varchar | FK → `dim_triage_category`. |
| `date_key` | integer | FK → `dim_date` at the 1 July start of the FY (YYYYMMDD). |
| `financial_year` | varchar | Degenerate dimension, "YYYY-YY". |
| `triage_code` | integer | Degenerate dimension, ATS 1–5. |
| `total_presentations` | integer | ED presentations in the cell. |
| `median_wait_minutes` | integer | Median wait to treatment (0–1440). |
| `pct_seen_on_time` | double | Proportion (0–1) seen within the ATS benchmark. |
| `four_hour_rule_pct` | double | Proportion completed within 4 hours (NEAT). |
| `national_median_wait_minutes` | integer | National median benchmark (seed). |
| `national_on_time_pct` | double | National on-time benchmark (seed). |
| `on_time_target_pct` | double | ACEM on-time target for the triage category. |
| `variance_from_national_minutes` | integer | hospital median − national median. |
| `benchmark_met_flag` | boolean | `pct_seen_on_time ≥ on_time_target_pct`. |

## `dim_hospital`
| Column | Type | Description |
|---|---|---|
| `hospital_key` | varchar | Surrogate key; `-1` = Unknown member. |
| `hospital_code` | varchar | AIHW hospital code (natural key). |
| `hospital_name` | varchar | Hospital name. |
| `state_code` / `state_name` | varchar | State/territory. |
| `lhn_name` | varchar | Local Hospital Network / health service. |
| `peer_group` | varchar | AIHW hospital peer group. |
| `latitude` / `longitude` | double | Location (for maps). |
| `is_paediatric` | boolean | True for children's hospitals. |

## `dim_triage_category`
| Column | Type | Description |
|---|---|---|
| `triage_key` | varchar | Surrogate key; `-1` = Unknown. |
| `triage_code` | integer | ATS 1–5. |
| `triage_name` | varchar | Resuscitation … Non-urgent. |
| `max_wait_minutes` | integer | ATS max wait to treatment. |
| `on_time_target_pct` | double | ACEM seen-on-time target. |
| `description` | varchar | Clinical description. |

## `dim_date`
| Column | Type | Description |
|---|---|---|
| `date_key` | integer | YYYYMMDD surrogate key. |
| `full_date` | date | Calendar date. |
| `day_of_week` | integer | ISO (1=Mon … 7=Sun). |
| `day_name` | varchar | Weekday name. |
| `calendar_year` / `calendar_month` / `calendar_quarter` | integer | Calendar parts. |
| `calendar_month_name` | varchar | Month name. |
| `aus_financial_year` | varchar | "YYYY-YY" (1 Jul – 30 Jun). |
| `aus_financial_year_start_date` | date | 1 July of the FY. |
| `aus_fy_month` | integer | Month within FY (Jul=1 … Jun=12). |
| `aus_fy_quarter` | integer | FY quarter (Q1=Jul–Sep … Q4=Apr–Jun). |
| `is_weekday` | boolean | Mon–Fri. |

## `mart_hospital_scorecard` (reporting mart)
Grain: **hospital × financial_year**.

| Column | Type | Description |
|---|---|---|
| `hospital_name`, `lhn_name`, `peer_group`, `state_name`, `state_code` | varchar | Hospital attributes. |
| `financial_year` | varchar | "YYYY-YY". |
| `total_ed_presentations` | integer | Sum across triage categories. |
| `median_ed_wait_all_triage` | integer | Presentation-weighted median wait. |
| `pct_ed_seen_on_time_cat2` / `_cat3` | double | Cat 2 / Cat 3 on-time. |
| `four_hour_rule_pct` | double | NEAT 4-hour proportion. |
| `scorecard_overall_rating` | varchar | Meets / At Risk / Below Benchmark (from Cat 2). |
| `yoy_ed_presentations_growth_pct` | double | YoY presentation growth. |
| `yoy_median_wait_change_minutes` | integer | YoY median wait change. |
| `latitude` / `longitude` | double | Location (for maps). |
