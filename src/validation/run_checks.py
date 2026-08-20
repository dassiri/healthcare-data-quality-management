"""Load datasets and execute the data quality rule catalog."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.config import PROCESSED_DIR, RAW_DIR, REFERENCE_DIR, REPORTS_DIR
from src.quality_rules.engine import load_rule_catalog, run_rules


def load_datasets(stage: str = "raw") -> dict[str, pd.DataFrame]:
    """Load synthetic tables for `raw` or `processed` stage."""
    base = RAW_DIR if stage == "raw" else PROCESSED_DIR
    required = ["patients", "providers", "facilities", "encounters"]
    missing = [name for name in required if not (base / f"{name}.csv").exists()]
    if missing:
        raise FileNotFoundError(
            f"Missing {stage} files {missing}. Run `python -m src.generate_data` "
            "and, for processed data, `python -m src.pipeline`."
        )
    datasets = {name: pd.read_csv(base / f"{name}.csv", dtype="string") for name in required}
    master_path = REFERENCE_DIR / "facilities_master.csv"
    if stage == "processed" and (base / "facilities_master.csv").exists():
        master_path = base / "facilities_master.csv"
    datasets["facilities_master"] = pd.read_csv(master_path, dtype="string")
    return datasets


def dimension_scores(results: pd.DataFrame) -> pd.DataFrame:
    """Average rule scores by data quality dimension."""
    grouped = (
        results.groupby("dimension", as_index=False)
        .agg(
            rules=("rule_id", "count"),
            records_checked=("records_checked", "sum"),
            passed=("passed", "sum"),
            failed=("failed", "sum"),
            score=("score", "mean"),
        )
        .sort_values("dimension")
    )
    grouped["score"] = grouped["score"].round(2)
    return grouped


def overall_score(results: pd.DataFrame) -> float:
    """Overall score is the unweighted mean of rule-level scores."""
    if results.empty:
        return 0.0
    return round(float(results["score"].mean()), 2)


def export_failures(
    datasets: dict[str, pd.DataFrame],
    masks: dict[str, pd.Series],
    catalog: list[dict],
    output_path: Path,
) -> pd.DataFrame:
    """Write a sample of failing records for each rule."""
    rows = []
    catalog_by_id = {item["rule_id"]: item for item in catalog}
    for rule_id, mask in masks.items():
        meta = catalog_by_id[rule_id]
        df = datasets[meta["dataset"]]
        failed = df.loc[mask].copy()
        if failed.empty:
            continue
        sample = failed.head(25)
        sample = sample.copy()
        sample.insert(0, "rule_id", rule_id)
        sample.insert(1, "data_element", meta["data_element"])
        rows.append(sample)
    if not rows:
        empty = pd.DataFrame(columns=["rule_id", "data_element"])
        empty.to_csv(output_path, index=False)
        return empty
    out = pd.concat(rows, ignore_index=True, sort=False)
    out.to_csv(output_path, index=False)
    return out


def run_checks(stage: str = "raw") -> dict:
    """Execute rules and persist CSV results under reports/."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    datasets = load_datasets(stage)
    results, masks, catalog = run_rules(datasets)
    dim = dimension_scores(results)
    overall = overall_score(results)
    suffix = "before" if stage == "raw" else "after"
    results.to_csv(REPORTS_DIR / f"dq_results_{suffix}.csv", index=False)
    dim.to_csv(REPORTS_DIR / f"dimension_scores_{suffix}.csv", index=False)
    export_failures(
        datasets,
        masks,
        catalog,
        REPORTS_DIR / f"failed_records_{suffix}.csv",
    )
    summary = pd.DataFrame(
        [
            {
                "stage": stage,
                "label": "Before Remediation" if stage == "raw" else "After Remediation",
                "overall_dq_score": overall,
                "rules_executed": len(results),
                "total_failed_records": int(results["failed"].sum()),
            }
        ]
    )
    summary.to_csv(REPORTS_DIR / f"overall_score_{suffix}.csv", index=False)
    return {
        "results": results,
        "dimensions": dim,
        "overall": overall,
        "masks": masks,
        "catalog": catalog,
        "datasets": datasets,
    }


def main() -> None:
    catalog = load_rule_catalog()
    print(f"Executing {len(catalog)} data quality rules against raw synthetic data...")
    outcome = run_checks(stage="raw")
    print(outcome["results"].to_string(index=False))
    print()
    print("Dimension scores")
    print(outcome["dimensions"].to_string(index=False))
    print()
    print(f"Overall Data Quality Score: {outcome['overall']}%")


if __name__ == "__main__":
    main()
