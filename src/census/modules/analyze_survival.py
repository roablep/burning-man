import sys
import os
import asyncio
from collections import Counter
from pydantic import BaseModel, Field
from typing import Literal

# Add parent directory to path to find analysis_utils
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import analysis_utils as utils

class SurvivalAnalysis(BaseModel):
    mentions_hardship: bool = Field(..., description="Does the participant mention physical hardships like mud, heat, dust, hunger, or exhaustion?")
    hardship_level: Literal["None", "Low", "Medium", "High"] = Field(..., description="The intensity of the physical ordeal described.")
    describes_breakthrough: bool = Field(..., description="Does the participant describe a significant emotional or spiritual breakthrough?")
    hardship_was_catalyst: bool = Field(..., description="Is the physical hardship explicitly described as the cause or catalyst for the breakthrough?")

async def run_analysis():
    print("Loading Survival and Transformation Data...")
    
    # 1. Establish Hardship Baseline (from Survival question sets)
    # Question set J (2024) is Survival
    survival_data = utils.load_data(2024, "Survival")
    survival_texts = [row.get("Q5", "") + " " + row.get("Q6", "") for row in survival_data if len(row.get("Q5", "")) > 10]
    
    # Analyze general hardship prevalence
    baseline_prompt = "Identify if this person mentions physical hardship (mud, heat, dust). Intensity: None, Low, Medium, High.\nText: \"{{TEXT}}\""
    baseline_results = await utils.batch_process_with_llm(survival_texts[:200], baseline_prompt, response_schema=SurvivalAnalysis)
    
    valid_baseline = [r for r in baseline_results if "error" not in r]
    baseline_hardship_pct = sum([1 for r in valid_baseline if r.get("mentions_hardship")]) / len(valid_baseline) if valid_baseline else 0
    
    # 2. Analyze Transformation narratives for the "Link"
    trans_data = utils.load_data(2024, "Transformation") + utils.load_data(2025, "Transformation")
    test_subjects = []
    for row in trans_data:
        narrative = " ".join([row.get(f"Q{i}", "") for i in range(5, 10)])
        if len(narrative.strip()) > 30:
            test_subjects.append(narrative)

    print(f"Total transformation narratives: {len(test_subjects)}")
    prompt = "Analyze this Burning Man transformation narrative. Determine if physical hardship played a role.\nNarrative: \"{{TEXT}}\""
    results = await utils.batch_process_with_llm(test_subjects, prompt, response_schema=SurvivalAnalysis)
    
    # Tally Results
    stats = Counter()
    valid_results = 0
    for i, res in enumerate(results):
        if isinstance(res, dict) and "error" in res: continue
        valid_results += 1
        if res.get("mentions_hardship"): stats["Hardship"] += 1
        if res.get("describes_breakthrough"): stats["Breakthrough"] += 1
        if res.get("hardship_was_catalyst"): stats["Linked"] += 1
        level = res.get("hardship_level", "None")
        stats[f"Level_{level}"] += 1

    # Dynamic Conclusion Logic
    total = valid_results
    if total == 0:
        conclusion = ["No valid narratives found."]
    else:
        linked_pct = stats['Linked'] / total
        hardship_mention_pct = stats['Hardship'] / total
        
        conclusion = []
        conclusion.append(f"**The Ordeal Gap:** While {baseline_hardship_pct:.1%} of participants in survival surveys report significant physical hardship, only {hardship_mention_pct:.1%} of those describing a transformation mention it as a factor.")
        
        if linked_pct > 0.15:
            conclusion.append(f"**Direct Link:** For {linked_pct:.1%} of participants, the 'Ordeal' is the explicit engine of their transformation.")
        elif linked_pct > 0.05:
            conclusion.append(f"**Normalization:** Hardship is common but rarely cited as the primary driver of epiphany, suggesting it is normalized as 'background noise' on the playa.")
        else:
            conclusion.append("**Hypothesis Weakened:** The 'Ordeal Hypothesis' is largely unsupported by the data; participants describe transformation through social and creative lenses, not physical survival.")

    # Generate Report
    report = ["# Module 2: The 'Ordeal' as Catalyst (Survival vs. Epiphany)\n"]
    report.append(f"**Methodology:** Comparative analysis of {len(valid_baseline)} survival responses (Baseline) vs {total} transformation narratives.\n")
    
    report.append("### Findings")
    report.append(f"- **Baseline Hardship Prevalence:** {baseline_hardship_pct:.1%}")
    report.append(f"- **Transformation Narratives Mentioning Hardship:** {hardship_mention_pct:.1%}")
    report.append(f"- **Hardship as Explicit Catalyst:** {linked_pct:.1%}")
    
    report.append("\n### Hardship Intensity (Transformation Set)")
    report.append("| Level | Count |")
    report.append("| :--- | :--- |")
    for level in ["High", "Medium", "Low", "None"]:
        report.append(f"| {level} | {stats[f'Level_{level}']} |")

    report.append("\n## Conclusion")
    report.append("> " + " ".join(conclusion))

    utils.save_report("module_2_survival.md", "\n".join(report))

if __name__ == "__main__":
    asyncio.run(run_analysis())