#!/usr/bin/env python3
"""Generate Plotly visuals for the 2025 cohort retention analysis."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

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
        "--firsttimer-camp-share",
        default="reports/census_next_gen_rs/census2025_firsttimer_camp_share.csv",
        help="Path to first-timer camp placement share CSV.",
    )
    parser.add_argument(
        "--output-dir",
        default="reports/census_next_gen_rs/figures",
        help="Directory for Plotly HTML outputs.",
    )
    return parser.parse_args()


def prepare_retention_by_age_band(
    retention: pd.DataFrame, cohort_year: int | None = None
) -> pd.DataFrame:
    df = retention.copy()
    if cohort_year is not None:
        df = df.loc[df["cohort_year"] == cohort_year]
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


def filter_last_n_years(df: pd.DataFrame, n_years: int = 10) -> pd.DataFrame:
    if df.empty:
        return df
    max_year = int(df["cohort_year"].max())
    return df.loc[df["cohort_year"] >= max_year - (n_years - 1)]


def prepare_firsttimer_camp_share(firsttimer: pd.DataFrame) -> pd.DataFrame:
    df = firsttimer.copy()
    df["age_band"] = pd.Categorical(df["age_band"], categories=AGE_LABELS, ordered=True)
    return df


def write_plot(fig, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.write_html(output_path, include_plotlyjs="cdn")


def build_retention_by_age_band_chart(retention: pd.DataFrame) -> go.Figure:
    years = sorted(retention["cohort_year"].dropna().unique())
    if years:
        max_year = int(years[-1])
        years = [year for year in years if year >= max_year - 9]
    options = [("All cohorts", None)] + [(str(year), int(year)) for year in years]
    fig = go.Figure()

    visibility_map: dict[str, list[bool]] = {}
    trace_index = 0
    for label, cohort_year in options:
        aggregated = prepare_retention_by_age_band(retention, cohort_year=cohort_year)
        for camp in ["yes", "no"]:
            camp_df = aggregated.loc[aggregated["campPlaced"] == camp]
            fig.add_trace(
                go.Bar(
                    x=camp_df["age_band"],
                    y=camp_df["weighted_return_rate"],
                    name=camp,
                    legendgroup=camp,
                    customdata=camp_df[["weighted_count", "unweighted_n", "small_n"]].to_numpy(),
                    hovertemplate=(
                        "Age band: %{x}"
                        "<br>Camp placed: %{fullData.name}"
                        "<br>Return next year: %{y:.1%}"
                        "<br>Weighted count: %{customdata[0]:.2f}"
                        "<br>Unweighted n: %{customdata[1]}"
                        "<br>Small n: %{customdata[2]}"
                        "<extra></extra>"
                    ),
                    visible=(cohort_year is None),
                )
            )
            visibility = visibility_map.setdefault(label, [False] * (len(options) * 2))
            visibility[trace_index] = True
            trace_index += 1

    buttons = []
    for label, cohort_year in options:
        title_suffix = "All cohorts" if cohort_year is None else f"Cohort year {cohort_year}"
        buttons.append(
            dict(
                label=label,
                method="update",
                args=[
                    {"visible": visibility_map[label]},
                    {"title": f"Second-Year Return Rate by Age Band ({title_suffix})"},
                ],
            )
        )

    fig.update_layout(
        title="Second-Year Return Rate by Age Band (All cohorts)",
        barmode="group",
        legend_title_text="campPlaced",
        legend_traceorder="reversed",
        legend=dict(orientation="h", y=-0.2, x=0.0),
        updatemenus=[
            dict(
                buttons=buttons,
                direction="down",
                x=1.02,
                xanchor="left",
                y=1.0,
                yanchor="top",
                showactive=True,
            )
        ],
    )
    fig.update_xaxes(categoryorder="array", categoryarray=AGE_LABELS, title_text="Age band")
    fig.update_yaxes(tickformat=".0%", title_text="Return next year (weighted)")
    return fig


def build_retention_slopegraph_last10(retention: pd.DataFrame) -> go.Figure:
    df = retention.copy()
    df = df.loc[df["campPlaced"].isin(["yes", "no"])]
    df = df.loc[df["age_band"].isin(AGE_LABELS)]
    df = filter_last_n_years(df, n_years=10)
    df["age_band"] = pd.Categorical(df["age_band"], categories=AGE_LABELS, ordered=True)
    df["campPlaced"] = pd.Categorical(df["campPlaced"], categories=["no", "yes"], ordered=True)
    df["cohort_year"] = df["cohort_year"].astype(int)

    fig = px.line(
        df,
        x="campPlaced",
        y="weighted_return_rate",
        color="cohort_year",
        line_group="cohort_year",
        markers=True,
        facet_col="age_band",
        facet_col_wrap=3,
        hover_data=["weighted_count", "unweighted_n"],
        labels={
            "campPlaced": "Camp placed",
            "weighted_return_rate": "Return next year (weighted)",
            "cohort_year": "Cohort year",
        },
        title="Cohort Slopegraph by Age Band (Last 10 Years)",
    )
    fig.update_yaxes(tickformat=".0%")
    fig.update_layout(legend_title_text="Cohort year")
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


def build_under30_ribbon_last10(under30: pd.DataFrame) -> go.Figure:
    df = filter_last_n_years(under30, n_years=10)
    df = df.loc[df["campPlaced"].isin(["yes", "no"])]
    df = df.sort_values(["cohort_year", "campPlaced"])
    df["cohort_year"] = df["cohort_year"].astype(int)

    yes_df = df.loc[df["campPlaced"] == "yes"]
    no_df = df.loc[df["campPlaced"] == "no"]
    merged = pd.merge(
        yes_df[["cohort_year", "under30_share"]],
        no_df[["cohort_year", "under30_share"]],
        on="cohort_year",
        suffixes=("_yes", "_no"),
    ).sort_values("cohort_year")

    upper = merged[["under30_share_yes", "under30_share_no"]].max(axis=1)
    lower = merged[["under30_share_yes", "under30_share_no"]].min(axis=1)

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=merged["cohort_year"],
            y=upper,
            mode="lines",
            line=dict(color="rgba(0,0,0,0)"),
            hoverinfo="skip",
            showlegend=False,
        )
    )
    fig.add_trace(
        go.Scatter(
            x=merged["cohort_year"],
            y=lower,
            mode="lines",
            fill="tonexty",
            fillcolor="rgba(34,139,34,0.15)",
            line=dict(color="rgba(0,0,0,0)"),
            name="Gap (yes vs no)",
            hoverinfo="skip",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=yes_df["cohort_year"],
            y=yes_df["under30_share"],
            mode="lines+markers",
            name="campPlaced: yes",
            hovertemplate="Year: %{x}<br>Under-30 share: %{y:.1%}<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=no_df["cohort_year"],
            y=no_df["under30_share"],
            mode="lines+markers",
            name="campPlaced: no",
            hovertemplate="Year: %{x}<br>Under-30 share: %{y:.1%}<extra></extra>",
        )
    )
    fig.update_layout(
        title="Under-30 Share by Camp Placed (Last 10 Years)",
        xaxis_title="Cohort year",
        yaxis_title="Under-30 share (weighted)",
        legend_title_text="Series",
    )
    fig.update_yaxes(tickformat=".0%")
    return fig


def build_retention_gap_line_last10(retention: pd.DataFrame) -> go.Figure:
    df = retention.copy()
    df = df.loc[df["campPlaced"].isin(["yes", "no"])]
    df = df.loc[df["age_band"].isin(AGE_LABELS)]
    df = filter_last_n_years(df, n_years=10)
    df["cohort_year"] = df["cohort_year"].astype(int)

    pivot = df.pivot_table(
        index=["cohort_year", "age_band"],
        columns="campPlaced",
        values="weighted_return_rate",
        aggfunc="mean",
    ).reset_index()
    pivot["gap"] = pivot.get("yes") - pivot.get("no")

    fig = px.line(
        pivot,
        x="cohort_year",
        y="gap",
        color="age_band",
        markers=True,
        labels={
            "cohort_year": "Cohort year",
            "gap": "Return rate gap (yes - no)",
            "age_band": "Age band",
        },
        title="Return Rate Gap by Age Band (Last 10 Years)",
    )
    fig.add_hline(y=0, line_dash="dash", line_color="gray")
    fig.update_yaxes(tickformat=".0%")
    return fig


def build_retention_gap_heatmap_last10(retention: pd.DataFrame) -> go.Figure:
    df = retention.copy()
    df = df.loc[df["campPlaced"].isin(["yes", "no"])]
    df = df.loc[df["age_band"].isin(AGE_LABELS)]
    df = filter_last_n_years(df, n_years=10)
    df["age_band"] = pd.Categorical(df["age_band"], categories=AGE_LABELS, ordered=True)

    rate_pivot = df.pivot_table(
        index=["age_band", "cohort_year"],
        columns="campPlaced",
        values="weighted_return_rate",
        aggfunc="mean",
    )
    gap = (rate_pivot.get("yes") - rate_pivot.get("no")).unstack("cohort_year")

    n_pivot = df.pivot_table(
        index=["age_band", "cohort_year"],
        columns="campPlaced",
        values="unweighted_n",
        aggfunc="sum",
    )
    n_min = n_pivot.min(axis=1).unstack("cohort_year")

    fig = go.Figure()
    fig.add_trace(
        go.Heatmap(
            z=gap.values,
            x=gap.columns,
            y=gap.index,
            colorscale=px.colors.diverging.RdBu,
            zmid=0.0,
            colorbar=dict(title="Gap (yes - no)", tickformat=".0%"),
            customdata=n_min.values,
            hovertemplate=(
                "Cohort year: %{x}"
                "<br>Age band: %{y}"
                "<br>Return gap (yes-no): %{z:.1%}"
                "<br>Min unweighted n: %{customdata}"
                "<extra></extra>"
            ),
        )
    )
    small_n_mask = (n_min.values < SMALL_N_THRESHOLD).astype(float)
    fig.add_trace(
        go.Heatmap(
            z=small_n_mask,
            x=gap.columns,
            y=gap.index,
            colorscale=[
                [0.0, "rgba(255,255,255,0.0)"],
                [1.0, "rgba(255,255,255,0.6)"],
            ],
            showscale=False,
            hoverinfo="skip",
        )
    )
    fig.update_layout(
        title="Return Rate Gap Heatmap (Last 10 Years)",
        xaxis_title="Cohort year",
        yaxis_title="Age band",
    )
    fig.update_yaxes(categoryorder="array", categoryarray=AGE_LABELS)
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


def build_retention_heatmap_by_camp_last10(retention: pd.DataFrame) -> go.Figure:
    df = retention.copy()
    df = df.loc[df["campPlaced"].isin(["yes", "no"])]
    df = df.loc[df["age_band"].isin(AGE_LABELS)]
    df = filter_last_n_years(df, n_years=10)
    df["age_band"] = pd.Categorical(df["age_band"], categories=AGE_LABELS, ordered=True)

    camps = ["yes", "no"]
    fig = make_subplots(
        rows=1,
        cols=2,
        subplot_titles=["Camp placed: yes", "Camp placed: no"],
        shared_yaxes=True,
        horizontal_spacing=0.08,
    )
    for idx, camp in enumerate(camps, start=1):
        camp_df = df.loc[df["campPlaced"] == camp]
        rate_pivot = camp_df.pivot_table(
            index="age_band",
            columns="cohort_year",
            values="weighted_return_rate",
            aggfunc="mean",
        )
        n_pivot = camp_df.pivot_table(
            index="age_band",
            columns="cohort_year",
            values="unweighted_n",
            aggfunc="sum",
        )
        fig.add_trace(
            go.Heatmap(
                z=rate_pivot.values,
                x=rate_pivot.columns,
                y=rate_pivot.index,
                colorscale=px.colors.sequential.Greens,
                colorbar=dict(title="Return rate", tickformat=".0%") if idx == 2 else None,
                customdata=n_pivot.values,
                hovertemplate=(
                    "Cohort year: %{x}"
                    "<br>Age band: %{y}"
                    "<br>Return rate: %{z:.1%}"
                    "<br>Unweighted n: %{customdata}"
                    "<extra></extra>"
                ),
            ),
            row=1,
            col=idx,
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
            ),
            row=1,
            col=idx,
        )

    fig.update_layout(
        title="Return-Next-Year Heatmap by Camp Placed (Last 10 Years)",
        xaxis_title="Cohort year",
        yaxis_title="Age band",
    )
    fig.update_yaxes(categoryorder="array", categoryarray=AGE_LABELS)
    return fig


def build_firsttimer_camp_share_heatmap(df: pd.DataFrame) -> go.Figure:
    share_pivot = df.pivot_table(
        index="age_band",
        columns="cohort_year",
        values="camp_placed_share",
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
            z=share_pivot.values,
            x=share_pivot.columns,
            y=share_pivot.index,
            colorscale=px.colors.sequential.Blues,
            colorbar=dict(title="Camp placed share", tickformat=".0%"),
            customdata=n_pivot.values,
            hovertemplate=(
                "Cohort year: %{x}"
                "<br>Age band: %{y}"
                "<br>Camp placed share: %{z:.1%}"
                "<br>Unweighted n: %{customdata}"
                "<extra></extra>"
            ),
        )
    )
    small_n_mask = (n_pivot.values < SMALL_N_THRESHOLD).astype(float)
    fig.add_trace(
        go.Heatmap(
            z=small_n_mask,
            x=share_pivot.columns,
            y=share_pivot.index,
            colorscale=[
                [0.0, "rgba(255,255,255,0.0)"],
                [1.0, "rgba(255,255,255,0.6)"],
            ],
            showscale=False,
            hoverinfo="skip",
        )
    )
    fig.update_layout(
        title="First-Timer Camp Placement Share (Age Band x Cohort Year)",
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
    firsttimer_path = Path(args.firsttimer_camp_share)
    firsttimer = pd.read_csv(firsttimer_path) if firsttimer_path.exists() else None

    output_dir = Path(args.output_dir)

    trends_overall = prepare_retention_trends(trends)
    under30_share = prepare_under30_share(under30)
    heatmap_data = prepare_retention_heatmap(retention)
    firsttimer_share = prepare_firsttimer_camp_share(firsttimer) if firsttimer is not None else None

    charts = {
        "retention_by_age_band.html": build_retention_by_age_band_chart(retention),
        "retention_trends_by_cohort.html": build_retention_trends_chart(trends_overall),
        "under30_share_by_cohort.html": build_under30_share_chart(under30_share),
        "retention_heatmap_cohort_age.html": build_retention_heatmap(heatmap_data),
        "retention_slopegraph_age_band_last10.html": build_retention_slopegraph_last10(retention),
        "retention_heatmap_by_camp_last10.html": build_retention_heatmap_by_camp_last10(retention),
        "under30_share_ribbon_last10.html": build_under30_ribbon_last10(under30_share),
        "retention_gap_line_last10.html": build_retention_gap_line_last10(retention),
        "retention_gap_heatmap_last10.html": build_retention_gap_heatmap_last10(retention),
    }
    if firsttimer_share is not None:
        charts["firsttimer_camp_share_heatmap.html"] = build_firsttimer_camp_share_heatmap(
            firsttimer_share
        )

    for filename, fig in charts.items():
        write_plot(fig, output_dir / filename)

    print("Cohort visuals written.")
    for filename in charts:
        print(f"- {output_dir / filename}")


if __name__ == "__main__":
    main()
