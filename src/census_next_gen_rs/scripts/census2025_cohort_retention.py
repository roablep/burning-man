#!/usr/bin/env python3
"""Generate weighted cohort retention tables for the 2025 census dataset.

Methodology (high-level):
1) Identify attended-years columns like attendedYears.YYYY (e.g., attendedYears.1990Baker).
2) For each year, collapse multiple columns into a single 0/1 indicator by taking max
   across that year's columns (any attendance counts as attended).
3) Define cohort_year as the earliest year with attended == 1 for each respondent.
4) Define return_next_year as whether the respondent attended cohort_year + 1.
   If the next-year column does not exist, return_next_year is NaN and excluded.
5) Segment to age bands and campPlaced (yes/no only) and compute:
   - weighted_count = sum(weights)
   - weighted_return_rate = sum(weights * return_next_year) / sum(weights)
   - unweighted_n = row count
Note: This analysis is computed from the 2025 census respondent sample only. For recent
cohorts (e.g., 2024), "return_next_year" is right-censored and biased upward because the
sample already consists of 2025 attendees. Interpret near-100% return rates for the most
recent cohort as a sampling artifact, not true population retention.
Outputs:
- CSV: cohort_year x age_band x campPlaced table
- Markdown: summary + aggregated age_band x campPlaced table
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import numpy as np
import pandas as pd

AGE_BINS = [-np.inf, 22, 28, 34, 39, 49, 59, np.inf]
AGE_LABELS = ["<=22", "23-28", "29-34", "35-39", "40-49", "50-59", "60+"]
ATTENDED_PREFIX = "attendedYears."


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate weighted cohort retention tables for the 2025 census dataset.",
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
        "--output-csv",
        default="reports/census_next_gen_rs/census2025_cohort_retention.csv",
        help="Output CSV path for cohort table.",
    )
    parser.add_argument(
        "--output-md",
        default="reports/census_next_gen_rs/census2025_cohort_retention.md",
        help="Output markdown summary path.",
    )
    return parser.parse_args()


def normalize_sheet(sheet: object) -> object:
    if isinstance(sheet, str):
        stripped = sheet.strip()
        if stripped.isdigit():
            return int(stripped)
        return stripped
    return sheet


def discover_attended_year_columns(df: pd.DataFrame) -> dict[int, list[str]]:
    year_map: dict[int, list[str]] = {}
    pattern = re.compile(r"^attendedYears\.(\d{4})")
    for column in df.columns:
        match = pattern.match(column)
        if not match:
            continue
        year = int(match.group(1))
        year_map.setdefault(year, []).append(column)
    return dict(sorted(year_map.items()))


def build_attended_year_matrix(
    df: pd.DataFrame,
    year_map: dict[int, list[str]],
) -> pd.DataFrame:
    year_data: dict[int, pd.Series] = {}
    for year, columns in year_map.items():
        if len(columns) == 1:
            series = df[columns[0]]
        else:
            series = df[columns].max(axis=1, skipna=True)
        year_data[year] = series.fillna(0)
    return pd.DataFrame(year_data)


def compute_cohort_year(attended: pd.DataFrame) -> pd.Series:
    years = np.array(attended.columns, dtype=float)
    matrix = attended.to_numpy()
    attended_mask = matrix == 1
    cohort_year = np.full(matrix.shape[0], np.nan)
    valid = attended_mask.any(axis=1)
    if valid.any():
        cohort = np.where(attended_mask[valid], years, np.nan)
        cohort_year[valid] = np.nanmin(cohort, axis=1)
    return pd.Series(cohort_year, index=attended.index)


def compute_return_next_year(
    cohort_year: pd.Series,
    attended: pd.DataFrame,
) -> pd.Series:
    year_set = set(attended.columns)
    values: list[float] = []
    for idx, year in cohort_year.items():
        if pd.isna(year):
            values.append(np.nan)
            continue
        next_year = int(year) + 1
        if next_year not in year_set:
            values.append(np.nan)
            continue
        values.append(1.0 if attended.loc[idx, next_year] == 1 else 0.0)
    return pd.Series(values, index=cohort_year.index)


def build_age_band(age: pd.Series) -> pd.Series:
    age_band = pd.cut(age, bins=AGE_BINS, labels=AGE_LABELS, right=True)
    return pd.Categorical(age_band, categories=AGE_LABELS, ordered=True)


def prepare_cohort_dataframe(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[int, list[str]]]:
    year_map = discover_attended_year_columns(df)
    attended = build_attended_year_matrix(df, year_map)

    df = df.copy()
    df["cohort_year"] = compute_cohort_year(attended)
    df["return_next_year"] = compute_return_next_year(df["cohort_year"], attended)
    df["age_band"] = build_age_band(df["age"])
    df["campPlaced_clean"] = df["campPlaced"].where(df["campPlaced"].isin(["yes", "no"]))
    return df, year_map


def weighted_return_rate(group: pd.DataFrame) -> float:
    weight = group["weights"].sum()
    if weight == 0:
        return 0.0
    return float((group["weights"] * group["return_next_year"]).sum() / weight)


def build_cohort_table(df: pd.DataFrame) -> pd.DataFrame:
    grouped = df.groupby(
        ["cohort_year", "age_band", "campPlaced_clean"],
        dropna=False,
        observed=False,
    )
    rows = []
    for keys, group in grouped:
        cohort_year, age_band, camp = keys
        if pd.isna(cohort_year) or pd.isna(age_band) or pd.isna(camp):
            continue
        rows.append(
            {
                "cohort_year": int(cohort_year),
                "age_band": age_band,
                "campPlaced": camp,
                "weighted_count": float(group["weights"].sum()),
                "weighted_return_rate": weighted_return_rate(group),
                "unweighted_n": int(group.shape[0]),
            }
        )
    table = pd.DataFrame(rows)
    if not table.empty:
        table["age_band"] = pd.Categorical(
            table["age_band"], categories=AGE_LABELS, ordered=True
        )
    return table.sort_values(
        ["cohort_year", "age_band", "campPlaced"],
        ignore_index=True,
    )


def build_age_band_camp_table(df: pd.DataFrame) -> pd.DataFrame:
    grouped = df.groupby(["age_band", "campPlaced_clean"], dropna=False, observed=False)
    rows = []
    for keys, group in grouped:
        age_band, camp = keys
        if pd.isna(age_band) or pd.isna(camp):
            continue
        rows.append(
            {
                "age_band": age_band,
                "campPlaced": camp,
                "weighted_count": float(group["weights"].sum()),
                "weighted_return_rate": weighted_return_rate(group),
                "unweighted_n": int(group.shape[0]),
            }
        )
    table = pd.DataFrame(rows)
    if not table.empty:
        table["age_band"] = pd.Categorical(
            table["age_band"], categories=AGE_LABELS, ordered=True
        )
    return table.sort_values(
        ["age_band", "campPlaced"],
        ignore_index=True,
    )


def build_markdown_summary(
    df: pd.DataFrame,
    year_map: dict[int, list[str]],
    cohort_table: pd.DataFrame,
    age_band_table: pd.DataFrame,
    input_path: Path,
) -> str:
    total_rows = len(df)
    missing_cohort = int(df["cohort_year"].isna().sum())
    missing_return = int(df["return_next_year"].isna().sum())
    missing_age = int(df["age_band"].isna().sum())
    excluded_camp = int(df["campPlaced_clean"].isna().sum())

    lines: list[str] = []
    lines.append("# Census 2025 Weighted Cohort Retention")
    lines.append("")
    lines.append(f"- Source file: `{input_path}`")
    lines.append(f"- Rows: `{total_rows}`")
    if year_map:
        lines.append(f"- Attended years: `{min(year_map)}-{max(year_map)}`")
    lines.append("")
    lines.append("## Data Hygiene")
    lines.append("")
    lines.append(f"- Missing cohort year: `{missing_cohort}`")
    lines.append(f"- Missing return-next-year: `{missing_return}`")
    lines.append(f"- Missing/invalid age band: `{missing_age}`")
    lines.append(f"- Excluded campPlaced (dontKnow/missing): `{excluded_camp}`")
    lines.append("")
    lines.append("## Second-Year Return Rate By Age Band (campPlaced)")
    lines.append("")
    lines.append("| age_band | campPlaced | weighted_count | weighted_return_rate | unweighted_n |")
    lines.append("|---|---|---|---|---|")
    for _, row in age_band_table.iterrows():
        lines.append(
            f"| {row['age_band']} | {row['campPlaced']} | {row['weighted_count']:.2f} | "
            f"{row['weighted_return_rate']:.4f} | {int(row['unweighted_n'])} |"
        )
    lines.append("")
    lines.append("## Cohort Table")
    lines.append("")
    lines.append(
        "Full cohort table saved to CSV. Columns: "
        "`cohort_year`, `age_band`, `campPlaced`, `weighted_count`, "
        "`weighted_return_rate`, `unweighted_n`."
    )
    lines.append(f"- Rows: `{len(cohort_table)}`")
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    input_path = Path(args.input)
    output_csv = Path(args.output_csv)
    output_md = Path(args.output_md)

    sheet = normalize_sheet(args.sheet)
    df = pd.read_excel(input_path, sheet_name=sheet)
    df, year_map = prepare_cohort_dataframe(df)

    base_mask = df["cohort_year"].notna() & df["return_next_year"].notna()
    segmented_mask = base_mask & df["age_band"].notna() & df["campPlaced_clean"].notna()
    cohort_table = build_cohort_table(df.loc[segmented_mask])
    age_band_table = build_age_band_camp_table(df.loc[segmented_mask])

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    cohort_table.to_csv(output_csv, index=False)

    output_md.parent.mkdir(parents=True, exist_ok=True)
    summary = build_markdown_summary(
        df,
        year_map,
        cohort_table,
        age_band_table,
        input_path,
    )
    output_md.write_text(summary, encoding="utf-8")

    print("Census 2025 cohort retention outputs written.")
    print(f"- CSV: {output_csv}")
    print(f"- Markdown: {output_md}")
    print("")
    print("Second-year return rate by age band (campPlaced):")
    if age_band_table.empty:
        print("  (no rows after filtering)")
    else:
        display_table = age_band_table.copy()
        display_table["weighted_return_rate"] = display_table["weighted_return_rate"].map(
            lambda value: f"{value:.4f}"
        )
        print(display_table.to_string(index=False))


if __name__ == "__main__":
    main()
