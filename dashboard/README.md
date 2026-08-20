# Power BI dashboard specification

This repository does **not** include a `.pbix` file. A Power BI report was not implemented in this environment.

The files in this folder are generated from the executable pipeline. They are suitable for import into Power BI Desktop.

## Source files

| File | Suggested use |
| --- | --- |
| `overall_dq_score.csv` | Card visual for overall score |
| `dimension_scores.csv` | Clustered bar by dimension, sliced by snapshot |
| `rule_results.csv` | Rule pass/fail table and score bars |
| `issues.csv` | Issue list |
| `open_issues.csv` | Open / in-progress issues after remediation |
| `issues_by_severity.csv` | Issues by severity and status |
| `before_after.csv` | Before vs after comparison |
| `dq_trend.csv` | Two-point trend (before → after) |
| `dq_dashboard_source.xlsx` | Same tables as Excel sheets |

## Suggested model

1. Import `dq_dashboard_source.xlsx` (all sheets) or the CSV files.
2. Relate `rule_results[rule_id]` to `issues[Rule_ID]`.
3. Use `snapshot` / `snapshot_order` as a slicer (`Before Remediation`, `After Remediation`).

## Suggested visuals

- Card: Overall DQ Score (from `overall_dq_score`)
- Bar chart: Dimension scores
- Table: Rule pass/fail (`records_checked`, `passed`, `failed`, `score`)
- Donut: Issues by severity
- Clustered bar: Before vs After overall score
- Line chart: DQ trend using the two snapshots

Do not replace these files with typed-in metrics. Re-run `python -m src.pipeline` whenever the synthetic data or rules change.
