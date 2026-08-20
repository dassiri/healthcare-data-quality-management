"""Tests for remediation behaviour — rows are repaired, not silently deleted."""

from __future__ import annotations

import pandas as pd

from src.remediation.remediator import remediate


def test_remediation_assigns_ids_and_preserves_orphan_encounters():
    raw = {
        "facilities_master": pd.DataFrame(
            {
                "Facility_ID": ["FAC-001"],
                "Facility_Name": ["SYNTH_FACILITY_001"],
                "Facility_Type": ["Hospital"],
                "Region": ["North"],
                "Is_Active": ["Y"],
            }
        ),
        "facilities": pd.DataFrame(
            {
                "Facility_ID": ["fac-001"],
                "Facility_Name": ["SYNTH_FACILITY_001"],
                "Facility_Type": ["hospital"],
                "Region": ["North"],
                "Is_Active": ["Y"],
            }
        ),
        "providers": pd.DataFrame(
            {
                "Provider_ID": ["PRV001"],
                "Provider_Name": ["SYNTH_PROVIDER_001"],
                "Specialty": ["General Practice"],
                "Facility_ID": ["FAC-001"],
            }
        ),
        "patients": pd.DataFrame(
            {
                "Patient_ID": [None, "PAT-000001", "PAT-000001"],
                "Given_Name": ["SYNTH_GIVEN_000001", "SYNTH_GIVEN_000002", "SYNTH_GIVEN_000002"],
                "Family_Name": ["SYNTH_FAMILY_000001", "SYNTH_FAMILY_000002", "SYNTH_FAMILY_000002"],
                "Date_of_Birth": ["1990-01-01", "2028-01-01", "1991-02-02"],
                "Gender": ["M", "Female", "Female"],
                "Facility_ID": ["FAC-999", "FAC-001", "FAC-001"],
                "Registration_Date": ["2024-01-01", "2024-01-01", "2024-01-01"],
            }
        ),
        "encounters": pd.DataFrame(
            {
                "Encounter_ID": ["ENC-0000001", "ENC-0000001"],
                "Patient_ID": ["PAT-000999", "PAT-000001"],
                "Provider_ID": ["PRV-900", "PRV-001"],
                "Facility_ID": ["FAC-999", "FAC-001"],
                "Encounter_Date": ["2024-06-01", "not-a-date"],
                "Discharge_Date": ["2024-06-01", "2024-06-02"],
                "Encounter_Type": ["Outpatient", "Outpatient"],
            }
        ),
    }
    processed, log = remediate(raw)
    assert not processed["patients"]["Patient_ID"].isna().any()
    assert processed["encounters"].shape[0] == 2
    assert "FAC-UNK" in set(processed["facilities"]["Facility_ID"])
    assert "PRV-UNK" in set(processed["providers"]["Provider_ID"])
    assert "PAT-UNK" in set(processed["patients"]["Patient_ID"])
    assert log.shape[0] > 0
    assert "ROW_REMOVED" in set(log["after_value"]) or "deduplication" in set(log["action"])
