from __future__ import annotations

import sys
from pathlib import Path


def load_module():
    base = Path(__file__).resolve().parents[1] / "src" / "census_field_notes"
    sys.path.insert(0, str(base))
    from modules import cdx_analyze_nextgen_acculturation as module  # type: ignore

    return module


def test_score_record_positive_and_friction_markers():
    module = load_module()
    text = (
        "I felt strong community connection and volunteered to help build camp. "
        "Later I felt judged and unsafe in one interaction."
    )
    score = module.score_record(text)

    assert score["positive_total"] > 0
    assert score["friction_total"] > 0
    assert score["net_score"] == score["positive_total"] - score["friction_total"]


def test_aggregate_metrics_suppresses_low_n():
    module = load_module()
    rows = []
    for _ in range(3):
        rows.append(
            {
                "question_family": "Transformation",
                "next_gen_label": "<30",
                "positive_total": "2",
                "friction_total": "1",
                "net_score": "1",
            }
        )

    metrics = module.aggregate_metrics(rows, min_cell_n=5)
    assert metrics
    assert all(m["metric_value"] == "" for m in metrics)
    assert all(str(m["notes"]).startswith("suppressed_low_n") for m in metrics)
