import asyncio
from collections import Counter
import analysis_utils as utils

async def run_analysis():
    print("Refining Survival vs. Epiphany Analysis...")
    data_2024 = utils.load_data(2024, "Transformation")
    data_2025 = utils.load_data(2025, "Transformation")
    
    # Combined narrative from all open-ended columns
    # For Set A, Q5-Q9 are the key qualitative answers
    test_subjects = []
    for row in (data_2024 + data_2025):
        narrative = " ".join([row.get(f"Q{i}", "") for i in range(5, 10)])
        if len(narrative.strip()) > 30:
            test_subjects.append(narrative)

    print(f"Total narratives to analyze: {len(test_subjects)}")
    
    prompt = """
    Analyze the following Burning Man field notes.
    1. Does the person mention physical hardship (Mud, Rain, Heat, Dust, Hunger, Exhaustion, Logistics)?
    2. Does the person describe a breakthrough or shift?
    3. Is the hardship explicitly linked to the breakthrough? (Yes/No).
    
    Format: Hardship: [Yes/No], Breakthrough: [Yes/No], Linked: [Yes/No]
    
    Notes: "{TEXT}"""
    
    results = await utils.batch_process_with_llm(test_subjects[:150], prompt)
    
    stats = Counter()
    for res in results:
        if "ERROR" in res: continue
        if "Hardship: Yes" in res: stats["Hardship"] += 1
        if "Breakthrough: Yes" in res: stats["Breakthrough"] += 1
        if "Linked: Yes" in res: stats["Linked"] += 1

    report = ["# Module 2: The 'Ordeal' as Catalyst (Survival vs. Epiphany) - REFINED\n"]
    report.append(f"Analyzed {len(results)} multi-column narratives.\n")
    
    report.append("### Findings")
    report.append(f"- **Mentions Hardship:** {stats['Hardship']}")
    report.append(f"- **Mentions Breakthrough:** {stats['Breakthrough']}")
    report.append(f"- **Hardship as Catalyst:** {stats['Linked']}")
    
    report.append("\n**Conclusion:**")
    if stats['Linked'] > 0:
        report.append(f"> Found {stats['Linked']} participants who explicitly connected their growth to the physical struggle of the event.")
    
    utils.save_report("module_2_survival.md", "\n".join(report))

if __name__ == "__main__":
    asyncio.run(run_analysis())
