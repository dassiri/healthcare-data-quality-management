"""Persist validation, issue, comparison, and Power BI-ready dashboard files."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.config import DASHBOARD_DIR, REPORTS_DIR
from src.reporting.issues import build_issues
from src.reporting.markdown import dataframe_to_markdown


def write_issues(results: pd.DataFrame, stage: str) -> pd.DataFrame:
    issues = build_issues(results, stage)
    suffix = "before" if stage == "raw" else "after"
    issues.to_csv(REPORTS_DIR / f"issues_{suffix}.csv", index=False)
    return issues


def write_comparison(before: pd.DataFrame, after: pd.DataFrame, before_overall: float, after_overall: float) -> pd.DataFrame:
    merged = before.merge(
        after,
        on=["rule_id", "rule_name", "dimension", "data_element"],
        suffixes=("_before", "_after"),
    )
    merged["score_delta"] = (merged["score_after"] - merged["score_before"]).round(2)
    merged["failed_delta"] = merged["failed_after"] - merged["failed_before"]
    merged["improved"] = merged["score_delta"] > 0
    merged.to_csv(REPORTS_DIR / "dq_results_comparison.csv", index=False)

    summary = pd.DataFrame(
        [
            {
                "metric": "Overall Data Quality Score",
                "before_pct": before_overall,
                "after_pct": after_overall,
                "delta_pct": round(after_overall - before_overall, 2),
            }
        ]
    )
    summary.to_csv(REPORTS_DIR / "before_after_overall.csv", index=False)
    return merged


def write_summary_markdown(
    before: pd.DataFrame,
    after: pd.DataFrame,
    before_dim: pd.DataFrame,
    after_dim: pd.DataFrame,
    before_overall: float,
    after_overall: float,
    comparison: pd.DataFrame,
    issues_before: pd.DataFrame,
    issues_after: pd.DataFrame,
) -> Path:
    lines = [
        "# Data Quality Results",
        "",
        "Synthetic / Illustrative / Non-production. Scores are calculated from executable rules.",
        "",
        "## Overall",
        "",
        f"- Before remediation: **{before_overall}%**",
        f"- After remediation: **{after_overall}%**",
        f"- Improvement: **{round(after_overall - before_overall, 2)} percentage points**",
        "",
        "## Rule Results — Before Remediation",
        "",
        dataframe_to_markdown(
            before[
                ["rule_id", "rule_name", "dimension", "records_checked", "passed", "failed", "score"]
            ].rename(
                columns={
                    "rule_id": "Rule",
                    "rule_name": "Name",
                    "dimension": "Dimension",
                    "records_checked": "Records Checked",
                    "passed": "Passed",
                    "failed": "Failed",
                    "score": "Score",
                }
            )
        ),
        "",
        "## Rule Results — After Remediation",
        "",
        dataframe_to_markdown(
            after[
                ["rule_id", "rule_name", "dimension", "records_checked", "passed", "failed", "score"]
            ].rename(
                columns={
                    "rule_id": "Rule",
                    "rule_name": "Name",
                    "dimension": "Dimension",
                    "records_checked": "Records Checked",
                    "passed": "Passed",
                    "failed": "Failed",
                    "score": "Score",
                }
            )
        ),
        "",
        "## Dimension Scores",
        "",
        "### Before",
        "",
        dataframe_to_markdown(before_dim),
        "",
        "### After",
        "",
        dataframe_to_markdown(after_dim),
        "",
        "## Rules That Improved",
        "",
        dataframe_to_markdown(
            comparison.loc[
                comparison["improved"],
                ["rule_id", "rule_name", "score_before", "score_after", "score_delta", "failed_before", "failed_after"],
            ]
        ),
        "",
        "## Issue Management (portfolio simulation)",
        "",
        "### Before",
        "",
        dataframe_to_markdown(
            issues_before[["Issue_ID", "Rule_ID", "Data_Element", "Severity", "Status", "Failed_Records"]]
        ),
        "",
        "### After",
        "",
        dataframe_to_markdown(
            issues_after[["Issue_ID", "Rule_ID", "Data_Element", "Severity", "Status", "Failed_Records"]]
        ),
        "",
    ]
    path = REPORTS_DIR / "DATA_QUALITY_SUMMARY.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def write_dashboard(
    before: pd.DataFrame,
    after: pd.DataFrame,
    before_dim: pd.DataFrame,
    after_dim: pd.DataFrame,
    before_overall: float,
    after_overall: float,
    issues_before: pd.DataFrame,
    issues_after: pd.DataFrame,
) -> None:
    """Write Power BI-ready CSV and Excel extracts from generated results only."""
    DASHBOARD_DIR.mkdir(parents=True, exist_ok=True)

    overall = pd.DataFrame(
        [
            {"snapshot": "Before Remediation", "snapshot_order": 1, "overall_dq_score": before_overall},
            {"snapshot": "After Remediation", "snapshot_order": 2, "overall_dq_score": after_overall},
        ]
    )
    overall.to_csv(DASHBOARD_DIR / "overall_dq_score.csv", index=False)

    dim_before = before_dim.assign(snapshot="Before Remediation", snapshot_order=1)
    dim_after = after_dim.assign(snapshot="After Remediation", snapshot_order=2)
    dimensions = pd.concat([dim_before, dim_after], ignore_index=True)
    dimensions.to_csv(DASHBOARD_DIR / "dimension_scores.csv", index=False)

    rules = pd.concat(
        [
            before.assign(snapshot="Before Remediation", snapshot_order=1),
            after.assign(snapshot="After Remediation", snapshot_order=2),
        ],
        ignore_index=True,
    )
    rules.to_csv(DASHBOARD_DIR / "rule_results.csv", index=False)

    issues = pd.concat([issues_before, issues_after], ignore_index=True)
    issues.to_csv(DASHBOARD_DIR / "issues.csv", index=False)

    open_issues = issues_after.copy()
    open_issues["is_open"] = open_issues["Status"].isin(["Open", "In Progress"])
    open_issues.to_csv(DASHBOARD_DIR / "open_issues.csv", index=False)

    by_severity = (
        issues_after.groupby(["Severity", "Status"], as_index=False)
        .agg(issue_count=("Issue_ID", "count"), failed_records=("Failed_Records", "sum"))
    )
    by_severity.to_csv(DASHBOARD_DIR / "issues_by_severity.csv", index=False)

    before_after = pd.DataFrame(
        [
            {
                "metric": "Overall Data Quality Score",
                "before_pct": before_overall,
                "after_pct": after_overall,
                "delta_pct": round(after_overall - before_overall, 2),
            }
        ]
    )
    before_after.to_csv(DASHBOARD_DIR / "before_after.csv", index=False)

    trend = overall.rename(columns={"snapshot": "period"})
    trend.to_csv(DASHBOARD_DIR / "dq_trend.csv", index=False)

    excel_path = DASHBOARD_DIR / "dq_dashboard_source.xlsx"
    with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
        overall.to_excel(writer, sheet_name="overall_dq_score", index=False)
        dimensions.to_excel(writer, sheet_name="dimension_scores", index=False)
        rules.to_excel(writer, sheet_name="rule_results", index=False)
        issues.to_excel(writer, sheet_name="issues", index=False)
        by_severity.to_excel(writer, sheet_name="issues_by_severity", index=False)
        before_after.to_excel(writer, sheet_name="before_after", index=False)
        trend.to_excel(writer, sheet_name="dq_trend", index=False)
