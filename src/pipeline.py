"""End-to-end workflow: generate → profile → validate → remediate → re-test → report."""

from __future__ import annotations

import pandas as pd

from src.config import PROCESSED_DIR, REPORTS_DIR
from src.generate_data import generate_all
from src.profiling.profiler import profile_all
from src.quality_rules.engine import load_cde_catalog, load_rule_catalog
from src.remediation.remediator import remediate, write_processed
from src.reporting.export import write_comparison, write_dashboard, write_issues, write_summary_markdown
from src.validation.run_checks import run_checks


def run_pipeline() -> dict:
    generate_all()
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(load_cde_catalog()).to_csv(REPORTS_DIR / "cde_catalog.csv", index=False)
    pd.DataFrame(load_rule_catalog()).to_csv(REPORTS_DIR / "dq_rule_catalog.csv", index=False)
    before = run_checks(stage="raw")
    profile_all(
        {
            "patients": before["datasets"]["patients"],
            "providers": before["datasets"]["providers"],
            "facilities": before["datasets"]["facilities"],
            "encounters": before["datasets"]["encounters"],
        }
    )
    issues_before = write_issues(before["results"], stage="raw")

    processed, log = remediate(before["datasets"])
    write_processed(processed, log)
    log.to_csv(REPORTS_DIR / "remediation_log.csv", index=False)

    after = run_checks(stage="processed")
    issues_after = write_issues(after["results"], stage="processed")
    comparison = write_comparison(
        before["results"], after["results"], before["overall"], after["overall"]
    )
    write_summary_markdown(
        before["results"],
        after["results"],
        before["dimensions"],
        after["dimensions"],
        before["overall"],
        after["overall"],
        comparison,
        issues_before,
        issues_after,
    )
    write_dashboard(
        before["results"],
        after["results"],
        before["dimensions"],
        after["dimensions"],
        before["overall"],
        after["overall"],
        issues_before,
        issues_after,
    )
    return {
        "before_overall": before["overall"],
        "after_overall": after["overall"],
        "before_results": before["results"],
        "after_results": after["results"],
        "comparison": comparison,
        "remediation_actions": len(log),
        "processed_dir": PROCESSED_DIR,
        "reports_dir": REPORTS_DIR,
    }


def main() -> None:
    outcome = run_pipeline()
    print("Healthcare Data Quality Management pipeline complete.")
    print(f"Before remediation overall score: {outcome['before_overall']}%")
    print(f"After remediation overall score:  {outcome['after_overall']}%")
    print(f"Remediation actions logged:       {outcome['remediation_actions']}")
    print(f"Reports: {outcome['reports_dir']}")
    print()
    print(outcome["before_results"][["rule_id", "records_checked", "passed", "failed", "score"]].to_string(index=False))
    print()
    print("After:")
    print(outcome["after_results"][["rule_id", "records_checked", "passed", "failed", "score"]].to_string(index=False))


if __name__ == "__main__":
    main()
