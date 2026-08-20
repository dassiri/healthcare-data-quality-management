"""Remediate synthetic raw datasets and retain an auditable action log.

This is a portfolio simulation of a data-quality remediation workflow.
No real patient records are created, updated, or deleted.
"""

from __future__ import annotations

import re

import pandas as pd

from src.config import (
    AS_OF_DATE,
    DATASET_CLASSIFICATION,
    PROCESSED_DIR,
    UNKNOWN_FACILITY_ID,
    UNKNOWN_PATIENT_ID,
    UNKNOWN_PROVIDER_ID,
)
from src.quality_rules.engine import is_blank, parse_dates


AS_OF = pd.Timestamp(AS_OF_DATE)
DOB_MIN = pd.Timestamp("1900-01-01")

GENDER_MAP = {
    "m": "Male",
    "male": "Male",
    "f": "Female",
    "female": "Female",
    "u": "Unknown",
    "unk": "Unknown",
    "unknown": "Unknown",
}


def _log_row(actions: list[dict], **kwargs) -> None:
    record = {
        "action_id": f"REM-{len(actions) + 1:05d}",
        "dataset": kwargs.get("dataset", ""),
        "record_key": kwargs.get("record_key", ""),
        "data_element": kwargs.get("data_element", ""),
        "action": kwargs.get("action", ""),
        "before_value": kwargs.get("before_value", ""),
        "after_value": kwargs.get("after_value", ""),
        "rationale": kwargs.get("rationale", ""),
    }
    actions.append(record)


def _standardize_patient_id(value) -> str | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    text = str(value).strip()
    if text == "" or text.lower() == "nan":
        return None
    digits = re.sub(r"\D", "", text)
    if digits:
        return f"PAT-{int(digits):06d}"
    return None


def _standardize_provider_id(value) -> str | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    text = str(value).strip()
    if text == "" or text.lower() == "nan":
        return None
    digits = re.sub(r"\D", "", text)
    if digits and 1 <= int(digits) <= 999:
        return f"PRV-{int(digits):03d}"
    return None


def _standardize_facility_id(value) -> str | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    text = str(value).strip()
    if text == "" or text.lower() in {"nan", "n/a"}:
        return None
    digits = re.sub(r"\D", "", text)
    if digits and 1 <= int(digits) <= 12:
        return f"FAC-{int(digits):03d}"
    return None


def remediate_facilities(raw: pd.DataFrame, master: pd.DataFrame, actions: list[dict]) -> pd.DataFrame:
    """Rebuild processed facilities from the clean master plus an Unknown placeholder."""
    processed = master.copy()
    unknown = {
        "Facility_ID": UNKNOWN_FACILITY_ID,
        "Facility_Name": "SYNTH_FACILITY_UNKNOWN",
        "Facility_Type": "Unknown",
        "Region": "Unknown",
        "Is_Active": "N",
    }
    if "Dataset_Classification" in processed.columns:
        unknown["Dataset_Classification"] = DATASET_CLASSIFICATION
    processed = pd.concat([processed, pd.DataFrame([unknown])], ignore_index=True)
    _log_row(
        actions,
        dataset="facilities",
        record_key=UNKNOWN_FACILITY_ID,
        data_element="Facility_ID",
        action="referential_repair",
        before_value="",
        after_value=UNKNOWN_FACILITY_ID,
        rationale="Added Unknown facility placeholder so unmatched Facility_ID values can be repaired without silent deletion.",
    )
    for column in ["Facility_ID", "Facility_Type"]:
        if column in raw.columns:
            _log_row(
                actions,
                dataset="facilities",
                record_key="ALL",
                data_element=column,
                action="standardization",
                before_value="inconsistent raw formatting",
                after_value="facility master values",
                rationale="Raw facility file is replaced by the reference master for processed output.",
            )
    return processed


def remediate_providers(df: pd.DataFrame, valid_facilities: set[str], actions: list[dict]) -> pd.DataFrame:
    out = df.copy()
    next_id = 900
    for idx in out.index:
        original = out.at[idx, "Provider_ID"]
        standardized = _standardize_provider_id(original)
        if standardized is None:
            next_id += 1
            standardized = f"PRV-{next_id:03d}"
            _log_row(
                actions,
                dataset="providers",
                record_key=str(idx),
                data_element="Provider_ID",
                action="missing_value_handling",
                before_value=original,
                after_value=standardized,
                rationale="Assigned a new synthetic provider identifier for a blank or unparseable value.",
            )
        elif str(original).strip() != standardized:
            _log_row(
                actions,
                dataset="providers",
                record_key=standardized,
                data_element="Provider_ID",
                action="standardization",
                before_value=original,
                after_value=standardized,
                rationale="Normalised provider identifier to PRV-NNN.",
            )
        out.at[idx, "Provider_ID"] = standardized

        fac_original = out.at[idx, "Facility_ID"]
        fac = _standardize_facility_id(fac_original)
        if fac is None or fac not in valid_facilities:
            _log_row(
                actions,
                dataset="providers",
                record_key=standardized,
                data_element="Facility_ID",
                action="referential_repair",
                before_value=fac_original,
                after_value=UNKNOWN_FACILITY_ID,
                rationale="Unmatched provider facility reference assigned to Unknown facility.",
            )
            fac = UNKNOWN_FACILITY_ID
        elif str(fac_original).strip() != fac:
            _log_row(
                actions,
                dataset="providers",
                record_key=standardized,
                data_element="Facility_ID",
                action="standardization",
                before_value=fac_original,
                after_value=fac,
                rationale="Normalised facility identifier to FAC-NNN.",
            )
        out.at[idx, "Facility_ID"] = fac
    return out


def remediate_patients(
    df: pd.DataFrame, valid_facilities: set[str], actions: list[dict]
) -> pd.DataFrame:
    out = df.copy()
    assigned_serial = 800000

    for idx in out.index:
        original = out.at[idx, "Patient_ID"]
        standardized = _standardize_patient_id(original)
        if standardized is None:
            assigned_serial += 1
            standardized = f"PAT-{assigned_serial:06d}"
            _log_row(
                actions,
                dataset="patients",
                record_key=str(idx),
                data_element="Patient_ID",
                action="missing_value_handling",
                before_value=original,
                after_value=standardized,
                rationale="Assigned a new synthetic Patient_ID for a blank identifier. The original row was retained.",
            )
        elif str(original).strip() != standardized:
            _log_row(
                actions,
                dataset="patients",
                record_key=standardized,
                data_element="Patient_ID",
                action="standardization",
                before_value=original,
                after_value=standardized,
                rationale="Normalised Patient_ID to PAT-NNNNNN.",
            )
        out.at[idx, "Patient_ID"] = standardized

        dob_original = out.at[idx, "Date_of_Birth"]
        parsed = parse_dates(pd.Series([dob_original])).iloc[0]
        if pd.isna(parsed) or parsed < DOB_MIN or parsed > AS_OF:
            _log_row(
                actions,
                dataset="patients",
                record_key=out.at[idx, "Patient_ID"],
                data_element="Date_of_Birth",
                action="correction",
                before_value=dob_original,
                after_value="",
                rationale="Unparseable, future, or out-of-range date cleared. No source system exists to impute a replacement.",
            )
            out.at[idx, "Date_of_Birth"] = pd.NA
        else:
            iso = parsed.strftime("%Y-%m-%d")
            if str(dob_original).strip() != iso:
                _log_row(
                    actions,
                    dataset="patients",
                    record_key=out.at[idx, "Patient_ID"],
                    data_element="Date_of_Birth",
                    action="standardization",
                    before_value=dob_original,
                    after_value=iso,
                    rationale="Parsed mixed date formats into ISO-8601 (YYYY-MM-DD).",
                )
            out.at[idx, "Date_of_Birth"] = iso

        gender_original = out.at[idx, "Gender"]
        key = "" if pd.isna(gender_original) else str(gender_original).strip().lower()
        mapped = GENDER_MAP.get(key)
        if mapped is None:
            mapped = "Unknown"
            _log_row(
                actions,
                dataset="patients",
                record_key=out.at[idx, "Patient_ID"],
                data_element="Gender",
                action="correction",
                before_value=gender_original,
                after_value=mapped,
                rationale="Value not in the approved set; defaulted to Unknown.",
            )
        elif str(gender_original).strip() != mapped:
            _log_row(
                actions,
                dataset="patients",
                record_key=out.at[idx, "Patient_ID"],
                data_element="Gender",
                action="standardization",
                before_value=gender_original,
                after_value=mapped,
                rationale="Mapped gender synonym onto the approved value set.",
            )
        out.at[idx, "Gender"] = mapped

        fac_original = out.at[idx, "Facility_ID"]
        fac = _standardize_facility_id(fac_original)
        if fac is None or fac not in valid_facilities:
            _log_row(
                actions,
                dataset="patients",
                record_key=out.at[idx, "Patient_ID"],
                data_element="Facility_ID",
                action="referential_repair",
                before_value=fac_original,
                after_value=UNKNOWN_FACILITY_ID,
                rationale="Missing or invalid facility reference assigned to Unknown facility.",
            )
            fac = UNKNOWN_FACILITY_ID
        elif str(fac_original).strip() != fac:
            _log_row(
                actions,
                dataset="patients",
                record_key=out.at[idx, "Patient_ID"],
                data_element="Facility_ID",
                action="standardization",
                before_value=fac_original,
                after_value=fac,
                rationale="Normalised Facility_ID to FAC-NNN.",
            )
        out.at[idx, "Facility_ID"] = fac

    # Exact duplicate rows: keep the first occurrence.
    subset = [c for c in out.columns if c != "Dataset_Classification"]
    before_count = len(out)
    duplicated = out.duplicated(subset=subset, keep="first")
    for idx in out.index[duplicated]:
        _log_row(
            actions,
            dataset="patients",
            record_key=out.at[idx, "Patient_ID"],
            data_element="Patient_ID",
            action="deduplication",
            before_value=out.at[idx, "Patient_ID"],
            after_value="ROW_REMOVED",
            rationale="Removed an exact duplicate patient row. The first copy was retained.",
        )
    out = out.loc[~duplicated].copy()

    # Remaining duplicate IDs that are not exact row copies: keep the most complete row.
    completeness = out.notna().sum(axis=1)
    out = out.assign(_completeness=completeness)
    keep_idx = set()
    for patient_id, group in out.groupby("Patient_ID", dropna=False):
        if len(group) == 1:
            keep_idx.add(group.index[0])
            continue
        survivor = group.sort_values("_completeness", ascending=False).index[0]
        keep_idx.add(survivor)
        serial = 0
        for idx in group.index:
            if idx == survivor:
                continue
            serial += 1
            new_id = f"PAT-{int(str(patient_id).replace('PAT-', '')) + 700000 + serial:06d}"
            _log_row(
                actions,
                dataset="patients",
                record_key=patient_id,
                data_element="Patient_ID",
                action="deduplication",
                before_value=patient_id,
                after_value=new_id,
                rationale="Same Patient_ID on non-identical rows treated as a conflicting identity. Survivor kept the original ID; others received a new synthetic ID.",
            )
            out.at[idx, "Patient_ID"] = new_id
            keep_idx.add(idx)
    out = out.drop(columns=["_completeness"])
    _log_row(
        actions,
        dataset="patients",
        record_key="ALL",
        data_element="Patient_ID",
        action="deduplication",
        before_value=str(before_count),
        after_value=str(len(out)),
        rationale="Patient row count after exact-duplicate removal and conflicting-ID split.",
    )
    return out.reset_index(drop=True)


def remediate_encounters(
    df: pd.DataFrame,
    patients: pd.DataFrame,
    providers: pd.DataFrame,
    valid_facilities: set[str],
    actions: list[dict],
) -> pd.DataFrame:
    out = df.copy()
    patient_ids = set(patients["Patient_ID"].astype("string").str.strip())
    provider_ids = set(providers["Provider_ID"].astype("string").str.strip())
    stub_rows = []
    assigned_enc = 9000000
    unknown_patient_created = False

    seen_encounters: dict[str, int] = {}
    for idx in out.index:
        original_enc = out.at[idx, "Encounter_ID"]
        enc_text = "" if pd.isna(original_enc) else str(original_enc).strip()
        if enc_text == "" or enc_text.lower() == "nan":
            assigned_enc += 1
            enc_text = f"ENC-{assigned_enc:07d}"
            _log_row(
                actions,
                dataset="encounters",
                record_key=str(idx),
                data_element="Encounter_ID",
                action="missing_value_handling",
                before_value=original_enc,
                after_value=enc_text,
                rationale="Assigned a new synthetic Encounter_ID for a blank identifier.",
            )
        if enc_text in seen_encounters:
            assigned_enc += 1
            new_enc = f"ENC-{assigned_enc:07d}"
            _log_row(
                actions,
                dataset="encounters",
                record_key=enc_text,
                data_element="Encounter_ID",
                action="deduplication",
                before_value=enc_text,
                after_value=new_enc,
                rationale="Duplicate Encounter_ID reassigned to preserve uniqueness without dropping the clinical event row.",
            )
            enc_text = new_enc
        seen_encounters[enc_text] = idx
        out.at[idx, "Encounter_ID"] = enc_text

        original_pat = out.at[idx, "Patient_ID"]
        pat = _standardize_patient_id(original_pat)
        if pat is None or pat not in patient_ids:
            if not unknown_patient_created:
                stub_rows.append(
                    {
                        "Patient_ID": UNKNOWN_PATIENT_ID,
                        "Given_Name": "SYNTH_GIVEN_UNKNOWN",
                        "Family_Name": "SYNTH_FAMILY_UNKNOWN",
                        "Date_of_Birth": pd.NA,
                        "Gender": "Unknown",
                        "Facility_ID": UNKNOWN_FACILITY_ID,
                        "Registration_Date": AS_OF_DATE,
                        "Record_Status": "REMEDIATION_STUB",
                        "Dataset_Classification": DATASET_CLASSIFICATION,
                    }
                )
                patient_ids.add(UNKNOWN_PATIENT_ID)
                unknown_patient_created = True
            _log_row(
                actions,
                dataset="encounters",
                record_key=enc_text,
                data_element="Patient_ID",
                action="referential_repair",
                before_value=original_pat,
                after_value=UNKNOWN_PATIENT_ID,
                rationale="Orphan encounter linked to a single Unknown patient master record rather than being deleted.",
            )
            pat = UNKNOWN_PATIENT_ID
        out.at[idx, "Patient_ID"] = pat

        original_prv = out.at[idx, "Provider_ID"]
        prv = _standardize_provider_id(original_prv)
        if prv is None or prv not in provider_ids:
            _log_row(
                actions,
                dataset="encounters",
                record_key=enc_text,
                data_element="Provider_ID",
                action="referential_repair",
                before_value=original_prv,
                after_value=UNKNOWN_PROVIDER_ID,
                rationale="Unmatched provider reference assigned to Unknown provider.",
            )
            prv = UNKNOWN_PROVIDER_ID
        elif str(original_prv).strip() != prv:
            _log_row(
                actions,
                dataset="encounters",
                record_key=enc_text,
                data_element="Provider_ID",
                action="standardization",
                before_value=original_prv,
                after_value=prv,
                rationale="Normalised Provider_ID to PRV-NNN.",
            )
        out.at[idx, "Provider_ID"] = prv

        original_fac = out.at[idx, "Facility_ID"]
        fac = _standardize_facility_id(original_fac)
        if fac is None or fac not in valid_facilities:
            _log_row(
                actions,
                dataset="encounters",
                record_key=enc_text,
                data_element="Facility_ID",
                action="referential_repair",
                before_value=original_fac,
                after_value=UNKNOWN_FACILITY_ID,
                rationale="Unmatched encounter facility reference assigned to Unknown facility.",
            )
            fac = UNKNOWN_FACILITY_ID
        out.at[idx, "Facility_ID"] = fac

        original_date = out.at[idx, "Encounter_Date"]
        parsed = parse_dates(pd.Series([original_date])).iloc[0]
        if pd.isna(parsed) or parsed > AS_OF:
            _log_row(
                actions,
                dataset="encounters",
                record_key=enc_text,
                data_element="Encounter_Date",
                action="correction",
                before_value=original_date,
                after_value="",
                rationale="Unparseable or future encounter date cleared. No source system exists to impute a replacement.",
            )
            out.at[idx, "Encounter_Date"] = pd.NA
        else:
            out.at[idx, "Encounter_Date"] = parsed.strftime("%Y-%m-%d")

    if stub_rows:
        patients_extended = pd.concat([patients, pd.DataFrame(stub_rows)], ignore_index=True)
    else:
        patients_extended = patients
    return out, patients_extended


def remediate(raw: dict[str, pd.DataFrame]) -> tuple[dict[str, pd.DataFrame], pd.DataFrame]:
    """Return processed datasets and a full remediation action log."""
    actions: list[dict] = []
    master = raw["facilities_master"].copy()
    facilities = remediate_facilities(raw["facilities"], master, actions)
    valid_facilities = set(facilities["Facility_ID"].astype("string").str.strip())

    unknown_provider = pd.DataFrame(
        [
            {
                "Provider_ID": UNKNOWN_PROVIDER_ID,
                "Provider_Name": "SYNTH_PROVIDER_UNKNOWN",
                "Specialty": "Unknown",
                "Facility_ID": UNKNOWN_FACILITY_ID,
                "Dataset_Classification": DATASET_CLASSIFICATION,
            }
        ]
    )
    _log_row(
        actions,
        dataset="providers",
        record_key=UNKNOWN_PROVIDER_ID,
        data_element="Provider_ID",
        action="referential_repair",
        before_value="",
        after_value=UNKNOWN_PROVIDER_ID,
        rationale="Added Unknown provider placeholder for unmatched encounter provider references.",
    )

    providers = remediate_providers(raw["providers"], valid_facilities, actions)
    providers = pd.concat([providers, unknown_provider], ignore_index=True)

    patients = remediate_patients(raw["patients"], valid_facilities, actions)
    encounters, patients = remediate_encounters(
        raw["encounters"], patients, providers, valid_facilities, actions
    )

    processed = {
        "facilities": facilities,
        "facilities_master": facilities,
        "providers": providers,
        "patients": patients,
        "encounters": encounters,
    }
    log = pd.DataFrame(actions)
    return processed, log


def write_processed(processed: dict[str, pd.DataFrame], log: pd.DataFrame) -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    for name in ("patients", "providers", "facilities", "encounters"):
        processed[name].to_csv(PROCESSED_DIR / f"{name}.csv", index=False)
    processed["facilities_master"].to_csv(PROCESSED_DIR / "facilities_master.csv", index=False)
    log.to_csv(PROCESSED_DIR / "remediation_log.csv", index=False)
