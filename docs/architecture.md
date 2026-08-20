# Architecture

Synthetic / Illustrative / Non-production.

```text
Synthetic Data
      ↓
Profiling
      ↓
Critical Data Elements
      ↓
Data Quality Rules
      ↓
Validation (before)
      ↓
Issue records
      ↓
Remediation (with action log)
      ↓
Validation (after)
      ↓
Before vs After reporting / Power BI-ready extracts
```

## Layers

| Layer | Location | Role |
| --- | --- | --- |
| Data | `data/raw`, `data/reference`, `data/processed` | Synthetic source, value sets, cleaned output |
| Catalogs | `rules/` | CDE and DQ rule definitions |
| Execution | `src/` | Profiling, validation, remediation, reporting |
| Evidence | `reports/`, `dashboard/` | Generated scores, issues, comparison files |
| Tests | `tests/` | Rule and remediation unit tests |

The project is a local Python workflow. It does not depend on the Rafid Health Cluster Data Governance repository at runtime.
