# CLAUDE.md — Project: LittleVitals
## Melbourne Health-System Analytics Platform
### Master Build Instructions for Claude Code (Opus 4.8)

---

## 0. PURPOSE & MISSION

You are building **LittleVitals** — a production-grade, end-to-end modern data stack analytics
platform over Victorian and Australian public health system data, with a paediatric lens.

This is a **portfolio flagship project** for Karthik Reddy Tanigundala, a Master of Data Science
candidate at RMIT University Melbourne, targeting Data Analyst / BI Analyst / Data Scientist roles
at Melbourne employers including Royal Children's Hospital Decision Support Unit, Telstra Health,
Western Health, Eastern Health, Medibank, Deloitte, EY, and similar.

The project must read as work produced by a **senior analytics engineer with 5–10 years of
industry experience and insider domain knowledge**. Every architectural decision, naming
convention, DAX measure, dbt model, and documentation artefact must reflect that standard.

**The output of this project is:**
1. A fully deployed, publicly accessible analytics platform
2. A polished GitHub repository with a standout README
3. A live dbt docs site on GitHub Pages
4. A Power BI dashboard published via Publish-to-Web
5. A Streamlit companion app hosted on Streamlit Community Cloud
6. All assets demonstrating Karthik's skills across the full modern data stack

---

## 1. HIGH-LEVEL ARCHITECTURE

```
RAW DATA SOURCES (PUBLIC AUSTRALIAN OPEN DATA)
       │
       ▼
┌─────────────────────────────────┐
│  INGESTION / LANDING LAYER      │
│  Python scripts (pandas)        │
│  → CSV / JSON → Snowflake RAW   │
│  schema (Bronze)                │
└────────────────┬────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐
│  TRANSFORMATION LAYER           │
│  dbt Core (Snowflake adapter)   │
│  Medallion: Bronze→Silver→Gold  │
│  Kimball star schema in Gold    │
│  dbt tests + documentation      │
└────────────────┬────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│  SERVING / PRESENTATION LAYER                           │
│                                                         │
│  A) Power BI (primary BI layer)                         │
│     ├── Desktop .pbix (star schema, DAX, RLS)           │
│     ├── Paginated report (.rdl) — "Board Pack" PDF      │
│     └── Publish-to-Web (public embed link)              │
│                                                         │
│  B) Streamlit companion app (Python)                    │
│     ├── KPI summary tiles                               │
│     ├── Interactive Plotly charts                       │
│     └── Deployed on Streamlit Community Cloud           │
│                                                         │
│  C) dbt docs site                                       │
│     └── Deployed on GitHub Pages via GitHub Actions     │
└─────────────────────────────────────────────────────────┘
```

---

## 2. DATA SOURCES — EXACT SPECIFICATIONS

### 2.1 PRIMARY: AIHW MyHospitals API (Free, open, no auth required)

**Base URL:** `https://myhospitalsapi.aihw.gov.au`

**Key endpoints to ingest:**

```
# All measure categories (discovery)
GET /api/v1/measure-categories

# ED waiting times — the core dataset
GET /api/v1/measure-downloads/myh-ed
# Returns: hospital-level ED data going back to 2011-12
# Fields: hospital code, LHN, state, triage category, median wait, % seen on time,
#         4-hour rule compliance, total presentations

# Elective surgery waiting times
GET /api/v1/measure-downloads/myh-elective-surgery

# All reporting units (hospitals)
GET /api/v1/reporting-units
# Returns hospital name, code, state, LHN, peer group, lat/lon

# Data for a specific hospital (use RCH code)
GET /api/v1/reporting-units/{code}/data-items
# Royal Children's Hospital Melbourne = look up code in reporting-units endpoint
```

**What to ingest:**
- ED care data: 2015-16 through 2024-25 (10 financial years)
- Elective surgery: 2015-16 through 2024-25
- Focus on Victorian hospitals (state = "VIC")
- Keep national benchmarks for comparison

**Data volume:** ~50,000–100,000 rows across all tables after parsing. Manageable on Snowflake
free tier.

### 2.2 SECONDARY: AIHW Static Data Tables (direct XLSX downloads)

**Elective surgery waiting times 2023-24 (XLSX):**
```
https://www.aihw.gov.au/getmedia/d1f39fa7-644f-4b46-95a0-a4d04360f2b1/Elective-surgery-waiting-times-2023-24.xlsx
```

**Emergency department care 2024-25 data tables (XLSX):**
- Download from: https://www.aihw.gov.au/hospitals/latest-updates-and-downloads/data
- File: "Emergency department care 2024-25 data tables" (264 KB XLSX)

Parse these XLSX files with `pandas` + `openpyxl`. Each workbook has multiple sheets — parse
all relevant sheets and load to Snowflake RAW schema.

### 2.3 SYNTHETIC PATIENT-LEVEL DATA (Synthea — Australian configuration)

**Tool:** Synthea™ open-source synthetic patient generator
**GitHub:** https://github.com/synthetichealth/synthea
**Purpose:** Generate realistic de-identified synthetic patient records modelled on Victorian
demographics to simulate a hospital EDW. This is STANDARD practice in healthcare analytics
portfolios — cite Synthea explicitly in README and all documentation.

**Generation parameters:**
```bash
# Generate 10,000 synthetic Australian patients (Victorian demographics)
java -jar synthea-with-dependencies.jar \
  -p 10000 \
  --exporter.fhir.export=false \
  --exporter.csv.export=true \
  -s 42 \
  Victoria Australia
```

**Output tables to use:**
- `patients.csv` — demographics (age, sex, suburb, postcode, ethnicity)
- `encounters.csv` — hospital visits (type, date, facility, duration, cost)
- `conditions.csv` — diagnoses (ICD-10 codes, onset date, resolved date)
- `procedures.csv` — clinical procedures
- `medications.csv` — prescriptions
- `observations.csv` — vitals, test results

**Why this is defensible:** Synthea is used by CSIRO, major AU health IT vendors, and academic
researchers. The CSIRO Data Access Portal hosts an Australian Synthea dataset. In interviews,
state: "I used Synthea to generate 10,000 synthetic Victorian patients — this is the standard
tool in healthcare analytics when patient-level data cannot be shared publicly."

**IMPORTANT:** Always clearly label synthetic data in dashboards and README.

### 2.4 TERTIARY: ABS Geographic Reference Data

**Victorian SA2 boundaries (for choropleth maps):**
```
https://www.abs.gov.au/statistics/standards/australian-statistical-geography-standard-asgs-edition-3/jul2021-jun2026/access-and-downloads/digital-boundary-files
```
Download SA2 shapefile → convert to GeoJSON → load postcode → SA2 mapping to Snowflake.

**Population denominators (for rate calculations):**
```
ABS ERP (Estimated Resident Population) by age/sex/region
https://www.abs.gov.au/statistics/people/population/national-state-and-territory-population
```

---

## 3. SNOWFLAKE SCHEMA DESIGN

Use a **Snowflake free trial** (30 days, ~$400 free credits — sufficient for this entire project).

### 3.1 Database structure

```sql
-- Database
CREATE DATABASE LITTLEVITALS_DB;

-- Schemas (Medallion)
CREATE SCHEMA LITTLEVITALS_DB.BRONZE;   -- Raw ingested data, immutable
CREATE SCHEMA LITTLEVITALS_DB.SILVER;   -- Cleaned, deduplicated, typed
CREATE SCHEMA LITTLEVITALS_DB.GOLD;     -- Star schema, business-ready

-- Separate schema for dbt metadata
CREATE SCHEMA LITTLEVITALS_DB.DBT_METADATA;
```

### 3.2 BRONZE layer tables (raw ingestion, exact source structure)

```sql
-- AIHW MyHospitals API — ED data
BRONZE.RAW_AIHW_ED_PRESENTATIONS     -- one row per hospital × financial_year × triage_category
BRONZE.RAW_AIHW_ELECTIVE_SURGERY     -- one row per hospital × financial_year × urgency_category
BRONZE.RAW_AIHW_REPORTING_UNITS      -- hospital master list
BRONZE.RAW_AIHW_MEASURE_CATEGORIES   -- measure metadata

-- AIHW XLSX static tables
BRONZE.RAW_AIHW_ED_XLSX_NATIONAL     -- national ED summary
BRONZE.RAW_AIHW_ELECTIVE_XLSX_VIC    -- Victorian elective surgery detail

-- Synthea synthetic patient data
BRONZE.RAW_SYNTHEA_PATIENTS
BRONZE.RAW_SYNTHEA_ENCOUNTERS
BRONZE.RAW_SYNTHEA_CONDITIONS
BRONZE.RAW_SYNTHEA_PROCEDURES
BRONZE.RAW_SYNTHEA_MEDICATIONS
BRONZE.RAW_SYNTHEA_OBSERVATIONS

-- ABS geographic
BRONZE.RAW_ABS_SA2_POSTCODE_MAP
BRONZE.RAW_ABS_ERP_VIC
```

### 3.3 GOLD star schema (Power BI semantic layer target)

```sql
-- FACT TABLES
GOLD.FACT_ED_PRESENTATIONS          -- grain: hospital × financial_year × triage_category × month
GOLD.FACT_ELECTIVE_SURGERY          -- grain: hospital × financial_year × urgency_category × specialty
GOLD.FACT_PATIENT_ENCOUNTERS        -- grain: synthetic encounter (Synthea)
GOLD.FACT_HOSPITAL_PERFORMANCE_KPI  -- grain: hospital × financial_year × kpi_measure

-- DIMENSION TABLES
GOLD.DIM_HOSPITAL                   -- SCD Type 1: name, code, state, LHN, PHN, peer group, lat/lon
GOLD.DIM_DATE                       -- Standard date dimension: day, week, month, quarter, FY, AUS_FY
GOLD.DIM_TRIAGE_CATEGORY            -- Code 1–5 lookup with description and national benchmark
GOLD.DIM_URGENCY_CATEGORY           -- Elective surgery Cat 1/2/3 lookup
GOLD.DIM_SURGICAL_SPECIALTY         -- ICD/ACHI surgical specialty codes
GOLD.DIM_GEOGRAPHY                  -- Suburb, SA2, PHN, LHN, state hierarchy
GOLD.DIM_PATIENT_DEMOGRAPHICS       -- Synthetic: age_band, sex, SEIFA_quintile, Indigenous_status_flag
GOLD.DIM_DIAGNOSIS                  -- ICD-10-AM code lookup (top 50 paediatric diagnoses)
GOLD.DIM_PAEDIATRIC_FLAG            -- Age group: neonate/infant/toddler/child/adolescent/adult
```

### 3.4 RBAC in Snowflake

```sql
-- Roles (demonstrates governance maturity — mirrors real hospital EDW)
CREATE ROLE LITTLEVITALS_ANALYST;       -- Can query SILVER and GOLD
CREATE ROLE LITTLEVITALS_ENGINEER;      -- Can query all schemas
CREATE ROLE LITTLEVITALS_EXECUTIVE;     -- Can query GOLD only (KPI tables)
CREATE ROLE LITTLEVITALS_READONLY;      -- Public-facing: GOLD aggregate views only

-- Row-level access at the hospital/region level
-- Implemented as Snowflake row access policies
-- Documented in dbt schema.yml exposure block
```

---

## 4. DBT PROJECT STRUCTURE

### 4.1 Full directory layout

```
littlevitals_dbt/
├── dbt_project.yml
├── profiles.yml.example          # Template (real creds in .env, gitignored)
├── packages.yml                  # dbt-utils, dbt-expectations, codegen
├── .github/
│   └── workflows/
│       ├── dbt_ci.yml            # PR: dbt compile + dbt test (slim CI)
│       └── dbt_docs_deploy.yml   # Push to main: generate docs → GitHub Pages
├── models/
│   ├── bronze/                   # Staging from raw — source freshness tests
│   │   ├── _bronze__sources.yml
│   │   ├── bronze_aihw_ed_presentations.sql
│   │   ├── bronze_aihw_elective_surgery.sql
│   │   ├── bronze_aihw_reporting_units.sql
│   │   ├── bronze_synthea_patients.sql
│   │   ├── bronze_synthea_encounters.sql
│   │   ├── bronze_synthea_conditions.sql
│   │   └── bronze_synthea_procedures.sql
│   ├── silver/                   # Cleaned, typed, deduplicated
│   │   ├── _silver__schema.yml
│   │   ├── silver_hospitals.sql          -- unified hospital master
│   │   ├── silver_ed_presentations.sql   -- cleaned ED data, type-cast
│   │   ├── silver_elective_surgery.sql   -- cleaned elective data
│   │   ├── silver_patients.sql           -- Synthea patients, AUS-normalised
│   │   ├── silver_encounters.sql         -- Synthea encounters + joined conditions
│   │   └── silver_diagnoses_icd10.sql    -- ICD-10-AM code mapping + paediatric flag
│   ├── gold/                     # Star schema marts
│   │   ├── _gold__schema.yml
│   │   ├── dimensions/
│   │   │   ├── dim_hospital.sql
│   │   │   ├── dim_date.sql               -- full AUS financial year date spine
│   │   │   ├── dim_triage_category.sql
│   │   │   ├── dim_urgency_category.sql
│   │   │   ├── dim_geography.sql
│   │   │   ├── dim_patient_demographics.sql
│   │   │   ├── dim_diagnosis.sql
│   │   │   └── dim_paediatric_flag.sql
│   │   └── facts/
│   │       ├── fact_ed_presentations.sql
│   │       ├── fact_elective_surgery.sql
│   │       ├── fact_patient_encounters.sql
│   │       └── fact_hospital_performance_kpi.sql
│   ├── marts/                    # Business-ready aggregates for Power BI Gold layer
│   │   ├── mart_ed_kpi_summary.sql       -- pre-aggregated KPI tile data
│   │   ├── mart_ed_triage_trend.sql      -- time-series by triage cat
│   │   ├── mart_elective_surgery_wait.sql
│   │   ├── mart_paediatric_benchmarks.sql -- VIC children's health KPIs vs national
│   │   ├── mart_hospital_scorecard.sql   -- one row per hospital × KY year
│   │   └── mart_rls_security_mapping.sql -- hospital → role mapping for Power BI RLS
│   └── analyses/                 -- Ad hoc analytical SQL (not materialised)
│       ├── four_hour_rule_decomposition.sql
│       └── paediatric_ed_seasonality.sql
├── tests/
│   ├── assert_ed_wait_times_positive.sql
│   ├── assert_triage_categories_complete.sql
│   └── assert_financial_year_spine_complete.sql
├── seeds/
│   ├── seed_triage_categories.csv        -- Code 1-5 definitions + ACEM benchmarks
│   ├── seed_urgency_categories.csv       -- Cat 1/2/3 definitions + recommended times
│   ├── seed_surgical_specialties.csv     -- ACHI specialty codes
│   ├── seed_icd10_paediatric_top50.csv   -- Top 50 paediatric diagnoses (ICD-10-AM)
│   ├── seed_state_names.csv
│   └── seed_national_benchmarks.csv      -- AIHW national median benchmarks per FY
├── macros/
│   ├── generate_surrogate_key.sql        -- wraps dbt-utils
│   ├── australian_financial_year.sql     -- converts calendar date → FY string "2023-24"
│   ├── triage_benchmark_met.sql          -- bool: actual_wait <= benchmark_wait
│   └── rolling_4qtr_average.sql         -- window function macro for KPI trends
├── snapshots/
│   └── snapshot_hospital_master.sql      -- SCD Type 2 on hospital metadata
└── docs/
    └── overview.md                       -- project overview shown in dbt docs homepage
```

### 4.2 Critical dbt model specifications

#### `gold/dimensions/dim_date.sql`
```sql
-- Australian financial year date dimension
-- FY runs 1 July – 30 June
-- Must include: date_key (YYYYMMDD int), full_date, day_of_week,
--   week_of_year, calendar_month_name, calendar_quarter,
--   aus_financial_year (e.g. "2023-24"), aus_financial_year_month (1-12, July=1),
--   aus_financial_quarter (Q1=Jul-Sep, Q2=Oct-Dec, Q3=Jan-Mar, Q4=Apr-Jun),
--   is_weekday, is_public_holiday_vic (seed from VIC public holidays list)
-- Spine: 1 Jan 2010 – 31 Dec 2030
-- Use dbt-utils date_spine macro
```

#### `gold/facts/fact_ed_presentations.sql`
```sql
-- Grain: one row per hospital × financial_year × triage_category × reporting_period
-- Surrogate key: surrogate_key(hospital_code, financial_year, triage_category)
-- Measures:
--   total_presentations
--   median_wait_minutes
--   pct_seen_on_time          -- % seen within ACEM benchmark
--   four_hour_rule_pct        -- % ED visits completed <4 hours
--   benchmark_met_flag        -- bool: pct_seen_on_time >= national benchmark
--   national_benchmark_median -- from seed_national_benchmarks
--   variance_from_national    -- hospital median - national median
-- Foreign keys: hospital_key, date_key, triage_category_key
-- Slowly changing: include valid_from, valid_to for historical rebasing
```

#### `mart_hospital_scorecard.sql`
```sql
-- One row per hospital per financial year
-- This is the primary mart consumed by the Power BI executive scorecard page
-- Columns:
--   hospital_name, lhn_name, peer_group, state
--   financial_year
--   total_ed_presentations
--   median_ed_wait_all_triage (minutes)
--   pct_ed_seen_on_time_cat2  -- Category 2 (Emergency) — most scrutinised
--   pct_ed_seen_on_time_cat3  -- Category 3 (Urgent)
--   four_hour_rule_pct
--   elective_median_wait_days_cat1
--   elective_median_wait_days_cat2
--   elective_median_wait_days_cat3
--   pct_elective_cat1_on_time
--   pct_elective_cat2_on_time
--   scorecard_overall_rating  -- computed: "Meets Benchmark" / "At Risk" / "Below Benchmark"
--                               based on weighted composite of key KPIs
--   yoy_ed_presentations_growth_pct
--   yoy_median_wait_change_minutes
```

### 4.3 dbt tests to implement

**Schema tests (in _schema.yml files):**
```yaml
# Every fact table PK:
- unique
- not_null

# Every FK:
- relationships: to: ref('dim_hospital'), field: hospital_key

# Business logic:
- accepted_values:
    values: [1, 2, 3, 4, 5]  # for triage_category_code
- dbt_utils.accepted_range:
    min_value: 0
    max_value: 100  # for percentage measures
- dbt_expectations.expect_column_values_to_be_between:
    min_value: 0
    max_value: 1440  # ED wait time can't exceed 24 hours (1440 minutes)
```

**Singular tests (in /tests directory):**
```sql
-- assert_ed_wait_times_positive.sql
SELECT * FROM {{ ref('fact_ed_presentations') }}
WHERE median_wait_minutes < 0

-- assert_financial_year_spine_complete.sql
-- Verify no gaps in the date spine for the range 2015-16 to 2024-25
```

### 4.4 GitHub Actions — CI/CD

**File: `.github/workflows/dbt_ci.yml`**
```yaml
# Triggers on every PR to main
# Steps:
# 1. Checkout
# 2. Install dbt-snowflake (pip)
# 3. dbt debug (connection test using GitHub Secrets for Snowflake creds)
# 4. dbt deps
# 5. dbt seed
# 6. dbt compile (syntax check without running)
# 7. dbt test --select state:modified+ (slim CI — only test changed models)
# 8. Comment PR with test results summary
```

**File: `.github/workflows/dbt_docs_deploy.yml`**
```yaml
# Triggers on push to main
# Steps:
# 1. Checkout
# 2. Install dbt-snowflake
# 3. dbt deps + dbt seed + dbt run
# 4. dbt docs generate
# 5. Deploy target/index.html + target/catalog.json + target/manifest.json to gh-pages branch
# 6. GitHub Pages serves at: https://karthikreddy-tanigundala.github.io/littlevitals/
```

---

## 5. POWER BI DESIGN SPECIFICATIONS

### 5.1 Data connection

**Connection type:** DirectQuery to Snowflake (preferred for a portfolio demo — proves live
pipeline, not static data)
**Connection string:**
```
Server: <snowflake_account>.snowflakecomputing.com
Warehouse: COMPUTE_WH
Database: LITTLEVITALS_DB
Schema: GOLD
Role: LITTLEVITALS_READONLY
```

**Import all GOLD tables + marts as the semantic model.**

### 5.2 Star schema in Power BI semantic model

Connect tables using:
```
FACT_ED_PRESENTATIONS → DIM_HOSPITAL (many-to-one on hospital_key)
FACT_ED_PRESENTATIONS → DIM_DATE (many-to-one on date_key)
FACT_ED_PRESENTATIONS → DIM_TRIAGE_CATEGORY (many-to-one on triage_category_key)
FACT_ELECTIVE_SURGERY → DIM_HOSPITAL
FACT_ELECTIVE_SURGERY → DIM_DATE
FACT_ELECTIVE_SURGERY → DIM_URGENCY_CATEGORY
FACT_PATIENT_ENCOUNTERS → DIM_HOSPITAL
FACT_PATIENT_ENCOUNTERS → DIM_DATE
FACT_PATIENT_ENCOUNTERS → DIM_PATIENT_DEMOGRAPHICS
FACT_PATIENT_ENCOUNTERS → DIM_DIAGNOSIS
```

**All relationships: single direction. No bidirectional. No many-to-many without a bridge.**

### 5.3 DAX measures to build (minimum 20 — demonstrates full-stack DAX fluency)

```dax
-- SECTION 1: BASE MEASURES
[Total ED Presentations] =
    SUM(FACT_ED_PRESENTATIONS[total_presentations])

[Median ED Wait (Minutes)] =
    AVERAGEX(FACT_ED_PRESENTATIONS,
        FACT_ED_PRESENTATIONS[median_wait_minutes])

[% Seen On Time - Cat 2] =
    CALCULATE(
        AVERAGE(FACT_ED_PRESENTATIONS[pct_seen_on_time]),
        DIM_TRIAGE_CATEGORY[triage_code] = 2
    )

[4-Hour Rule Compliance %] =
    AVERAGE(FACT_ED_PRESENTATIONS[four_hour_rule_pct])

[Elective Median Wait Cat 2 (Days)] =
    CALCULATE(
        AVERAGE(FACT_ELECTIVE_SURGERY[median_wait_days]),
        DIM_URGENCY_CATEGORY[urgency_code] = 2
    )

-- SECTION 2: TIME INTELLIGENCE (Australian FY-aware)
[YoY ED Presentations Growth %] =
    VAR CurrentYear = [Total ED Presentations]
    VAR PriorYear =
        CALCULATE([Total ED Presentations],
            DATEADD(DIM_DATE[full_date], -1, YEAR))
    RETURN DIVIDE(CurrentYear - PriorYear, PriorYear, BLANK())

[Rolling 4-Quarter Avg Wait (Cat 2)] =
    AVERAGEX(
        DATESINPERIOD(DIM_DATE[full_date],
            LASTDATE(DIM_DATE[full_date]), -4, QUARTER),
        [Median ED Wait (Minutes)]
    )

[ED Presentations - Same Period Last Year] =
    CALCULATE(
        [Total ED Presentations],
        SAMEPERIODLASTYEAR(DIM_DATE[full_date])
    )

-- SECTION 3: BENCHMARK COMPARISON
[vs National Median (Minutes)] =
    [Median ED Wait (Minutes)] -
    AVERAGE(FACT_ED_PRESENTATIONS[national_benchmark_median])

[Benchmark Status] =
    SWITCH(TRUE(),
        [% Seen On Time - Cat 2] >= 0.80, "✅ Meets Benchmark",
        [% Seen On Time - Cat 2] >= 0.70, "⚠️ At Risk",
        "🔴 Below Benchmark"
    )

[Benchmark Met %] =
    DIVIDE(
        COUNTROWS(FILTER(FACT_ED_PRESENTATIONS,
            FACT_ED_PRESENTATIONS[benchmark_met_flag] = TRUE())),
        COUNTROWS(FACT_ED_PRESENTATIONS),
        0
    )

-- SECTION 4: PATIENT/PAEDIATRIC MEASURES (Synthea layer)
[Total Paediatric Encounters] =
    CALCULATE(
        COUNTROWS(FACT_PATIENT_ENCOUNTERS),
        DIM_PATIENT_DEMOGRAPHICS[age_band] IN
            {"Neonate (0–28d)", "Infant (1–12m)", "Toddler (1–3y)",
             "Child (4–12y)", "Adolescent (13–17y)"}
    )

[Avg Length of Stay (Hours) - Paediatric] =
    CALCULATE(
        AVERAGE(FACT_PATIENT_ENCOUNTERS[los_hours]),
        DIM_PATIENT_DEMOGRAPHICS[age_band] IN
            {"Neonate (0–28d)", "Infant (1–12m)", "Toddler (1–3y)",
             "Child (4–12y)", "Adolescent (13–17y)"}
    )

[Paediatric Readmission Rate %] =
    DIVIDE(
        CALCULATE(COUNTROWS(FACT_PATIENT_ENCOUNTERS),
            FACT_PATIENT_ENCOUNTERS[is_readmission_30d] = TRUE(),
            DIM_PATIENT_DEMOGRAPHICS[age_band] <> "Adult (18+y)"),
        [Total Paediatric Encounters],
        0
    )

[Top Diagnosis - Paediatric] =
    FIRSTNONBLANK(
        TOPN(1,
            SUMMARIZE(FACT_PATIENT_ENCOUNTERS,
                DIM_DIAGNOSIS[diagnosis_description],
                "Count", COUNTROWS(FACT_PATIENT_ENCOUNTERS)),
            [Count], DESC),
        1
    )

-- SECTION 5: RLS-AWARE MEASURES
[Hospitals in View] =
    DISTINCTCOUNT(DIM_HOSPITAL[hospital_code])

[My LHN Performance vs State Avg] =
    [Median ED Wait (Minutes)] -
    CALCULATE([Median ED Wait (Minutes)],
        REMOVEFILTERS(DIM_HOSPITAL))
```

### 5.4 Row-Level Security (RLS) — Dynamic pattern

```dax
-- In Power BI Desktop: Modelling → Manage Roles → Create Role

-- Role: HOSPITAL_ANALYST
-- Table: DIM_HOSPITAL
-- DAX filter:
[hospital_code] IN
    SELECTCOLUMNS(
        FILTER(MART_RLS_SECURITY_MAPPING,
            MART_RLS_SECURITY_MAPPING[user_email] = USERPRINCIPALNAME()),
        "hospital_code", MART_RLS_SECURITY_MAPPING[hospital_code]
    )

-- Role: LHN_MANAGER
-- Table: DIM_HOSPITAL
-- DAX filter:
[lhn_name] IN
    SELECTCOLUMNS(
        FILTER(MART_RLS_SECURITY_MAPPING,
            MART_RLS_SECURITY_MAPPING[user_email] = USERPRINCIPALNAME()),
        "lhn_name", MART_RLS_SECURITY_MAPPING[lhn_name]
    )

-- Role: STATE_EXECUTIVE
-- No filter (sees all VIC data)

-- Role: NATIONAL_BENCHMARKS
-- Table: DIM_HOSPITAL
-- [state] = "VIC"  -- restricts to Victorian hospitals only
```

**Document the RLS model in:** `/docs/security/rls_architecture.md`
**Include in README:** A screenshot of "View as role" for each role.

### 5.5 Dashboard pages (minimum 6 pages)

**Page 1: Executive Overview (hero page)**
- KPI card tiles: Total ED Presentations | 4-Hour Rule % | Median Wait Cat 2 | Benchmark Status
- Line chart: ED presentations trend (2015-16 to 2024-25) by triage category
- Clustered bar: Top 10 Victorian hospitals by total ED presentations
- Map: Victorian hospitals with bubble size = presentations, colour = benchmark status
- Slicers: Financial Year | Hospital | LHN | Hospital Peer Group

**Page 2: ED Performance Deep Dive**
- Matrix: Hospital × Triage Category → Median Wait Minutes (conditional formatting)
- Scatter: Median Wait vs % Seen On Time (each dot = one hospital, one FY)
- Waterfall: YoY change in presentations (net new vs same-period-last-year)
- KPI trend line: 4-hour rule % over time vs national benchmark line
- Decomposition tree: Drill into which hospitals/triage cats drive benchmark failures

**Page 3: Elective Surgery Tracker**
- KPI tiles: Median wait Cat 1/2/3 | % seen on time | Overdue patients (>365 days)
- Gantt-style bar chart: Time-to-treatment by surgical specialty
- Line chart: Historical trend of median wait times (FY2015-16 to FY2024-25)
- Stacked bar: Removals from waitlist — admitted vs other reasons

**Page 4: Paediatric Health Intelligence (flagship differentiator)**
- KPI tiles targeting the AIHW Children's Headline Indicators (CHI) framework
- Bar chart: Top 10 paediatric diagnoses by encounter volume
- Age band distribution: Neonate / Infant / Toddler / Child / Adolescent encounters
- Line chart: Paediatric ED presentations by season (flu peaks visible in winter)
- Stacked area: Paediatric length of stay distribution
- Map: Geographic distribution of paediatric presentations (suburb heat map)
- NOTE: Clearly label Synthea synthetic data on this page

**Page 5: Hospital Scorecard (RLS-filtered)**
- Table with conditional formatting: hospital scorecard grid
- Traffic light icons for each KPI (Green/Amber/Red)
- Small multiples: Each hospital's wait time trend vs LHN average
- This page demonstrates RLS — show screenshots of same page for different roles in README

**Page 6: Benchmark Intelligence**
- Victorian performance vs national benchmark on all key measures
- Dot plot: Distribution of hospitals around the national median
- Callout cards: Best performer / Worst performer / Most improved hospital

### 5.6 Paginated Report — "Board Pack"

**Purpose:** Demonstrate paginated report skills (rare skill — high resume value)
**Tool:** Power BI Report Builder (free download)
**Dataset:** `mart_hospital_scorecard` via Snowflake connection

**Page layout:**
```
Page 1: Title page
  - "Victorian Health System Performance Report"
  - "Reporting Period: Financial Year 2024–25"
  - "Prepared by: LittleVitals Analytics Platform"
  - Date of extraction

Page 2: Executive Summary (4 KPI tables, auto-generated from parameterised dataset)

Page 3–N: Hospital Detail Pages (one page per hospital, auto-generated by report parameter)
  - Hospital name, LHN, peer group
  - ED KPI table: this year vs prior year vs national benchmark
  - Elective surgery KPI table
  - Trend sparkline (mini line chart)
  - Overall rating badge

Last page: Methodology and Data Sources
```

**Save as .rdl file. Include in GitHub repo under `/reports/`.**

### 5.7 Publishing

```
1. Sign up for Power BI Pro free 60-day trial (or use Fabric free tier)
2. Publish .pbix to Power BI Service workspace
3. Publish-to-Web: File → Embed Report → Publish to Web
   → Copy the public embed URL
   → Add to README and Streamlit companion app as an iframe
4. Schedule dataset refresh: 24-hour refresh pointing to Snowflake
5. IMPORTANT: Only use genuinely public/aggregate data in the published version
   Synthea patient-level synthetic data: include in .pbix but do NOT publish
   patient-level pages via Publish-to-Web. Export as screenshot instead.
```

---

## 6. STREAMLIT COMPANION APP

**File:** `streamlit_app/app.py`
**Deployment:** Streamlit Community Cloud (free)
**Repo requirement:** `requirements.txt` in root or `streamlit_app/`

### 6.1 App structure

```python
# Multi-page Streamlit app
# streamlit_app/
# ├── app.py               -- main entry point
# ├── pages/
# │   ├── 01_Overview.py
# │   ├── 02_ED_Performance.py
# │   ├── 03_Elective_Surgery.py
# │   ├── 04_Paediatric_Intel.py
# │   └── 05_Hospital_Scorecard.py
# ├── utils/
# │   ├── snowflake_connector.py   -- st.cache_data wrapped queries
# │   ├── chart_helpers.py
# │   └── kpi_calculations.py
# └── assets/
#     ├── littlevitals_logo.png
#     └── style.css
```

### 6.2 Snowflake connection in Streamlit

```python
import snowflake.connector
import streamlit as st

@st.cache_resource
def get_snowflake_connection():
    return snowflake.connector.connect(
        account=st.secrets["snowflake"]["account"],
        user=st.secrets["snowflake"]["user"],
        password=st.secrets["snowflake"]["password"],
        warehouse="COMPUTE_WH",
        database="LITTLEVITALS_DB",
        schema="GOLD",
        role="LITTLEVITALS_READONLY"
    )

@st.cache_data(ttl=3600)
def query_snowflake(sql: str) -> pd.DataFrame:
    conn = get_snowflake_connection()
    cur = conn.cursor()
    cur.execute(sql)
    return cur.fetch_pandas_all()
```

**Store Snowflake secrets in `.streamlit/secrets.toml` (gitignored).**
**Add secrets to Streamlit Community Cloud via the Secrets management UI.**

### 6.3 Key charts (use Plotly throughout — interactive)

```python
# Page 01_Overview.py

import plotly.express as px
import plotly.graph_objects as go

# KPI tiles using st.metric
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total ED Presentations (2024-25)",
              f"{total_presentations:,.0f}",
              delta=f"{yoy_change:+.1%} vs 2023-24")

# Time-series with benchmark reference line
fig = go.Figure()
fig.add_trace(go.Scatter(
    x=trend_df['financial_year'],
    y=trend_df['pct_seen_on_time_cat2'],
    mode='lines+markers',
    name='Victoria',
    line=dict(color='#1a6b5e', width=2.5)
))
fig.add_hline(
    y=0.80,
    line_dash="dash",
    line_color="red",
    annotation_text="National Benchmark (80%)",
    annotation_position="bottom right"
)

# Choropleth map of Victorian hospitals
fig_map = px.scatter_mapbox(
    hospitals_df,
    lat='latitude', lon='longitude',
    size='total_presentations',
    color='benchmark_status',
    color_discrete_map={
        'Meets Benchmark': '#2ecc71',
        'At Risk': '#f39c12',
        'Below Benchmark': '#e74c3c'
    },
    hover_name='hospital_name',
    hover_data=['lhn_name', 'median_wait_minutes', 'pct_seen_on_time_cat2'],
    mapbox_style='carto-positron',
    zoom=6,
    center={'lat': -37.8, 'lon': 144.9}  # Melbourne
)
```

---

## 7. PYTHON INGESTION SCRIPTS

**File structure:**
```
ingestion/
├── README.md                      -- how to run each script
├── requirements.txt
├── .env.example                   -- template (real .env gitignored)
├── config.py                      -- reads .env, exposes constants
├── snowflake_loader.py            -- reusable write-to-snowflake function
├── 01_ingest_aihw_api.py          -- MyHospitals API → Snowflake BRONZE
├── 02_ingest_aihw_xlsx.py         -- XLSX downloads → Snowflake BRONZE
├── 03_generate_synthea.py         -- Synthea generation + load instructions
├── 04_ingest_synthea_csvs.py      -- Synthea CSVs → Snowflake BRONZE
├── 05_ingest_abs_geography.py     -- ABS SA2/postcode → Snowflake BRONZE
└── run_all_ingestion.sh           -- orchestrate all scripts in order
```

### 7.1 Key ingestion pattern

```python
# ingestion/snowflake_loader.py
import snowflake.connector
from snowflake.connector.pandas_tools import write_pandas
import pandas as pd
import logging

logger = logging.getLogger(__name__)

def get_connection():
    return snowflake.connector.connect(
        account=os.getenv('SNOWFLAKE_ACCOUNT'),
        user=os.getenv('SNOWFLAKE_USER'),
        password=os.getenv('SNOWFLAKE_PASSWORD'),
        warehouse='COMPUTE_WH',
        database='LITTLEVITALS_DB',
        role='LITTLEVITALS_ENGINEER'
    )

def load_dataframe_to_snowflake(
    df: pd.DataFrame,
    table_name: str,
    schema: str = 'BRONZE',
    if_exists: str = 'replace'  # or 'append'
) -> None:
    """
    Load a pandas DataFrame to a Snowflake table.
    Adds ingestion metadata columns automatically.
    """
    df = df.copy()
    df['_ingested_at'] = pd.Timestamp.utcnow()
    df['_source_file'] = table_name

    # Normalise column names for Snowflake
    df.columns = [c.upper().replace(' ', '_').replace('-', '_')
                  for c in df.columns]

    conn = get_connection()
    success, nchunks, nrows, _ = write_pandas(
        conn=conn,
        df=df,
        table_name=table_name.upper(),
        schema=schema,
        database='LITTLEVITALS_DB',
        auto_create_table=True,
        overwrite=(if_exists == 'replace')
    )
    logger.info(f"Loaded {nrows} rows to {schema}.{table_name}")
    conn.close()
```

### 7.2 AIHW API ingestion

```python
# ingestion/01_ingest_aihw_api.py
import requests
import pandas as pd
from snowflake_loader import load_dataframe_to_snowflake

BASE_URL = "https://myhospitalsapi.aihw.gov.au/api/v1"

def fetch_reporting_units():
    """Fetch all hospital reporting units."""
    r = requests.get(f"{BASE_URL}/reporting-units", timeout=30)
    r.raise_for_status()
    return pd.json_normalize(r.json())

def fetch_ed_data():
    """
    Download the full ED measure dataset.
    Returns a DataFrame with one row per hospital × period × triage category.
    """
    r = requests.get(
        f"{BASE_URL}/measure-downloads/myh-ed",
        headers={"Accept": "text/csv"},
        timeout=120
    )
    r.raise_for_status()
    from io import StringIO
    df = pd.read_csv(StringIO(r.text))
    # Filter to VIC only for Bronze load
    # (keep all in raw, filter in Silver dbt model)
    return df

def fetch_elective_surgery_data():
    r = requests.get(
        f"{BASE_URL}/measure-downloads/myh-elective-surgery",
        headers={"Accept": "text/csv"},
        timeout=120
    )
    r.raise_for_status()
    from io import StringIO
    return pd.read_csv(StringIO(r.text))

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    print("Ingesting AIHW reporting units...")
    units_df = fetch_reporting_units()
    load_dataframe_to_snowflake(units_df, 'RAW_AIHW_REPORTING_UNITS')

    print("Ingesting AIHW ED data...")
    ed_df = fetch_ed_data()
    load_dataframe_to_snowflake(ed_df, 'RAW_AIHW_ED_PRESENTATIONS')

    print("Ingesting AIHW elective surgery data...")
    es_df = fetch_elective_surgery_data()
    load_dataframe_to_snowflake(es_df, 'RAW_AIHW_ELECTIVE_SURGERY')

    print("All AIHW ingestion complete.")
```

---

## 8. REPOSITORY STRUCTURE (ROOT LEVEL)

```
littlevitals/
├── README.md                      ← THE most important file — see spec in Section 9
├── ARCHITECTURE.md                ← full architecture diagram + design decisions
├── DATA_DICTIONARY.md             ← field-level definitions for all Gold tables
├── SECURITY.md                    ← RLS model documentation
├── CHANGELOG.md
├── LICENSE                        ← MIT
├── .gitignore                     ← MUST include: .env, profiles.yml, *.pbix (optional),
│                                     target/, dbt_packages/, __pycache__/
├── ingestion/                     ← Section 7
├── littlevitals_dbt/              ← Section 4
├── streamlit_app/                 ← Section 6
├── reports/                       ← Power BI files
│   ├── LittleVitals.pbix          ← main Power BI file
│   ├── BoardPack.rdl              ← paginated report
│   └── screenshots/               ← dashboard screenshots + GIF demo
│       ├── demo.gif               ← animated walkthrough (record with OBS/Loom)
│       ├── page1_executive.png
│       ├── page4_paediatric.png
│       └── rls_demo_hospital_role.png
├── docs/
│   ├── security/
│   │   └── rls_architecture.md
│   └── adr/                       ← Architecture Decision Records
│       ├── ADR-001-medallion-architecture.md
│       ├── ADR-002-synthea-for-patient-level-data.md
│       └── ADR-003-power-bi-directquery-vs-import.md
└── tests/                         ← pytest for ingestion scripts
    ├── test_aihw_api.py
    └── test_snowflake_loader.py
```

---

## 9. README.md — COMPLETE SPECIFICATION

The README is the most critical file. It must function as a technical thesis and a recruiter hook.

### 9.1 Structure

```markdown
# 🏥 LittleVitals — Melbourne Health-System Analytics Platform

> End-to-end modern data stack analytics platform over Victorian and Australian
> public health system performance data — built with Snowflake, dbt Core, Power BI,
> and Python. Live demo below.

---

## 🎯 Live Demo

| Asset | Link |
|---|---|
| 📊 Power BI Dashboard (interactive) | [Open Dashboard](POWER_BI_EMBED_URL) |
| 📄 dbt Documentation Site | [Open Docs](GITHUB_PAGES_URL) |
| 🚀 Streamlit App | [Open App](STREAMLIT_CLOUD_URL) |
| 🗄️ dbt DAG (lineage diagram) | [View DAG](GITHUB_PAGES_URL/#!/overview) |

<!-- INSERT demo.gif here -->
![LittleVitals Dashboard Demo](reports/screenshots/demo.gif)

---

## 📐 Architecture

<!-- INSERT architecture diagram (Mermaid.js or image) -->
\`\`\`mermaid
flowchart LR
    A[AIHW MyHospitals API] -->|Python ingestion| B[Snowflake BRONZE]
    C[AIHW XLSX Tables] -->|pandas| B
    D[Synthea Synthetic Patients] -->|CSV load| B
    E[ABS Geography] -->|pandas| B
    B -->|dbt Core| F[Snowflake SILVER]
    F -->|dbt Core| G[Snowflake GOLD\nStar Schema]
    G -->|DirectQuery| H[Power BI\nInteractive Dashboard]
    G -->|Snowflake connector| I[Streamlit\nCompanion App]
    H -->|Publish-to-Web| J[Public Embed]
    G -->|dbt docs generate| K[GitHub Pages\nDocumentation Site]
\`\`\`

---

## 🗂️ Project Highlights

- **10 years of Victorian ED and elective surgery data** (2015-16 to 2024-25) from AIHW
- **10,000 synthetic Victorian patients** generated with Synthea for patient-level analytics
- **Medallion architecture** (Bronze → Silver → Gold) in Snowflake with dbt Core
- **Kimball star schema** with 4 fact tables and 9 dimension tables
- **35+ dbt models** with full data quality tests and column-level documentation
- **20+ DAX measures** including Australian financial year time intelligence
- **Dynamic Row-Level Security** implemented in both Snowflake (row access policies) and Power BI (USERPRINCIPALNAME RLS)
- **Paginated "Board Pack" report** (.rdl) for executive PDF distribution
- **CI/CD pipeline**: GitHub Actions runs dbt tests on PRs and deploys docs to GitHub Pages on merge to main
- **Paediatric lens**: age-band segmentation aligned with AIHW Children's Headline Indicators framework

---

## 📊 Key Business Questions Answered

1. Which Victorian hospitals are failing the 4-hour ED rule, and by how much?
2. How has Category 2 elective surgery wait time changed over the past 5 years?
3. What are the top 10 paediatric diagnoses driving ED presentations?
4. How does Royal Children's Hospital Melbourne compare to state and national benchmarks?
5. Which Local Hospital Networks (LHNs) have improved the most year-on-year?
6. Are paediatric readmission rates within acceptable ranges?

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Data Warehouse | Snowflake (free trial) |
| Data Transformation | dbt Core 1.8+ (dbt-snowflake adapter) |
| Orchestration | GitHub Actions (CI/CD + dbt docs deployment) |
| BI / Dashboarding | Power BI Desktop + Service (DAX, Power Query, RLS, Paginated Reports) |
| Companion App | Streamlit (Python) |
| Ingestion | Python 3.11 (pandas, requests, snowflake-connector-python) |
| Data Sources | AIHW MyHospitals API · AIHW XLSX · Synthea Synthetic Patients · ABS Geography |
| Testing | dbt schema tests · dbt singular tests · pytest (ingestion layer) |
| Documentation | dbt docs (GitHub Pages) · Architecture Decision Records |
| Version Control | Git / GitHub |

---

## 🗄️ Data Sources

### Public Australian Open Data
| Source | What | URL |
|---|---|---|
| AIHW MyHospitals API | ED waiting times, elective surgery, hospital metadata (2015-25) | myhospitalsapi.aihw.gov.au |
| AIHW Data Tables | ED and elective surgery XLSX tables | aihw.gov.au |
| ABS ERP | Population denominators for rate calculations | abs.gov.au |
| ABS ASGS | SA2 geographic boundaries for mapping | abs.gov.au |

### Synthetic Data
| Source | What | Citation |
|---|---|---|
| Synthea™ (MITRE Corp) | 10,000 synthetic Victorian patients | synthetichealth.github.io/synthea. Also used by CSIRO (Guo et al. 2024, doi:10.1007/978-981-97-2671-4_3) |

> ⚠️ **Synthetic data disclaimer:** All patient-level data in this project is fully synthetic,
> generated by Synthea. No real patient data is used or referenced. Aggregate AIHW data is
> publicly available and de-identified by AIHW prior to publication.

---

## 🏗️ Repository Structure
[show directory tree]

## 🚀 Getting Started
[step-by-step setup instructions]

## 🧪 Running Tests
[dbt test + pytest commands]

## 📖 dbt Documentation
[link to GitHub Pages]

## 🔒 Security Model (RLS)
[link to docs/security/rls_architecture.md]

## 📚 Architecture Decision Records
[links to /docs/adr/]

## 🎓 About This Project
Built by Karthik Reddy Tanigundala as part of a flagship data analytics portfolio targeting
BI Analyst / Data Analyst / Data Scientist roles in Melbourne. The project demonstrates
end-to-end modern data stack proficiency with a focus on Australian healthcare data,
governance, and executive-level reporting.

LinkedIn: linkedin.com/in/karthik-reddy-datascience
GitHub: github.com/KarthikReddy-Tanigundala
```

---

## 10. ENVIRONMENT SETUP INSTRUCTIONS FOR CLAUDE CODE

When you begin, execute the following setup sequence:

### 10.1 Install all dependencies

```bash
# Python
pip install \
  snowflake-connector-python[pandas] \
  pandas \
  requests \
  openpyxl \
  python-dotenv \
  plotly \
  streamlit \
  pytest \
  pyyaml

# dbt
pip install dbt-core dbt-snowflake

# Node (for any optional tooling)
# Not required for this project
```

### 10.2 Environment variables (.env file — gitignored)

```bash
SNOWFLAKE_ACCOUNT=your_account.region
SNOWFLAKE_USER=your_username
SNOWFLAKE_PASSWORD=your_password
SNOWFLAKE_DATABASE=LITTLEVITALS_DB
SNOWFLAKE_WAREHOUSE=COMPUTE_WH
SNOWFLAKE_ROLE=LITTLEVITALS_ENGINEER
```

### 10.3 dbt profiles.yml (~/.dbt/profiles.yml — NOT in repo)

```yaml
littlevitals:
  target: dev
  outputs:
    dev:
      type: snowflake
      account: "{{ env_var('SNOWFLAKE_ACCOUNT') }}"
      user: "{{ env_var('SNOWFLAKE_USER') }}"
      password: "{{ env_var('SNOWFLAKE_PASSWORD') }}"
      role: LITTLEVITALS_ENGINEER
      database: LITTLEVITALS_DB
      warehouse: COMPUTE_WH
      schema: DBT_DEV
      threads: 4
      client_session_keep_alive: false
    prod:
      type: snowflake
      account: "{{ env_var('SNOWFLAKE_ACCOUNT') }}"
      user: "{{ env_var('SNOWFLAKE_USER') }}"
      password: "{{ env_var('SNOWFLAKE_PASSWORD') }}"
      role: LITTLEVITALS_ENGINEER
      database: LITTLEVITALS_DB
      warehouse: COMPUTE_WH
      schema: GOLD
      threads: 8
```

---

## 11. BUILD ORDER (Claude Code Execution Sequence)

Follow this exact sequence. Do not jump ahead.

```
PHASE 1 — FOUNDATION (do this first, validate before proceeding)
  Step 1.1: Create full repo directory structure
  Step 1.2: Write .gitignore, LICENSE, requirements.txt, packages.yml
  Step 1.3: Write dbt_project.yml with correct materialization config
  Step 1.4: Create Snowflake database + schemas + RBAC SQL script
             → File: /sql/00_snowflake_setup.sql

PHASE 2 — DATA INGESTION
  Step 2.1: Write ingestion/config.py, snowflake_loader.py
  Step 2.2: Write and test 01_ingest_aihw_api.py
             → Validate: check BRONZE.RAW_AIHW_REPORTING_UNITS has rows
  Step 2.3: Write 02_ingest_aihw_xlsx.py
  Step 2.4: Document Synthea setup in ingestion/README.md
             → Write 04_ingest_synthea_csvs.py (assumes Synthea already run)
  Step 2.5: Write 05_ingest_abs_geography.py
  Step 2.6: Write run_all_ingestion.sh

PHASE 3 — DBT MODELS
  Step 3.1: Write all seed CSV files (triage categories, urgency, benchmarks, ICD-10)
  Step 3.2: Write Bronze staging models + _bronze__sources.yml
             → dbt run --select bronze.* && dbt test --select bronze.*
  Step 3.3: Write Silver models + _silver__schema.yml
             → dbt run --select silver.* && dbt test --select silver.*
  Step 3.4: Write all dimension models (dim_date first — everything depends on it)
  Step 3.5: Write all fact models
             → dbt run --select gold.* && dbt test --select gold.*
  Step 3.6: Write mart models
  Step 3.7: Write all macros
  Step 3.8: Write all custom singular tests
  Step 3.9: Write docs/overview.md for dbt docs homepage
             → dbt docs generate && dbt docs serve (validate locally)

PHASE 4 — CI/CD
  Step 4.1: Write .github/workflows/dbt_ci.yml
  Step 4.2: Write .github/workflows/dbt_docs_deploy.yml
  Step 4.3: Configure GitHub Secrets (document in ARCHITECTURE.md)

PHASE 5 — POWER BI
  Step 5.1: Document semantic model relationships in reports/SEMANTIC_MODEL.md
  Step 5.2: Write all DAX measures (copy from Section 5.3 of this file)
  Step 5.3: Document RLS configuration in docs/security/rls_architecture.md
  Step 5.4: Take RLS screenshots

PHASE 6 — STREAMLIT APP
  Step 6.1: Write streamlit_app/utils/ modules
  Step 6.2: Write each page
  Step 6.3: Write .streamlit/config.toml (theme configuration)
  Step 6.4: Write requirements.txt for Streamlit Cloud

PHASE 7 — DOCUMENTATION
  Step 7.1: Write Architecture Decision Records (3 ADRs)
  Step 7.2: Write DATA_DICTIONARY.md
  Step 7.3: Write SECURITY.md
  Step 7.4: Write README.md (full spec from Section 9)
  Step 7.5: Write ingestion/README.md (setup guide)

PHASE 8 — FINAL POLISH
  Step 8.1: Add column descriptions to ALL dbt schema.yml files
             (every column in every gold model must have a description)
  Step 8.2: Add meta tags to dbt models (owner, domain, contains_pii)
  Step 8.3: Verify all tests pass: dbt build
  Step 8.4: Record demo.gif (OBS Studio or Loom)
  Step 8.5: Final README review — every link works, every screenshot current
```

---

## 12. QUALITY STANDARDS — NON-NEGOTIABLE

Every deliverable must meet these standards before being committed:

### Code quality
- All Python files: type hints, docstrings, logging (not print statements)
- All dbt models: description in schema.yml for the model AND every column
- All SQL: CTEs named descriptively, no `SELECT *` in gold/mart models
- All dbt macros: docstring block explaining purpose and arguments

### Documentation quality
- README must be self-contained — someone with zero prior context can set it up
- Architecture diagram must be accurate (update if you change the design)
- Every ADR: Context / Decision / Consequences format

### Data quality
- Zero dbt test failures on main branch (enforced by CI)
- All fact table PKs: unique + not_null
- All percentage measures: bounded 0–100
- All wait time measures: non-negative, capped at 1440 minutes (24 hours)

### Security
- No credentials in any committed file
- .gitignore must include: .env, profiles.yml, *.pbix (large binary), target/,
  dbt_packages/, __pycache__/, .DS_Store
- GitHub Secrets used for all CI/CD credentials

---

## 13. INTERVIEW DEFENSIBILITY MAP

Every element of this project maps to interview questions Karthik will face.
For each component, the stated rationale is his interview answer.

| Component | Interview Question | Answer (quote verbatim) |
|---|---|---|
| Medallion architecture | "Why three layers?" | "Separation of concerns — Bronze preserves source fidelity so we can always reprocess; Silver handles type-casting and deduplication once; Gold is optimised purely for query performance. In healthcare specifically, you need Bronze immutability for audit trails." |
| Synthea synthetic data | "Is this real data?" | "No — I used Synthea, the open-source synthetic patient generator from MITRE Corp. It's the standard tool in healthcare IT when you can't use real patient data. CSIRO used it in a published 2024 paper to generate Australian patient data. My aggregate AIHW data is real and publicly released by AIHW." |
| dbt tests | "How do you ensure data quality?" | "dbt gives me a declarative test framework — I define schema tests like uniqueness and referential integrity in YAML, and singular tests in SQL for business logic. The CI pipeline runs `dbt test` on every PR, so no model reaches main without passing tests." |
| Dynamic RLS | "How does RLS work?" | "In Power BI, I used USERPRINCIPALNAME() in a DAX filter expression that joins against a security mapping table. So a LHN manager's UPN maps to their hospitals — they see only their data, but the VP sees everything. It's declarative and scales without rebuilding reports." |
| DAX time intelligence | "Can you do year-over-year in DAX?" | "Yes — for Australian financial year, which runs July to June, I built a custom date dimension with an aus_financial_year column. Time intelligence functions like SAMEPERIODLASTYEAR work on the date table, not the calendar year, so all my YoY measures respect the FY boundary correctly." |
| Paginated reports | "What's a paginated report?" | "A paginated report is designed for pixel-perfect, multi-page output — like a PDF board pack. Unlike interactive dashboards, it renders every row of data across as many pages as needed. I built a hospital-by-hospital board pack using Power BI Report Builder, parameterised so each hospital gets its own page automatically." |
| GitHub Actions CI | "How do you deploy your dbt project?" | "I have two workflows — a CI workflow that runs on every PR, compiling and testing only the changed models using dbt's slim CI pattern; and a docs deployment workflow that triggers on merge to main, runs the full build, generates dbt docs, and pushes to GitHub Pages automatically." |

---

## 14. KNOWN CONSTRAINTS AND WORKAROUNDS

| Constraint | Workaround | Note |
|---|---|---|
| VEMD patient-level data is access-controlled | Use Synthea for patient-level analytics; use AIHW public aggregate for hospital performance | Clearly labelled in dashboard |
| AIHW CHI interactive portal uses Flash (deprecated) | Download CHI data tables directly from AIHW website as XLSX | Only 12 of 19 CHI indicators have data — design around those 12 |
| Power BI Publish-to-Web has no per-user auth | Do NOT publish patient-level Synthea pages via Publish-to-Web | Publish aggregate hospital performance only; show Synthea pages as screenshots |
| Snowflake free trial = 30 days | Use Snowflake efficiently — suspend warehouse when not querying | Total queries for this project are well within free tier limits if warehouse is suspended |
| Power BI Pro required for Publish-to-Web | Start 60-day free Pro trial | Record demo.gif before trial expires as permanent fallback |
| dbt Cloud free tier limits | Use dbt Core (open source) locally + GitHub Actions for CI/CD | dbt Core is free forever |

---

## 15. FINAL DELIVERABLES CHECKLIST

Before marking this project complete:

- [ ] GitHub repository: public, clean history, no credentials committed
- [ ] README.md: demo GIF + architecture diagram + live links in first 20 lines
- [ ] Live Power BI embed URL: working, displays at least 4 dashboard pages
- [ ] Live Streamlit app URL: working, connects to Snowflake, all pages load
- [ ] dbt docs site: live on GitHub Pages, DAG visible, all models documented
- [ ] All dbt tests passing: zero failures
- [ ] All Gold model columns: have descriptions in schema.yml
- [ ] Architecture Decision Records: 3 ADRs committed
- [ ] RLS demonstration: screenshots of 3 different role views in README
- [ ] Paginated report (.rdl): committed to /reports/
- [ ] Synthea data: clearly labelled as synthetic everywhere it appears
- [ ] Interview defensibility: Karthik can speak for 60+ seconds on every component

---

## 16. ERRATA, CLARIFICATIONS & DESIGN-DECISION REVISIONS

> Read this **before** building. These corrections override anything earlier in the document
> that conflicts. They exist because Sections 1–15 contain a few aspirational assumptions that
> do not survive contact with the real data. A senior engineer documents these honestly rather
> than letting them silently break the build. Each one is also an interview talking point.

### 16.1 The ED fact grain is **annual**, not monthly
Sections 3.3 and 4.2 imply a `× month` grain for `FACT_ED_PRESENTATIONS`. **AIHW MyHospitals
public data is published per financial year, not per month.** There is no public monthly hospital-
level ED feed. Therefore:

- **Canonical ED/elective grain = `hospital × financial_year × triage_category` (annual).** The
  `reporting_period` column = the AIHW reporting financial year. Drop "month" from the AIHW facts.
- **Monthly/seasonal granularity comes ONLY from the Synthea encounter layer** (which has true
  encounter timestamps). Any monthly ED chart on the *AIHW* data is therefore not available; the
  "paediatric seasonality" and "winter flu peak" visuals are built on **Synthea encounters** and
  **must be labelled synthetic**.
- If a monthly *shape* is ever shown over AIHW data, it must be explicitly captioned
  "illustrative monthly disaggregation — source data is annual" and never presented as real.

### 16.2 Power BI connection: **Import is the default, not DirectQuery**
Section 5.1 names DirectQuery as "preferred." For *this* project that is the wrong default, and
knowing why is itself a strong interview answer:

- The Snowflake warehouse **auto-suspends** to protect the free trial (Section 22). DirectQuery
  against a cold warehouse means every demo interaction triggers a multi-second warehouse resume
  → the dashboard looks broken to a recruiter.
- The dataset is tiny (tens of thousands of rows) → Import mode is instant, works offline, and
  keeps Publish-to-Web fast and free.
- **Decision: ship Import mode with a scheduled refresh.** Build *one* DirectQuery page as proof
  of capability and document the trade-off in `ADR-003`. Interview line: *"I chose Import because
  with an auto-suspending trial warehouse, DirectQuery's cold-start latency would degrade the demo;
  Import gives sub-second interactivity. I'd switch to DirectQuery or a hybrid composite model the
  moment data volume or freshness-SLA justified the warehouse staying warm."*

### 16.3 The AIHW API is **not a stable contract** — design for it changing
The endpoints in Section 2.1 are best-effort and have changed historically. **Do not let the whole
build depend on a live API call succeeding.** Mandatory resilience pattern:

1. Every ingestion script writes the **raw API/XLSX response to `data/raw_snapshots/`** (gitignored,
   but a tiny **sampled** fixture is committed to `tests/fixtures/`).
2. If the live endpoint 404s or changes shape, fall back to the **committed static XLSX downloads**
   (Section 2.2) — these are durable.
3. The dbt + BI layers consume **Snowflake**, never the API directly, so a source outage never
   breaks downstream. Re-ingestion is a deliberate, logged action.
4. Add a `--source live|snapshot` flag to each ingestion script so the pipeline is reproducible
   without internet access (and so CI never hits AIHW).

### 16.4 Naming-convention reconciliation
Section 4 mixes medallion prefixes (`bronze_`, `silver_`) with Kimball prefixes (`dim_`, `fact_`).
Adopt this single convention and apply it everywhere (see §27 for the full table):
`stg_<source>__<entity>` (bronze staging) → `int_<entity>__<verb>` (silver intermediate) →
`dim_<entity>` / `fct_<entity>` (gold) → `mart_<subject>` (marts). Where the existing file says
`bronze_aihw_ed_presentations`, read it as `stg_aihw__ed_presentations`, etc. Keep the medallion
*schemas* (BRONZE/SILVER/GOLD); change only the *model name* prefixes for consistency.

### 16.5 Windows-first execution
Karthik builds on **Windows 11** (Power BI Desktop is Windows-only — convenient). The `.sh`
orchestrators in Sections 7 and 2 will not run natively. **Ship a cross-platform Python
orchestrator `ingestion/run_all_ingestion.py`** as the canonical entrypoint and keep the `.sh`
as a thin wrapper. All "bash" snippets must also have a documented PowerShell equivalent in
`ingestion/README.md`. Synthea needs a JDK (Temurin 17+) — document the Windows install.

---

## 17. HEALTHCARE DOMAIN KNOWLEDGE PACK (insider layer)

This is the domain fluency that separates a "data person who found a health dataset" from
"an analyst who understands the health system." Encode these facts into **seeds**, **column
descriptions**, and **README/ADR prose** so they surface naturally.

### 17.1 Australasian Triage Scale (ATS) — exact clinical targets
Seed `seed_triage_categories.csv` must carry these (source: ACEM):

| Code | Name | Max wait to treatment | "Seen on time" performance target |
|---|---|---|---|
| 1 | Resuscitation | Immediate (0 min) | 100% |
| 2 | Emergency | 10 min | 80% |
| 3 | Urgent | 30 min | 75% |
| 4 | Semi-urgent | 60 min | 70% |
| 5 | Non-urgent | 120 min | 70% |

> Category 2 is the most politically scrutinised because it captures genuine emergencies (e.g.
> chest pain, acute paediatric distress) where the 10-minute target is frequently missed under load.

### 17.2 NEAT / the "4-hour rule" — the nuance that signals insider knowledge
- The **National Emergency Access Target (NEAT)** was introduced ~2012 with a headline goal of
  **90% of ED patients departing (admitted / discharged / transferred) within 4 hours**.
- **It was effectively never met nationally**, was de-emphasised federally after ~2015, and most
  states retained their own variants. Victoria reports time-in-ED percentile measures.
- **Why it matters for the build:** treat the 4-hour metric as an *operational signal*, not a
  pass/fail truth. The dashboard should show the *trend and gap to target*, not a green tick.
  Interview line: *"NEAT is a useful directional KPI but it was politically set and rarely achieved;
  I present it as a trajectory against benchmark rather than as a binary, which is how a DSU would
  actually brief an exec."*

### 17.3 Elective surgery — urgency categories & clinically recommended max wait
Seed `seed_urgency_categories.csv`:

| Category | Clinical meaning | Recommended max wait |
|---|---|---|
| 1 | Procedure needed within 30 days (potential to deteriorate quickly) | 30 days |
| 2 | Needed within 90 days (some pain/dysfunction, unlikely to deteriorate quickly) | 90 days |
| 3 | Needed within 365 days (minimal pain/dysfunction) | 365 days |

Key derived measures: **% seen within clinically recommended time**, **median & 90th-percentile
wait days**, **count "overdue" (waited > recommended)**, **removals from list (admitted vs other)**.

### 17.4 Victorian data landscape — why we use AIHW + Synthea (not the real microdata)
Document this in `ADR-002`:

| Dataset | Custodian | Content | Access |
|---|---|---|---|
| **VAED** (Victorian Admitted Episodes Dataset) | DH Victoria | Admitted episodes, AR-DRG, ICD-10-AM | Access-controlled (data request, ethics) |
| **VEMD** (Victorian Emergency Minimum Dataset) | DH Victoria | ED presentations, patient-level | Access-controlled |
| **ESIS** (Elective Surgery Information System) | DH Victoria | Waitlist episodes | Access-controlled |
| **AIHW MyHospitals** | AIHW (Commonwealth) | De-identified **aggregate** hospital performance | **Public** ✅ |

> Interview line: *"Patient-level Victorian data (VAED/VEMD/ESIS) sits behind a data-request and
> ethics process I can't satisfy for a public portfolio, so I split the problem: real **aggregate**
> performance from AIHW's public release, and **synthetic** patient-level data from Synthea to
> demonstrate the patient-grain modelling I'd do on VAED in a real role."*

### 17.5 Coding & casemix systems (use the right acronym in the right place)
- **ICD-10-AM** — diagnoses (Australian Modification). Drives `dim_diagnosis`.
- **ACHI** — Australian Classification of Health Interventions = **procedures** (not "surgical
  specialty"; specialty is an administrative grouping). Fix the §3.3 wording accordingly.
- **AR-DRG** — Australian Refined Diagnosis Related Groups = casemix/funding classification.
- **SRG / surgical specialty** — administrative grouping for elective surgery reporting.

### 17.6 AIHW Children's Headline Indicators (CHI)
The paediatric page (§5.5 Page 4) should explicitly map tiles to the **CHI framework** (19
indicators across health, early learning, safety, wellbeing). Per §14, only ~12 have usable public
data — **design around those 12 and say so**. Examples to target: immunisation coverage, potentially
preventable hospitalisations (PPH) in children, injury presentations, dental, mental health.

### 17.7 Geography & equity reference
- **LHN** (Local Hospital Network) — national grouping; in Victoria these are mostly individual
  **public health services** (e.g., The Royal Children's Hospital is its own health service).
- **PHN** (Primary Health Network) — primary-care region.
- **SA2/SA3/SA4** — ABS Statistical Areas (ASGS Edition 3). SA2 ≈ suburb-cluster, the standard
  small-area unit for choropleths and rate denominators.
- **SEIFA / IRSD** — Socio-Economic Indexes for Areas; **IRSD quintile 1 = most disadvantaged,
  5 = least**. Powers all equity analysis (§18).
- **ERP** — Estimated Resident Population (ABS); the **denominator** for any *rate per 100,000*.
- **Remoteness (ASGS-RA)** — Major Cities / Inner Regional / Outer Regional / Remote / Very Remote.

### 17.8 Acronym glossary (put a copy in `DATA_DICTIONARY.md`)
ACEM, ATS, NEAT, ED, LHN, PHN, DSU (Decision Support Unit), VAED, VEMD, ESIS, AR-DRG, ICD-10-AM,
ACHI, PPH (Potentially Preventable Hospitalisation), CHI, SEIFA, IRSD, ERP, SA2, ASGS, RA
(Remoteness Area), FY (Financial Year), RLS, SCD, DAG, CI/CD.

---

## 18. DATA SCIENCE & ADVANCED ANALYTICS LAYER (the differentiator for DS roles)

The current spec is strong **analytics engineering** but weak **data science** — yet the target
includes Data Scientist roles. This section adds a defensible, statistically literate analytics
layer. Build it in `analytics/` (notebooks + reusable `.py`), surface headline results in a
Streamlit **"Insights"** page, and **materialise the scored outputs back into GOLD** (e.g.
`gold/fct_ed_demand_forecast.sql` reading a scored CSV via a seed or a Python model) so Power BI
can consume them too.

```
analytics/
├── README.md
├── requirements.txt                 # statsmodels, prophet, scikit-learn, lifelines, scipy
├── 01_ed_demand_forecast.ipynb      # SARIMA / Prophet on presentations
├── 02_funnel_plot_comparison.ipynb  # fair institutional comparison (Spiegelhalter)
├── 03_seasonality_decomposition.ipynb
├── 04_equity_analysis.ipynb         # SEIFA / remoteness gradients
├── 05_readmission_model.ipynb       # logistic regression on Synthea (clearly synthetic)
├── 06_waitlist_survival.ipynb       # Kaplan–Meier time-to-treatment
├── 07_hospital_clustering.ipynb     # k-means peer-group discovery
└── src/
    ├── forecasting.py
    ├── funnel.py                    # control limits + outlier flagging
    ├── stats_tests.py               # two-proportion z-test, CIs
    └── plotting.py
```

### 18.1 Use-case catalogue (each = method → output → where surfaced → interview value)

| # | Use case | Method | Output | Surfaced in |
|---|---|---|---|---|
| 1 | **ED demand forecasting** | SARIMA / Prophet on FY/quarterly presentations; capture winter respiratory surge in paediatrics | 4-quarter-ahead forecast + 80/95% prediction intervals | Streamlit Insights + `fct_ed_demand_forecast` → Power BI |
| 2 | **Fair hospital comparison** | **Funnel plot** (Spiegelhalter 2005): indicator vs volume with binomial 95%/99.8% control limits around the pooled mean | Outlier hospitals flagged "special-cause", not naive league-table rank | Power BI Page 6 + notebook |
| 3 | **Anomaly detection** | STL decomposition residuals / robust z-score (IQR) on wait-time series | Flagged anomalous hospital-years | dbt test (`anomaly`) + Insights |
| 4 | **Seasonality** | STL decomposition on **Synthea** paediatric ED encounters | Trend/seasonal/residual; quantified winter amplitude | Page 4 (labelled synthetic) |
| 5 | **Equity / disparity** | Wait-time & PPH rate by **SEIFA quintile** and **remoteness**; test linear trend (Cochran-Armitage / regression slope) | Disadvantage gradient + significance | Page 6 + Insights |
| 6 | **Readmission risk (synthetic)** | Logistic regression: 30-day readmission ~ age_band + comorbidity_count + LOS; report **ROC-AUC**, calibration | Risk score + feature importances | Page 4 (clearly synthetic) |
| 7 | **Waitlist survival** | **Kaplan–Meier** time-to-admission by urgency category; log-rank test | Survival curves; median time-to-treatment | Page 3 / Insights |
| 8 | **Peer-group discovery** | k-means on standardised KPI vector; validate against AIHW peer groups | Data-driven hospital clusters | Notebook + Insights |
| 9 | **Hypothesis testing** | **Two-proportion z-test** + 95% CI: is hospital's on-time rate ≠ state? | "Significantly above/below/within state" label | DAX-adjacent measure / Insights |
| 10 | **Scenario / what-if** | Parameterised growth on presentations → benchmark impact | Interactive what-if | Power BI what-if parameter / Streamlit slider |

### 18.2 Funnel plots — the single highest-credibility addition
> **Why this matters:** ranking hospitals in a "league table" is a known statistical fallacy —
> small hospitals have noisier rates and dominate the extremes. The health-services-research
> standard (Spiegelhalter, *Statistics in Medicine* 2005) is the **funnel plot**: plot each
> hospital's indicator against its case volume, draw control limits that *widen for low volume*,
> and only flag points outside the limits as genuine outliers. Implementing this signals real
> domain literacy. Provide `funnel.py` with binomial control limits and overdispersion adjustment,
> and put one funnel plot on **Page 6 (Benchmark Intelligence)** with a caption explaining it.

### 18.3 Statistical honesty rules (enforced in notebooks & captions)
- Always show **uncertainty** (CIs / prediction intervals), never a bare point estimate for a
  comparison.
- **No causal language** on observational data ("associated with", not "causes").
- State **n** and apply **small-number suppression** (mask cells with n < 5; AIHW does this — mirror it).
- Forecasts: report backtest error (MAPE/MAE on a holdout) — never ship an unvalidated forecast.

---

## 19. SEMANTIC / METRICS LAYER (governed metrics, single source of truth)

Define business metrics **once**, in dbt, so Power BI, Streamlit, and ad-hoc SQL cannot drift.
Use the **dbt Semantic Layer (MetricFlow)** spec for semantic models + metrics. (Note: the hosted
Semantic Layer *API* needs dbt Cloud; with dbt Core you still define metrics in YAML and can query
them via the `dbt-metricflow` CLI — document this limitation in the README.)

```yaml
# models/gold/_semantic_models.yml
semantic_models:
  - name: ed_presentations
    model: ref('fct_ed_presentations')
    entities:
      - {name: hospital, type: foreign, expr: hospital_key}
      - {name: triage,   type: foreign, expr: triage_category_key}
    dimensions:
      - {name: financial_year, type: categorical}
    measures:
      - {name: total_presentations, agg: sum,  expr: total_presentations}
      - {name: wait_minutes_sum,    agg: sum,  expr: median_wait_minutes}
      - {name: on_time_pct_avg,     agg: average, expr: pct_seen_on_time}

metrics:
  - name: total_ed_presentations
    type: simple
    label: "Total ED Presentations"
    type_params: {measure: total_presentations}
  - name: pct_seen_on_time_cat2
    type: ratio            # demonstrates governed ratio metric
    label: "% Seen On Time (Cat 2)"
    type_params:
      numerator: on_time_pct_avg
      denominator: total_presentations   # illustrative; wire to seen-on-time numerator in build
```

> Interview line: *"Defining metrics in the semantic layer means 'Total ED Presentations' has one
> governed definition; the DAX measure, the Streamlit query, and a future Looker/Tableau consumer
> all inherit it, so the exec never sees two different numbers for the same KPI in two tools."*

Maintain a **`docs/METRICS.md`** registry: metric name · grain · definition · owner · source model.

---

## 20. CI/CD WITHOUT SNOWFLAKE + DEVELOPER TOOLING (free, fast, reproducible)

The CI in Section 4.4 requires live Snowflake credentials in GitHub Actions — slow, costs trial
credits, breaks when the trial expires, and fails for any external contributor. **Senior pattern:
run CI against an ephemeral local warehouse (DuckDB), reserve Snowflake for the docs/prod deploy.**

### 20.1 Dual-target dbt (Snowflake for prod, DuckDB for CI)
- Add a **`ci` output** to `profiles.yml` using **`dbt-duckdb`** (in-process, zero infra).
- Commit **small fixture seeds** (`tests/fixtures/*.csv`, a few hundred rows sampled from real
  AIHW + a tiny Synthea slice) so `dbt build --target ci` runs the **full DAG + all tests** with
  no secrets and no network. This is what actually proves the models compile and tests pass on a PR.
- Keep SQL **portable**: branch Snowflake-specific syntax with `{% if target.type == 'snowflake' %}`
  or `adapter.dispatch`. Document any function that needs this.

```yaml
# .github/workflows/dbt_ci.yml  (revised — no Snowflake secrets needed)
# 1. checkout  2. pip install dbt-duckdb sqlfluff
# 3. dbt deps  4. dbt seed --target ci  (loads fixtures)
# 5. dbt build --target ci            (run + test + unit tests on DuckDB)
# 6. sqlfluff lint models/            (style gate)
# 7. comment PR with test summary
```
`dbt_docs_deploy.yml` keeps using Snowflake secrets (it needs the real prod build for the catalog).

### 20.2 Code-quality gates
- **sqlfluff** (dialect: snowflake, templater: dbt) + `.sqlfluff` config; run in CI and pre-commit.
- **pre-commit** hooks: `sqlfluff-lint`, `dbt parse`, `trailing-whitespace`, `end-of-file-fixer`,
  `detect-secrets` (blocks committed credentials), `black` + `ruff` for Python.
- **`Makefile`** (and a `make.ps1` PowerShell twin for Windows) with targets: `setup`, `ingest`,
  `build`, `test`, `lint`, `docs`, `serve`, `ci`.
- **`.devcontainer/`** (optional) so the env is reproducible in Codespaces.

### 20.3 Reproducibility
- Pin versions: `requirements.txt` with hashes (or `uv`/`pip-tools` lockfile); pin `dbt-core`,
  `dbt-snowflake`, `dbt-duckdb` to the same minor.
- `.tool-versions` (asdf) or documented Python 3.11 + JDK 17.
- A committed **`data/sample/`** so the whole pipeline is demonstrable offline.

---

## 21. ORCHESTRATION & SCHEDULING

For a portfolio of this size, **don't over-engineer** — but show you know the landscape and chose
deliberately (an ADR-worthy decision).

- **Chosen:** GitHub Actions (cron) as a lightweight scheduler + a single Python orchestrator
  (`run_all_ingestion.py`) calling staged steps. Rationale: zero infra, free, already in the stack.
- **Considered & rejected (document why):** Airflow / Dagster / Prefect — correct for a real
  platform with many interdependent pipelines and SLAs, but operationally heavy for one daily run.
  Dagster's asset model maps cleanly onto dbt assets; note it as the "next step at scale."
- **DAG ordering is owned by dbt** (`ref()` builds the lineage); the orchestrator only sequences
  *ingest → dbt build → docs*.
- A nightly `cron` workflow runs ingest (snapshot mode) + `dbt build` + refresh trigger, with
  failure notifications. Idempotent: every step is safe to re-run.

---

## 22. COST & FINOPS (Snowflake trial discipline)

The $400/30-day trial is **more than enough** if managed; blowing it is an avoidable own-goal.

```sql
-- Warehouse: smallest size, aggressive auto-suspend, auto-resume
CREATE WAREHOUSE COMPUTE_WH
  WAREHOUSE_SIZE = 'XSMALL'
  AUTO_SUSPEND = 60          -- seconds idle before suspend
  AUTO_RESUME = TRUE
  INITIALLY_SUSPENDED = TRUE;

-- Hard guardrail: stop runaway spend
CREATE RESOURCE MONITOR LITTLEVITALS_MONITOR
  WITH CREDIT_QUOTA = 50      -- well under the 400 trial allotment
  FREQUENCY = MONTHLY
  TRIGGERS
    ON 75 PERCENT DO NOTIFY
    ON 90 PERCENT DO SUSPEND
    ON 100 PERCENT DO SUSPEND_IMMEDIATE;
ALTER WAREHOUSE COMPUTE_WH SET RESOURCE_MONITOR = LITTLEVITALS_MONITOR;

-- Prevent stuck/expensive queries
ALTER WAREHOUSE COMPUTE_WH SET STATEMENT_TIMEOUT_IN_SECONDS = 300;
```

**FinOps notes for README/ADR:**
- Dataset is small → keep everything in **table** materialisations except where incremental adds
  value; no need for large warehouses.
- **Suspend when idle**; never leave a warehouse running overnight.
- Power BI **Import** (not DirectQuery) means the warehouse is touched only at refresh, not on
  every dashboard click (ties back to §16.2).
- Document an **"after the trial expires" fallback**: the entire pipeline runs on **DuckDB +
  local Parquet** (`dbt-duckdb` target) so the repo stays runnable forever, even when the
  Snowflake account lapses. This is also the CI engine (§20). Record the demo GIF + screenshots
  **before** the trial ends as the permanent visual fallback.

---

## 23. GOVERNANCE, PRIVACY & THE FIVE SAFES

Even with synthetic data, demonstrating a governance posture is exactly what a hospital DSU,
Medibank, or a consultancy wants to see. Frame the whole project against the **Five Safes**
(the framework the ABS/AIHW actually use):

| Safe | How LittleVitals addresses it |
|---|---|
| **Safe projects** | Stated purpose: public, educational benchmarking analytics — documented in README. |
| **Safe people** | Single analyst; RBAC roles model real least-privilege separation (§3.4). |
| **Safe settings** | No real patient data leaves Snowflake; secrets in env/Secrets, never committed. |
| **Safe data** | Patient-level = **synthetic (Synthea)**; aggregate = AIHW public/de-identified. |
| **Safe outputs** | Small-number suppression (n<5); patient-level pages **not** Publish-to-Web (screenshots only). |

### 23.1 Demonstrate Snowflake-native governance (capability signal)
Even on synthetic columns, implement and document:
```sql
-- Object tagging for data classification
CREATE TAG data_classification;            -- values: PUBLIC | INTERNAL | SENSITIVE_SYNTHETIC
ALTER TABLE GOLD.DIM_PATIENT_DEMOGRAPHICS  SET TAG data_classification = 'SENSITIVE_SYNTHETIC';

-- Dynamic masking policy (applied to quasi-identifiers, even though synthetic)
CREATE MASKING POLICY mask_postcode AS (val STRING) RETURNS STRING ->
  CASE WHEN CURRENT_ROLE() IN ('LITTLEVITALS_ENGINEER') THEN val
       ELSE LEFT(val, 2) || 'XX' END;     -- non-privileged roles see coarsened geography
```
Document a **data-classification matrix** in `SECURITY.md` and a **PII / quasi-identifier register**
for the Synthea columns (patient_id → hashed, full postcode → SA2-only for public roles).

### 23.2 Reproducibility & lineage as governance
- `dbt docs` DAG = end-to-end lineage (source → model → exposure).
- Declare **`exposures`** in dbt for the Power BI dashboard and Streamlit app so lineage shows
  "who consumes this model" — and `dbt run --select +exposure:power_bi_dashboard` can rebuild only
  what the dashboard needs.
- Every model carries `meta:` tags: `owner`, `domain`, `contains_pii`, `data_classification`,
  `refresh_cadence`.

---

## 24. DASHBOARD UX, ACCESSIBILITY & DATA-STORYTELLING STANDARDS

A health exec audience and a hiring panel both reward clarity over chart-junk.

### 24.1 Design tokens (consistent across Power BI + Streamlit)
- **Palette:** primary teal `#1a6b5e`; status palette must be **colour-blind safe** — never rely on
  red/green alone. Pair status colour with an **icon/shape** (●▲■) and a text label
  (`Meets / At Risk / Below`). Use Okabe-Ito or ColorBrewer-safe ramps for sequential maps.
- **Typography & number formatting:** thousands separators, consistent decimals, minutes vs days
  units always labelled, FY shown as `2023–24` (en dash) everywhere.
- **One theme file:** Power BI `theme.json` + Streamlit `style.css` + Plotly template share the
  same hex tokens.

### 24.2 Accessibility (relevant for public-sector / health employers)
- WCAG AA contrast on all text/background pairs.
- Alt text on key visuals; tab order set in Power BI; never convey meaning by colour alone.
- Map + table pairing so colour-blind / screen-reader users get the same information.

### 24.3 Storytelling layer (turn dashboards into a narrative)
- Each page opens with a **BLUF** ("Bottom Line Up Front") text card: the one-sentence takeaway.
- **Dynamic narrative** title measures (DAX `SELECTEDVALUE` + `FORMAT`) e.g.
  *"Cat 2 on-time performance fell 4.2 pts to 71% in FY2024–25, below the 80% benchmark."*
- Annotate benchmark lines and notable inflection points directly on charts.
- Consistent **page header** with title, filter context, "data current as of", and a synthetic-data
  badge where applicable.

---

## 25. LIMITATIONS, CAVEATS & INTELLECTUAL HONESTY

> Put a candid **"Limitations"** section in the README and `ARCHITECTURE.md`. Naming your own
> limitations is one of the strongest credibility signals in an interview — it shows you understand
> the data, not just the tools.

- **AIHW data is annual & aggregated** — no real intra-year, patient-level, or causal analysis is
  possible on it (see §16.1). Monthly/seasonal views are **Synthea-only** and labelled.
- **Synthea is illustrative, not epidemiologically accurate for Australia** — base modules encode
  largely US-derived prevalence; the "Victoria, Australia" config sets demographics/geography but
  not local disease epidemiology. **Never present Synthea numbers as real Victorian health facts.**
- **Small-number suppression & non-publishable cells (`n.p.`)** in AIHW data create nulls — handle
  explicitly, don't impute silently.
- **Hospital identity / peer-group changes over time** (mergers, renames) → the SCD-2 snapshot
  (§4.1) is genuinely needed; document any pre-2018 comparability breaks.
- **DirectQuery demo caveat** (§16.2) — the live page may cold-start; Import is the reliable demo.
- **No clinical validation** — this is an analytics-engineering & BI portfolio, not a clinical tool;
  it must not be used for care decisions. State this plainly.

---

## 26. RISK REGISTER & MVP SCOPING (ship something real, fast)

### 26.1 Risk register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| AIHW API shape changes / 404 | High | High | Snapshot + static-XLSX fallback (§16.3); BI reads Snowflake, not API |
| Snowflake trial expires mid-build | Med | High | DuckDB fallback target (§22); capture GIF/screenshots early |
| Scope creep (spec is huge) | High | Med | MVP cut-lines below; build vertical slice first |
| Power BI Pro trial expires before recording | Med | Med | Record demo + Publish-to-Web link early; screenshots as permanent fallback |
| Synthea/JDK setup friction on Windows | Med | Low | Document Temurin 17 install; commit a pre-generated sample CSV slice |
| Time (single builder, part-time) | High | High | Phased delivery; each phase independently demoable |
| SQL not portable Snowflake↔DuckDB | Med | Med | `adapter.dispatch` / target branching; lint in CI |

### 26.2 MVP — the "Minimum Lovable Build" (target first, ~1–2 weeks)
A complete **vertical slice** that already looks like a real project:
1. Snowflake DB + schemas + XS warehouse + one role.
2. Ingest **AIHW ED (VIC)** only → BRONZE (live-or-snapshot).
3. Seeds: triage categories + national benchmarks.
4. dbt: `stg → int → dim_date + dim_hospital + dim_triage + fct_ed_presentations →
   mart_hospital_scorecard`; 3 tests; `dbt docs` on GitHub Pages.
5. Power BI (**Import**): Pages 1 (Executive) + 2 (ED Deep Dive) + 6 (Benchmark/funnel).
6. README with architecture diagram + live dbt-docs link + screenshots.
**This alone is portfolio-worthy.** Everything below is incremental polish.

### 26.3 Build tiers (cut from the bottom under time pressure)
- **Tier 1 (MVP):** the slice above.
- **Tier 2:** elective surgery fact + Page 3; Streamlit Overview + ED pages; CI on DuckDB; ADRs.
- **Tier 3:** Synthea patient layer + Page 4 (paediatric) + readmission model; RLS + Page 5.
- **Tier 4 (stretch):** paginated Board Pack; full DS notebooks (forecast, survival, clustering);
  semantic layer; masking policies; elementary observability.

### 26.4 Rough effort guide (solo, part-time)
Foundation+ingest ½–1 wk · dbt core 1 wk · Power BI 4–5 days · Streamlit 2–3 days ·
DS notebooks 3–5 days · docs/ADRs/README 2–3 days · CI/CD 1–2 days. **MVP ≈ 1–2 weeks; full
build ≈ 5–7 weeks part-time.** Don't wait for "full" to publish — ship MVP, then iterate in public.

---

## 27. ANALYTICS-ENGINEERING CONVENTIONS (canonical reference)

### 27.1 Model layers & naming (resolves §16.4)

| Layer | Schema | Name pattern | Materialisation | Purpose |
|---|---|---|---|---|
| Source | BRONZE (raw) | `source()` in `_sources.yml` | — | Declared raw tables + freshness |
| Staging | BRONZE | `stg_<source>__<entity>` | view | 1:1 with source; rename, cast, no joins |
| Intermediate | SILVER | `int_<entity>__<verb>` | view / ephemeral | joins, dedupe, business logic building blocks |
| Dimension | GOLD | `dim_<entity>` | table | conformed dims; surrogate keys; unknown member |
| Fact | GOLD | `fct_<entity>` | table / incremental | additive measures; FKs to dims |
| Mart | GOLD | `mart_<subject>` | table | denormalised, BI-ready aggregates |

### 27.2 Standards (non-negotiable, enforced by sqlfluff + review)
- **Surrogate keys** via `dbt_utils.generate_surrogate_key([...])`; never expose raw source PKs to BI.
- **Unknown member:** every dimension has a `-1` "Unknown/Not Applicable" row; facts `COALESCE` failed
  joins to `-1` so `relationships` tests stay green and totals never silently drop rows.
- **No `SELECT *`** in gold/mart models; every CTE named for what it does; final `SELECT` is explicit.
- **`ref()` / `source()` only** — never hardcode database/schema names.
- **One model = one file**; staging models are thin; business logic lives in intermediate, not BI.
- **Incremental facts** use a stable unique key + `is_incremental()` guard; document the strategy.
- **`dbt build`** (not separate run/test) is the canonical command so tests gate every run.

### 27.3 Data contracts & unit tests (dbt ≥1.8)
- **Enforce contracts** on all GOLD models: `config(contract={enforced: true})` + declared
  `data_type` per column in schema.yml → schema drift fails the build.
- **Unit tests** for transformation logic (not just data) — e.g. the `australian_financial_year`
  macro: given `2023-08-15` expect `"2023-24"`; given `2024-06-30` expect `"2023-24"`; given
  `2024-07-01` expect `"2024-25"`. Put these in `models/**/_unit_tests.yml`.

### 27.4 Observability & reconciliation (proves the numbers are right)
- **Source freshness** (`dbt source freshness`) with warn/error thresholds.
- **Reconciliation tests** (singular): sum of VIC presentations in `fct_ed_presentations` must
  match the published AIHW VIC total **within tolerance**; row counts vs source within tolerance.
  This is the test that proves you didn't quietly mangle the data in transformation.
- **Volume/anomaly tests** via `dbt_utils` / `dbt_expectations` (e.g. row count within expected
  band; no FY missing in the spine).
- **(Stretch)** `elementary-data` package → an anomaly-monitoring report published alongside dbt docs.

---

## 28. INTERVIEW STORY BANK (STAR-format, beyond the §13 one-liners)

For each, Karthik should be able to give a 60–90s answer. Keep these in `docs/INTERVIEW_NOTES.md`
(gitignored or private) — they are *his* prep, not repo marketing.

1. **"Walk me through a data-quality problem you solved."**
   *Situation:* AIHW cells are suppressed (`n.p.`) for small counts. *Task:* avoid corrupting
   aggregates. *Action:* explicit null handling + a reconciliation test asserting Gold totals match
   the published AIHW VIC total within tolerance, run in CI. *Result:* provable correctness; the
   exec sees numbers that tie out to the official source.
2. **"How would you compare hospital performance fairly?"** → funnel plots vs league tables
   (§18.2); explain why naive ranking is statistically wrong.
3. **"Tell me about a trade-off you made."** → Import vs DirectQuery under an auto-suspend trial
   warehouse (§16.2); plus DuckDB-for-CI vs Snowflake-for-CI (§20).
4. **"How do you keep BI numbers consistent across tools?"** → semantic/metrics layer (§19).
5. **"How do you handle sensitive data?"** → Five Safes + synthetic patient layer + masking/tagging
   (§23), even though the data is synthetic — *because the capability is what's being assessed.*
6. **"What are the limitations of your analysis?"** → §25 verbatim; lead with the annual-grain and
   Synthea caveats. Volunteering limits builds more trust than hiding them.
7. **"Show me you can forecast."** → SARIMA/Prophet with backtested MAPE + prediction intervals
   (§18.1 #1); explain why you reported the holdout error.

---

## 29. UPDATED DEFINITION OF DONE (supersedes & extends §15)

Tier 1 (MVP) items are the gate to publish; Tiers 2–4 are iterative.

**MVP gate (publish when all true):**
- [ ] Vertical slice (§26.2) live: Snowflake → dbt → Power BI(Import) → README → dbt-docs on Pages
- [ ] `dbt build --target ci` green on DuckDB with **no secrets** (CI passes on a fresh clone)
- [ ] Reconciliation test ties Gold VIC totals to published AIHW totals within tolerance
- [ ] README first screen: architecture diagram + live dbt-docs link + 2 screenshots + limitations link
- [ ] Demo GIF + screenshots captured (permanent fallback, independent of any trial)

**Full build (extends §15):**
- [ ] Data science notebooks reproducible; forecast reports backtest error; funnel plot on Page 6
- [ ] dbt **contracts enforced** on all Gold models; **unit tests** for FY macro pass
- [ ] Source freshness + volume/anomaly tests configured
- [ ] Semantic layer metrics defined + `docs/METRICS.md` registry
- [ ] Object tagging + masking policy demonstrated; `SECURITY.md` classification matrix
- [ ] `exposures` declared for Power BI + Streamlit (lineage shows consumers)
- [ ] Limitations & caveats section published (README + ARCHITECTURE.md)
- [ ] sqlfluff + pre-commit + detect-secrets all green; `Makefile`/`make.ps1` targets work
- [ ] DuckDB fallback target documented & working (repo runnable after trial expiry)
- [ ] Every Synthea-derived visual carries a synthetic-data badge

---

*CLAUDE.md v2.0 — LittleVitals Project*
*v1.0 → v2.0 additions: §16 errata/clarifications · §17 healthcare domain pack · §18 data-science
layer (forecasting, funnel plots, equity, survival, readmission) · §19 semantic layer · §20 DuckDB
CI + dev tooling · §21 orchestration · §22 FinOps · §23 Five-Safes governance · §24 UX/accessibility ·
§25 limitations · §26 risk register & MVP scoping · §27 AE conventions/contracts · §28 interview
story bank · §29 updated Definition of Done.*
*Generated for Karthik Reddy Tanigundala — RMIT Master of Data Science 2026*
*Target: Melbourne BI Analyst / Data Analyst / Data Scientist roles, AUD $90k–$160k band*
