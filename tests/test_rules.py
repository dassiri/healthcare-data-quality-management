"""Unit tests for executable data quality rules using small synthetic fixtures."""

from __future__ import annotations

import pandas as pd
import pytest

from src.quality_rules import engine


def _meta(rule_id: str, **kwargs) -> dict:
    base = {
        "rule_id": rule_id,
        "rule_name": rule_id,
        "dimension": kwargs.get("dimension", "Test"),
        "data_element": kwargs.get("data_element", "Patient_ID"),
        "dataset": kwargs.get("dataset", "patients"),
        "severity": "High",
        "cde": "CDE-001",
        "owner": "Synthetic Owner",
        "steward": "Synthetic Steward",
    }
    base.update(kwargs)
    return base


def test_patient_id_completeness_detects_blank_and_null():
    data = {
        "patients": pd.DataFrame({"Patient_ID": ["PAT-000001", None, "  ", "PAT-000002"]})
    }
    result, mask = engine.dq_001_patient_id_completeness(data, _meta("DQ-001"))
    assert result.records_checked == 4
    assert result.failed == 2
    assert result.passed == 2
    assert mask.tolist() == [False, True, True, False]


def test_patient_id_uniqueness_ignores_nulls_and_flags_duplicates():
    data = {
        "patients": pd.DataFrame(
            {"Patient_ID": ["PAT-000001", "PAT-000001", "PAT-000002", None]}
        )
    }
    result, mask = engine.dq_002_patient_id_uniqueness(data, _meta("DQ-002"))
    assert result.records_checked == 3
    assert result.failed == 2
    assert mask.tolist() == [True, True, False, False]


def test_date_of_birth_rejects_future_malformed_and_out_of_range():
    data = {
        "patients": pd.DataFrame(
            {
                "Date_of_Birth": [
                    "1990-01-15",
                    "2028-03-15",
                    "not-a-date",
                    None,
                    "1850-01-01",
                ]
            }
        )
    }
    result, mask = engine.dq_003_dob_validity(
        data, _meta("DQ-003", data_element="Date_of_Birth")
    )
    assert result.records_checked == 4
    assert result.passed == 1
    assert result.failed == 3
    assert mask.tolist() == [False, True, True, False, True]


def test_gender_conformity_requires_approved_value_set():
    data = {
        "patients": pd.DataFrame({"Gender": ["Female", "Male", "Unknown", "M", "Other", None]})
    }
    result, mask = engine.dq_004_gender_conformity(
        data, _meta("DQ-004", data_element="Gender", dimension="Consistency")
    )
    assert result.passed == 3
    assert result.failed == 3
    assert mask.tolist() == [False, False, False, True, True, True]


def test_facility_referential_integrity():
    data = {
        "patients": pd.DataFrame({"Facility_ID": ["FAC-001", "FAC-999", None]}),
        "facilities_master": pd.DataFrame({"Facility_ID": ["FAC-001", "FAC-002"]}),
    }
    result, mask = engine.dq_005_facility_ri(
        data, _meta("DQ-005", data_element="Facility_ID", dimension="Referential Integrity")
    )
    assert result.passed == 1
    assert result.failed == 2
    assert mask.tolist() == [False, True, True]


def test_encounter_patient_referential_integrity():
    data = {
        "patients": pd.DataFrame({"Patient_ID": ["PAT-000001", None]}),
        "encounters": pd.DataFrame({"Patient_ID": ["PAT-000001", "PAT-000999", None]}),
    }
    result, mask = engine.dq_006_encounter_patient_ri(
        data,
        _meta(
            "DQ-006",
            data_element="Patient_ID",
            dataset="encounters",
            dimension="Referential Integrity",
        ),
    )
    assert result.passed == 1
    assert result.failed == 2


def test_encounter_provider_referential_integrity():
    data = {
        "providers": pd.DataFrame({"Provider_ID": ["PRV-001"]}),
        "encounters": pd.DataFrame({"Provider_ID": ["PRV-001", "PRV-900"]}),
    }
    result, mask = engine.dq_007_encounter_provider_ri(
        data,
        _meta(
            "DQ-007",
            data_element="Provider_ID",
            dataset="encounters",
            dimension="Referential Integrity",
        ),
    )
    assert result.passed == 1
    assert result.failed == 1


def test_rule_score_formula():
    data = {"patients": pd.DataFrame({"Patient_ID": ["A", None, "B", "C"]})}
    result, _ = engine.dq_001_patient_id_completeness(data, _meta("DQ-001"))
    assert result.score == 75.0


def test_catalog_covers_implemented_rules():
    catalog = engine.load_rule_catalog()
    ids = {item["rule_id"] for item in catalog}
    assert ids == set(engine.RULE_FUNCTIONS)
    assert "DQ-001" in ids
    assert "DQ-007" in ids
