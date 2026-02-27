from __future__ import annotations

import argparse
import os
import statistics
from collections import Counter, defaultdict
from typing import Dict, Iterable, List

from ._nextgen_common import read_csv, write_csv

DEFAULT_OUTPUT_DIR = "reports/field_notes/next_gen"
BASE_FILENAME = "nextgen_pooled_base.csv"
TABLE_FILENAME = "nextgen_engagement_tables.csv"
SUMMARY_FILENAME = "nextgen_engagement_summary.md"


def to_int(value: str | int | None) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(float(value))
    except ValueError:
        return None


def mean_or_none(values: Iterable[int]) -> float | None:
    values_list = list(values)
    if not values_list:
        return None
    return float(statistics.mean(values_list))


def make_metric(
    group_type: str,
    group_value: str,
    metric_name: str,
    metric_value: float | int | None,
    n: int,
    year_scope: str,
    question_family: str,
    min_cell_n: int,
    notes: str = "",
) -> Dict[str, object]:
    suppressed = n < min_cell_n
    display_value = "" if suppressed or metric_value is None else metric_value
    note_parts = []
    if suppressed:
        note_parts.append(f"suppressed_low_n<{min_cell_n}")
    if notes:
        note_parts.append(notes)
    return {
        "group_type": group_type,
        "group_value": group_value,
        "metric_name": metric_name,
        "metric_value": display_value,
        "n": n,
        "year_scope": year_scope,
        "question_family": question_family,
        "notes": ";".join(note_parts),
    }


def build_engagement_metrics(rows: List[Dict[str, str]], min_cell_n: int = 20) -> List[Dict[str, object]]:
    metrics: List[Dict[str, object]] = []

    by_year = defaultdict(list)
    for row in rows:
        by_year[str(row["year"])].append(row)

    for year, group in sorted(by_year.items()):
        known_flags = [to_int(r.get("next_gen_flag")) for r in group if to_int(r.get("next_gen_flag")) is not None]
        n_known = len(known_flags)
        next_gen_n = sum(known_flags)
        share = (next_gen_n / n_known) if n_known else None
        metrics.append(
            make_metric(
                group_type="year",
                group_value=year,
                metric_name="next_gen_share",
                metric_value=share,
                n=n_known,
                year_scope=year,
                question_family="all",
                min_cell_n=min_cell_n,
            )
        )

    by_family = defaultdict(list)
    for row in rows:
        by_family[row.get("question_family", "Unknown")].append(row)

    for family, group in sorted(by_family.items()):
        known_flags = [to_int(r.get("next_gen_flag")) for r in group if to_int(r.get("next_gen_flag")) is not None]
        n_known = len(known_flags)
        next_gen_n = sum(known_flags)
        share = (next_gen_n / n_known) if n_known else None
        metrics.append(
            make_metric(
                group_type="question_family",
                group_value=family,
                metric_name="next_gen_share",
                metric_value=share,
                n=n_known,
                year_scope="pooled",
                question_family=family,
                min_cell_n=min_cell_n,
            )
        )

    next_gen_rows = [r for r in rows if to_int(r.get("next_gen_flag")) == 1]
    by_tenure = defaultdict(list)
    for row in next_gen_rows:
        by_tenure[row.get("tenure_band", "Unknown")].append(row)

    for tenure, group in sorted(by_tenure.items()):
        word_lengths = [to_int(r.get("response_len_words")) for r in group]
        word_lengths = [x for x in word_lengths if x is not None]
        answered = [to_int(r.get("answered_open_questions")) for r in group]
        answered = [x for x in answered if x is not None]

        metrics.append(
            make_metric(
                group_type="next_gen_tenure",
                group_value=tenure,
                metric_name="avg_response_len_words",
                metric_value=mean_or_none(word_lengths),
                n=len(word_lengths),
                year_scope="pooled",
                question_family="all",
                min_cell_n=min_cell_n,
            )
        )
        metrics.append(
            make_metric(
                group_type="next_gen_tenure",
                group_value=tenure,
                metric_name="avg_answered_open_questions",
                metric_value=mean_or_none(answered),
                n=len(answered),
                year_scope="pooled",
                question_family="all",
                min_cell_n=min_cell_n,
            )
        )

    age_counter = Counter(r.get("age_band_nextgen", "Unknown") for r in next_gen_rows)
    total_next_gen = sum(age_counter.values())
    for age_band, count in sorted(age_counter.items()):
        metrics.append(
            make_metric(
                group_type="next_gen_age_band",
                group_value=age_band,
                metric_name="share_within_next_gen",
                metric_value=(count / total_next_gen) if total_next_gen else None,
                n=count,
                year_scope="pooled",
                question_family="all",
                min_cell_n=min_cell_n,
            )
        )

    return metrics


def build_summary(rows: List[Dict[str, str]], metrics: List[Dict[str, object]], min_cell_n: int) -> str:
    total = len(rows)
    next_gen_rows = [r for r in rows if to_int(r.get("next_gen_flag")) == 1]
    known_age = [r for r in rows if to_int(r.get("next_gen_flag")) is not None]

    lines = [
        "# Next Gen Engagement Summary",
        "",
        f"- Total pooled records: **{total}**",
        f"- Records with known age band: **{len(known_age)}**",
        f"- Next Gen (<30) records: **{len(next_gen_rows)}**",
        f"- Suppression threshold: cells with n < **{min_cell_n}**",
        "",
        "## Highlights",
    ]

    year_rows = [m for m in metrics if m["group_type"] == "year" and m["metric_name"] == "next_gen_share"]
    for row in sorted(year_rows, key=lambda x: x["group_value"]):
        value = row["metric_value"]
        if value == "":
            lines.append(f"- {row['group_value']}: suppressed due to low n ({row['n']}).")
        else:
            lines.append(f"- {row['group_value']}: Next Gen share = {float(value):.1%} (n={row['n']}).")

    lines.append("")
    lines.append("## Notes")
    lines.append("- This module is descriptive and intended to frame deeper acculturation/theme analyses.")
    lines.append("- Metrics are pooled across years unless noted in `year_scope`.")
    return "\n".join(lines)


def run_analysis(
    input_csv: str,
    output_dir: str = DEFAULT_OUTPUT_DIR,
    min_cell_n: int = 20,
) -> tuple[str, str]:
    rows = read_csv(input_csv)
    metrics = build_engagement_metrics(rows, min_cell_n=min_cell_n)

    table_path = os.path.join(output_dir, TABLE_FILENAME)
    summary_path = os.path.join(output_dir, SUMMARY_FILENAME)

    write_csv(
        table_path,
        metrics,
        [
            "group_type",
            "group_value",
            "metric_name",
            "metric_value",
            "n",
            "year_scope",
            "question_family",
            "notes",
        ],
    )

    summary = build_summary(rows, metrics, min_cell_n=min_cell_n)
    os.makedirs(output_dir, exist_ok=True)
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write(summary)

    print(f"Wrote engagement summary: {summary_path}")
    print(f"Wrote engagement table: {table_path}")
    return summary_path, table_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Next Gen engagement descriptive analysis.")
    parser.add_argument("--input-csv", default=os.path.join(DEFAULT_OUTPUT_DIR, BASE_FILENAME))
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--min-cell-n", type=int, default=20)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run_analysis(input_csv=args.input_csv, output_dir=args.output_dir, min_cell_n=args.min_cell_n)


if __name__ == "__main__":
    main()
