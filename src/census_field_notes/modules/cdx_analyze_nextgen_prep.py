from __future__ import annotations

import argparse
import csv
import os
from typing import Dict, Iterable, List

from .cdx_nextgen_common import (
    age_band_nextgen,
    collect_open_ended_text,
    count_words,
    map_question_family,
    normalize_tenure,
    safe_int,
    write_csv,
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
DEFAULT_OUTPUT_DIR = "reports/field_notes/cdx_next_gen"
OUTPUT_FILENAME = "cdx_nextgen_pooled_base.csv"


def source_path_for_year(year: int) -> str:
    return os.path.join(DATA_DIR, f"{year}-field-note-transcriptions-normalized.csv")


def build_base_record(row: Dict[str, str], year: int, next_gen_cutoff: int) -> Dict[str, object]:
    age = safe_int(row.get("Norm_Age"))
    burn_count = safe_int(row.get("Norm_Burn_Count"))
    combined_text, answered_count = collect_open_ended_text(row, min_q=5)
    question_family = map_question_family(year, row.get("Subfolder"))

    next_gen_flag: int | None
    if age is None:
        next_gen_flag = None
    else:
        next_gen_flag = int(age < next_gen_cutoff)

    return {
        "year": year,
        "folder": (row.get("Folder") or "").strip(),
        "subfolder": (row.get("Subfolder") or "").strip(),
        "filename": (row.get("Filename") or "").strip(),
        "entry_index": (row.get("EntryIndex") or "").strip(),
        "question_family": question_family,
        "norm_age": age if age is not None else "",
        "age_band_nextgen": age_band_nextgen(age),
        "next_gen_flag": "" if next_gen_flag is None else next_gen_flag,
        "norm_gender": (row.get("Norm_Gender") or "").strip(),
        "norm_region": (row.get("Norm_Region") or "").strip(),
        "norm_burn_count": burn_count if burn_count is not None else "",
        "tenure_band": normalize_tenure(row.get("Burn_Status")),
        "answered_open_questions": answered_count,
        "response_len_words": count_words(combined_text),
        "response_text_combined": combined_text,
    }


def build_pooled_base(years: Iterable[int], next_gen_cutoff: int) -> List[Dict[str, object]]:
    output: List[Dict[str, object]] = []
    for year in years:
        src = source_path_for_year(year)
        with open(src, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                output.append(build_base_record(row=row, year=year, next_gen_cutoff=next_gen_cutoff))
    return output


def run_analysis(
    years: Iterable[int] = (2024, 2025),
    next_gen_cutoff: int = 30,
    output_dir: str = DEFAULT_OUTPUT_DIR,
) -> str:
    rows = build_pooled_base(years=years, next_gen_cutoff=next_gen_cutoff)
    path = os.path.join(output_dir, OUTPUT_FILENAME)
    fieldnames = [
        "year",
        "folder",
        "subfolder",
        "filename",
        "entry_index",
        "question_family",
        "norm_age",
        "age_band_nextgen",
        "next_gen_flag",
        "norm_gender",
        "norm_region",
        "norm_burn_count",
        "tenure_band",
        "answered_open_questions",
        "response_len_words",
        "response_text_combined",
    ]
    write_csv(path, rows, fieldnames)
    print(f"Prepared pooled Next Gen base data: {path} ({len(rows)} rows)")
    return path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare pooled Next Gen base dataset.")
    parser.add_argument("--years", default="2024,2025", help="Comma-separated years (default: 2024,2025)")
    parser.add_argument("--next-gen-cutoff", type=int, default=30, help="Age cutoff for next_gen_flag")
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR, help="Output directory")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    years = [int(x.strip()) for x in args.years.split(",") if x.strip()]
    run_analysis(years=years, next_gen_cutoff=args.next_gen_cutoff, output_dir=args.output_dir)


if __name__ == "__main__":
    main()
