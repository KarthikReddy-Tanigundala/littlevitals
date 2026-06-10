"""
Generate deterministic SYNTHETIC elective-surgery waitlist episodes, standing in
for AIHW/ESIS-style elective surgery data so the elective layer + Kaplan-Meier
waitlist survival analysis run offline.

Grain: one row per waitlist episode. Includes censoring (episodes still waiting at
the extract date, or removed for non-surgical reasons) so the survival analysis
has genuine right-censored data. SYNTHETIC (seed=42) — not real waiting times.

Run:  python data/sample/generate_elective_surgery.py
Output: littlevitals_dbt/seeds/fixtures/raw_elective_surgery_episodes.csv
"""

from __future__ import annotations

import csv
import random
from datetime import date, timedelta
from pathlib import Path

SEED = 42
N_EPISODES = 10000
LIST_START = date(2020, 7, 1)         # FY2020-21
EXTRACT_DATE = date(2025, 6, 30)      # observation cut-off (FY2024-25 end)

# VIC hospitals (match dim_hospital) with a wait-time multiplier (perf variation).
HOSPITALS = {
    "H0001": 0.90, "H0002": 1.00, "H0003": 1.10, "H0004": 0.95, "H0005": 1.20,
    "H0006": 1.00, "H0007": 1.05, "H0008": 1.22, "H0009": 1.12, "H0010": 0.98,
}

# Urgency category -> (weight, gamma shape, gamma scale, recommended max wait days).
URGENCY = {
    1: (0.15, 2.0, 12.0, 30),
    2: (0.35, 2.0, 35.0, 90),
    3: (0.50, 2.0, 110.0, 365),
}

# Surgical specialties (names must match seed_surgical_specialties.csv) + weights.
SPECIALTIES = [
    ("Ophthalmology", 18), ("Orthopaedic surgery", 16), ("General surgery", 15),
    ("Ear nose and throat", 12), ("Urology", 10), ("Gynaecology", 9),
    ("Plastic surgery", 6), ("Vascular surgery", 5), ("Cardiothoracic surgery", 4),
    ("Neurosurgery", 5),
]

REPO_ROOT = Path(__file__).resolve().parents[2]
OUT = REPO_ROOT / "littlevitals_dbt" / "seeds" / "fixtures" / "raw_elective_surgery_episodes.csv"


def main() -> None:
    rng = random.Random(SEED)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    span = (EXTRACT_DATE - LIST_START).days
    codes = [u for u in URGENCY]
    u_weights = [URGENCY[u][0] for u in codes]
    spec_names = [s for s, _ in SPECIALTIES]
    spec_weights = [w for _, w in SPECIALTIES]

    rows = []
    for i in range(1, N_EPISODES + 1):
        hosp = rng.choice(list(HOSPITALS))
        urg = rng.choices(codes, weights=u_weights, k=1)[0]
        _, shape, scale, recommended = URGENCY[urg]
        specialty = rng.choices(spec_names, weights=spec_weights, k=1)[0]
        added = LIST_START + timedelta(days=rng.randint(0, span))

        # Intended time-to-treatment (days), worse at high-multiplier hospitals.
        intended = int(rng.gammavariate(shape, scale) * HOSPITALS[hosp])
        intended = max(1, intended)

        if added + timedelta(days=intended) > EXTRACT_DATE:
            # Right-censored: still on the list at the extract date.
            removal = "Still waiting"
            admitted = 0
            wait_days = (EXTRACT_DATE - added).days
        elif rng.random() < 0.12:
            # Removed for a non-surgical reason (also censored for survival).
            removal = "Removed - other"
            admitted = 0
            wait_days = intended
        else:
            removal = "Admitted"
            admitted = 1
            wait_days = intended

        rows.append([f"ES{i:06d}", hosp, urg, specialty, added.isoformat(),
                     max(0, wait_days), removal, admitted])

    with OUT.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["episode_id", "hospital_code", "urgency_category", "specialty",
                    "added_date", "wait_days", "removal_reason", "admitted_flag"])
        w.writerows(rows)
    print(f"[ok] {OUT.relative_to(REPO_ROOT)}  ({len(rows):,} episodes, seed={SEED}, SYNTHETIC)")


if __name__ == "__main__":
    main()
