"""
Generate a deterministic SYNTHETIC patient-level dataset (Synthea-style schema)
for the paediatric layer, standing in for a real Synthea export.

Production path (documented in ingestion/README.md) runs the Synthea generator:
    java -jar synthea-with-dependencies.jar -p 10000 -s 42 Victoria Australia
and lands patients.csv / encounters.csv / conditions.csv into BRONZE. This script
produces the SAME column shape so the dbt models are identical, but runs instantly
with no Java/download. SYNTHETIC (seed=42) — never present as real patient data.

Run:  python data/sample/generate_synthea_sample.py
Output (littlevitals_dbt/seeds/fixtures/):
    raw_synthea_patients.csv, raw_synthea_encounters.csv, raw_synthea_conditions.csv
"""

from __future__ import annotations

import csv
import random
from datetime import date, timedelta
from pathlib import Path

SEED = 42
N_PATIENTS = 2000
ENC_DATE_START = date(2019, 1, 1)
ENC_DATE_END = date(2024, 12, 31)

# Victorian postcodes used (geography attributes live in seed_vic_geography.csv).
POSTCODES = ["3000", "3052", "3168", "3084", "3011", "3128", "3220", "3021",
             "3076", "3199", "3030", "3174", "3056", "3145", "3805"]

# Hospital codes (match raw_aihw_reporting_units / dim_hospital). RCH is paediatric.
PAED_HOSPITALS = ["H0001", "H0001", "H0001", "H0003", "H0007", "H0009"]  # RCH-weighted
ADULT_HOSPITALS = ["H0002", "H0004", "H0005", "H0006", "H0008", "H0010"]

ENCOUNTER_CLASSES = ["emergency", "inpatient", "ambulatory", "wellness"]
CLASS_WEIGHTS = [0.46, 0.18, 0.28, 0.08]
LOS_HOURS = {"emergency": (1.5, 9.0), "inpatient": (20.0, 140.0),
             "ambulatory": (0.4, 2.5), "wellness": (0.2, 0.8)}

# ICD-10-AM diagnoses (code, description, sample_weight). Codes match seed_icd10_paediatric.
PAED_DX = [
    ("J06.9", "Acute upper respiratory infection", 18),
    ("J21.9", "Acute bronchiolitis", 11),
    ("J45.9", "Asthma", 9),
    ("A09", "Infectious gastroenteritis", 11),
    ("R50.9", "Fever, unspecified", 8),
    ("H66.9", "Otitis media, unspecified", 7),
    ("J03.9", "Acute tonsillitis", 6),
    ("R10.4", "Abdominal pain", 6),
    ("L20.9", "Atopic dermatitis", 4),
    ("S52.50", "Fracture of lower end of radius", 6),
    ("B34.9", "Viral infection, unspecified", 5),
    ("J18.9", "Pneumonia, unspecified", 4),
    ("S00.9", "Superficial injury of head", 3),
    ("R11.2", "Nausea with vomiting", 4),
    ("N39.0", "Urinary tract infection", 3),
    ("F90.0", "Attention-deficit hyperactivity disorder", 2),
    ("G40.9", "Epilepsy, unspecified", 2),
    ("K59.0", "Constipation", 3),
]
ADULT_DX = [("I10", "Essential hypertension"), ("E11.9", "Type 2 diabetes mellitus"),
            ("J44.9", "Chronic obstructive pulmonary disease"), ("R07.4", "Chest pain")]
# Winter (Jun-Aug) boosts respiratory codes for children.
RESP_CODES = {"J06.9", "J21.9", "J45.9", "J03.9", "J18.9", "B34.9"}

REPO_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = REPO_ROOT / "littlevitals_dbt" / "seeds" / "fixtures"


def weighted_dx(rng: random.Random, month: int) -> tuple[str, str]:
    codes = [c for c, _, _ in PAED_DX]
    weights = [w * (2.0 if (c in RESP_CODES and month in (6, 7, 8)) else 1.0)
               for c, _, w in PAED_DX]
    code = rng.choices(codes, weights=weights, k=1)[0]
    desc = next(d for c, d, _ in PAED_DX if c == code)
    return code, desc


def main() -> None:
    rng = random.Random(SEED)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    patients, encounters, conditions = [], [], []
    enc_seq = 0
    for i in range(1, N_PATIENTS + 1):
        pid = f"P{i:05d}"
        is_child = rng.random() < 0.65
        if is_child:                       # born 2002-2024 -> mostly paediatric
            birth = date(2002, 1, 1) + timedelta(days=rng.randint(0, 22 * 365))
        else:                              # adults
            birth = date(1950, 1, 1) + timedelta(days=rng.randint(0, 52 * 365))
        sex = rng.choice(["M", "F"])
        postcode = rng.choice(POSTCODES)
        indigenous = "Y" if rng.random() < 0.04 else "N"
        patients.append([pid, birth.isoformat(), sex, postcode, indigenous])

        for _ in range(rng.choices([1, 2, 3, 4, 5], weights=[40, 28, 18, 9, 5])[0]):
            enc_seq += 1
            eid = f"E{enc_seq:06d}"
            # Encounter must occur on/after birth and within the reporting window.
            earliest = max(ENC_DATE_START, birth)
            if earliest >= ENC_DATE_END:
                start = ENC_DATE_END
            else:
                start = earliest + timedelta(days=rng.randint(0, (ENC_DATE_END - earliest).days))
            eclass = rng.choices(ENCOUNTER_CLASSES, weights=CLASS_WEIGHTS, k=1)[0]
            lo, hi = LOS_HOURS[eclass]
            los = round(rng.uniform(lo, hi), 1)
            cost = round(rng.uniform(120, 2600) * (1 + los / 24.0), 2)
            age_years = (start - birth).days / 365.25
            if age_years < 18:
                code, desc = weighted_dx(rng, start.month)
                hosp = rng.choice(PAED_HOSPITALS)
            else:
                code, desc = rng.choice(ADULT_DX)
                hosp = rng.choice(ADULT_HOSPITALS)
            encounters.append([eid, pid, start.isoformat(), eclass, hosp, los, cost, code])
            conditions.append([pid, eid, code, desc, start.isoformat()])

    _write("raw_synthea_patients.csv",
           ["patient_id", "birthdate", "sex", "postcode", "indigenous_flag"], patients)
    _write("raw_synthea_encounters.csv",
           ["encounter_id", "patient_id", "start_date", "encounter_class",
            "hospital_code", "los_hours", "total_cost", "primary_diagnosis_code"], encounters)
    _write("raw_synthea_conditions.csv",
           ["patient_id", "encounter_id", "condition_code", "condition_description",
            "onset_date"], conditions)
    print(f"[ok] {len(patients):,} patients, {len(encounters):,} encounters "
          f"(seed={SEED}, SYNTHETIC)")


def _write(name: str, header: list[str], rows: list[list]) -> None:
    with (OUT_DIR / name).open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        w.writerows(rows)


if __name__ == "__main__":
    main()
