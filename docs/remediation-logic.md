# Remediation logic

Synthetic / Illustrative / Non-production. This workflow demonstrates documented repair, not silent deletion.

Raw defects such as invalid dates of birth, missing facility identifiers, and duplicate patient identifiers are processed as follows:

```text
Raw data
    ↓
Standardisation, correction, deduplication, referential repair, missing-value handling
    ↓
Cleaned dataset in data/processed/
    ↓
Quality checks re-run
    ↓
Before vs After comparison in reports/
```

Every change is appended to `reports/remediation_log.csv` with the previous value, the new value, and the rationale.

| Action | Behaviour |
| --- | --- |
| Standardisation | Patient, provider, and facility identifiers are normalised to `PAT-NNNNNN`, `PRV-NNN`, and `FAC-NNN`. Dates that parse successfully are stored as `YYYY-MM-DD`. Gender synonyms (`M`/`F`/`male`/…) are mapped onto the approved set. |
| Missing-value handling | Blank Patient_ID, Provider_ID, and Encounter_ID values receive new synthetic identifiers. Rows are retained. |
| Deduplication | Exact duplicate patient rows are removed (first copy kept). Conflicting rows that share a Patient_ID but are not identical are split: one survivor keeps the original ID; others receive a new synthetic ID. Duplicate Encounter_IDs are reassigned rather than dropped. |
| Referential repair | Unmatched facility and provider keys are assigned to `FAC-UNK` / `PRV-UNK` placeholders that are added to the processed reference tables. Orphan encounters are linked to a single `PAT-UNK` unknown patient master record instead of being deleted. |
| Correction | Dates that are unparseable, in the future, or before 1900-01-01 are cleared. No replacement date is invented. Unmatched gender values default to `Unknown`. |

## Methodological limits of placeholder assignment

`FAC-UNK`, `PRV-UNK`, and `PAT-UNK` are synthetic placeholders. They restore **structural / referential integrity** for this portfolio demonstration so unmatched keys can pass the implemented referential-integrity rules without silent row deletion.

They do **not**:

- establish business accuracy
- recover missing source-of-truth information
- identify the real facility, provider, or patient that should have been recorded

A 100% rule-pass score after remediation means every implemented rule passed on the remediated dataset. It does not mean the dataset is universally complete, clinically accurate, or fit for every business purpose. Invalid dates that cannot be reconstructed are cleared rather than invented; those blanks remain in the processed files and are visible in profiling.
