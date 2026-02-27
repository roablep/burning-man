from __future__ import annotations

import argparse
import os
import re
from collections import defaultdict
from typing import Dict, Iterable, List

from .cdx_nextgen_common import read_csv, write_csv

DEFAULT_OUTPUT_DIR = "reports/field_notes/cdx_next_gen"
BASE_FILENAME = "cdx_nextgen_pooled_base.csv"
TABLE_FILENAME = "cdx_nextgen_pathways.csv"
SUMMARY_FILENAME = "cdx_nextgen_pathways.md"

HARDSHIP_PATTERNS = [
    r"\bheat\b", r"\bdust\b", r"\bdehydrat", r"\bhunger\b", r"\bexhaust", r"\bfatigue", r"\bcold\b", r"\bwind\b", r"\bmud\b",
]

BREAKTHROUGH_PATTERNS = [
    r"\bbreakthrough\b", r"\bchanged me\b", r"\blearned\b", r"\bgrew\b", r"\brealized\b", r"\btransformed\b", r"\bnew perspective\b",
]

LINK_PATTERNS = [r"\bbecause\b", r"\bthrough\b", r"\bdue to\b", r"\bafter\b", r"\bled to\b"]


def to_int(value: str | int | None) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(float(value))
    except ValueError:
        return None


def has_any(text: str, patterns: Iterable[str]) -> bool:
    lowered = text.lower()
    return any(re.search(p, lowered) for p in patterns)


def pathway_flags(text: str) -> Dict[str, int]:
    hardship = int(has_any(text, HARDSHIP_PATTERNS))
    breakthrough = int(has_any(text, BREAKTHROUGH_PATTERNS))
    linked = int(hardship and breakthrough and has_any(text, LINK_PATTERNS))
    return {
        "hardship": hardship,
        "breakthrough": breakthrough,
        "linked": linked,
    }


def build_pathway_rows(rows: List[Dict[str, str]]) -> List[Dict[str, object]]:
    output: List[Dict[str, object]] = []
    grouped = defaultdict(list)

    enriched = []
    for row in rows:
        flags = pathway_flags(row.get("response_text_combined", ""))
        enriched.append({**row, **flags})

    for row in enriched:
        grouped[("age_band_nextgen", row.get("age_band_nextgen", "Unknown"))].append(row)
        grouped[("tenure_band", row.get("tenure_band", "Unknown"))].append(row)

    for (group_type, group_value), group in sorted(grouped.items()):
        n = len(group)
        if n == 0:
            continue
        hardship_rate = sum(int(r["hardship"]) for r in group) / n
        breakthrough_rate = sum(int(r["breakthrough"]) for r in group) / n
        linked_rate = sum(int(r["linked"]) for r in group) / n

        for name, value in [
            ("hardship_rate", hardship_rate),
            ("breakthrough_rate", breakthrough_rate),
            ("linked_pathway_rate", linked_rate),
        ]:
            output.append(
                {
                    "group_type": group_type,
                    "group_value": group_value,
                    "metric_name": name,
                    "metric_value": value,
                    "n": n,
                    "year_scope": "pooled",
                    "question_family": "all",
                    "notes": "",
                }
            )

    return output


def run_analysis(input_csv: str, output_dir: str = DEFAULT_OUTPUT_DIR) -> tuple[str, str]:
    rows = read_csv(input_csv)
    pathway_rows = build_pathway_rows(rows)

    os.makedirs(output_dir, exist_ok=True)
    table_path = os.path.join(output_dir, TABLE_FILENAME)
    summary_path = os.path.join(output_dir, SUMMARY_FILENAME)

    write_csv(
        table_path,
        pathway_rows,
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

    lines = [
        "# Next Gen Pathways (Hardship to Growth)",
        "",
        "Rule-based pathway rates estimated from combined text across open-ended responses.",
        "",
    ]

    age_rows = [r for r in pathway_rows if r["group_type"] == "age_band_nextgen" and r["metric_name"] == "linked_pathway_rate"]
    for row in sorted(age_rows, key=lambda x: x["group_value"]):
        lines.append(f"- {row['group_value']}: linked pathway rate = {float(row['metric_value']):.1%} (n={row['n']})")

    with open(summary_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"Wrote pathways summary: {summary_path}")
    print(f"Wrote pathways table: {table_path}")
    return summary_path, table_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Next Gen hardship-to-growth pathway analysis.")
    parser.add_argument("--input-csv", default=os.path.join(DEFAULT_OUTPUT_DIR, BASE_FILENAME))
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run_analysis(input_csv=args.input_csv, output_dir=args.output_dir)


if __name__ == "__main__":
    main()
