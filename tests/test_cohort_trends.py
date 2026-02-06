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
        / "census2025_cohort_trends.py"
    )
    spec = importlib.util.spec_from_file_location("cohort_trends", script_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_trend_table_weighted_return_rate():
    module = load_module()
    df = pd.DataFrame(
        {
            "attendedYears.2020": [1.0, 1.0, 1.0, 1.0],
            "attendedYears.2021": [1.0, 0.0, 1.0, 0.0],
            "weights": [1.0, 1.0, 2.0, 2.0],
            "age": [25, 25, 35, 35],
            "campPlaced": ["yes", "yes", "no", "no"],
        }
    )
    df, _ = module.prepare_dataframe(df)
    mask = df["cohort_year"].notna() & df["return_next_year"].notna()
    trends = module.build_trend_table(df.loc[mask])

    overall_all = trends.loc[
        (trends["segment"] == "overall")
        & (trends["campPlaced"] == "all")
        & (trends["cohort_year"] == 2020)
    ].iloc[0]
    assert overall_all["weighted_count"] == 6.0
    assert overall_all["weighted_return_rate"] == 0.5

    camp_yes = trends.loc[
        (trends["segment"] == "overall")
        & (trends["campPlaced"] == "yes")
        & (trends["cohort_year"] == 2020)
    ].iloc[0]
    assert camp_yes["weighted_return_rate"] == 0.5


def test_under30_share_table():
    module = load_module()
    df = pd.DataFrame(
        {
            "attendedYears.2020": [1.0, 1.0, 1.0, 1.0],
            "attendedYears.2021": [1.0, 1.0, 1.0, 1.0],
            "weights": [1.0, 2.0, 3.0, 4.0],
            "age": [22, 28, 35, 40],
            "campPlaced": ["yes", "yes", "yes", "yes"],
        }
    )
    df, _ = module.prepare_dataframe(df)
    mask = df["cohort_year"].notna() & df["return_next_year"].notna()
    under30 = module.build_under30_share_table(df.loc[mask])

    row = under30.loc[
        (under30["cohort_year"] == 2020) & (under30["campPlaced"] == "yes")
    ].iloc[0]
    assert np.isclose(row["under30_weighted_count"], 3.0)
    assert np.isclose(row["total_weighted_count"], 10.0)
    assert np.isclose(row["under30_share"], 0.3)
