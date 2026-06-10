"""
Generate a deterministic SYNTHETIC monthly paediatric ED series for the
data-science layer (forecasting + seasonality), standing in for a Synthea-fed
monthly encounter aggregate.

AIHW public data is ANNUAL (CLAUDE.md §16.1), which is too short to model
seasonality or forecast. This synthetic monthly series encodes a realistic
Australian-winter respiratory surge (June–August peak in children) so the
SARIMA / STL analyses have genuine signal. It is SYNTHETIC and labelled as such
everywhere it is used — never present it as real AIHW data.

Run:  python data/sample/generate_monthly_encounters.py
Output: data/sample/monthly_paediatric_ed.csv  (Jan 2019 – Dec 2024, 72 months)
"""

from __future__ import annotations

import csv
import random
from datetime import date
from pathlib import Path

SEED = 42
START_YEAR, END_YEAR = 2019, 2024
BASE_MONTHLY = 4000          # baseline paediatric ED presentations / month
MONTHLY_GROWTH = 0.003       # ~0.3% trend per month
# Seasonal multipliers — Australian winter (Jun–Aug) respiratory/flu surge.
SEASONAL = {
    1: 0.92, 2: 0.90, 3: 0.95, 4: 1.00, 5: 1.08, 6: 1.20,
    7: 1.28, 8: 1.22, 9: 1.08, 10: 1.00, 11: 0.95, 12: 0.98,
}

REPO_ROOT = Path(__file__).resolve().parents[2]
OUT = REPO_ROOT / "data" / "sample" / "monthly_paediatric_ed.csv"


def main() -> None:
    rng = random.Random(SEED)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["month_date", "year", "month", "presentations"])
        t = 0
        for year in range(START_YEAR, END_YEAR + 1):
            for month in range(1, 13):
                trend = BASE_MONTHLY * (1.0 + MONTHLY_GROWTH * t)
                value = trend * SEASONAL[month] * rng.uniform(0.96, 1.04)
                writer.writerow([date(year, month, 1).isoformat(), year, month,
                                 int(round(value))])
                t += 1
    n = sum(1 for _ in OUT.open(encoding="utf-8")) - 1
    print(f"[ok] {OUT.relative_to(REPO_ROOT)}  ({n} months, seed={SEED}, SYNTHETIC)")


if __name__ == "__main__":
    main()
