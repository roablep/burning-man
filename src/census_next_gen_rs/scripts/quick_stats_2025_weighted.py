#!/usr/bin/env python3
"""Generate weighted quick stats for the 2025 census dataset."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate weighted quick stats for the 2025 census dataset.",
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
        "--output",
        default="reports/census2025_weighted_quick_stats.md",
        help="Output markdown path.",
    )
    return parser.parse_args()


def build_age_band_table(df: pd.DataFrame) -> pd.DataFrame:
    bins = [-np.inf, 22, 28, 34, 39, 49, 59, np.inf]
    labels = ["<=22", "23-28", "29-34", "35-39", "40-49", "50-59", "60+"]

    df = df.copy()
    df["age_band"] = pd.cut(df["age"], bins=bins, labels=labels, right=True)

    age_band_weighted = df.groupby("age_band", dropna=False, observed=False)[
        "weights"
    ].sum()
    total_weight = age_band_weighted.dropna().sum()

    rows = []
    for band in labels:
        weighted_count = float(age_band_weighted.get(band, 0.0))
        weighted_pct = (weighted_count / total_weight * 100.0) if total_weight > 0 else 0.0
        unweighted_n = int(df.loc[df["age_band"] == band].shape[0])
        rows.append((band, weighted_count, weighted_pct, unweighted_n))

    return pd.DataFrame(
        rows,
        columns=["age_band", "weighted_count", "weighted_pct", "unweighted_n"],
    )


def build_camp_table(df: pd.DataFrame) -> pd.DataFrame:
    camp = df["campPlaced"].fillna("missing")
    camp_weighted = df.groupby(camp)["weights"].sum()
    camp_total = camp_weighted.sum()

    rows = []
    for val in ["yes", "no", "dontKnow", "missing"]:
        weighted_count = float(camp_weighted.get(val, 0.0))
        weighted_pct = (weighted_count / camp_total * 100.0) if camp_total > 0 else 0.0
        unweighted_n = int((camp == val).sum())
        rows.append((val, weighted_count, weighted_pct, unweighted_n))

    return pd.DataFrame(
        rows,
        columns=["campPlaced", "weighted_count", "weighted_pct", "unweighted_n"],
    )


def main() -> None:
    args = parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output)

    df = pd.read_excel(input_path, sheet_name=args.sheet)

    age_table = build_age_band_table(df)
    camp_table = build_camp_table(df)

    lines: list[str] = []
    lines.append("# Census 2025 Weighted Quick Stats")
    lines.append("")
    lines.append(f"- Source file: `{input_path}`")
    lines.append(f"- Rows: `{len(df)}`")
    lines.append(
        "- Weights: mean "
        f"{df['weights'].mean():.3f}, min {df['weights'].min():.6f}, "
        f"max {df['weights'].max():.6f}"
    )
    lines.append("")
    lines.append("## Weighted Age Band Distribution")
    lines.append("")
    lines.append("Age bands: <=22, 23-28, 29-34, 35-39, 40-49, 50-59, 60+")
    lines.append("")
    lines.append("| age_band | weighted_count | weighted_pct | unweighted_n |")
    lines.append("|---|---|---|---|")
    for _, row in age_table.iterrows():
        lines.append(
            f"| {row['age_band']} | {row['weighted_count']:.2f} | "
            f"{row['weighted_pct']:.2f}% | {int(row['unweighted_n'])} |"
        )

    lines.append("")
    lines.append("## Weighted Camp Placement (campPlaced)")
    lines.append("")
    lines.append("| campPlaced | weighted_count | weighted_pct | unweighted_n |")
    lines.append("|---|---|---|---|")
    for _, row in camp_table.iterrows():
        lines.append(
            f"| {row['campPlaced']} | {row['weighted_count']:.2f} | "
            f"{row['weighted_pct']:.2f}% | {int(row['unweighted_n'])} |"
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote quick stats to {output_path}")


if __name__ == "__main__":
    main()
