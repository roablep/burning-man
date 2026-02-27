import sys
import os
import asyncio

# Ensure src/census_field_notes is in path to allow "import analysis_utils"
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules import (
    analyze_youth_voice,
    analyze_acculturation,
    analyze_belonging,
    analyze_return_intent,
)


async def main():
    print("=== Starting Next-Gen / Rising Sparks Pipeline ===")

    steps = [
        ("Module 7: Youth Voice", analyze_youth_voice.run_analysis),
        ("Module 8: Acculturation Journey", analyze_acculturation.run_analysis),
        ("Module 9: Belonging & Camp Effect", analyze_belonging.run_analysis),
        ("Module 10: Return Intent Signals", analyze_return_intent.run_analysis),
    ]

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

    print("\n=== Next-Gen Pipeline Complete ===")
    print("Reports written to:")
    print("  reports/module_7_youth_voice.md")
    print("  reports/module_8_acculturation.md")
    print("  reports/module_9_belonging.md")
    print("  reports/module_10_return_intent.md")


if __name__ == "__main__":
    asyncio.run(main())
