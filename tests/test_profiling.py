"""Tests for profiling metrics."""

from __future__ import annotations

import pandas as pd

from src.profiling.profiler import profile_dataframe


def test_profiler_counts_nulls_and_uniqueness():
    df = pd.DataFrame(
        {
            "Patient_ID": ["PAT-000001", "PAT-000001", None],
            "Gender": ["Female", "Male", "Female"],
        }
    )
    profile = profile_dataframe(df, "patients").set_index("column")
    assert profile.loc["Patient_ID", "row_count"] == 3
    assert profile.loc["Patient_ID", "null_count"] == 1
    assert profile.loc["Patient_ID", "unique_count"] == 1
    assert profile.loc["Gender", "completeness_pct"] == 100.0
