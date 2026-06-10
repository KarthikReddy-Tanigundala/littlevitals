"""
Generate deterministic SAMPLE / FIXTURE data for LittleVitals.

This stands in for the AIHW MyHospitals raw landing tables so the whole dbt
pipeline runs offline on DuckDB (local dev + CI), with NO Snowflake and NO live
AIHW API call (see CLAUDE.md sections 16.3 and 20).

The numbers are SYNTHETIC and illustrative. They are shaped to be realistic
(Victorian hospital names, plausible ED volumes, ACEM triage distribution, a
mild post-COVID performance decline) but must never be presented as real AIHW
figures. The real ingestion path (ingestion/01_ingest_aihw_api.py) replaces
these with genuine public AIHW data when Snowflake is available.

Run:  python data/sample/generate_sample_data.py
Output: littlevitals_dbt/seeds/fixtures/{raw_aihw_reporting_units,raw_aihw_ed_presentations}.csv

Pure standard library (no pandas/numpy) so it runs on a bare Python install.
"""

from __future__ import annotations

import csv
import random
from pathlib import Path

SEED = 42
FINANCIAL_YEARS = ["2020-21", "2021-22", "2022-23", "2023-24", "2024-25"]
TRIAGE_CODES = [1, 2, 3, 4, 5]

# Share of total ED presentations by triage category (approx. national shape).
TRIAGE_SHARE = {1: 0.008, 2: 0.13, 3: 0.40, 4: 0.34, 5: 0.122}

# National "seen on time" baseline per triage (declines slightly each year).
NATIONAL_ON_TIME = {
    "2020-21": {1: 1.00, 2: 0.74, 3: 0.66, 4: 0.72, 5: 0.88},
    "2021-22": {1: 1.00, 2: 0.72, 3: 0.63, 4: 0.71, 5: 0.87},
    "2022-23": {1: 1.00, 2: 0.69, 3: 0.60, 4: 0.70, 5: 0.86},
    "2023-24": {1: 1.00, 2: 0.67, 3: 0.58, 4: 0.69, 5: 0.86},
    "2024-25": {1: 1.00, 2: 0.66, 3: 0.57, 4: 0.69, 5: 0.85},
}

# National median wait (minutes) per triage (rises slightly each year).
NATIONAL_MEDIAN = {
    "2020-21": {1: 0, 2: 8, 3: 22, 4: 36, 5: 50},
    "2021-22": {1: 0, 2: 9, 3: 24, 4: 38, 5: 52},
    "2022-23": {1: 0, 2: 10, 3: 26, 4: 40, 5: 54},
    "2023-24": {1: 0, 2: 11, 3: 28, 4: 42, 5: 55},
    "2024-25": {1: 0, 2: 11, 3: 29, 4: 43, 5: 56},
}

# Hospital master.
#   (code, name, state, lhn_name, peer_group, lat, lon,
#    annual_presentations_base, performance_offset)
# performance_offset shifts on-time % up (better) or down (worse) vs national.
HOSPITALS = [
    ("H0001", "Royal Children's Hospital", "VIC", "The Royal Children's Hospital", "Children's hospitals", -37.7935, 144.9509, 92000, 0.06),
    ("H0002", "The Royal Melbourne Hospital", "VIC", "Melbourne Health", "Principal referral", -37.7990, 144.9558, 84000, 0.01),
    ("H0003", "Monash Medical Centre", "VIC", "Monash Health", "Principal referral", -37.9210, 145.1230, 88000, -0.02),
    ("H0004", "Austin Hospital", "VIC", "Austin Health", "Principal referral", -37.7560, 145.0580, 79000, 0.02),
    ("H0005", "Footscray Hospital", "VIC", "Western Health", "Public acute group A", -37.8000, 144.8990, 61000, -0.05),
    ("H0006", "Box Hill Hospital", "VIC", "Eastern Health", "Public acute group A", -37.8190, 145.1230, 64000, 0.00),
    ("H0007", "University Hospital Geelong", "VIC", "Barwon Health", "Principal referral", -38.1480, 144.3620, 72000, -0.01),
    ("H0008", "Sunshine Hospital", "VIC", "Western Health", "Public acute group A", -37.7610, 144.8270, 70000, -0.06),
    ("H0009", "The Northern Hospital", "VIC", "Northern Health", "Public acute group A", -37.6420, 145.0150, 75000, -0.04),
    ("H0010", "Frankston Hospital", "VIC", "Peninsula Health", "Public acute group A", -38.1530, 145.1230, 66000, 0.01),
    # National comparators (kept for benchmark context; Silver filters to VIC).
    ("H0100", "The Children's Hospital at Westmead", "NSW", "Sydney Children's Hospitals Network", "Children's hospitals", -33.8020, 150.9930, 64000, 0.03),
    ("H0101", "Royal Brisbane and Women's Hospital", "QLD", "Metro North", "Principal referral", -27.4470, 153.0290, 81000, 0.00),
]

REPO_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = REPO_ROOT / "littlevitals_dbt" / "seeds" / "fixtures"


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def write_reporting_units() -> Path:
    path = OUT_DIR / "raw_aihw_reporting_units.csv"
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(
            ["hospital_code", "hospital_name", "state", "lhn_name",
             "peer_group", "latitude", "longitude"]
        )
        for code, name, state, lhn, peer, lat, lon, _base, _off in HOSPITALS:
            writer.writerow([code, name, state, lhn, peer, lat, lon])
    return path


def write_ed_presentations(rng: random.Random) -> Path:
    path = OUT_DIR / "raw_aihw_ed_presentations.csv"
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(
            ["hospital_code", "hospital_name", "state", "financial_year",
             "triage_category", "total_presentations", "median_wait_minutes",
             "pct_seen_on_time", "four_hour_rule_pct"]
        )
        for code, name, state, _lhn, _peer, _lat, _lon, base, perf_off in HOSPITALS:
            for yi, fy in enumerate(FINANCIAL_YEARS):
                # Mild YoY growth in volume plus hospital-specific noise.
                year_volume = base * (1.0 + 0.02 * yi) * rng.uniform(0.97, 1.03)
                four_hr = clamp(0.78 - 0.03 * yi + rng.uniform(-0.04, 0.04), 0.40, 0.95)
                for tc in TRIAGE_CODES:
                    presentations = int(round(year_volume * TRIAGE_SHARE[tc]
                                              * rng.uniform(0.95, 1.05)))
                    # Wait time: national median scaled by inverse performance.
                    base_wait = NATIONAL_MEDIAN[fy][tc]
                    wait = base_wait * (1.0 - perf_off * 1.5) * rng.uniform(0.85, 1.15)
                    median_wait = max(0, int(round(wait)))
                    # On-time %: national baseline shifted by hospital performance.
                    on_time = NATIONAL_ON_TIME[fy][tc] + perf_off + rng.uniform(-0.03, 0.03)
                    on_time = round(clamp(on_time, 0.30, 1.00), 3)
                    if tc == 1:
                        on_time, median_wait = 1.000, 0  # Cat 1 seen immediately
                    writer.writerow([code, name, state, fy, tc, presentations,
                                     median_wait, on_time, round(four_hr, 3)])
    return path


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rng = random.Random(SEED)
    units_path = write_reporting_units()
    ed_path = write_ed_presentations(rng)
    units_rows = sum(1 for _ in units_path.open(encoding="utf-8")) - 1
    ed_rows = sum(1 for _ in ed_path.open(encoding="utf-8")) - 1
    print(f"[ok] {units_path.relative_to(REPO_ROOT)}  ({units_rows} hospitals)")
    print(f"[ok] {ed_path.relative_to(REPO_ROOT)}  ({ed_rows} rows)")
    print("Deterministic (seed=42). Re-run any time to reproduce identical fixtures.")


if __name__ == "__main__":
    main()
