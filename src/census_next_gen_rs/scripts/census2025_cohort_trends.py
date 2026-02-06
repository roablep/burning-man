#!/usr/bin/env python3
"""Generate cohort trend summaries for the 2025 census dataset."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import numpy as np
import pandas as pd

AGE_BINS = [-np.inf, 22, 28, 34, 39, 49, 59, np.inf]
AGE_LABELS = ["<=22", "23-28", "29-34", "35-39", "40-49", "50-59", "60+"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate cohort trend summaries for the 2025 census dataset.",
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
        default="reports/census_next_gen_rs/census2025_cohort_trends.csv",
        help="Output CSV path for cohort trend table.",
    )
    parser.add_argument(
        "--output-under30-csv",
        default="reports/census_next_gen_rs/census2025_under30_share.csv",
        help="Output CSV path for under-30 share table.",
    )
    parser.add_argument(
        "--output-md",
        default="reports/census_next_gen_rs/census2025_cohort_trends.md",
        help="Output markdown summary path.",
    )
    parser.add_argument(
        "--output-firsttimer-camp-csv",
        default="reports/census_next_gen_rs/census2025_firsttimer_camp_share.csv",
        help="Output CSV path for first-timer camp placement share table.",
    )
    parser.add_argument(
        "--output-multiyear-retention-csv",
        default="reports/census_next_gen_rs/census2025_multiyear_retention.csv",
        help="Output CSV path for multi-year retention (pooled across cohorts).",
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


def compute_return_in_offset_year(
    cohort_year: pd.Series,
    attended: pd.DataFrame,
    offset: int,
) -> pd.Series:
    year_set = set(attended.columns)
    values: list[float] = []
    for idx, year in cohort_year.items():
        if pd.isna(year):
            values.append(np.nan)
            continue
        target_year = int(year) + offset
        if target_year not in year_set:
            values.append(np.nan)
            continue
        values.append(1.0 if attended.loc[idx, target_year] == 1 else 0.0)
    return pd.Series(values, index=cohort_year.index)


def compute_return_after_offset(
    cohort_year: pd.Series,
    attended: pd.DataFrame,
    offset: int,
) -> pd.Series:
    year_set = sorted(attended.columns)
    values: list[float] = []
    for idx, year in cohort_year.items():
        if pd.isna(year):
            values.append(np.nan)
            continue
        start_year = int(year) + offset
        future_years = [y for y in year_set if y >= start_year]
        if not future_years:
            values.append(np.nan)
            continue
        attended_any = any(attended.loc[idx, y] == 1 for y in future_years)
        values.append(1.0 if attended_any else 0.0)
    return pd.Series(values, index=cohort_year.index)


def build_age_band(age: pd.Series) -> pd.Series:
    age_band = pd.cut(age, bins=AGE_BINS, labels=AGE_LABELS, right=True)
    return pd.Categorical(age_band, categories=AGE_LABELS, ordered=True)


def prepare_dataframe(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[int, list[str]], pd.DataFrame]:
    year_map = discover_attended_year_columns(df)
    attended = build_attended_year_matrix(df, year_map)

    df = df.copy()
    df["cohort_year"] = compute_cohort_year(attended)

    # Fix: Infer cohort_year for virgins who don't have attendedYears data
    # Virgins responding to the 2025 census are first-time attendees in 2025
    if "virgin" in df.columns and year_map:
        census_year = max(year_map.keys())  # Assume census year is the latest year in data
        is_virgin_no_cohort = (df["virgin"] == "virgin") & df["cohort_year"].isna()
        df.loc[is_virgin_no_cohort, "cohort_year"] = float(census_year)

    df["return_next_year"] = compute_return_next_year(df["cohort_year"], attended)
    df["age_band"] = build_age_band(df["age"])
    df["campPlaced_clean"] = df["campPlaced"].where(df["campPlaced"].isin(["yes", "no"]))
    df["under30"] = df["age_band"].isin(["<=22", "23-28"])
    if "virgin" in df.columns:
        df["first_timer"] = df["virgin"] == "virgin"
    elif "nburns" in df.columns:
        df["first_timer"] = df["nburns"] == 1
    else:
        df["first_timer"] = False
    return df, year_map, attended


def weighted_return_rate(group: pd.DataFrame) -> float:
    weight = group["weights"].sum()
    if weight == 0:
        return 0.0
    return float((group["weights"] * group["return_next_year"]).sum() / weight)


def build_trend_table(df: pd.DataFrame) -> pd.DataFrame:
    segments = {
        "overall": df,
        "under30": df.loc[df["under30"]],
        "age30plus": df.loc[~df["under30"]],
    }
    camp_filters = {
        "all": df,
        "yes": df.loc[df["campPlaced_clean"] == "yes"],
        "no": df.loc[df["campPlaced_clean"] == "no"],
    }

    rows = []
    for segment_name, segment_df in segments.items():
        for camp_label, camp_df in camp_filters.items():
            subset = segment_df.loc[camp_df.index.intersection(segment_df.index)]
            grouped = subset.groupby("cohort_year", dropna=False, observed=False)
            for cohort_year, group in grouped:
                if pd.isna(cohort_year):
                    continue
                rows.append(
                    {
                        "cohort_year": int(cohort_year),
                        "segment": segment_name,
                        "campPlaced": camp_label,
                        "weighted_count": float(group["weights"].sum()),
                        "weighted_return_rate": weighted_return_rate(group),
                        "unweighted_n": int(group.shape[0]),
                    }
                )
    table = pd.DataFrame(rows)
    return table.sort_values(
        ["cohort_year", "segment", "campPlaced"],
        ignore_index=True,
    )


def build_under30_share_table(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for camp_label in ["yes", "no", "all"]:
        if camp_label == "all":
            subset = df
        else:
            subset = df.loc[df["campPlaced_clean"] == camp_label]
        grouped = subset.groupby("cohort_year", dropna=False, observed=False)
        for cohort_year, group in grouped:
            if pd.isna(cohort_year):
                continue
            total_weight = float(group["weights"].sum())
            under30_weight = float(group.loc[group["under30"], "weights"].sum())
            share = (under30_weight / total_weight) if total_weight > 0 else 0.0
            rows.append(
                {
                    "cohort_year": int(cohort_year),
                    "campPlaced": camp_label,
                    "under30_weighted_count": under30_weight,
                    "total_weighted_count": total_weight,
                    "under30_share": share,
                    "unweighted_n": int(group.shape[0]),
                }
            )
    table = pd.DataFrame(rows)
    return table.sort_values(
        ["cohort_year", "campPlaced"],
        ignore_index=True,
    )


def build_multiyear_retention_table(df: pd.DataFrame) -> pd.DataFrame:
    segments = {
        "overall": df,
        "under30": df.loc[df["under30"]],
        "age30plus": df.loc[~df["under30"]],
    }
    rows = []
    metrics = [
        ("return_year_1", "return_1yr"),
        ("return_year_2", "return_2yr"),
        ("return_year_3plus", "return_3plus"),
    ]
    for segment_name, segment_df in segments.items():
        for camp_label in ["yes", "no"]:
            subset = segment_df.loc[segment_df["campPlaced_clean"] == camp_label]
            for column, metric in metrics:
                metric_df = subset.loc[subset[column].notna()]
                if metric_df.empty:
                    continue
                rows.append(
                    {
                        "segment": segment_name,
                        "campPlaced": camp_label,
                        "metric": metric,
                        "weighted_count": float(metric_df["weights"].sum()),
                        "weighted_return_rate": float(
                            (metric_df["weights"] * metric_df[column]).sum()
                            / metric_df["weights"].sum()
                        ),
                        "unweighted_n": int(metric_df.shape[0]),
                    }
                )
    table = pd.DataFrame(rows)
    return table.sort_values(
        ["segment", "campPlaced", "metric"],
        ignore_index=True,
    )


def build_firsttimer_camp_share_table(df: pd.DataFrame) -> pd.DataFrame:
    subset = df.loc[df["first_timer"]]
    subset = subset.loc[subset["campPlaced_clean"].notna()]
    subset = subset.loc[subset["age_band"].notna() & subset["cohort_year"].notna()]

    rows = []
    grouped = subset.groupby(["cohort_year", "age_band"], dropna=False, observed=False)
    for (cohort_year, age_band), group in grouped:
        if pd.isna(cohort_year) or pd.isna(age_band):
            continue
        yes_weight = float(group.loc[group["campPlaced_clean"] == "yes", "weights"].sum())
        no_weight = float(group.loc[group["campPlaced_clean"] == "no", "weights"].sum())
        total_weight = yes_weight + no_weight
        share = (yes_weight / total_weight) if total_weight > 0 else 0.0
        rows.append(
            {
                "cohort_year": int(cohort_year),
                "age_band": age_band,
                "weighted_yes_count": yes_weight,
                "weighted_no_count": no_weight,
                "weighted_total_count": total_weight,
                "camp_placed_share": share,
                "unweighted_n": int(group.shape[0]),
            }
        )
    table = pd.DataFrame(rows)
    if not table.empty:
        table["age_band"] = pd.Categorical(
            table["age_band"], categories=AGE_LABELS, ordered=True
        )
        return table.sort_values(
            ["cohort_year", "age_band"],
            ignore_index=True,
        )
    return table


def build_markdown_summary(
    df: pd.DataFrame,
    year_map: dict[int, list[str]],
    trends: pd.DataFrame,
    under30_share: pd.DataFrame,
    firsttimer_camp_share: pd.DataFrame,
    multiyear_retention: pd.DataFrame,
    input_path: Path,
) -> str:
    total_rows = len(df)
    missing_cohort = int(df["cohort_year"].isna().sum())
    missing_return = int(df["return_next_year"].isna().sum())
    excluded_camp = int(df["campPlaced_clean"].isna().sum())

    lines: list[str] = []
    lines.append("# Census 2025 Cohort Trends")
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
    lines.append(f"- Excluded campPlaced (dontKnow/missing): `{excluded_camp}`")
    lines.append("")
    lines.append("## Trend Table")
    lines.append("")
    lines.append(
        "Saved to CSV with columns: `cohort_year`, `segment`, `campPlaced`, "
        "`weighted_count`, `weighted_return_rate`, `unweighted_n`."
    )
    lines.append(f"- Rows: `{len(trends)}`")
    lines.append("")
    lines.append("## Age ≤28 Share Table")
    lines.append("")
    lines.append(
        "**What this measures:** The proportion of each cohort that is age 28 or younger. "
        "This is a composition metric (what % of the cohort is young), NOT a retention metric. "
        "Age ≤28 includes age bands `<=22` and `23-28`."
    )
    lines.append("")
    lines.append(
        "Saved to CSV with columns: `cohort_year`, `campPlaced`, "
        "`under30_weighted_count`, `total_weighted_count`, "
        "`under30_share`, `unweighted_n`."
    )
    lines.append(f"- Rows: `{len(under30_share)}`")
    lines.append("")
    lines.append(
        "_Note: The variable is named 'under30' in the code for historical reasons, "
        "but actually measures age ≤28 based on the age band definitions._"
    )
    lines.append("")
    lines.append("## First-Timer Camp Placement Share")
    lines.append("")
    lines.append(
        "Saved to CSV with columns: `cohort_year`, `age_band`, `weighted_yes_count`, "
        "`weighted_no_count`, `weighted_total_count`, `camp_placed_share`, `unweighted_n`."
    )
    lines.append(f"- Rows: `{len(firsttimer_camp_share)}`")
    lines.append("")
    lines.append("## Multi-Year Retention (Pooled Across Cohorts)")
    lines.append("")
    lines.append(
        "Saved to CSV with columns: `segment`, `campPlaced`, `metric`, "
        "`weighted_count`, `weighted_return_rate`, `unweighted_n`."
    )
    lines.append(f"- Rows: `{len(multiyear_retention)}`")
    if not multiyear_retention.empty:
        lines.append("")
        lines.append("| segment | campPlaced | metric | weighted_count | weighted_return_rate | unweighted_n |")
        lines.append("|---|---|---|---|---|---|")
        for _, row in multiyear_retention.iterrows():
            lines.append(
                f"| {row['segment']} | {row['campPlaced']} | {row['metric']} | "
                f"{row['weighted_count']:.2f} | {row['weighted_return_rate']:.4f} | "
                f"{int(row['unweighted_n'])} |"
            )
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    input_path = Path(args.input)
    output_csv = Path(args.output_csv)
    output_under30_csv = Path(args.output_under30_csv)
    output_md = Path(args.output_md)
    output_firsttimer_csv = Path(args.output_firsttimer_camp_csv)
    output_multiyear_csv = Path(args.output_multiyear_retention_csv)

    sheet = normalize_sheet(args.sheet)
    df = pd.read_excel(input_path, sheet_name=sheet)
    df, year_map, attended = prepare_dataframe(df)

    df["return_year_1"] = compute_return_in_offset_year(df["cohort_year"], attended, 1)
    df["return_year_2"] = compute_return_in_offset_year(df["cohort_year"], attended, 2)
    df["return_year_3plus"] = compute_return_after_offset(df["cohort_year"], attended, 3)

    base_mask = df["cohort_year"].notna() & df["return_year_1"].notna()
    df_return = df.loc[base_mask]

    trends = build_trend_table(df_return)
    under30_share = build_under30_share_table(df_return)
    firsttimer_camp_share = build_firsttimer_camp_share_table(df)
    multiyear_retention = build_multiyear_retention_table(df)

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    trends.to_csv(output_csv, index=False)

    output_under30_csv.parent.mkdir(parents=True, exist_ok=True)
    under30_share.to_csv(output_under30_csv, index=False)

    output_firsttimer_csv.parent.mkdir(parents=True, exist_ok=True)
    firsttimer_camp_share.to_csv(output_firsttimer_csv, index=False)

    output_multiyear_csv.parent.mkdir(parents=True, exist_ok=True)
    multiyear_retention.to_csv(output_multiyear_csv, index=False)

    output_md.parent.mkdir(parents=True, exist_ok=True)
    summary = build_markdown_summary(
        df,
        year_map,
        trends,
        under30_share,
        firsttimer_camp_share,
        multiyear_retention,
        input_path,
    )
    output_md.write_text(summary, encoding="utf-8")

    print("Census 2025 cohort trend outputs written.")
    print(f"- Trend CSV: {output_csv}")
    print(f"- Under-30 share CSV: {output_under30_csv}")
    print(f"- First-timer camp share CSV: {output_firsttimer_csv}")
    print(f"- Multi-year retention CSV: {output_multiyear_csv}")
    print(f"- Markdown: {output_md}")
    print("")
    print("Trend preview (overall, campPlaced=all):")
    preview = trends.loc[(trends["segment"] == "overall") & (trends["campPlaced"] == "all")]
    if preview.empty:
        print("  (no rows after filtering)")
    else:
        preview = preview.sort_values("cohort_year")
        preview["weighted_return_rate"] = preview["weighted_return_rate"].map(
            lambda value: f"{value:.4f}"
        )
        print(preview.to_string(index=False))


if __name__ == "__main__":
    main()
