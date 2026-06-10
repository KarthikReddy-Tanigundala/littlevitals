# LittleVitals — Data-Science Layer

Reproducible analyses on top of the Gold warehouse. Reusable logic lives in
[`src/`](src); each numbered script runs standalone, prints its results, and
saves a figure to `analytics/outputs/`.

## Analyses

| Script | Method | Output |
|---|---|---|
| [`01_ed_demand_forecast.py`](01_ed_demand_forecast.py) | **SARIMA** with a 12-month backtest (reports MAPE/MAE before forecasting) | 12-month forecast + 95% prediction interval |
| [`02_seasonality_decomposition.py`](02_seasonality_decomposition.py) | **STL** decomposition | Seasonal strength + quantified winter (Jun–Aug) surge |
| [`03_hospital_clustering.py`](03_hospital_clustering.py) | **k-means** on standardised KPI vectors + PCA | Data-driven hospital clusters vs AIHW peer groups |
| [`04_benchmark_significance.py`](04_benchmark_significance.py) | **Two-proportion z-test** + **funnel plot** (Spiegelhalter) | Significance vs pooled rate, special-cause outliers |
| [`05_readmission_and_equity.py`](05_readmission_and_equity.py) | **Logistic regression** (held-out ROC-AUC) + **linear trend test** | 30-day readmission risk model (AUC ≈ 0.67) + SEIFA equity gradient |
| [`06_waitlist_survival.py`](06_waitlist_survival.py) | **Kaplan–Meier** + log-rank test | Elective time-to-admission curves by urgency (medians 22 / 66 / 209 days) |

## Run

```powershell
.\.venv\Scripts\Activate.ps1
python data\sample\generate_monthly_encounters.py      # one-off: build the monthly series
python analytics\01_ed_demand_forecast.py
python analytics\02_seasonality_decomposition.py
python analytics\03_hospital_clustering.py
python analytics\04_benchmark_significance.py
```

## Data sources & honesty (CLAUDE.md §18.3, §25)

- **Forecasting & seasonality (01, 02)** use a **synthetic monthly** paediatric ED
  series (`data/sample/monthly_paediatric_ed.csv`, seed=42). AIHW public data is
  annual and too short to model seasonality — this stands in for a Synthea-fed
  monthly encounter aggregate and is **labelled synthetic** in every chart title.
- **Clustering & significance (03, 04)** use the **real Gold tables** built by dbt.
- Forecasts always report a **backtested error** (never an unvalidated forecast).
- Comparisons report **uncertainty** (CIs / prediction intervals); funnel plots
  replace league-table ranking. No causal claims are made on observational data.

## Planned (next)

- **Calibration** — add a calibration curve + Brier score to the readmission model.
- **Cox model** — covariate-adjusted hazard of admission (lifelines `CoxPHFitter`).
