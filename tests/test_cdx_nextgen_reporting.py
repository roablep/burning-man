from __future__ import annotations

import sys
from pathlib import Path


def load_module():
    base = Path(__file__).resolve().parents[1] / "src" / "census_field_notes"
    sys.path.insert(0, str(base))
    from modules import cdx_analyze_nextgen_engagement as module  # type: ignore

    return module


def test_make_metric_suppression_behavior():
    module = load_module()
    metric = module.make_metric(
        group_type="year",
        group_value="2025",
        metric_name="next_gen_share",
        metric_value=0.12,
        n=4,
        year_scope="2025",
        question_family="all",
        min_cell_n=20,
    )
    assert metric["metric_value"] == ""
    assert str(metric["notes"]).startswith("suppressed_low_n")


def test_build_engagement_metrics_generates_year_rows():
    module = load_module()
    rows = [
        {
            "year": "2024",
            "next_gen_flag": "1",
            "question_family": "Transformation",
            "tenure_band": "Virgin",
            "response_len_words": "50",
            "answered_open_questions": "3",
            "age_band_nextgen": "<25",
        },
        {
            "year": "2024",
            "next_gen_flag": "0",
            "question_family": "Transformation",
            "tenure_band": "Veteran",
            "response_len_words": "45",
            "answered_open_questions": "2",
            "age_band_nextgen": "40+",
        },
    ]

    metrics = module.build_engagement_metrics(rows, min_cell_n=1)
    year_metrics = [m for m in metrics if m["group_type"] == "year" and m["metric_name"] == "next_gen_share"]
    assert len(year_metrics) == 1
    assert float(year_metrics[0]["metric_value"]) == 0.5
