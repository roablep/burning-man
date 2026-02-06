import sys
import os
import asyncio
import argparse

# Ensure src/census is in path to allow "import analysis_utils"
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import modules dynamically to avoid top-level import errors if paths aren't set yet
from modules import (
    generate_basic_stats,
    analyze_descriptive_stats,
    analyze_transformation,
    analyze_survival,
    analyze_identity,
    analyze_symbolism,
    analyze_diversity,
    analyze_relationships,
    synthesize_report
)
import analyze_cross_theme

def parse_args():
    parser = argparse.ArgumentParser(description="Run the Burning Man analysis pipeline.")
    parser.add_argument(
        "--skip-cross-theme",
        action="store_true",
        help="Skip cross-theme cohort analysis (TF-IDF clustering + correlations).",
    )
    return parser.parse_args()


async def main():
    args = parse_args()
    print("=== Starting Analysis Pipeline ===")
    
    steps = [
        ("Module 0: Basic Stats", generate_basic_stats.run_analysis),
        ("Module 0b: Descriptive Stats by Theme", analyze_descriptive_stats.run_analysis),
        ("Module 1: Transformation", analyze_transformation.run_analysis),
        ("Module 2: Survival", analyze_survival.run_analysis),
        ("Module 3: Identity", analyze_identity.run_analysis),
        ("Module 4: Symbolism", analyze_symbolism.run_analysis),
        ("Module 5: Diversity", analyze_diversity.run_analysis),
        ("Module 6: Relationships", analyze_relationships.run_analysis),
        ("Synthesis: Final Report", synthesize_report.run_synthesis)
    ]

    if not args.skip_cross_theme:
        steps.append(("Cross-Theme Cohort Analysis", analyze_cross_theme.main))
    
    for name, func in steps:
        print(f"\n--- Running {name} ---")
        try:
            if asyncio.iscoroutinefunction(func):
                await func()
            else:
                func()
        except Exception as e:
            print(f"ERROR in {name}: {e}")
            import traceback
            traceback.print_exc()

    print("\n=== Pipeline Complete ===")

if __name__ == "__main__":
    asyncio.run(main())
