#!/usr/bin/env python3
"""Generate a grok-focused 2025 weighted analysis report with charts."""

from __future__ import annotations

import argparse
import math
import re
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

AGE_BINS = [-np.inf, 22, 28, 34, 39, 49, 59, np.inf]
AGE_LABELS = ["<=22", "23-28", "29-34", "35-39", "40-49", "50-59", "60+"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate grok-focused 2025 weighted analysis report.",
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
        "--output-report",
        default="reports/census2025_weighted_analysis_report.md",
        help="Output markdown report path.",
    )
    parser.add_argument(
        "--output-dir",
        default="reports",
        help="Directory for charts and supporting outputs.",
    )
    parser.add_argument(
        "--bootstrap",
        type=int,
        default=300,
        help="Bootstrap iterations for logistic regression CIs.",
    )
    return parser.parse_args()


def add_age_band(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["age_band"] = pd.cut(df["age"], bins=AGE_BINS, labels=AGE_LABELS, right=True)
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


def parse_attended_years(df: pd.DataFrame) -> dict[int, str]:
    pattern = re.compile(r"^attendedYears\.(\d{4})")
    year_map: dict[int, str] = {}
    for col in df.columns:
        match = pattern.match(col)
        if match:
            year = int(match.group(1))
            # Prefer exact year columns if duplicates exist (e.g., 1990Baker/1990BlackRock).
            if year in year_map and col != f"attendedYears.{year}":
                continue
            year_map[year] = col
    return dict(sorted(year_map.items()))


def compute_cohort_year(attended: pd.DataFrame, year_map: dict[int, str]) -> pd.Series:
    years = list(year_map.items())
    cohort_year = []
    for _, row in attended.iterrows():
        year = None
        for yr, col in years:
            val = row[col]
            if pd.notna(val) and float(val) == 1.0:
                year = yr
                break
        cohort_year.append(year)
    return pd.Series(cohort_year, index=attended.index)


def compute_return_next_year(
    cohort_year: pd.Series, attended: pd.DataFrame, year_map: dict[int, str]
) -> pd.Series:
    values = []
    year_cols = year_map
    for idx, year in cohort_year.items():
        if pd.isna(year):
            values.append(np.nan)
            continue
        next_year = int(year) + 1
        if next_year not in year_cols:
            values.append(np.nan)
            continue
        val = attended.loc[idx, year_cols[next_year]]
        if pd.isna(val):
            values.append(np.nan)
        else:
            values.append(1.0 if float(val) == 1.0 else 0.0)
    return pd.Series(values, index=cohort_year.index)


def weighted_share(series: pd.Series, weights: pd.Series) -> pd.Series:
    grouped = series.groupby(series)
    values = {}
    for key, idx in grouped.groups.items():
        w = weights.loc[idx].sum()
        values[key] = w
    total = sum(values.values())
    return pd.Series({k: (v / total * 100.0 if total else 0.0) for k, v in values.items()})


def weighted_return_rate(group: pd.DataFrame) -> float:
    weight = group["weights"].sum()
    if weight <= 0:
        return 0.0
    return float((group["weights"] * group["return_next_year"]).sum() / weight)


def camp_share_within_group(df: pd.DataFrame, group_col: str) -> pd.DataFrame:
    base = df[df["campPlaced_clean"].isin(["yes", "no"])].copy()
    grouped = (
        base.groupby([group_col, "campPlaced_clean"])["weights"].sum().reset_index()
    )
    totals = grouped.groupby(group_col)["weights"].sum().reset_index()
    merged = grouped.merge(totals, on=group_col, suffixes=("", "_total"))
    merged["weighted_pct"] = (merged["weights"] / merged["weights_total"]) * 100.0
    return merged


def write_svg_bar_chart(
    categories: Iterable[str],
    values: Iterable[float],
    title: str,
    x_label: str,
    path: Path,
    color: str = "#2b6cb0",
) -> None:
    categories = list(categories)
    values = list(values)
    width = 900
    bar_height = 22
    gap = 10
    left_pad = 180
    right_pad = 40
    top_pad = 50
    bottom_pad = 50
    height = top_pad + bottom_pad + len(categories) * (bar_height + gap)
    max_val = max(values) if values else 1.0
    scale = (width - left_pad - right_pad) / max_val if max_val else 1.0

    lines = [
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{width}' height='{height}'>",
        f"<style>text {{ font-family: Arial, sans-serif; font-size: 12px; }}</style>",
        f"<text x='{left_pad}' y='28' font-size='16' font-weight='bold'>{title}</text>",
        f"<text x='{left_pad}' y='{height - 15}' font-size='12'>{x_label}</text>",
    ]

    for i, (cat, val) in enumerate(zip(categories, values)):
        y = top_pad + i * (bar_height + gap)
        bar_w = val * scale
        lines.append(f"<text x='10' y='{y + 15}'>{cat}</text>")
        lines.append(
            f"<rect x='{left_pad}' y='{y}' width='{bar_w:.1f}' height='{bar_height}' fill='{color}' />"
        )
        lines.append(
            f"<text x='{left_pad + bar_w + 6:.1f}' y='{y + 15}'>{val:.1f}%</text>"
        )

    lines.append("</svg>")
    path.write_text("\n".join(lines), encoding="utf-8")


def write_svg_grouped_bar_chart(
    categories: Iterable[str],
    values_a: Iterable[float],
    values_b: Iterable[float],
    label_a: str,
    label_b: str,
    title: str,
    x_label: str,
    path: Path,
) -> None:
    categories = list(categories)
    values_a = list(values_a)
    values_b = list(values_b)
    width = 900
    bar_height = 16
    gap = 8
    group_gap = 12
    left_pad = 180
    right_pad = 40
    top_pad = 70
    bottom_pad = 50
    height = top_pad + bottom_pad + len(categories) * (2 * bar_height + gap + group_gap)
    max_val = max(values_a + values_b) if values_a or values_b else 1.0
    scale = (width - left_pad - right_pad) / max_val if max_val else 1.0

    lines = [
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{width}' height='{height}'>",
        f"<style>text {{ font-family: Arial, sans-serif; font-size: 12px; }}</style>",
        f"<text x='{left_pad}' y='28' font-size='16' font-weight='bold'>{title}</text>",
        f"<rect x='{left_pad}' y='40' width='14' height='14' fill='#2b6cb0' />",
        f"<text x='{left_pad + 20}' y='52'>{label_a}</text>",
        f"<rect x='{left_pad + 120}' y='40' width='14' height='14' fill='#c53030' />",
        f"<text x='{left_pad + 140}' y='52'>{label_b}</text>",
        f"<text x='{left_pad}' y='{height - 15}' font-size='12'>{x_label}</text>",
    ]

    for i, cat in enumerate(categories):
        y_base = top_pad + i * (2 * bar_height + gap + group_gap)
        lines.append(f"<text x='10' y='{y_base + 14}'>{cat}</text>")

        for j, (val, color) in enumerate(((values_a[i], "#2b6cb0"), (values_b[i], "#c53030"))):
            y = y_base + j * (bar_height + gap)
            bar_w = val * scale
            lines.append(
                f"<rect x='{left_pad}' y='{y}' width='{bar_w:.1f}' height='{bar_height}' fill='{color}' />"
            )
            lines.append(
                f"<text x='{left_pad + bar_w + 6:.1f}' y='{y + 12}'>{val:.1f}%</text>"
            )

    lines.append("</svg>")
    path.write_text("\n".join(lines), encoding="utf-8")


def write_csv(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)


def bootstrap_logit(
    X: pd.DataFrame,
    y: pd.Series,
    weights: pd.Series,
    iterations: int,
    seed: int = 42,
) -> tuple[pd.Series, pd.DataFrame]:
    rng = np.random.default_rng(seed)
    coef_samples = []
    for _ in range(iterations):
        idx = rng.integers(0, len(X), len(X))
        Xb = X.iloc[idx]
        yb = y.iloc[idx]
        wb = weights.iloc[idx]
        model = LogisticRegression(max_iter=1000, solver="lbfgs")
        try:
            model.fit(Xb, yb, sample_weight=wb)
            coef_samples.append(model.coef_[0])
        except Exception:
            continue
    coef_samples = np.array(coef_samples)
    coef_mean = coef_samples.mean(axis=0)
    ci_low = np.percentile(coef_samples, 2.5, axis=0)
    ci_high = np.percentile(coef_samples, 97.5, axis=0)
    summary = pd.DataFrame(
        {
            "coef": coef_mean,
            "ci_low": ci_low,
            "ci_high": ci_high,
        },
        index=X.columns,
    )
    return pd.Series(coef_mean, index=X.columns), summary


def format_table(df: pd.DataFrame) -> str:
    lines = ["| " + " | ".join([str(c) for c in df.columns]) + " |", "| " + " | ".join(["---"] * len(df.columns)) + " |"]
    for _, row in df.iterrows():
        lines.append("| " + " | ".join([str(v) for v in row.values]) + " |")
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    input_path = Path(args.input)
    output_dir = Path(args.output_dir)
    output_report = Path(args.output_report)
    output_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_excel(input_path, sheet_name=args.sheet)
    df = add_age_band(df)
    df = add_nburns_bucket(df)
    df["campPlaced_clean"] = df["campPlaced"].fillna("missing")

    # Data hygiene
    missing_age = int(df["age"].isna().sum())
    missing_camp = int(df["campPlaced"].isna().sum())
    missing_virgin = int(df["virgin"].isna().sum())

    # Weighted baselines
    weights = df["weights"]
    age_dist = df.dropna(subset=["age_band"]).groupby("age_band")["weights"].sum()
    age_dist = (age_dist / age_dist.sum() * 100.0).reindex(AGE_LABELS)

    camp_dist = df.groupby("campPlaced_clean")["weights"].sum()
    camp_dist = (camp_dist / camp_dist.sum() * 100.0).reindex(["yes", "no", "dontKnow", "missing"]).fillna(0.0)

    df["virgin_clean"] = df["virgin"].fillna("missing")
    virgin_dist = df.groupby("virgin_clean")["weights"].sum()
    virgin_dist = (virgin_dist / virgin_dist.sum() * 100.0)

    under30_mask = df["age"].notna() & (df["age"] <= 29)
    under30_share = float((weights[under30_mask].sum() / weights[df["age"].notna()].sum()) * 100.0)

    # Under-30 by campPlaced
    under30_by_camp = (
        df[df["campPlaced_clean"].isin(["yes", "no"])].assign(under30=lambda d: d["age"] <= 29)
        .groupby("campPlaced_clean")
        .apply(lambda g: (g.loc[g["under30"], "weights"].sum() / g["weights"].sum()) * 100.0)
    )

    # campPlaced by age_band (yes/no only, within age band)
    camp_by_age = camp_share_within_group(df, "age_band")
    camp_by_age_pivot = camp_by_age.pivot(
        index="age_band", columns="campPlaced_clean", values="weighted_pct"
    ).reindex(AGE_LABELS)

    # campPlaced by under30 vs 30+ (yes/no only, within group)
    df["age_under30"] = np.where(df["age"] <= 29, "under30", "30plus")
    camp_by_under30 = camp_share_within_group(df, "age_under30")
    camp_by_under30_pivot = camp_by_under30.pivot(
        index="age_under30", columns="campPlaced_clean", values="weighted_pct"
    ).reindex(["under30", "30plus"])

    # Cohort/retention
    year_map = parse_attended_years(df)
    attended = df[list(year_map.values())]
    cohort_year = compute_cohort_year(attended, year_map)
    return_next_year = compute_return_next_year(cohort_year, attended, year_map)

    df["cohort_year"] = cohort_year
    df["return_next_year"] = return_next_year

    retention_base = df[
        df["cohort_year"].notna()
        & df["return_next_year"].notna()
        & df["campPlaced_clean"].isin(["yes", "no"])
    ].copy()

    retention_table = (
        retention_base.groupby(["age_band", "campPlaced_clean"])
        .apply(
            lambda g: pd.Series(
                {
                    "weighted_count": g["weights"].sum(),
                    "weighted_return_rate": weighted_return_rate(g),
                    "unweighted_n": len(g),
                }
            )
        )
        .reset_index()
    )
    retention_table["weighted_return_rate"] = retention_table["weighted_return_rate"].map(lambda v: f"{v:.3f}")
    retention_table["weighted_count"] = retention_table["weighted_count"].map(lambda v: f"{v:.1f}")

    # Charts
    write_svg_bar_chart(
        AGE_LABELS,
        [age_dist.get(label, 0.0) for label in AGE_LABELS],
        "Age Distribution (Weighted %)",
        "Share of respondents",
        output_dir / "census2025_age_distribution.svg",
    )
    write_svg_bar_chart(
        ["yes", "no", "dontKnow", "missing"],
        [camp_dist.get(label, 0.0) for label in ["yes", "no", "dontKnow", "missing"]],
        "Placed Camp Membership (Weighted %)",
        "Share of respondents",
        output_dir / "census2025_camp_placed_share.svg",
        color="#c05621",
    )

    # Return rate chart (yes vs no)
    yes_rates = []
    no_rates = []
    for band in AGE_LABELS:
        subset = retention_base[retention_base["age_band"] == band]
        yes = subset[subset["campPlaced_clean"] == "yes"]
        no = subset[subset["campPlaced_clean"] == "no"]
        yes_rates.append(weighted_return_rate(yes) * 100.0 if len(yes) else 0.0)
        no_rates.append(weighted_return_rate(no) * 100.0 if len(no) else 0.0)

    write_svg_grouped_bar_chart(
        AGE_LABELS,
        yes_rates,
        no_rates,
        "campPlaced=yes",
        "campPlaced=no",
        "Return Next Year by Age Band (Weighted %)",
        "Return rate",
        output_dir / "census2025_return_rate_by_age_camp.svg",
    )

    # Logistic regression (minimal covariates)
    model_df = retention_base.dropna(subset=["age_band", "virgin"]).copy()
    model_df["campPlaced_yes"] = (model_df["campPlaced_clean"] == "yes").astype(int)
    model_df["virgin_yes"] = (model_df["virgin"] == "virgin").astype(int)

    X = pd.get_dummies(model_df["age_band"], prefix="age", drop_first=True)
    X = pd.concat([model_df[["campPlaced_yes", "virgin_yes"]], X], axis=1)
    y = model_df["return_next_year"].astype(int)

    coef_mean, coef_ci = bootstrap_logit(X, y, model_df["weights"], args.bootstrap)
    odds = np.exp(coef_ci[["coef", "ci_low", "ci_high"]])
    odds = odds.reset_index().rename(columns={"index": "term"})
    odds["odds_ratio"] = odds["coef"].map(lambda v: f"{v:.2f}")
    odds["ci_low"] = odds["ci_low"].map(lambda v: f"{v:.2f}")
    odds["ci_high"] = odds["ci_high"].map(lambda v: f"{v:.2f}")
    odds = odds[["term", "odds_ratio", "ci_low", "ci_high"]]

    # Report
    lines: list[str] = []
    lines.append("# Census 2025 Weighted Analysis (Grok-Focused)")
    lines.append("")
    lines.append("## Executive Summary")
    lines.append("")
    lines.append("This report summarizes who is coming, who is returning, and how placed camps relate to retention in 2025 (weighted data). It is built for internal decision-making, with a brief public summary at the end.")
    lines.append("")

    lines.append("## Data Hygiene")
    lines.append("")
    lines.append(f"- Rows: `{len(df)}`")
    lines.append(f"- Missing age: `{missing_age}`")
    lines.append(f"- Missing campPlaced: `{missing_camp}`")
    lines.append(f"- Missing virgin: `{missing_virgin}`")
    lines.append("")

    lines.append("## Composition Baselines")
    lines.append("")
    lines.append(f"- Under-30 share (weighted, <=29): **{under30_share:.1f}%**")
    lines.append("")
    lines.append("### Age Distribution (Weighted %)")
    lines.append("")
    age_table = pd.DataFrame({"age_band": AGE_LABELS, "weighted_pct": [f"{age_dist.get(label, 0.0):.1f}%" for label in AGE_LABELS]})
    lines.append(format_table(age_table))
    lines.append("")
    lines.append("Chart: `reports/census2025_age_distribution.svg`")
    lines.append("")

    lines.append("### Camp Placement (Weighted %)")
    lines.append("")
    camp_table = pd.DataFrame({"campPlaced": ["yes", "no", "dontKnow", "missing"], "weighted_pct": [f"{camp_dist.get(label, 0.0):.1f}%" for label in ["yes", "no", "dontKnow", "missing"]]})
    lines.append(format_table(camp_table))
    lines.append("")
    lines.append("Chart: `reports/census2025_camp_placed_share.svg`")
    lines.append("")

    lines.append("### Under-30 Share by Camp Placement (Weighted %)")
    lines.append("")
    under30_table = pd.DataFrame({
        "campPlaced": ["yes", "no"],
        "under30_pct": [f"{under30_by_camp.get('yes', 0.0):.1f}%", f"{under30_by_camp.get('no', 0.0):.1f}%"],
    })
    lines.append(format_table(under30_table))
    lines.append("")

    lines.append("### Camp Placement by Age Band (Weighted %, within age band)")
    lines.append("")
    camp_by_age_table = pd.DataFrame({
        "age_band": AGE_LABELS,
        "campPlaced_yes": [f"{camp_by_age_pivot.loc[label].get('yes', 0.0):.1f}%" for label in AGE_LABELS],
        "campPlaced_no": [f"{camp_by_age_pivot.loc[label].get('no', 0.0):.1f}%" for label in AGE_LABELS],
    })
    lines.append(format_table(camp_by_age_table))
    lines.append("")

    lines.append("### Camp Placement by Under-30 vs 30+ (Weighted %, within group)")
    lines.append("")
    camp_by_under30_table = pd.DataFrame({
        "age_group": ["under30", "30plus"],
        "campPlaced_yes": [f"{camp_by_under30_pivot.loc['under30'].get('yes', 0.0):.1f}%", f"{camp_by_under30_pivot.loc['30plus'].get('yes', 0.0):.1f}%"],
        "campPlaced_no": [f"{camp_by_under30_pivot.loc['under30'].get('no', 0.0):.1f}%", f"{camp_by_under30_pivot.loc['30plus'].get('no', 0.0):.1f}%"],
    })
    lines.append(format_table(camp_by_under30_table))
    lines.append("")

    camp_by_age_csv = output_dir / "census2025_campPlaced_by_age_band.csv"
    camp_by_under30_csv = output_dir / "census2025_campPlaced_by_under30.csv"
    write_csv(camp_by_age_table, camp_by_age_csv)
    write_csv(camp_by_under30_table, camp_by_under30_csv)

    lines.append("## Crosstabs")
    lines.append("")
    lines.append("See `reports/census2025_weighted_crosstabs.md` and CSV outputs in `reports/`.")
    lines.append("")

    lines.append("## Retention: Return Next Year")
    lines.append("")
    lines.append("The table below shows weighted return rates by age band and camp placement (yes/no). `dontKnow` and missing campPlaced are excluded from the comparison.")
    lines.append("")
    lines.append(format_table(retention_table))
    lines.append("")
    lines.append("Chart: `reports/census2025_return_rate_by_age_camp.svg`")
    lines.append("")

    lines.append("## Inference (Weighted Logistic Regression)")
    lines.append("")
    lines.append("Model: return-next-year ~ campPlaced + virgin + age_band (reference: <=22). Odds ratios are from a bootstrap (percentile) CI.")
    lines.append("")
    lines.append(format_table(odds))
    lines.append("")

    lines.append("## Interpretation Framework")
    lines.append("")
    lines.append("For each key metric, interpret using: What we see → Why it might matter → What it does not prove → Actionable question.")
    lines.append("")

    lines.append("## Public Summary (Draft)")
    lines.append("")
    lines.append("In 2025, the weighted census shows that younger participation is concentrated in the under‑30 band, and placed camps appear associated with higher return‑next‑year rates across most age groups. These patterns suggest camps are an important retention channel, though the analysis is associative rather than causal. The Census can use these insights to help camps benchmark their age mix and track newcomer retention over time.")
    lines.append("")

    output_report.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote report to {output_report}")


if __name__ == "__main__":
    main()
