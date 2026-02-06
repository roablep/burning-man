from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd


def load_module():
    script_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "census_next_gen_rs"
        / "scripts"
        / "census2025_cohort_retention.py"
    )
    spec = importlib.util.spec_from_file_location("cohort_retention", script_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_cohort_year_inference():
    module = load_module()
    df = pd.DataFrame(
        {
            "attendedYears.2020": [1.0, 0.0, 0.0],
            "attendedYears.2021": [1.0, 1.0, 0.0],
            "attendedYears.1990BlackRock": [0.0, 0.0, 1.0],
            "weights": [1.0, 1.0, 1.0],
            "age": [25, 30, 40],
            "campPlaced": ["yes", "no", "yes"],
        }
    )
    year_map = module.discover_attended_year_columns(df)
    attended = module.build_attended_year_matrix(df, year_map)
    cohort_year = module.compute_cohort_year(attended)
    assert cohort_year.tolist() == [2020.0, 2021.0, 1990.0]


def test_return_next_year_calculation():
    module = load_module()
    df = pd.DataFrame(
        {
            "attendedYears.2020": [1.0, 1.0, 0.0],
            "attendedYears.2021": [1.0, 0.0, 1.0],
            "attendedYears.2022": [0.0, 1.0, 0.0],
            "weights": [1.0, 1.0, 1.0],
            "age": [25, 30, 40],
            "campPlaced": ["yes", "no", "yes"],
        }
    )
    year_map = module.discover_attended_year_columns(df)
    attended = module.build_attended_year_matrix(df, year_map)
    cohort_year = module.compute_cohort_year(attended)
    returns = module.compute_return_next_year(cohort_year, attended)
    assert returns.tolist() == [1.0, 0.0, 0.0]


def test_missing_next_year_is_nan():
    module = load_module()
    df = pd.DataFrame(
        {
            "attendedYears.2024": [1.0],
            "weights": [1.0],
            "age": [25],
            "campPlaced": ["yes"],
        }
    )
    year_map = module.discover_attended_year_columns(df)
    attended = module.build_attended_year_matrix(df, year_map)
    cohort_year = module.compute_cohort_year(attended)
    returns = module.compute_return_next_year(cohort_year, attended)
    assert np.isnan(returns.iloc[0])


def test_campplaced_exclusion_and_weighted_rate():
    module = load_module()
    df = pd.DataFrame(
        {
            "attendedYears.2020": [1.0, 1.0, 1.0, 1.0],
            "attendedYears.2021": [1.0, 0.0, 1.0, 0.0],
            "weights": [1.0, 2.0, 3.0, 4.0],
            "age": [25, 25, 25, 25],
            "campPlaced": ["yes", "no", "dontKnow", None],
        }
    )
    df, _ = module.prepare_cohort_dataframe(df)
    mask = (
        df["cohort_year"].notna()
        & df["return_next_year"].notna()
        & df["age_band"].notna()
        & df["campPlaced_clean"].notna()
    )
    cohort_table = module.build_cohort_table(df.loc[mask])
    assert set(cohort_table["campPlaced"]) == {"yes", "no"}

    yes_row = cohort_table.loc[cohort_table["campPlaced"] == "yes"].iloc[0]
    assert yes_row["weighted_count"] == 1.0
    assert yes_row["weighted_return_rate"] == 1.0
