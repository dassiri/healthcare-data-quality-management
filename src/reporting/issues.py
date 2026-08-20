"""Portfolio issue-management records derived from actual rule failures.

Statuses and owners are a simulation for demonstration. They are not a live
ticketing integration.
"""

from __future__ import annotations

import pandas as pd

ROOT_CAUSE = {
    "DQ-001": "Missing identifiers were injected in the synthetic generator to simulate incomplete source extracts.",
    "DQ-002": "Duplicate Patient_ID values were injected, including exact duplicate rows and conflicting identities sharing an ID.",
    "DQ-003": "Future, malformed, missing, and out-of-range dates were injected to simulate mixed source formats.",
    "DQ-004": "Synonyms and invalid codes (M/F/X/Other) were injected instead of the approved value set.",
    "DQ-005": "Missing and non-existent Facility_ID values were injected to simulate broken reference data.",
    "DQ-006": "Orphan encounter Patient_ID values and blank keys were injected to simulate incomplete interface loads.",
    "DQ-007": "Orphan encounter Provider_ID values were injected to simulate unmatched provider master keys.",
    "DQ-008": "Invalid encounter Facility_ID values were injected to simulate referential drift.",
    "DQ-009": "Future and malformed encounter dates were injected to simulate calendar and format errors.",
}

REMEDIATION_PLAN = {
    "DQ-001": "Assign a new synthetic Patient_ID; retain the row; log the assignment.",
    "DQ-002": "Remove exact duplicate rows; split conflicting identities onto new IDs.",
    "DQ-003": "Parse mixed formats to ISO-8601; clear dates that cannot be validated.",
    "DQ-004": "Map synonyms onto Female/Male/Unknown; default unmatched values to Unknown.",
    "DQ-005": "Standardise Facility_ID; assign unmatched values to FAC-UNK.",
    "DQ-006": "Link orphan encounters to PAT-UNK; do not delete the encounter.",
    "DQ-007": "Assign unmatched providers to PRV-UNK.",
    "DQ-008": "Assign unmatched encounter facilities to FAC-UNK.",
    "DQ-009": "Parse valid dates; clear future or unparseable dates.",
}


def build_issues(results: pd.DataFrame, stage: str) -> pd.DataFrame:
    """Create one simulated issue per rule that has failures (plus resolved after)."""
    rows = []
    for _, rule in results.iterrows():
        failed = int(rule["failed"])
        if stage == "raw":
            status = "Open" if failed else "Closed"
        elif failed == 0:
            status = "Resolved"
        else:
            status = "In Progress"
        issue_id = f"ISS-{str(rule['rule_id']).replace('DQ-', '')}"
        description = (
            f"{rule['rule_name']}: {failed} of {int(rule['records_checked'])} "
            f"records failed on {rule['dataset']}.{rule['data_element']}."
        )
        rows.append(
            {
                "Issue_ID": issue_id,
                "Rule_ID": rule["rule_id"],
                "Data_Element": rule["data_element"],
                "Description": description,
                "Severity": rule["severity"],
                "Owner": rule["owner"],
                "Steward": rule["steward"],
                "Root_Cause": ROOT_CAUSE[rule["rule_id"]],
                "Status": status,
                "Remediation": REMEDIATION_PLAN[rule["rule_id"]],
                "Failed_Records": failed,
                "Stage": "before" if stage == "raw" else "after",
                "Workflow_Type": "Portfolio simulation — not a production ticketing system",
            }
        )
    return pd.DataFrame(rows)
