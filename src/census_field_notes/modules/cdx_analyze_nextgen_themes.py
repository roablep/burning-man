from __future__ import annotations

import argparse
import math
import os
from collections import Counter, defaultdict
from typing import Dict, Iterable, List

from .cdx_nextgen_common import read_csv, tokenize, write_csv

DEFAULT_OUTPUT_DIR = "reports/field_notes/cdx_next_gen"
BASE_FILENAME = "cdx_nextgen_pooled_base.csv"
DELTA_FILENAME = "cdx_nextgen_theme_deltas.csv"
SUMMARY_FILENAME = "cdx_nextgen_theme_deltas.md"


def to_int(value: str | int | None) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(float(value))
    except ValueError:
        return None


def token_counter(rows: Iterable[Dict[str, str]]) -> Counter:
    counter = Counter()
    for row in rows:
        counter.update(tokenize(row.get("response_text_combined", "")))
    return counter


def prevalence(counter: Counter) -> Dict[str, float]:
    total = sum(counter.values())
    if not total:
        return {}
    return {token: count / total for token, count in counter.items()}


def build_delta_rows(group_a: List[Dict[str, str]], group_b: List[Dict[str, str]], segment: str, top_n: int = 40) -> List[Dict[str, object]]:
    c_a = token_counter(group_a)
    c_b = token_counter(group_b)
    p_a = prevalence(c_a)
    p_b = prevalence(c_b)

    tokens = set(p_a) | set(p_b)
    rows = []
    for token in tokens:
        delta = p_a.get(token, 0.0) - p_b.get(token, 0.0)
        rows.append(
            {
                "segment": segment,
                "token": token,
                "pct_a": p_a.get(token, 0.0),
                "pct_b": p_b.get(token, 0.0),
                "delta": delta,
                "n_a": len(group_a),
                "n_b": len(group_b),
            }
        )

    rows.sort(key=lambda r: abs(float(r["delta"])), reverse=True)
    return rows[:top_n]


def run_analysis(input_csv: str, output_dir: str = DEFAULT_OUTPUT_DIR) -> tuple[str, str]:
    rows = read_csv(input_csv)
    next_gen = [r for r in rows if to_int(r.get("next_gen_flag")) == 1]
    older = [r for r in rows if to_int(r.get("next_gen_flag")) == 0]

    all_rows = build_delta_rows(next_gen, older, segment="<30_vs_30+", top_n=80)

    for tenure in ["Virgin", "Sophomore", "Veteran", "Elder"]:
        ng_tenure = [r for r in next_gen if r.get("tenure_band") == tenure]
        ng_other = [r for r in next_gen if r.get("tenure_band") != tenure]
        if len(ng_tenure) < 20 or len(ng_other) < 20:
            continue
        all_rows.extend(
            build_delta_rows(ng_tenure, ng_other, segment=f"cdx_nextgen_{tenure}_vs_rest", top_n=30)
        )

    os.makedirs(output_dir, exist_ok=True)
    csv_path = os.path.join(output_dir, DELTA_FILENAME)
    write_csv(csv_path, all_rows, ["segment", "token", "pct_a", "pct_b", "delta", "n_a", "n_b"])

    primary = [r for r in all_rows if r["segment"] == "<30_vs_30+"]
    top_young = sorted(primary, key=lambda r: float(r["delta"]), reverse=True)[:10]
    top_old = sorted(primary, key=lambda r: float(r["delta"]))[:10]

    lines = [
        "# Next Gen Theme Deltas",
        "",
        "Comparative token prevalence between younger (<30) and older (30+) cohorts.",
        "",
        f"- n(<30)={len(next_gen)}, n(30+)={len(older)}",
        "",
        "## Tokens Over-indexed in <30",
    ]
    lines.extend([f"- `{r['token']}` (delta={float(r['delta']):.4f})" for r in top_young])
    lines.append("")
    lines.append("## Tokens Over-indexed in 30+")
    lines.extend([f"- `{r['token']}` (delta={float(r['delta']):.4f})" for r in top_old])

    md_path = os.path.join(output_dir, SUMMARY_FILENAME)
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"Wrote theme delta summary: {md_path}")
    print(f"Wrote theme delta table: {csv_path}")
    return md_path, csv_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Next Gen theme delta analysis.")
    parser.add_argument("--input-csv", default=os.path.join(DEFAULT_OUTPUT_DIR, BASE_FILENAME))
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run_analysis(input_csv=args.input_csv, output_dir=args.output_dir)


if __name__ == "__main__":
    main()
