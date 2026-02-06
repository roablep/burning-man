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
        / "census2025_cohort_briefing.py"
    )
    spec = importlib.util.spec_from_file_location("cohort_briefing", script_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_compute_trend_slope():
    module = load_module()
    trends = pd.DataFrame(
        {
            "segment": ["overall", "overall"],
            "campPlaced": ["all", "all"],
            "cohort_year": [2020, 2021],
            "weighted_return_rate": [0.5, 0.6],
        }
    )
    slope, n = module.compute_trend_slope(trends)
    assert n == 2
    assert np.isclose(slope, 0.1)


def test_compute_age_band_gaps():
    module = load_module()
    retention = pd.DataFrame(
        {
            "age_band": ["<=22", "<=22"],
            "campPlaced": ["yes", "no"],
            "weighted_return_rate": [0.8, 0.5],
        }
    )
    gaps = module.compute_age_band_gaps(retention)
    row = gaps.iloc[0]
    assert np.isclose(row["gap_yes_minus_no"], 0.3)
