"""Markdown helpers that do not require the optional tabulate dependency."""

from __future__ import annotations

import pandas as pd


def dataframe_to_markdown(df: pd.DataFrame) -> str:
    """Render a DataFrame as a GitHub-flavoured markdown table."""
    if df.empty:
        return "_No rows._"
    columns = [str(col) for col in df.columns]
    header = "| " + " | ".join(columns) + " |"
    sep = "| " + " | ".join("---" for _ in columns) + " |"
    body = []
    for _, row in df.iterrows():
        cells = ["" if pd.isna(value) else str(value) for value in row.tolist()]
        body.append("| " + " | ".join(cells) + " |")
    return "\n".join([header, sep, *body])
