from __future__ import annotations

import sys
from pathlib import Path


def load_module():
    base = Path(__file__).resolve().parents[1] / "src" / "census_field_notes"
    sys.path.insert(0, str(base))
    from modules import analyze_nextgen_prep as module  # type: ignore

    return module


def test_build_base_record_nextgen_fields():
    module = load_module()
    row = {
        "Folder": "2024",
        "Subfolder": "A1 ",
        "Filename": "demo.txt",
        "EntryIndex": "4",
        "Q5": "I learned to rely on community.",
        "Q6": "",
        "Q7": "It changed me.",
        "Norm_Age": "24",
        "Norm_Burn_Count": "1",
        "Norm_Gender": "F",
        "Norm_Region": "US-West",
        "Burn_Status": "Virgin",
    }

    rec = module.build_base_record(row=row, year=2024, next_gen_cutoff=30)
    assert rec["question_family"] == "Transformation"
    assert rec["next_gen_flag"] == 1
    assert rec["age_band_nextgen"] == "<25"
    assert rec["tenure_band"] == "Virgin"
    assert rec["answered_open_questions"] == 2
    assert rec["response_len_words"] > 0


def test_build_base_record_unknown_age():
    module = load_module()
    row = {
        "Subfolder": "F1",
        "Q5": "No age available but text exists.",
        "Norm_Age": "",
        "Burn_Status": "",
    }

    rec = module.build_base_record(row=row, year=2025, next_gen_cutoff=30)
    assert rec["question_family"] == "Diversity & Inclusion"
    assert rec["next_gen_flag"] == ""
    assert rec["age_band_nextgen"] == "Unknown"
    assert rec["tenure_band"] == "Unknown"
