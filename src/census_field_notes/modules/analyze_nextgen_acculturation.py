from __future__ import annotations

import argparse
import asyncio
import os
import random
import re
from collections import Counter, defaultdict
from typing import Dict, Iterable, List

from pydantic import BaseModel, Field

from ._nextgen_common import read_csv, write_csv

DEFAULT_OUTPUT_DIR = "reports/field_notes/next_gen"
BASE_FILENAME = "nextgen_pooled_base.csv"
SCORES_FILENAME = "nextgen_acculturation_scores.csv"
VALIDATION_FILENAME = "nextgen_acculturation_validation.csv"
SUMMARY_FILENAME = "nextgen_acculturation_summary.md"

POSITIVE_MARKERS = {
    "belonging_community": [
        r"\bbelong", r"\bcommunity", r"\bconnection", r"\bfamily", r"\bsupported", r"\btogether",
    ],
    "contribution_service": [
        r"\bvolunteer", r"\bbuild", r"\bhelp(ed|ing)?\b", r"\bgift(ing)?\b", r"\bserve", r"\bcontribut",
    ],
    "identity_integration": [
        r"\bauthentic", r"\btrue self", r"\bself[- ]expression", r"\bseen", r"\baccepted", r"\bconfidence",
    ],
    "agency_self_efficacy": [
        r"\blearn(ed|ing)?\b", r"\bcan do", r"\bcapable", r"\bresilien", r"\badapt", r"\bgrew\b",
    ],
}

FRICTION_MARKERS = {
    "exclusion_friction": [
        r"\bexclude", r"\bignored", r"\bunsafe", r"\bjudg", r"\bharass", r"\bdiscrimin", r"\balienat",
    ]
}


class AcculturationValidation(BaseModel):
    positive_markers: int = Field(..., description="Count of positive acculturation signals in the text.")
    friction_markers: int = Field(..., description="Count of friction/exclusion signals in the text.")
    net_score: int = Field(..., description="positive_markers - friction_markers")


def to_int(value: str | int | None) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(float(value))
    except ValueError:
        return None


def count_matches(text: str, patterns: Iterable[str]) -> int:
    total = 0
    lowered = text.lower()
    for pattern in patterns:
        total += len(re.findall(pattern, lowered))
    return total


def score_record(text: str) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    positive_total = 0
    friction_total = 0

    for name, patterns in POSITIVE_MARKERS.items():
        value = count_matches(text, patterns)
        counts[name] = value
        positive_total += value

    for name, patterns in FRICTION_MARKERS.items():
        value = count_matches(text, patterns)
        counts[name] = value
        friction_total += value

    counts["positive_total"] = positive_total
    counts["friction_total"] = friction_total
    counts["net_score"] = positive_total - friction_total
    return counts


def aggregate_metrics(rows: List[Dict[str, str]], min_cell_n: int) -> List[Dict[str, object]]:
    output: List[Dict[str, object]] = []
    groups = defaultdict(list)

    for row in rows:
        next_gen = to_int(row.get("next_gen_flag"))
        label = "<30" if next_gen == 1 else "30+" if next_gen == 0 else "unknown"
        key = (label, row.get("question_family", "Unknown"))
        groups[key].append(row)

    for (label, family), group in sorted(groups.items()):
        n = len(group)
        suppressed = n < min_cell_n

        mean_net = sum(float(r["net_score"]) for r in group) / n if n else 0.0
        mean_positive = sum(float(r["positive_total"]) for r in group) / n if n else 0.0
        mean_friction = sum(float(r["friction_total"]) for r in group) / n if n else 0.0

        for metric_name, metric_value in [
            ("mean_net_acculturation", mean_net),
            ("mean_positive_markers", mean_positive),
            ("mean_friction_markers", mean_friction),
        ]:
            output.append(
                {
                    "group_type": "acculturation_group",
                    "group_value": label,
                    "metric_name": metric_name,
                    "metric_value": "" if suppressed else metric_value,
                    "n": n,
                    "year_scope": "pooled",
                    "question_family": family,
                    "notes": f"suppressed_low_n<{min_cell_n}" if suppressed else "",
                }
            )

    return output


async def run_llm_validation(
    scored_rows: List[Dict[str, str]],
    max_samples_per_cell: int,
    min_cell_n: int,
) -> List[Dict[str, object]]:
    from .. import analysis_utils as utils

    if not os.getenv("GEMINI_API_KEY"):
        return [
            {
                "cell": "all",
                "sample_size": 0,
                "mean_det_net": "",
                "mean_llm_net": "",
                "mean_abs_delta": "",
                "notes": "skipped_no_gemini_api_key",
            }
        ]

    grouped = defaultdict(list)
    for row in scored_rows:
        key = (row["next_gen_label"], row.get("question_family", "Unknown"))
        grouped[key].append(row)

    validation_rows: List[Dict[str, object]] = []
    prompt = (
        "Read the field-note response and estimate acculturation signals. "
        "Count positive acculturation markers, count friction markers, and return net score.\n"
        "Response: {{TEXT}}"
    )

    for (label, family), group in sorted(grouped.items()):
        if len(group) < min_cell_n:
            continue

        sample = group[:]
        random.shuffle(sample)
        sample = sample[:max_samples_per_cell]
        texts = [r["response_text_combined"] for r in sample]
        llm_results = await utils.batch_process_with_llm(
            texts,
            prompt_template=prompt,
            response_schema=AcculturationValidation,
            batch_size=8,
            rate_limit_delay=0.25,
        )

        paired = []
        for det, llm in zip(sample, llm_results, strict=False):
            if not isinstance(llm, dict) or "error" in llm:
                continue
            try:
                llm_net = int(llm.get("net_score", 0))
            except (TypeError, ValueError):
                continue
            det_net = int(det["net_score"])
            paired.append(abs(det_net - llm_net))

        if not paired:
            continue

        validation_rows.append(
            {
                "cell": f"{label}|{family}",
                "sample_size": len(paired),
                "mean_det_net": sum(int(r["net_score"]) for r in sample[: len(paired)]) / len(paired),
                "mean_llm_net": "",  # not needed for memo, keep compact
                "mean_abs_delta": sum(paired) / len(paired),
                "notes": "",
            }
        )

    if not validation_rows:
        validation_rows.append(
            {
                "cell": "all",
                "sample_size": 0,
                "mean_det_net": "",
                "mean_llm_net": "",
                "mean_abs_delta": "",
                "notes": "no_cells_met_validation_criteria",
            }
        )

    return validation_rows


def build_summary(scored_rows: List[Dict[str, str]], metrics: List[Dict[str, object]], llm_enabled: bool) -> str:
    next_gen = [r for r in scored_rows if r["next_gen_label"] == "<30"]
    older = [r for r in scored_rows if r["next_gen_label"] == "30+"]

    def avg_net(rows: List[Dict[str, str]]) -> float:
        if not rows:
            return 0.0
        return sum(float(r["net_score"]) for r in rows) / len(rows)

    lines = [
        "# Next Gen Acculturation Summary",
        "",
        "Lexicon proxy index: positive markers (belonging, contribution, identity integration, agency) minus friction markers.",
        "",
        f"- Mean net score, <30: **{avg_net(next_gen):.3f}** (n={len(next_gen)})",
        f"- Mean net score, 30+: **{avg_net(older):.3f}** (n={len(older)})",
        f"- LLM validation enabled: **{'yes' if llm_enabled else 'no'}**",
        "",
        "## Notes",
        "- This is exploratory proxying, not a causal estimate.",
        "- Use question-family slices and low-n flags before operational decisions.",
    ]

    suppressed_count = sum(1 for m in metrics if str(m.get("notes", "")).startswith("suppressed_low_n"))
    lines.append(f"- Suppressed metric cells: **{suppressed_count}**")

    return "\n".join(lines)


async def run_analysis(
    input_csv: str,
    output_dir: str = DEFAULT_OUTPUT_DIR,
    min_cell_n: int = 20,
    enable_llm_validation: bool = True,
    llm_max_samples_per_cell: int = 40,
) -> tuple[str, str, str]:
    rows = read_csv(input_csv)
    scored_rows: List[Dict[str, str]] = []

    for row in rows:
        text = row.get("response_text_combined", "")
        score = score_record(text)
        next_gen = to_int(row.get("next_gen_flag"))
        scored_rows.append(
            {
                **row,
                **{k: str(v) for k, v in score.items()},
                "next_gen_label": "<30" if next_gen == 1 else "30+" if next_gen == 0 else "unknown",
            }
        )

    metrics = aggregate_metrics(scored_rows, min_cell_n=min_cell_n)

    validation_rows: List[Dict[str, object]]
    if enable_llm_validation:
        validation_rows = await run_llm_validation(
            scored_rows=scored_rows,
            max_samples_per_cell=llm_max_samples_per_cell,
            min_cell_n=min_cell_n,
        )
    else:
        validation_rows = [
            {
                "cell": "all",
                "sample_size": 0,
                "mean_det_net": "",
                "mean_llm_net": "",
                "mean_abs_delta": "",
                "notes": "skipped_disabled",
            }
        ]

    os.makedirs(output_dir, exist_ok=True)
    scores_path = os.path.join(output_dir, SCORES_FILENAME)
    validation_path = os.path.join(output_dir, VALIDATION_FILENAME)
    summary_path = os.path.join(output_dir, SUMMARY_FILENAME)

    write_csv(
        scores_path,
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
    write_csv(
        validation_path,
        validation_rows,
        ["cell", "sample_size", "mean_det_net", "mean_llm_net", "mean_abs_delta", "notes"],
    )

    summary = build_summary(scored_rows, metrics, llm_enabled=enable_llm_validation)
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write(summary)

    print(f"Wrote acculturation summary: {summary_path}")
    print(f"Wrote acculturation metrics: {scores_path}")
    print(f"Wrote acculturation validation: {validation_path}")
    return summary_path, scores_path, validation_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Next Gen acculturation proxy analysis.")
    parser.add_argument("--input-csv", default=os.path.join(DEFAULT_OUTPUT_DIR, BASE_FILENAME))
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--min-cell-n", type=int, default=20)
    parser.add_argument("--enable-llm-validation", choices=["true", "false"], default="true")
    parser.add_argument("--llm-max-samples-per-cell", type=int, default=40)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    asyncio.run(
        run_analysis(
            input_csv=args.input_csv,
            output_dir=args.output_dir,
            min_cell_n=args.min_cell_n,
            enable_llm_validation=args.enable_llm_validation == "true",
            llm_max_samples_per_cell=args.llm_max_samples_per_cell,
        )
    )


if __name__ == "__main__":
    main()
