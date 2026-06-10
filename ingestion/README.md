# Ingestion layer

Python loaders that land raw source data into Snowflake **BRONZE**. Built for
resilience (CLAUDE.md §16.3): every fetch runs **`--source live`** (hit the API /
download, save a raw snapshot) or **`--source snapshot`** (read committed
fixtures, no network). Downstream dbt/BI always read Snowflake, never the API.

## Modules (run order)

| Module | What |
|---|---|
| [`config.py`](config.py) | Reads `.env`; exposes paths + Snowflake params. |
| [`snowflake_loader.py`](snowflake_loader.py) | `prepare_dataframe` (metadata + name normalisation) + `load_dataframe_to_snowflake`. |
| [`ingest_aihw_api.py`](ingest_aihw_api.py) | AIHW MyHospitals API → `RAW_AIHW_*`. |
| [`ingest_aihw_xlsx.py`](ingest_aihw_xlsx.py) | Durable AIHW XLSX tables → BRONZE. |
| [`ingest_synthea.py`](ingest_synthea.py) | Synthea patient CSVs → `RAW_SYNTHEA_*`. |
| [`ingest_abs_geography.py`](ingest_abs_geography.py) | ABS postcode→SA2/SEIFA → BRONZE. |
| [`run_all_ingestion.py`](run_all_ingestion.py) | Canonical cross-platform orchestrator. |

## Quickstart (offline — no Snowflake, no network)

```powershell
# Windows / PowerShell  (use the repo venv)
.\.venv\Scripts\Activate.ps1
python ingestion\run_all_ingestion.py --source snapshot --dry-run
```
```bash
# macOS / Linux
python ingestion/run_all_ingestion.py --source snapshot --dry-run
# or: ./ingestion/run_all_ingestion.sh --source snapshot --dry-run
```

## Live load to Snowflake

1. Provision Snowflake once: run [`../sql/00_snowflake_setup.sql`](../sql/00_snowflake_setup.sql).
2. Copy `ingestion/.env.example` → repo-root `.env` and fill in credentials (gitignored).
3. `pip install -r ingestion/requirements.txt`
4. Load:
   ```powershell
   python ingestion\run_all_ingestion.py --source live
   ```
5. Transform: `dbt build --project-dir littlevitals_dbt --profiles-dir littlevitals_dbt --target prod`

## Synthea (production patient data)

The offline build uses a Synthea-style synthetic fixture. To use real Synthea:

1. Install a JDK (Temurin 17+). Verify: `java -version`.
2. Download `synthea-with-dependencies.jar` from
   <https://github.com/synthetichealth/synthea/releases>.
3. Generate Victorian patients:
   ```bash
   java -jar synthea-with-dependencies.jar -p 10000 -s 42 \
     --exporter.csv.export=true --exporter.fhir.export=false Victoria Australia
   ```
4. Load the CSV output:
   ```powershell
   python ingestion\ingest_synthea.py --synthea-output path\to\synthea\output\csv
   ```

## Tests

```powershell
python -m pytest tests -q
```
The tests cover the pure transforms (column normalisation, metadata) and the
offline snapshot fetch — no Snowflake or network required.
