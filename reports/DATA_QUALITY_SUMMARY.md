# Data Quality Results

Synthetic / Illustrative / Non-production. Scores are calculated from executable rules.

## Overall

- Before remediation: **93.57%**
- After remediation: **100.0%**
- Improvement: **6.43 percentage points**

## Rule Results — Before Remediation

| Rule | Name | Dimension | Records Checked | Passed | Failed | Score |
| --- | --- | --- | --- | --- | --- | --- |
| DQ-001 | Patient ID Completeness | Completeness | 1020 | 940 | 80 | 92.16 |
| DQ-002 | Patient ID Uniqueness | Uniqueness | 940 | 820 | 120 | 87.23 |
| DQ-003 | Date of Birth Validity | Validity | 970 | 900 | 70 | 92.78 |
| DQ-004 | Gender Conformity | Consistency | 1020 | 925 | 95 | 90.69 |
| DQ-005 | Facility Referential Integrity | Referential Integrity | 1020 | 945 | 75 | 92.65 |
| DQ-006 | Encounter Patient Referential Integrity | Referential Integrity | 2500 | 2350 | 150 | 94.0 |
| DQ-007 | Encounter Provider Referential Integrity | Referential Integrity | 2500 | 2420 | 80 | 96.8 |
| DQ-008 | Encounter Facility Referential Integrity | Referential Integrity | 2500 | 2430 | 70 | 97.2 |
| DQ-009 | Encounter Date Validity | Validity | 2500 | 2465 | 35 | 98.6 |

## Rule Results — After Remediation

| Rule | Name | Dimension | Records Checked | Passed | Failed | Score |
| --- | --- | --- | --- | --- | --- | --- |
| DQ-001 | Patient ID Completeness | Completeness | 1001 | 1001 | 0 | 100.0 |
| DQ-002 | Patient ID Uniqueness | Uniqueness | 1001 | 1001 | 0 | 100.0 |
| DQ-003 | Date of Birth Validity | Validity | 880 | 880 | 0 | 100.0 |
| DQ-004 | Gender Conformity | Consistency | 1001 | 1001 | 0 | 100.0 |
| DQ-005 | Facility Referential Integrity | Referential Integrity | 1001 | 1001 | 0 | 100.0 |
| DQ-006 | Encounter Patient Referential Integrity | Referential Integrity | 2500 | 2500 | 0 | 100.0 |
| DQ-007 | Encounter Provider Referential Integrity | Referential Integrity | 2500 | 2500 | 0 | 100.0 |
| DQ-008 | Encounter Facility Referential Integrity | Referential Integrity | 2500 | 2500 | 0 | 100.0 |
| DQ-009 | Encounter Date Validity | Validity | 2465 | 2465 | 0 | 100.0 |

## Dimension Scores

### Before

| dimension | rules | records_checked | passed | failed | score |
| --- | --- | --- | --- | --- | --- |
| Completeness | 1 | 1020 | 940 | 80 | 92.16 |
| Consistency | 1 | 1020 | 925 | 95 | 90.69 |
| Referential Integrity | 4 | 8520 | 8145 | 375 | 95.16 |
| Uniqueness | 1 | 940 | 820 | 120 | 87.23 |
| Validity | 2 | 3470 | 3365 | 105 | 95.69 |

### After

| dimension | rules | records_checked | passed | failed | score |
| --- | --- | --- | --- | --- | --- |
| Completeness | 1 | 1001 | 1001 | 0 | 100.0 |
| Consistency | 1 | 1001 | 1001 | 0 | 100.0 |
| Referential Integrity | 4 | 8501 | 8501 | 0 | 100.0 |
| Uniqueness | 1 | 1001 | 1001 | 0 | 100.0 |
| Validity | 2 | 3345 | 3345 | 0 | 100.0 |

## Rules That Improved

| rule_id | rule_name | score_before | score_after | score_delta | failed_before | failed_after |
| --- | --- | --- | --- | --- | --- | --- |
| DQ-001 | Patient ID Completeness | 92.16 | 100.0 | 7.84 | 80 | 0 |
| DQ-002 | Patient ID Uniqueness | 87.23 | 100.0 | 12.77 | 120 | 0 |
| DQ-003 | Date of Birth Validity | 92.78 | 100.0 | 7.22 | 70 | 0 |
| DQ-004 | Gender Conformity | 90.69 | 100.0 | 9.31 | 95 | 0 |
| DQ-005 | Facility Referential Integrity | 92.65 | 100.0 | 7.35 | 75 | 0 |
| DQ-006 | Encounter Patient Referential Integrity | 94.0 | 100.0 | 6.0 | 150 | 0 |
| DQ-007 | Encounter Provider Referential Integrity | 96.8 | 100.0 | 3.2 | 80 | 0 |
| DQ-008 | Encounter Facility Referential Integrity | 97.2 | 100.0 | 2.8 | 70 | 0 |
| DQ-009 | Encounter Date Validity | 98.6 | 100.0 | 1.4 | 35 | 0 |

## Issue Management (portfolio simulation)

### Before

| Issue_ID | Rule_ID | Data_Element | Severity | Status | Failed_Records |
| --- | --- | --- | --- | --- | --- |
| ISS-001 | DQ-001 | Patient_ID | High | Open | 80 |
| ISS-002 | DQ-002 | Patient_ID | High | Open | 120 |
| ISS-003 | DQ-003 | Date_of_Birth | High | Open | 70 |
| ISS-004 | DQ-004 | Gender | Medium | Open | 95 |
| ISS-005 | DQ-005 | Facility_ID | High | Open | 75 |
| ISS-006 | DQ-006 | Patient_ID | High | Open | 150 |
| ISS-007 | DQ-007 | Provider_ID | High | Open | 80 |
| ISS-008 | DQ-008 | Facility_ID | High | Open | 70 |
| ISS-009 | DQ-009 | Encounter_Date | Medium | Open | 35 |

### After

| Issue_ID | Rule_ID | Data_Element | Severity | Status | Failed_Records |
| --- | --- | --- | --- | --- | --- |
| ISS-001 | DQ-001 | Patient_ID | High | Resolved | 0 |
| ISS-002 | DQ-002 | Patient_ID | High | Resolved | 0 |
| ISS-003 | DQ-003 | Date_of_Birth | High | Resolved | 0 |
| ISS-004 | DQ-004 | Gender | Medium | Resolved | 0 |
| ISS-005 | DQ-005 | Facility_ID | High | Resolved | 0 |
| ISS-006 | DQ-006 | Patient_ID | High | Resolved | 0 |
| ISS-007 | DQ-007 | Provider_ID | High | Resolved | 0 |
| ISS-008 | DQ-008 | Facility_ID | High | Resolved | 0 |
| ISS-009 | DQ-009 | Encounter_Date | Medium | Resolved | 0 |
