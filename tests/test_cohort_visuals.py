from __future__ import annotations

import importlib.util
from pathlib import Path

import pandas as pd


def load_module():
    script_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "census_next_gen_rs"
        / "scripts"
        / "census2025_cohort_visuals.py"
    )
    spec = importlib.util.spec_from_file_location("cohort_visuals", script_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_prepare_retention_by_age_band_orders_and_flags():
    module = load_module()
    df = pd.DataFrame(
        {
            "age_band": ["23-28", "<=22"],
            "campPlaced": ["yes", "no"],
            "weighted_count": [50.0, 10.0],
            "weighted_return_rate": [0.8, 0.6],
            "unweighted_n": [20, 5],
        }
    )
    prepared = module.prepare_retention_by_age_band(df)
    assert prepared["small_n"].tolist() == [False, True]
    assert list(prepared["age_band"].cat.categories) == module.AGE_LABELS


def test_prepare_retention_trends_filters_segment():
    module = load_module()
    df = pd.DataFrame(
        {
            "segment": ["overall", "under30"],
            "campPlaced": ["all", "all"],
            "cohort_year": [2020, 2020],
            "weighted_count": [40.0, 40.0],
            "weighted_return_rate": [0.8, 0.7],
            "unweighted_n": [10, 10],
        }
    )
    prepared = module.prepare_retention_trends(df)
    assert prepared["segment"].unique().tolist() == ["overall"]
