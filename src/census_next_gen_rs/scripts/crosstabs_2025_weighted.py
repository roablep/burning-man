#!/usr/bin/env python3
"""Generate weighted crosstabs for the 2025 census dataset."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate weighted crosstabs for the 2025 census dataset.",
    )
    parser.add_argument(
        "--input",
        default="/Users/peter/Downloads/census2025_cleaned_weighted.xlsx",
        help="Path to the weighted 2025 XLSX file.",
    )
    parser.add_argument(
        "--sheet",
        default=0,
        help="Sheet name or index (defaults to first sheet).",
    )
    parser.add_argument(
        "--output-dir",
        default="reports",
        help="Directory for output files.",
    )
    return parser.parse_args()


def add_age_band(df: pd.DataFrame) -> pd.DataFrame:
    bins = [-np.inf, 22, 28, 34, 39, 49, 59, np.inf]
    labels = ["<=22", "23-28", "29-34", "35-39", "40-49", "50-59", "60+"]
    df = df.copy()
    df["age_band"] = pd.cut(df["age"], bins=bins, labels=labels, right=True)
    return df


def add_nburns_bucket(df: pd.DataFrame) -> pd.DataFrame:
    def bucket(val: float | int | None) -> str:
        if pd.isna(val):
            return "missing"
        try:
            n = int(val)
        except (TypeError, ValueError):
            return "missing"
        if n <= 0:
            return "0"
        if n == 1:
            return "1"
        if n == 2:
            return "2"
        if n == 3:
            return "3"
        if n == 4:
            return "4"
        return "5+"

    df = df.copy()
    df["nburns_bucket"] = df["nburns"].apply(bucket)
    return df


def weighted_pivot(
    df: pd.DataFrame,
    index: str,
    columns: str,
    values: str,
) -> pd.DataFrame:
    pivot = pd.pivot_table(
        df,
        index=index,
        columns=columns,
        values=values,
        aggfunc="sum",
        fill_value=0.0,
        observed=False,
    )
    # Ensure stable column order where possible
    return pivot


def row_percentages(pivot: pd.DataFrame) -> pd.DataFrame:
    row_sums = pivot.sum(axis=1).replace(0, np.nan)
    pct = pivot.div(row_sums, axis=0) * 100.0
    return pct.fillna(0.0)


def write_csv(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path)


def flatten_columns(df: pd.DataFrame, sep: str = "__") -> pd.DataFrame:
    if not isinstance(df.columns, pd.MultiIndex):
        return df.copy()
    flat = df.copy()
    flat.columns = [sep.join(map(str, col)).strip() for col in flat.columns]
    return flat


def write_markdown_table(df: pd.DataFrame, path: Path, title: str) -> None:
    def esc(val: object) -> str:
        text = str(val)
        return text.replace("|", "\\|").replace("\n", " ")

    lines: list[str] = []
    lines.append(f"## {title}")
    lines.append("")

    header = [""] + [esc(col) for col in df.columns]
    lines.append("| " + " | ".join(header) + " |")
    lines.append("| " + " | ".join(["---"] * len(header)) + " |")

    for idx, row in df.iterrows():
        cells = [esc(idx)] + [esc(f"{val:.2f}") for val in row.values]
        lines.append("| " + " | ".join(cells) + " |")

    lines.append("")

    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        existing = path.read_text(encoding="utf-8")
        path.write_text(existing + "\n" + "\n".join(lines), encoding="utf-8")
    else:
        path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    input_path = Path(args.input)
    output_dir = Path(args.output_dir)

    df = pd.read_excel(input_path, sheet_name=args.sheet)
    df = add_age_band(df)
    df = add_nburns_bucket(df)

    df["campPlaced_clean"] = df["campPlaced"].fillna("missing")

    camp_order = ["yes", "no", "dontKnow", "missing"]
    nburns_order = ["0", "1", "2", "3", "4", "5+", "missing"]
    age_order = ["<=22", "23-28", "29-34", "35-39", "40-49", "50-59", "60+"]

    report_path = output_dir / "census2025_weighted_crosstabs.md"
    if report_path.exists():
        report_path.unlink()

    print("Generating weighted crosstabs...")

    for camp in camp_order:
        subset = df.loc[df["campPlaced_clean"] == camp]
        pivot = weighted_pivot(
            subset,
            index="age_band",
            columns="nburns_bucket",
            values="weights",
        )

        # Reindex for stable ordering
        pivot = pivot.reindex(index=age_order).fillna(0.0)
        pivot = pivot.reindex(columns=nburns_order).fillna(0.0)

        pct = row_percentages(pivot)

        counts_csv = output_dir / f"census2025_crosstab_counts_campPlaced_{camp}.csv"
        pct_csv = output_dir / f"census2025_crosstab_pct_campPlaced_{camp}.csv"

        write_csv(pivot, counts_csv)
        write_csv(pct, pct_csv)

        write_markdown_table(
            pivot,
            report_path,
            title=f"Weighted Counts — campPlaced={camp}",
        )
        write_markdown_table(
            pct,
            report_path,
            title=f"Row % (within age band) — campPlaced={camp}",
        )

        print(f"campPlaced={camp}:")
        print(pivot)
        print("")

    # Combined table with campPlaced as an additional column level
    combined = pd.pivot_table(
        df,
        index="age_band",
        columns=["campPlaced_clean", "nburns_bucket"],
        values="weights",
        aggfunc="sum",
        fill_value=0.0,
        observed=False,
    )
    combined = combined.reindex(index=age_order).fillna(0.0)
    combined = combined.reindex(columns=camp_order, level=0).fillna(0.0)
    combined = combined.reindex(columns=nburns_order, level=1).fillna(0.0)

    combined_pct = row_percentages(combined)

    combined_counts_csv = output_dir / "census2025_crosstab_counts_all_campPlaced.csv"
    combined_pct_csv = output_dir / "census2025_crosstab_pct_all_campPlaced.csv"

    write_csv(combined, combined_counts_csv)
    write_csv(combined_pct, combined_pct_csv)

    combined_flat = flatten_columns(combined)
    combined_pct_flat = flatten_columns(combined_pct)

    combined_counts_flat_csv = (
        output_dir / "census2025_crosstab_counts_all_campPlaced_flat.csv"
    )
    combined_pct_flat_csv = (
        output_dir / "census2025_crosstab_pct_all_campPlaced_flat.csv"
    )

    write_csv(combined_flat, combined_counts_flat_csv)
    write_csv(combined_pct_flat, combined_pct_flat_csv)

    write_markdown_table(
        combined,
        report_path,
        title="Weighted Counts — campPlaced x nburns_bucket (combined)",
    )
    write_markdown_table(
        combined_pct,
        report_path,
        title="Row % (within age band) — campPlaced x nburns_bucket (combined)",
    )
    write_markdown_table(
        combined_flat,
        report_path,
        title="Weighted Counts — campPlaced x nburns_bucket (combined, flat)",
    )
    write_markdown_table(
        combined_pct_flat,
        report_path,
        title="Row % (within age band) — campPlaced x nburns_bucket (combined, flat)",
    )

    print("combined campPlaced x nburns_bucket:")
    print(combined)
    print("")
    print("combined campPlaced x nburns_bucket (flat):")
    print(combined_flat)
    print("")

    print(f"Wrote markdown report to {report_path}")
    print(f"Wrote CSVs to {output_dir}")


if __name__ == "__main__":
    main()
