#!/usr/bin/env python3
"""Generate a human-friendly briefing for the 2025 cohort retention analysis."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Tuple

import numpy as np
import pandas as pd

AGE_LABELS = ["<=22", "23-28", "29-34", "35-39", "40-49", "50-59", "60+"]
SMALL_N_THRESHOLD = 30.0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a briefing for 2025 cohort retention analysis.",
    )
    parser.add_argument(
        "--cohort-retention",
        default="reports/census_next_gen_rs/census2025_cohort_retention.csv",
        help="Path to cohort retention CSV.",
    )
    parser.add_argument(
        "--cohort-trends",
        default="reports/census_next_gen_rs/census2025_cohort_trends.csv",
        help="Path to cohort trends CSV.",
    )
    parser.add_argument(
        "--under30-share",
        default="reports/census_next_gen_rs/census2025_under30_share.csv",
        help="Path to under-30 share CSV.",
    )
    parser.add_argument(
        "--output-md",
        default="reports/census_next_gen_rs/census2025_cohort_analysis_briefing.md",
        help="Output markdown path.",
    )
    return parser.parse_args()


def load_tables(
    retention_path: str,
    trends_path: str,
    under30_path: str,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    retention = pd.read_csv(retention_path)
    trends = pd.read_csv(trends_path)
    under30 = pd.read_csv(under30_path)
    return retention, trends, under30


def compute_age_band_gaps(retention: pd.DataFrame) -> pd.DataFrame:
    df = retention.copy()
    df = df.loc[df["campPlaced"].isin(["yes", "no"])]
    df["age_band"] = pd.Categorical(df["age_band"], categories=AGE_LABELS, ordered=True)
    pivot = df.pivot_table(
        index="age_band",
        columns="campPlaced",
        values="weighted_return_rate",
        aggfunc="mean",
    )
    pivot["gap_yes_minus_no"] = pivot["yes"] - pivot["no"]
    return pivot.reset_index()


def compute_top_bottom_cells(retention: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    df = retention.copy()
    df = df.loc[df["campPlaced"].isin(["yes", "no"])]
    df = df.sort_values("weighted_return_rate", ascending=False)
    top = df.head(5)
    bottom = df.tail(5).sort_values("weighted_return_rate", ascending=True)
    return top, bottom


def compute_trend_slope(trends: pd.DataFrame) -> Tuple[float, int]:
    df = trends.copy()
    df = df.loc[(df["segment"] == "overall") & (df["campPlaced"] == "all")]
    df = df.sort_values("cohort_year")
    if df.empty:
        return 0.0, 0
    x = df["cohort_year"].to_numpy(dtype=float)
    y = df["weighted_return_rate"].to_numpy(dtype=float)
    slope = np.polyfit(x, y, 1)[0] if len(df) > 1 else 0.0
    return float(slope), len(df)


def compute_under30_slope(under30: pd.DataFrame) -> Tuple[float, int]:
    df = under30.copy()
    df = df.loc[df["campPlaced"] == "all"]
    df = df.sort_values("cohort_year")
    if df.empty:
        return 0.0, 0
    x = df["cohort_year"].to_numpy(dtype=float)
    y = df["under30_share"].to_numpy(dtype=float)
    slope = np.polyfit(x, y, 1)[0] if len(df) > 1 else 0.0
    return float(slope), len(df)


def small_n_cells(retention: pd.DataFrame) -> pd.DataFrame:
    df = retention.copy()
    df = df.loc[df["weighted_count"] < SMALL_N_THRESHOLD]
    return df.sort_values(["age_band", "campPlaced"])


def build_analysis_prompt(
    top: pd.DataFrame,
    bottom: pd.DataFrame,
    gaps: pd.DataFrame,
    trend_slope: float,
    under30_slope: float,
) -> str:
    lines: list[str] = []
    lines.append("You are a human analyst reviewing the 2025 Burning Man cohort data.")
    lines.append("Write an insight memo (short paragraphs + bullets) explaining:")
    lines.append("- Where retention is strongest and weakest")
    lines.append("- CampPlaced effect (yes vs no)")
    lines.append("- Under-30 trends")
    lines.append("- Key caveats and small-N warnings")
    lines.append("")
    lines.append("Key stats (Global linear trends across all cohorts):")
    lines.append(f"- Overall retention trend slope: {trend_slope:.6f} per cohort year")
    lines.append(f"- Under-30 share slope: {under30_slope:.6f} per cohort year")
    lines.append("")
    lines.append("Top retention cells (Highest likelihood of return; age_band, campPlaced, rate):")
    for _, row in top.iterrows():
        lines.append(
            f"- {row['age_band']} / {row['campPlaced']}: "
            f"{row['weighted_return_rate']:.4f} (w={row['weighted_count']:.2f})"
        )
    lines.append("")
    lines.append("Lowest retention cells (Lowest return rates; age_band, campPlaced, rate):")
    for _, row in bottom.iterrows():
        lines.append(
            f"- {row['age_band']} / {row['campPlaced']}: "
            f"{row['weighted_return_rate']:.4f} (w={row['weighted_count']:.2f})"
        )
    lines.append("")
    lines.append("CampPlaced gaps (Delta between placed and unplaced camps; yes - no) by age_band:")
    for _, row in gaps.iterrows():
        if pd.isna(row.get("gap_yes_minus_no")):
            continue
        lines.append(f"- {row['age_band']}: {row['gap_yes_minus_no']:.4f}")
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    retention, trends, under30 = load_tables(
        args.cohort_retention,
        args.cohort_trends,
        args.under30_share,
    )

    top, bottom = compute_top_bottom_cells(retention)
    gaps = compute_age_band_gaps(retention)
    trend_slope, trend_n = compute_trend_slope(trends)
    under30_slope, under30_n = compute_under30_slope(under30)
    small_n = small_n_cells(retention)

    lines: list[str] = []
    lines.append("# Census 2025 Cohort Analysis Briefing")
    lines.append("")
    lines.append("## Highlights")
    lines.append("Summary of global linear trends across all cohorts for retention and youth participation.")
    lines.append("")
    lines.append(
        f"- Overall retention trend slope (overall, campPlaced=all): "
        f"`{trend_slope:.6f}` per cohort year (n={trend_n})"
    )
    lines.append(
        f"- Under-30 share slope (campPlaced=all): "
        f"`{under30_slope:.6f}` per cohort year (n={under30_n})"
    )
    lines.append("")
    lines.append("## Top Retention Cells")
    lines.append("The demographic segments (age and camp status) with the highest likelihood of returning to Black Rock City.")
    lines.append("")
    for _, row in top.iterrows():
        lines.append(
            f"- {row['age_band']} / {row['campPlaced']}: "
            f"{row['weighted_return_rate']:.4f} (w={row['weighted_count']:.2f})"
        )
    lines.append("")
    lines.append("## Lowest Retention Cells")
    lines.append("Segments with the lowest return rates, highlighting where the community may be losing members.")
    lines.append("")
    for _, row in bottom.iterrows():
        lines.append(
            f"- {row['age_band']} / {row['campPlaced']}: "
            f"{row['weighted_return_rate']:.4f} (w={row['weighted_count']:.2f})"
        )
    lines.append("")
    lines.append("## CampPlaced Gaps (Yes - No)")
    lines.append("The delta in retention rates between those in placed camps ('yes') versus those not ('no'). Positive values suggest placement correlates with higher retention.")
    lines.append("")
    for _, row in gaps.iterrows():
        if pd.isna(row.get("gap_yes_minus_no")):
            continue
        lines.append(f"- {row['age_band']}: {row['gap_yes_minus_no']:.4f}")
    lines.append("")
    lines.append("## Small-N Warnings (weighted_count < 30)")
    lines.append("Data points where the weighted sample size is below 30, indicating results should be interpreted with caution due to high variance.")
    lines.append("")
    if small_n.empty:
        lines.append("- None")
    else:
        for _, row in small_n.iterrows():
            lines.append(
                f"- {row['cohort_year']} / {row['age_band']} / {row['campPlaced']}: "
                f"w={row['weighted_count']:.2f}, n={int(row['unweighted_n'])}"
            )
    lines.append("")
    lines.append("## Analyze This Prompt")
    lines.append("")
    lines.append("```text")
    lines.append(build_analysis_prompt(top, bottom, gaps, trend_slope, under30_slope))
    lines.append("```")

    output_path = Path(args.output_md)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")

    print("Cohort analysis briefing written.")
    print(f"- {output_path}")


if __name__ == "__main__":
    main()
