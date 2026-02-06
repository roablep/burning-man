#!/usr/bin/env python3
"""Generate Plotly visuals for the 2025 cohort retention analysis."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

AGE_LABELS = ["<=22", "23-28", "29-34", "35-39", "40-49", "50-59", "60+"]
SMALL_N_THRESHOLD = 15.0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate Plotly visuals for 2025 cohort retention analysis.",
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
        "--output-dir",
        default="reports/census_next_gen_rs/figures",
        help="Directory for Plotly HTML outputs.",
    )
    return parser.parse_args()


def prepare_retention_by_age_band(retention: pd.DataFrame) -> pd.DataFrame:
    df = retention.copy()
    df = df.loc[df["campPlaced"].isin(["yes", "no"])]
    df["age_band"] = pd.Categorical(df["age_band"], categories=AGE_LABELS, ordered=True)

    grouped = df.groupby(["age_band", "campPlaced"], observed=False, as_index=False).apply(
        lambda g: pd.Series(
            {
                "weighted_count": g["weighted_count"].sum(),
                "unweighted_n": g["unweighted_n"].sum(),
                "weighted_return_rate": (
                    (g["weighted_return_rate"] * g["weighted_count"]).sum() / g["weighted_count"].sum()
                    if g["weighted_count"].sum() > 0
                    else 0.0
                ),
            }
        )
    )
    grouped["small_n"] = grouped["weighted_count"] < SMALL_N_THRESHOLD
    return grouped.sort_values(["age_band", "campPlaced"])


def prepare_retention_trends(trends: pd.DataFrame) -> pd.DataFrame:
    df = trends.copy()
    df = df.loc[df["segment"] == "overall"]
    df = df.loc[df["campPlaced"].isin(["yes", "no"])]
    df["small_n"] = df["weighted_count"] < SMALL_N_THRESHOLD
    return df.sort_values(["cohort_year", "campPlaced"])


def prepare_under30_share(under30: pd.DataFrame) -> pd.DataFrame:
    df = under30.copy()
    df = df.loc[df["campPlaced"].isin(["yes", "no"])]
    df["small_n"] = df["total_weighted_count"] < SMALL_N_THRESHOLD
    return df.sort_values(["cohort_year", "campPlaced"])


def prepare_retention_heatmap(retention: pd.DataFrame) -> pd.DataFrame:
    df = retention.copy()
    df = df.loc[df["campPlaced"].isin(["yes", "no"])]
    df["age_band"] = pd.Categorical(df["age_band"], categories=AGE_LABELS, ordered=True)
    return df


def write_plot(fig, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.write_html(output_path, include_plotlyjs="cdn")


def build_retention_by_age_band_chart(df: pd.DataFrame) -> px.bar:
    fig = px.bar(
        df,
        x="age_band",
        y="weighted_return_rate",
        color="campPlaced",
        barmode="group",
        hover_data=["weighted_count", "unweighted_n", "small_n"],
        labels={
            "age_band": "Age band",
            "weighted_return_rate": "Return next year (weighted)",
            "campPlaced": "Camp placed",
        },
        title="Second-Year Return Rate by Age Band (campPlaced)",
    )
    fig.update_yaxes(tickformat=".0%")
    fig.update_layout(legend_title_text="campPlaced")
    return fig


def build_retention_trends_chart(df: pd.DataFrame) -> px.line:
    fig = px.line(
        df,
        x="cohort_year",
        y="weighted_return_rate",
        color="campPlaced",
        markers=True,
        hover_data=["weighted_count", "unweighted_n", "small_n"],
        labels={
            "cohort_year": "Cohort year",
            "weighted_return_rate": "Return next year (weighted)",
            "campPlaced": "Camp placed",
        },
        title="Return-Next-Year Trends by Cohort Year",
    )
    fig.update_yaxes(tickformat=".0%")
    return fig


def build_under30_share_chart(df: pd.DataFrame) -> px.line:
    fig = px.line(
        df,
        x="cohort_year",
        y="under30_share",
        color="campPlaced",
        markers=True,
        hover_data=["under30_weighted_count", "total_weighted_count", "small_n"],
        labels={
            "cohort_year": "Cohort year",
            "under30_share": "Under-30 share (weighted)",
            "campPlaced": "Camp placed",
        },
        title="Under-30 Share by Cohort Year",
    )
    fig.update_yaxes(tickformat=".0%")
    return fig


def build_retention_heatmap(df: pd.DataFrame) -> px.imshow:
    rate_pivot = df.pivot_table(
        index="age_band",
        columns="cohort_year",
        values="weighted_return_rate",
        aggfunc="mean",
    )
    n_pivot = df.pivot_table(
        index="age_band",
        columns="cohort_year",
        values="unweighted_n",
        aggfunc="sum",
    )
    fig = go.Figure()
    fig.add_trace(
        go.Heatmap(
            z=rate_pivot.values,
            x=rate_pivot.columns,
            y=rate_pivot.index,
            colorscale=px.colors.sequential.Greens,
            colorbar=dict(title="Return rate", tickformat=".0%"),
            customdata=n_pivot.values,
            hovertemplate=(
                "Cohort year: %{x}"
                "<br>Age band: %{y}"
                "<br>Return rate: %{z:.1%}"
                "<br>Unweighted n: %{customdata}"
                "<extra></extra>"
            ),
        )
    )
    small_n_mask = (n_pivot.values < SMALL_N_THRESHOLD).astype(float)
    fig.add_trace(
        go.Heatmap(
            z=small_n_mask,
            x=rate_pivot.columns,
            y=rate_pivot.index,
            colorscale=[
                [0.0, "rgba(255,255,255,0.0)"],
                [1.0, "rgba(255,255,255,0.6)"],
            ],
            showscale=False,
            hoverinfo="skip",
        )
    )
    fig.update_layout(
        title="Return-Next-Year Heatmap (Age Band x Cohort Year)",
        xaxis_title="Cohort year",
        yaxis_title="Age band",
    )
    fig.update_yaxes(categoryorder="array", categoryarray=AGE_LABELS)
    return fig


def main() -> None:
    args = parse_args()

    retention = pd.read_csv(args.cohort_retention)
    trends = pd.read_csv(args.cohort_trends)
    under30 = pd.read_csv(args.under30_share)

    output_dir = Path(args.output_dir)

    retention_age = prepare_retention_by_age_band(retention)
    trends_overall = prepare_retention_trends(trends)
    under30_share = prepare_under30_share(under30)
    heatmap_data = prepare_retention_heatmap(retention)

    charts = {
        "retention_by_age_band.html": build_retention_by_age_band_chart(retention_age),
        "retention_trends_by_cohort.html": build_retention_trends_chart(trends_overall),
        "under30_share_by_cohort.html": build_under30_share_chart(under30_share),
        "retention_heatmap_cohort_age.html": build_retention_heatmap(heatmap_data),
    }

    for filename, fig in charts.items():
        write_plot(fig, output_dir / filename)

    print("Cohort visuals written.")
    for filename in charts:
        print(f"- {output_dir / filename}")


if __name__ == "__main__":
    main()
