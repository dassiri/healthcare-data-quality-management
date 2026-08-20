"""Executable data quality rules.

Rule metadata is loaded from rules/dq_rules.yaml. Pass/fail counts are computed
from the supplied dataframes — they are never hard-coded.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Callable

import pandas as pd
import yaml

from src.config import AS_OF_DATE, CDE_CATALOG_PATH, GENDER_VALUE_SET, RULE_CATALOG_PATH


AS_OF = pd.Timestamp(AS_OF_DATE)
DOB_MIN = pd.Timestamp("1900-01-01")


@dataclass
class RuleResult:
    """Outcome of one data quality rule execution."""

    rule_id: str
    rule_name: str
    dimension: str
    data_element: str
    dataset: str
    records_checked: int
    passed: int
    failed: int
    score: float
    severity: str
    cde: str
    owner: str
    steward: str

    def to_dict(self) -> dict:
        return asdict(self)


def is_blank(series: pd.Series) -> pd.Series:
    """True when a value is null or whitespace-only."""
    as_str = series.astype("string")
    return as_str.isna() | as_str.str.strip().eq("") | as_str.str.strip().str.lower().eq("nan")


def parse_dates(series: pd.Series) -> pd.Series:
    """Parse ISO dates first, then a small set of explicit alternative formats."""
    text = series.astype("string").str.strip()
    parsed = pd.to_datetime(text, errors="coerce", format="%Y-%m-%d")
    unresolved = parsed.isna() & text.notna() & text.ne("") & text.str.lower().ne("nan")
    alt_formats = ("%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y", "%m-%d-%Y", "%d-%b-%Y", "%Y/%m/%d")
    for fmt in alt_formats:
        if not unresolved.any():
            break
        extra = pd.to_datetime(text[unresolved], errors="coerce", format=fmt)
        parsed.loc[extra.index[extra.notna()]] = extra[extra.notna()]
        unresolved = parsed.isna() & text.notna() & text.ne("") & text.str.lower().ne("nan")
    return parsed


def _score(checked: int, failed: int) -> float:
    if checked == 0:
        return 0.0
    passed = checked - failed
    return round(100.0 * passed / checked, 2)


def _result(meta: dict, checked: int, fail_mask: pd.Series) -> tuple[RuleResult, pd.DataFrame]:
    failed = int(fail_mask.sum())
    passed = checked - failed
    result = RuleResult(
        rule_id=meta["rule_id"],
        rule_name=meta["rule_name"],
        dimension=meta["dimension"],
        data_element=meta["data_element"],
        dataset=meta["dataset"],
        records_checked=checked,
        passed=passed,
        failed=failed,
        score=_score(checked, failed),
        severity=meta["severity"],
        cde=meta["cde"],
        owner=meta["owner"],
        steward=meta["steward"],
    )
    failures = fail_mask[fail_mask].index.to_frame(index=False)
    failures.columns = ["row_index"]
    failures["rule_id"] = meta["rule_id"]
    return result, failures


def load_rule_catalog() -> list[dict]:
    with RULE_CATALOG_PATH.open(encoding="utf-8") as handle:
        payload = yaml.safe_load(handle)
    return payload["rules"]


def load_cde_catalog() -> list[dict]:
    with CDE_CATALOG_PATH.open(encoding="utf-8") as handle:
        payload = yaml.safe_load(handle)
    return payload["cdes"]


def dq_001_patient_id_completeness(data: dict, meta: dict) -> tuple[RuleResult, pd.Series]:
    df = data["patients"]
    mask = is_blank(df["Patient_ID"])
    result, _ = _result(meta, len(df), mask)
    return result, mask


def dq_002_patient_id_uniqueness(data: dict, meta: dict) -> tuple[RuleResult, pd.Series]:
    df = data["patients"]
    ids = df["Patient_ID"].astype("string").str.strip()
    populated = ~is_blank(df["Patient_ID"])
    dup = ids.duplicated(keep=False) & populated
    result, _ = _result(meta, int(populated.sum()), dup)
    return result, dup


def dq_003_dob_validity(data: dict, meta: dict) -> tuple[RuleResult, pd.Series]:
    df = data["patients"]
    populated = ~is_blank(df["Date_of_Birth"])
    parsed = parse_dates(df["Date_of_Birth"])
    valid = populated & parsed.notna() & (parsed >= DOB_MIN) & (parsed <= AS_OF)
    fail = populated & ~valid
    result, _ = _result(meta, int(populated.sum()), fail)
    return result, fail


def dq_004_gender_conformity(data: dict, meta: dict) -> tuple[RuleResult, pd.Series]:
    df = data["patients"]
    values = df["Gender"].astype("string").str.strip()
    fail = ~values.isin(list(GENDER_VALUE_SET))
    result, _ = _result(meta, len(df), fail)
    return result, fail


def dq_005_facility_ri(data: dict, meta: dict) -> tuple[RuleResult, pd.Series]:
    df = data["patients"]
    master = set(data["facilities_master"]["Facility_ID"].astype("string").str.strip())
    values = df["Facility_ID"].astype("string").str.strip()
    fail = is_blank(df["Facility_ID"]) | ~values.isin(master)
    result, _ = _result(meta, len(df), fail)
    return result, fail


def dq_006_encounter_patient_ri(data: dict, meta: dict) -> tuple[RuleResult, pd.Series]:
    enc = data["encounters"]
    patients = set(
        data["patients"].loc[~is_blank(data["patients"]["Patient_ID"]), "Patient_ID"]
        .astype("string")
        .str.strip()
    )
    values = enc["Patient_ID"].astype("string").str.strip()
    fail = is_blank(enc["Patient_ID"]) | ~values.isin(patients)
    result, _ = _result(meta, len(enc), fail)
    return result, fail


def dq_007_encounter_provider_ri(data: dict, meta: dict) -> tuple[RuleResult, pd.Series]:
    enc = data["encounters"]
    providers = set(
        data["providers"].loc[~is_blank(data["providers"]["Provider_ID"]), "Provider_ID"]
        .astype("string")
        .str.strip()
    )
    values = enc["Provider_ID"].astype("string").str.strip()
    fail = is_blank(enc["Provider_ID"]) | ~values.isin(providers)
    result, _ = _result(meta, len(enc), fail)
    return result, fail


def dq_008_encounter_facility_ri(data: dict, meta: dict) -> tuple[RuleResult, pd.Series]:
    enc = data["encounters"]
    master = set(data["facilities_master"]["Facility_ID"].astype("string").str.strip())
    values = enc["Facility_ID"].astype("string").str.strip()
    fail = is_blank(enc["Facility_ID"]) | ~values.isin(master)
    result, _ = _result(meta, len(enc), fail)
    return result, fail


def dq_009_encounter_date_validity(data: dict, meta: dict) -> tuple[RuleResult, pd.Series]:
    enc = data["encounters"]
    populated = ~is_blank(enc["Encounter_Date"])
    parsed = parse_dates(enc["Encounter_Date"])
    valid = populated & parsed.notna() & (parsed <= AS_OF)
    fail = populated & ~valid
    result, _ = _result(meta, int(populated.sum()), fail)
    return result, fail


RULE_FUNCTIONS: dict[str, Callable] = {
    "DQ-001": dq_001_patient_id_completeness,
    "DQ-002": dq_002_patient_id_uniqueness,
    "DQ-003": dq_003_dob_validity,
    "DQ-004": dq_004_gender_conformity,
    "DQ-005": dq_005_facility_ri,
    "DQ-006": dq_006_encounter_patient_ri,
    "DQ-007": dq_007_encounter_provider_ri,
    "DQ-008": dq_008_encounter_facility_ri,
    "DQ-009": dq_009_encounter_date_validity,
}


def run_rules(data: dict) -> tuple[pd.DataFrame, dict[str, pd.Series], list[dict]]:
    """Execute every catalogued rule. Returns results table, fail masks, catalog."""
    catalog = load_rule_catalog()
    results = []
    masks: dict[str, pd.Series] = {}
    for meta in catalog:
        func = RULE_FUNCTIONS[meta["rule_id"]]
        result, mask = func(data, meta)
        results.append(result.to_dict())
        masks[meta["rule_id"]] = mask
    return pd.DataFrame(results), masks, catalog
