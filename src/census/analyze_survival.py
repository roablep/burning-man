import asyncio
from collections import Counter
from pydantic import BaseModel, Field
from typing import Literal
import analysis_utils as utils

class SurvivalAnalysis(BaseModel):
    mentions_hardship: bool = Field(..., description="Does the participant mention physical hardships like mud, heat, dust, hunger, or exhaustion?")
    hardship_level: Literal["None", "Low", "Medium", "High"] = Field(..., description="The intensity of the physical ordeal described.")
    describes_breakthrough: bool = Field(..., description="Does the participant describe a significant emotional or spiritual breakthrough?")
    hardship_was_catalyst: bool = Field(..., description="Is the physical hardship explicitly described as the cause or catalyst for the breakthrough?")

async def run_analysis():
    print("Refining Survival vs. Epiphany Analysis (Structured).")
    
    # Load Data
    data_2024 = utils.load_data(2024, "Transformation")
    data_2025 = utils.load_data(2025, "Transformation")
    
    # Extract Narratives
    test_subjects = []
    for row in (data_2024 + data_2025):
        # Join Q5-Q9 to get full context
        narrative = " ".join([row.get(f"Q{i}", "") for i in range(5, 10)])
        if len(narrative.strip()) > 30:
            test_subjects.append(narrative)

    print(f"Total narratives to analyze: {len(test_subjects)}")
    
    # Prompt (Simplified now that we have a schema)
    prompt = """
    Analyze this Burning Man transformation narrative.
    Determine if physical hardship (the 'Ordeal') played a role in their transformation.
    
    Narrative: "{{TEXT}}"
    """
    
    # Run Batch Process with Schema
    results = await utils.batch_process_with_llm(
        test_subjects, 
        prompt,
        response_schema=SurvivalAnalysis
    )
    
    # Tally Results
    stats = Counter()
    linked_examples = []

    valid_results = 0
    for i, res in enumerate(results):
        if isinstance(res, dict) and "error" in res: continue
        valid_results += 1
        
        # res is a dict matching the Pydantic model
        if res.get("mentions_hardship"): stats["Hardship"] += 1
        if res.get("describes_breakthrough"): stats["Breakthrough"] += 1
        if res.get("hardship_was_catalyst"): 
            stats["Linked"] += 1
            # Save a snippet for the report
            linked_examples.append(test_subjects[i][:200] + "...")

        level = res.get("hardship_level", "None")
        stats[f"Level_{level}"] += 1

    # Dynamic Conclusion Logic
    total = valid_results
    if total == 0:
        conclusion = ["No valid narratives found for analysis."]
    else:
        linked_pct = stats['Linked'] / total
        hardship_pct = stats['Hardship'] / total
        breakthrough_pct = stats['Breakthrough'] / total
        
        conclusion = []
        conclusion.append(f"**Prevalence of Hardship:** {hardship_pct:.1%} of transformation narratives explicitly mention physical hardships.")
        
        if linked_pct > 0.20:
            conclusion.append(f"**Catalytic Role:** For a significant minority ({linked_pct:.1%}), this hardship was explicitly cited as the driver of their breakthrough.")
        elif linked_pct > 0.05:
            conclusion.append(f"**Occasional Catalyst:** While hardship is common, only {linked_pct:.1%} of participants explicitly link it as the cause of their transformation.")
        else:
            conclusion.append(f"**Rarely Causal:** Despite the prevalence of hardship ({hardship_pct:.1%}), it is almost never ({linked_pct:.1%}) described as the primary catalyst for epiphany.")

    # Generate Report
    report = ["# Module 2: The 'Ordeal' as Catalyst (Survival vs. Epiphany)\n"]
    report.append(f"**Methodology:** Analyzed {len(results)} narratives using structured LLM extraction.\n")
    
    report.append("### Findings")
    report.append(f"- **Mentions Hardship:** {stats['Hardship']} ({stats['Hardship']/len(results):.1%})")
    report.append(f"- **Mentions Breakthrough:** {stats['Breakthrough']} ({stats['Breakthrough']/len(results):.1%})")
    report.append(f"- **Hardship as Catalyst:** {stats['Linked']} ({stats['Linked']/len(results):.1%})")
    
    report.append("\n### Hardship Intensity Distribution")
    report.append("| Level | Count |")
    report.append("| :--- | :--- |")
    for level in ["High", "Medium", "Low", "None"]:
        report.append(f"| {level} | {stats[f'Level_{level}']} |")

    report.append("\n### Examples of the 'Ordeal' leading to Transformation")
    if linked_examples:
        for ex in linked_examples[:5]:
            report.append(f"- *\"{ex}\"*")
    else:
        report.append("*None found in this sample.*")

    report.append("\n## Conclusion")
    report.append("> " + " ".join(conclusion))

    utils.save_report("module_2_survival.md", "\n".join(report))

if __name__ == "__main__":
    asyncio.run(run_analysis())