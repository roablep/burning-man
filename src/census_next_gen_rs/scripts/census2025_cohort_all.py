#!/usr/bin/env python3
"""Run the full 2025 cohort pipeline: retention, trends, visuals, briefing."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the full 2025 cohort pipeline (retention, trends, visuals, briefing).",
    )
    parser.add_argument(
        "--input",
        default="/Users/peter/Downloads/census2025_cleaned_weighted.xlsx",
        help="Path to the weighted 2025 XLSX file.",
    )
    parser.add_argument(
        "--sheet",
        default=0,
        help="Sheet name or index (defaults to first sheet).",
    )
    return parser.parse_args()


def run_step(step: str, args: list[str]) -> None:
    print(f"\n==> {step}")
    subprocess.run(args, check=True)


def main() -> None:
    args = parse_args()
    scripts_dir = Path(__file__).resolve().parent
    python = sys.executable

    retention = scripts_dir / "census2025_cohort_retention.py"
    trends = scripts_dir / "census2025_cohort_trends.py"
    visuals = scripts_dir / "census2025_cohort_visuals.py"
    briefing = scripts_dir / "census2025_cohort_briefing.py"

    run_step(
        "Cohort retention",
        [python, str(retention), "--input", str(args.input), "--sheet", str(args.sheet)],
    )
    run_step(
        "Cohort trends",
        [python, str(trends), "--input", str(args.input), "--sheet", str(args.sheet)],
    )
    run_step("Cohort visuals", [python, str(visuals)])
    run_step("Cohort briefing", [python, str(briefing)])

    print("\nAll cohort outputs generated.")


if __name__ == "__main__":
    main()
