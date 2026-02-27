from __future__ import annotations

import argparse
import asyncio
import os

from modules import (
    cdx_analyze_nextgen_acculturation,
    cdx_analyze_nextgen_engagement,
    cdx_analyze_nextgen_pathways,
    cdx_analyze_nextgen_prep,
    cdx_analyze_nextgen_themes,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run cdx Next Gen / Rising Sparks exploratory analysis pipeline.")
    parser.add_argument("--years", default="2024,2025", help="Comma-separated years to include")
    parser.add_argument("--next-gen-cutoff", type=int, default=30)
    parser.add_argument("--min-cell-n", type=int, default=20)
    parser.add_argument("--enable-llm-validation", choices=["true", "false"], default="true")
    parser.add_argument("--llm-max-samples-per-cell", type=int, default=40)
    parser.add_argument("--output-dir", default="reports/field_notes/cdx_next_gen")
    return parser.parse_args()


def write_decision_memo(output_dir: str) -> str:
    memo_path = os.path.join(output_dir, "cdx_NEXT_GEN_EXPLORATORY_MEMO.md")
    lines = [
        "# cdx Next Gen / Rising Sparks Exploratory Memo",
        "",
        "## What This Package Contains",
        "- `cdx_nextgen_pooled_base.csv`: pooled and harmonized records (2024+2025 by default)",
        "- `cdx_nextgen_engagement_summary.md` + `cdx_nextgen_engagement_tables.csv`: composition and response-depth cuts",
        "- `cdx_nextgen_acculturation_summary.md` + `cdx_nextgen_acculturation_scores.csv`: proxy acculturation index",
        "- `cdx_nextgen_theme_deltas.md` + `cdx_nextgen_theme_deltas.csv`: language and theme deltas",
        "- `cdx_nextgen_pathways.md` + `cdx_nextgen_pathways.csv`: hardship-to-growth pathway rates",
        "",
        "## How To Use",
        "1. Start with engagement summary to identify viable segments (n and low-n suppression).",
        "2. Read acculturation summary by question family and age/tenure segment.",
        "3. Use theme deltas to translate findings into messaging/program hypotheses.",
        "4. Validate intervention ideas against pathway rates and low-n caveats.",
        "",
        "## Caveats",
        "- This output is exploratory and descriptive, not causal.",
        "- Cross-year pooling uses harmonized families; non-overlapping sets remain contextual.",
        "- LLM validation is optional and may be skipped when no API key is configured.",
    ]
    os.makedirs(output_dir, exist_ok=True)
    with open(memo_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return memo_path


async def main() -> None:
    args = parse_args()
    years = [int(x.strip()) for x in args.years.split(",") if x.strip()]
    output_dir = args.output_dir

    print("=== cdx Next Gen / Rising Sparks Pipeline ===")
    base_csv = cdx_analyze_nextgen_prep.run_analysis(
        years=years,
        next_gen_cutoff=args.next_gen_cutoff,
        output_dir=output_dir,
    )

    cdx_analyze_nextgen_engagement.run_analysis(
        input_csv=base_csv,
        output_dir=output_dir,
        min_cell_n=args.min_cell_n,
    )

    await cdx_analyze_nextgen_acculturation.run_analysis(
        input_csv=base_csv,
        output_dir=output_dir,
        min_cell_n=args.min_cell_n,
        enable_llm_validation=(args.enable_llm_validation == "true"),
        llm_max_samples_per_cell=args.llm_max_samples_per_cell,
    )

    cdx_analyze_nextgen_themes.run_analysis(input_csv=base_csv, output_dir=output_dir)
    cdx_analyze_nextgen_pathways.run_analysis(input_csv=base_csv, output_dir=output_dir)
    memo_path = write_decision_memo(output_dir)

    print(f"Decision memo written: {memo_path}")
    print("=== cdx Next Gen pipeline complete ===")


if __name__ == "__main__":
    asyncio.run(main())
