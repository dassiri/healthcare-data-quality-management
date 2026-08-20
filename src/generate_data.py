"""Generate fully synthetic healthcare datasets with intentional data-quality defects.

Every identifier, name, and attribute is fabricated. No real personal data is used.
The generator is deterministic (fixed seed) so profiling and validation are reproducible.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.config import (
    AS_OF_DATE,
    DATASET_CLASSIFICATION,
    DATASET_NOTICE,
    ENCOUNTER_TYPE_VALUE_SET,
    GENDER_VALUE_SET,
    RAW_DIR,
    REFERENCE_DIR,
    SEED,
)


N_FACILITIES = 12
N_PROVIDERS = 40
N_PATIENTS = 1000
N_ENCOUNTERS = 2500


def _notice_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Attach dataset classification to every row."""
    out = df.copy()
    out["Dataset_Classification"] = DATASET_CLASSIFICATION
    return out


def _write_csv(path: Path, df: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    _notice_frame(df).to_csv(path, index=False)


def generate_facilities(rng: np.random.Generator) -> pd.DataFrame:
    """Create a clean facility reference (gold standard) and a slightly noisy raw copy."""
    types = ["Primary Care", "Hospital", "Specialty Clinic", "Emergency Centre"]
    regions = ["North", "South", "East", "West", "Central"]
    rows = []
    for i in range(1, N_FACILITIES + 1):
        rows.append(
            {
                "Facility_ID": f"FAC-{i:03d}",
                "Facility_Name": f"SYNTH_FACILITY_{i:03d}",
                "Facility_Type": types[(i - 1) % len(types)],
                "Region": regions[(i - 1) % len(regions)],
                "Is_Active": "Y",
            }
        )
    master = pd.DataFrame(rows)
    raw = master.copy()
    # Intentional raw-only noise: inconsistent formatting on two rows.
    raw.loc[0, "Facility_ID"] = "fac-001"
    raw.loc[1, "Facility_Type"] = "hospital"
    return master, raw


def generate_providers(rng: np.random.Generator) -> pd.DataFrame:
    specialties = [
        "General Practice",
        "Cardiology",
        "Paediatrics",
        "Emergency Medicine",
        "Internal Medicine",
    ]
    rows = []
    for i in range(1, N_PROVIDERS + 1):
        rows.append(
            {
                "Provider_ID": f"PRV-{i:03d}",
                "Provider_Name": f"SYNTH_PROVIDER_{i:03d}",
                "Specialty": specialties[(i - 1) % len(specialties)],
                "Facility_ID": f"FAC-{((i - 1) % N_FACILITIES) + 1:03d}",
            }
        )
    df = pd.DataFrame(rows)
    # Inconsistent identifier formatting.
    df.loc[5, "Provider_ID"] = "PRV005"
    df.loc[8, "Provider_ID"] = "prv-009"
    df.loc[12, "Provider_ID"] = np.nan
    df.loc[20, "Facility_ID"] = "FAC-99"
    return df


def generate_patients(rng: np.random.Generator) -> pd.DataFrame:
    n = N_PATIENTS
    as_of = pd.Timestamp(AS_OF_DATE)
    start = pd.Timestamp("1945-01-01")
    end = pd.Timestamp("2018-12-31")
    span_days = (end - start).days

    patient_ids = [f"PAT-{i:06d}" for i in range(1, n + 1)]
    dobs = [
        (start + pd.Timedelta(int(rng.integers(0, span_days + 1)), unit="D")).strftime(
            "%Y-%m-%d"
        )
        for _ in range(n)
    ]
    genders = rng.choice(list(GENDER_VALUE_SET), size=n, p=[0.48, 0.48, 0.04])
    facility_ids = [f"FAC-{int(rng.integers(1, N_FACILITIES + 1)):03d}" for _ in range(n)]

    df = pd.DataFrame(
        {
            "Patient_ID": patient_ids,
            "Given_Name": [f"SYNTH_GIVEN_{i:06d}" for i in range(1, n + 1)],
            "Family_Name": [f"SYNTH_FAMILY_{i:06d}" for i in range(1, n + 1)],
            "Date_of_Birth": dobs,
            "Gender": genders,
            "Facility_ID": facility_ids,
            "Registration_Date": [
                (as_of - pd.Timedelta(int(rng.integers(30, 2000)), unit="D")).strftime(
                    "%Y-%m-%d"
                )
                for _ in range(n)
            ],
        }
    )

    idx = np.arange(n)
    rng.shuffle(idx)
    cursor = 0

    def take(k: int) -> np.ndarray:
        nonlocal cursor
        sl = idx[cursor : cursor + k]
        cursor += k
        return sl

    missing_id = take(80)
    dup_sources = take(40)
    dup_targets = take(40)
    format_id = take(35)
    missing_dob = take(50)
    future_dob = take(25)
    malformed_dob = take(30)
    old_dob = take(15)
    missing_gender = take(40)
    invalid_gender = take(55)
    missing_fac = take(35)
    invalid_fac = take(40)

    df.loc[missing_id, "Patient_ID"] = np.nan
    df.loc[dup_targets, "Patient_ID"] = df.loc[dup_sources, "Patient_ID"].values

    # Inconsistent Patient_ID formatting (still referring to the same synthetic ID).
    for i, row_i in enumerate(format_id):
        original = df.at[row_i, "Patient_ID"]
        if pd.isna(original):
            continue
        digits = str(original).replace("PAT-", "")
        styles = [
            f"pat-{digits}",
            f"PAT{digits}",
            f"  {original}  ",
            f"Pat-{digits}",
        ]
        df.at[row_i, "Patient_ID"] = styles[i % len(styles)]

    df.loc[missing_dob, "Date_of_Birth"] = np.nan
    df.loc[future_dob, "Date_of_Birth"] = "2028-03-15"
    malformed = ["32/13/1990", "not-a-date", "1990-13-40", "01-99-2010", "31-Feb-1985"]
    for i, row_i in enumerate(malformed_dob):
        df.at[row_i, "Date_of_Birth"] = malformed[i % len(malformed)]
    df.loc[old_dob, "Date_of_Birth"] = "1850-01-01"

    df.loc[missing_gender, "Gender"] = np.nan
    invalid_g = ["M", "F", "male", "FEMALE", "X", "Other", "U", " "]
    for i, row_i in enumerate(invalid_gender):
        df.at[row_i, "Gender"] = invalid_g[i % len(invalid_g)]

    df.loc[missing_fac, "Facility_ID"] = np.nan
    invalid_f = ["FAC-999", "FAC-000", "fac-1", "N/A", "FAC99"]
    for i, row_i in enumerate(invalid_fac):
        df.at[row_i, "Facility_ID"] = invalid_f[i % len(invalid_f)]

    # Exact duplicate records (same synthetic person, repeated row).
    exact_dup_src = take(20)
    exact_dups = df.loc[exact_dup_src].copy()
    df = pd.concat([df, exact_dups], ignore_index=True)

    defect_manifest = {
        "missing_patient_id_rows": int(len(missing_id)),
        "duplicate_patient_id_pairs": int(len(dup_targets)),
        "inconsistent_patient_id_format_rows": int(len(format_id)),
        "missing_dob_rows": int(len(missing_dob)),
        "future_dob_rows": int(len(future_dob)),
        "malformed_dob_rows": int(len(malformed_dob)),
        "out_of_range_dob_rows": int(len(old_dob)),
        "missing_gender_rows": int(len(missing_gender)),
        "invalid_gender_rows": int(len(invalid_gender)),
        "missing_facility_id_rows": int(len(missing_fac)),
        "invalid_facility_id_rows": int(len(invalid_fac)),
        "exact_duplicate_patient_rows_appended": int(len(exact_dups)),
        "final_patient_row_count": int(len(df)),
    }
    return df, defect_manifest


def generate_encounters(
    rng: np.random.Generator, patients: pd.DataFrame, providers: pd.DataFrame
) -> tuple[pd.DataFrame, dict]:
    n = N_ENCOUNTERS
    valid_patient_ids = (
        patients["Patient_ID"].dropna().astype(str).str.strip().unique().tolist()
    )
    # Only use well-formed IDs for the "valid" base so injected orphans are obvious.
    valid_patient_ids = [p for p in valid_patient_ids if p.startswith("PAT-") and len(p) == 10]
    valid_provider_ids = [
        p
        for p in providers["Provider_ID"].dropna().astype(str).str.strip().unique().tolist()
        if p.startswith("PRV-") and len(p) == 7
    ]
    valid_facility_ids = [f"FAC-{i:03d}" for i in range(1, N_FACILITIES + 1)]

    as_of = pd.Timestamp(AS_OF_DATE)
    start = pd.Timestamp("2023-01-01")
    span_days = (as_of - start).days

    rows = []
    for i in range(1, n + 1):
        enc_date = start + pd.Timedelta(int(rng.integers(0, span_days + 1)), unit="D")
        enc_type = ENCOUNTER_TYPE_VALUE_SET[i % len(ENCOUNTER_TYPE_VALUE_SET)]
        los = int(rng.integers(0, 5)) if enc_type == "Inpatient" else 0
        rows.append(
            {
                "Encounter_ID": f"ENC-{i:07d}",
                "Patient_ID": str(rng.choice(valid_patient_ids)),
                "Provider_ID": str(rng.choice(valid_provider_ids)),
                "Facility_ID": str(rng.choice(valid_facility_ids)),
                "Encounter_Date": enc_date.strftime("%Y-%m-%d"),
                "Discharge_Date": (enc_date + pd.Timedelta(los, unit="D")).strftime(
                    "%Y-%m-%d"
                ),
                "Encounter_Type": enc_type,
            }
        )
    df = pd.DataFrame(rows)

    idx = np.arange(n)
    rng.shuffle(idx)
    cursor = 0

    def take(k: int) -> np.ndarray:
        nonlocal cursor
        sl = idx[cursor : cursor + k]
        cursor += k
        return sl

    orphan_patient = take(120)
    orphan_provider = take(80)
    orphan_facility = take(70)
    missing_enc_id = take(25)
    dup_enc_src = take(20)
    dup_enc_tgt = take(20)
    future_enc = take(20)
    malformed_enc = take(15)
    missing_patient = take(30)

    df.loc[orphan_patient, "Patient_ID"] = [
        f"PAT-{900000 + i:06d}" for i in range(len(orphan_patient))
    ]
    df.loc[orphan_provider, "Provider_ID"] = [
        f"PRV-{900 + (i % 50):03d}" for i in range(len(orphan_provider))
    ]
    df.loc[orphan_facility, "Facility_ID"] = [
        ["FAC-999", "FAC-000", "HOSP-1"][i % 3] for i in range(len(orphan_facility))
    ]
    df.loc[missing_enc_id, "Encounter_ID"] = np.nan
    df.loc[dup_enc_tgt, "Encounter_ID"] = df.loc[dup_enc_src, "Encounter_ID"].values
    df.loc[future_enc, "Encounter_Date"] = "2027-11-01"
    for i, row_i in enumerate(malformed_enc):
        df.at[row_i, "Encounter_Date"] = ["13/40/2024", "not-a-date", "2024-15-01"][i % 3]
    df.loc[missing_patient, "Patient_ID"] = np.nan

    manifest = {
        "orphan_patient_id_rows": int(len(orphan_patient)),
        "orphan_provider_id_rows": int(len(orphan_provider)),
        "orphan_facility_id_rows": int(len(orphan_facility)),
        "missing_encounter_id_rows": int(len(missing_enc_id)),
        "duplicate_encounter_id_pairs": int(len(dup_enc_tgt)),
        "future_encounter_date_rows": int(len(future_enc)),
        "malformed_encounter_date_rows": int(len(malformed_enc)),
        "missing_encounter_patient_id_rows": int(len(missing_patient)),
        "final_encounter_row_count": int(len(df)),
    }
    return df, manifest


def generate_all() -> dict:
    """Write raw and reference datasets plus a defect manifest. Returns file paths."""
    rng = np.random.default_rng(SEED)
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    REFERENCE_DIR.mkdir(parents=True, exist_ok=True)

    facilities_master, facilities_raw = generate_facilities(rng)
    providers = generate_providers(rng)
    patients, patient_manifest = generate_patients(rng)
    encounters, encounter_manifest = generate_encounters(rng, patients, providers)

    gender_vs = pd.DataFrame(
        {
            "Value": list(GENDER_VALUE_SET),
            "Description": ["Female", "Male", "Not specified / unknown"],
            "Is_Approved": ["Y", "Y", "Y"],
        }
    )
    enc_type_vs = pd.DataFrame(
        {
            "Value": list(ENCOUNTER_TYPE_VALUE_SET),
            "Description": list(ENCOUNTER_TYPE_VALUE_SET),
            "Is_Approved": ["Y"] * len(ENCOUNTER_TYPE_VALUE_SET),
        }
    )

    _write_csv(REFERENCE_DIR / "facilities_master.csv", facilities_master)
    _write_csv(REFERENCE_DIR / "gender_value_set.csv", gender_vs)
    _write_csv(REFERENCE_DIR / "encounter_type_value_set.csv", enc_type_vs)
    _write_csv(RAW_DIR / "facilities.csv", facilities_raw)
    _write_csv(RAW_DIR / "providers.csv", providers)
    _write_csv(RAW_DIR / "patients.csv", patients)
    _write_csv(RAW_DIR / "encounters.csv", encounters)

    notice_path = RAW_DIR.parent / "NOTICE.txt"
    notice_path.write_text(
        DATASET_NOTICE
        + "\n\nDo not treat these files as real healthcare records.\n"
        + f"Generated with seed={SEED} as_of={AS_OF_DATE}.\n",
        encoding="utf-8",
    )

    manifest = {
        "notice": DATASET_NOTICE,
        "seed": SEED,
        "as_of_date": AS_OF_DATE,
        "classification": DATASET_CLASSIFICATION,
        "patients": patient_manifest,
        "encounters": encounter_manifest,
        "providers": {
            "row_count": int(len(providers)),
            "injected_format_or_missing_ids": 3,
            "invalid_facility_references": 1,
        },
        "facilities_raw": {
            "row_count": int(len(facilities_raw)),
            "inconsistent_formatting_rows": 2,
        },
    }
    manifest_path = RAW_DIR / "injected_defects_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return {
        "patients": RAW_DIR / "patients.csv",
        "providers": RAW_DIR / "providers.csv",
        "facilities": RAW_DIR / "facilities.csv",
        "encounters": RAW_DIR / "encounters.csv",
        "manifest": manifest_path,
    }


def main() -> None:
    paths = generate_all()
    print("Synthetic datasets written:")
    for name, path in paths.items():
        print(f"  {name}: {path}")


if __name__ == "__main__":
    main()
