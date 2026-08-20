# Critical Data Elements

These CDE definitions are **synthetic project definitions** for this portfolio repository. They are not an organisational CDE inventory, and they do not represent a real healthcare entity.

The machine-readable catalog is `rules/cde_catalog.yaml`. A generated copy is written to `reports/cde_catalog.csv` when the pipeline runs.

| CDE ID | Data Element | Definition | Domain | Owner | Steward | Classification | Criticality |
| --- | --- | --- | --- | --- | --- | --- | --- |
| CDE-001 | Patient_ID | Synthetic unique identifier assigned to a fabricated patient record. | Patient | Chief Data Officer (Synthetic) | Patient Master Data Steward (Synthetic) | Confidential (synthetic demonstration label) | High |
| CDE-002 | Date_of_Birth | Synthetic date of birth used to test date validity and completeness. | Patient | Chief Data Officer (Synthetic) | Patient Master Data Steward (Synthetic) | Confidential (synthetic demonstration label) | High |
| CDE-003 | Gender | Synthetic administrative gender constrained to an approved value set. | Patient | Chief Data Officer (Synthetic) | Patient Master Data Steward (Synthetic) | Confidential (synthetic demonstration label) | Medium |
| CDE-004 | Facility_ID | Synthetic identifier of the facility associated with a record. | Facility | Chief Data Officer (Synthetic) | Facility Reference Data Steward (Synthetic) | Internal (synthetic demonstration label) | High |
| CDE-005 | Provider_ID | Synthetic identifier of the care provider associated with an encounter. | Provider | Chief Data Officer (Synthetic) | Provider Master Data Steward (Synthetic) | Internal (synthetic demonstration label) | High |
| CDE-006 | Encounter_ID | Synthetic unique identifier assigned to a fabricated encounter record. | Encounter | Chief Data Officer (Synthetic) | Clinical Data Steward (Synthetic) | Confidential (synthetic demonstration label) | High |
| CDE-007 | Encounter_Date | Synthetic date on which a fabricated encounter occurred. | Encounter | Chief Data Officer (Synthetic) | Clinical Data Steward (Synthetic) | Confidential (synthetic demonstration label) | Medium |
