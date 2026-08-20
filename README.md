# Healthcare Data Quality Management

Synthetic / Illustrative / Non-production portfolio project.

This repository implements a hands-on data quality workflow against **fully synthetic** healthcare-like datasets. It is not a clinical system, not a production platform, and not an organisational implementation.

## Project Overview

The project generates fabricated patient, provider, facility, and encounter records that contain realistic data-quality defects. It then:

1. Profiles the raw datasets
2. Applies a small Critical Data Element (CDE) catalog
3. Executes documented data quality rules
4. Records pass/fail results and dimension scores
5. Opens simulated data-quality issues
6. Remediates the data with an auditable action log
7. Re-runs the same rules
8. Publishes before/after comparison files and Power BI-ready extracts

All names, identifiers, and attributes are fabricated (`SYNTH_GIVEN_000001`, `PAT-000001`, and similar). No real patient information is used.

## Relationship to Rafid

Rafid demonstrates Data Governance and Data Management framework design. This project demonstrates hands-on Data Quality implementation.

The two repositories are complementary portfolio pieces. They are **not** technically dependent. This project does not import, clone, or modify Rafid.

Related governance framework (separate repository): [rafid-health-cluster-data-governance](https://github.com/dassiri/rafid-health-cluster-data-governance)

| Repository | Focus |
| --- | --- |
| Rafid Health Cluster Data Governance | Enterprise governance and management framework design |
| Healthcare Data Quality Management (this repo) | Practical data quality implementation on synthetic data |

## Architecture

```text
Synthetic Data → Profiling → CDEs → Rules → Validation → Issues → Remediation → Re-test → Reporting
```

| Path | Contents |
| --- | --- |
| `data/raw/` | Synthetic source tables with injected defects |
| `data/reference/` | Facility master and approved value sets |
| `data/processed/` | Remediated tables |
| `rules/` | CDE catalog and DQ rule catalog |
| `src/` | Profiling, validation, remediation, reporting |
| `reports/` | Generated scores, failures, issues, comparison |
| `dashboard/` | Power BI-ready CSV/Excel extracts (no `.pbix` file) |
| `tests/` | Unit tests for core quality rules |

See `docs/architecture.md` for a short layer description.

## Technologies

- Python 3
- pandas
- NumPy
- PyYAML
- openpyxl (Excel extract for Power BI)
- pytest

Power BI is **not** implemented as a `.pbix` report. CSV and Excel files are generated so a report can be built later. SQL, cloud services, and external APIs are not used.

## Data Quality Dimensions

The executable rules cover:

- Completeness
- Uniqueness
- Validity
- Consistency
- Referential Integrity

## Critical Data Elements

Seven synthetic CDEs are defined in `rules/cde_catalog.yaml` and documented in `docs/cde-catalog.md`:

`Patient_ID`, `Date_of_Birth`, `Gender`, `Facility_ID`, `Provider_ID`, `Encounter_ID`, `Encounter_Date`

These are synthetic project definitions only.

## Data Quality Rules

| Rule | Name | Dimension |
| --- | --- | --- |
| DQ-001 | Patient ID Completeness | Completeness |
| DQ-002 | Patient ID Uniqueness | Uniqueness |
| DQ-003 | Date of Birth Validity | Validity |
| DQ-004 | Gender Conformity | Consistency |
| DQ-005 | Facility Referential Integrity | Referential Integrity |
| DQ-006 | Encounter Patient Referential Integrity | Referential Integrity |
| DQ-007 | Encounter Provider Referential Integrity | Referential Integrity |
| DQ-008 | Encounter Facility Referential Integrity | Referential Integrity |
| DQ-009 | Encounter Date Validity | Validity |

The catalog is `rules/dq_rules.yaml`. Implementations live in `src/quality_rules/engine.py`.

## How to Run

From the repository root, using Python 3.10+:

```bash
python3 -m pip install -r requirements.txt
python3 -m pytest
python3 -m src.pipeline
```

Individual steps:

```bash
python3 -m src.generate_data
python3 -m src.profiling.run_profile
python3 -m src.validation.run_checks
```

`python3 -m src.pipeline` regenerates the synthetic data (fixed seed `42`), profiles it, validates it, remediates it, re-validates it, and writes reports.

## Results

The figures below were produced by `python3 -m src.pipeline` against the synthetic datasets in this repository. They are calculated by executable rules, not typed by hand. Re-running the pipeline regenerates `reports/DATA_QUALITY_SUMMARY.md`.

### Before Remediation

Overall Data Quality Score: **93.57%**

| Rule | Records Checked | Passed | Failed | Score |
| --- | ---: | ---: | ---: | ---: |
| DQ-001 | 1020 | 940 | 80 | 92.16 |
| DQ-002 | 940 | 820 | 120 | 87.23 |
| DQ-003 | 970 | 900 | 70 | 92.78 |
| DQ-004 | 1020 | 925 | 95 | 90.69 |
| DQ-005 | 1020 | 945 | 75 | 92.65 |
| DQ-006 | 2500 | 2350 | 150 | 94.00 |
| DQ-007 | 2500 | 2420 | 80 | 96.80 |
| DQ-008 | 2500 | 2430 | 70 | 97.20 |
| DQ-009 | 2500 | 2465 | 35 | 98.60 |

Dimension scores before remediation: Completeness 92.16%, Uniqueness 87.23%, Validity 95.69%, Consistency 90.69%, Referential Integrity 95.16%.

### After Remediation

Overall Data Quality Score: **100.00%**

| Rule | Records Checked | Passed | Failed | Score |
| --- | ---: | ---: | ---: | ---: |
| DQ-001 | 1001 | 1001 | 0 | 100.00 |
| DQ-002 | 1001 | 1001 | 0 | 100.00 |
| DQ-003 | 880 | 880 | 0 | 100.00 |
| DQ-004 | 1001 | 1001 | 0 | 100.00 |
| DQ-005 | 1001 | 1001 | 0 | 100.00 |
| DQ-006 | 2500 | 2500 | 0 | 100.00 |
| DQ-007 | 2500 | 2500 | 0 | 100.00 |
| DQ-008 | 2500 | 2500 | 0 | 100.00 |
| DQ-009 | 2465 | 2465 | 0 | 100.00 |

All nine rules improved. The 100% after-score means the executable rules passed on the remediated dataset. Invalid dates were **cleared, not invented**, so they leave the validity denominator. Processed patients still contain blank dates of birth (visible in profiling) because no source system exists to replace them.

Improvement: **+6.43 percentage points**.

Generated outputs:

- `reports/dq_results_before.csv` / `reports/dq_results_after.csv`
- `reports/dimension_scores_before.csv` / `reports/dimension_scores_after.csv`
- `reports/dq_results_comparison.csv`
- `reports/issues_before.csv` / `reports/issues_after.csv`
- `reports/remediation_log.csv`
- `reports/DATA_QUALITY_SUMMARY.md`
- `dashboard/*.csv` and `dashboard/dq_dashboard_source.xlsx`

## Limitations

- Synthetic data only
- Portfolio project
- Non-production
- No real healthcare data
- No organisational implementation
- No regulatory compliance claim

Issue statuses (`Open`, `In Progress`, `Resolved`, `Closed`) are a portfolio simulation.

Further detail: `docs/limitations.md`.
