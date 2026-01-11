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
    
    # Analyze general hardship prevalence by Age
    age_baselines = {"Under 30": [], "30-39": [], "40-49": [], "50+": []}
    for row in survival_data:
        text = row.get("Q5", "") + " " + row.get("Q6", "")
        if len(row.get("Q5", "")) > 10:
            age = utils.get_age_bucket(row.get("Norm_Age"))
            if age in age_baselines:
                age_baselines[age].append(text)
    
    baseline_stats = {}
    baseline_prompt = "Identify if this person mentions physical hardship (mud, heat, dust). Intensity: None, Low, Medium, High.\nText: \"{{TEXT}}\""
    
    print("Analyzing Baseline Hardship by Age...")
    for age, texts in age_baselines.items():
        if not texts:
            baseline_stats[age] = 0
            continue
        # Limit sample for baseline to save tokens/time
        res = await utils.batch_process_with_llm(texts[:50], baseline_prompt, response_schema=SurvivalAnalysis)
        valid = [r for r in res if "error" not in r]
        pct = sum([1 for r in valid if r.get("mentions_hardship")]) / len(valid) if valid else 0
        baseline_stats[age] = pct

    # Overall Baseline (for original report section)
    all_survival_texts = [t for sublist in age_baselines.values() for t in sublist]
    # We already have age-specific stats, can weigh them or just use the aggregate logic if we want total. 
    # Let's keep the logic consistent with the previous version for the main section, or just aggregate.
    # To save re-running, let's just use the age stats to infer total if needed, but the original code re-ran a batch.
    # We'll just skip the redundant total run and use the aggregate of the age runs for the total stats? 
    # Or just keep the age analysis additive.
    
    # 2. Analyze Transformation narratives for the "Link"
    trans_data = utils.load_data(2024, "Transformation") + utils.load_data(2025, "Transformation")
    test_subjects = [] # List of (age, narrative)
    
    for row in trans_data:
        narrative = " ".join([row.get(f"Q{i}", "") for i in range(5, 10)])
        if len(narrative.strip()) > 30:
            age = utils.get_age_bucket(row.get("Norm_Age"))
            test_subjects.append((age, narrative))

    print(f"Total transformation narratives: {len(test_subjects)}")
    prompt = "Analyze this Burning Man transformation narrative. Determine if physical hardship played a role.\nNarrative: \"{{TEXT}}\""
    
    # We need to process them, then bucket the results by age
    narratives_only = [x[1] for x in test_subjects]
    results = await utils.batch_process_with_llm(narratives_only, prompt, response_schema=SurvivalAnalysis)
    
    # Tally Results by Age
    age_link_stats = {a: {"Hardship": 0, "Linked": 0, "Total": 0} for a in age_baselines.keys()}
    
    # Tally Results (Overall)
    stats = Counter()
    valid_results = 0
    
    for i, res in enumerate(results):
        if isinstance(res, dict) and "error" in res: continue
        valid_results += 1
        
        age_group = test_subjects[i][0]
        
        # Overall Stats
        if res.get("mentions_hardship"): stats["Hardship"] += 1
        if res.get("describes_breakthrough"): stats["Breakthrough"] += 1
        if res.get("hardship_was_catalyst"): stats["Linked"] += 1
        level = res.get("hardship_level", "None")
        stats[f"Level_{level}"] += 1
        
        # Age Stats
        if age_group in age_link_stats:
            age_link_stats[age_group]["Total"] += 1
            if res.get("mentions_hardship"): age_link_stats[age_group]["Hardship"] += 1
            if res.get("hardship_was_catalyst"): age_link_stats[age_group]["Linked"] += 1

    # Dynamic Conclusion Logic
    total = valid_results
    if total == 0:
        conclusion = ["No valid narratives found."]
        baseline_hardship_pct = 0 # Fallback
    else:
        linked_pct = stats['Linked'] / total
        hardship_mention_pct = stats['Hardship'] / total
        # Calculate weighted average for total baseline or just take mean of age baselines
        baseline_hardship_pct = sum(baseline_stats.values()) / 4 # Rough approx
        
        conclusion = []
        conclusion.append(f"**The Ordeal Gap:** Hardship is prevalent (Baseline ~{baseline_hardship_pct:.1%}), but only {hardship_mention_pct:.1%} of transformation narratives mention it.")
        
        if linked_pct > 0.15:
            conclusion.append(f"**Direct Link:** For {linked_pct:.1%} of participants, the 'Ordeal' is the explicit engine of their transformation.")
        elif linked_pct > 0.05:
            conclusion.append(f"**Normalization:** Hardship is common but rarely cited as the primary driver of epiphany, suggesting it is normalized as 'background noise' on the playa.")
        else:
            conclusion.append("**Hypothesis Weakened:** The 'Ordeal Hypothesis' is largely unsupported by the data; participants describe transformation through social and creative lenses, not physical survival.")

    # Generate Report
    report = ["# Module 2: The 'Ordeal' as Catalyst (Survival vs. Epiphany)\n"]
    report.append(f"**Methodology:** Comparative analysis of survival responses (Baseline) vs {total} transformation narratives, segmented by **Age**.\n")
    
    report.append("### Findings")
    report.append(f"- **Transformation Narratives Mentioning Hardship:** {hardship_mention_pct:.1%}")
    report.append(f"- **Hardship as Explicit Catalyst:** {linked_pct:.1%}")
    
    report.append("\n### Hardship Intensity (Transformation Set)")
    report.append("| Level | Count |")
    report.append("| :--- | :--- |")
    for level in ["High", "Medium", "Low", "None"]:
        report.append(f"| {level} | {stats[f'Level_{level}']} |")
        
    report.append("\n### Age Analysis: Who Suffers, Who Grows?")
    report.append("| Age Group | Baseline Hardship % | Transf. Hardship % | Catalyst Rate (Linked) |")
    report.append("| :--- | :--- | :--- | :--- |")
    
    for age in ["Under 30", "30-39", "40-49", "50+"]:
        base = baseline_stats.get(age, 0)
        group_data = age_link_stats.get(age, {"Total": 0})
        tot = group_data["Total"]
        
        if tot > 0:
            trans_hard = group_data["Hardship"] / tot
            cat_rate = group_data["Linked"] / tot
        else:
            trans_hard = 0
            cat_rate = 0
            
        report.append(f"| {age} | {base:.1%} | {trans_hard:.1%} | {cat_rate:.1%} |")

    report.append("\n## Conclusion")
    report.append("> " + " ".join(conclusion))

    utils.save_report("module_2_survival.md", "\n".join(report))

if __name__ == "__main__":
    asyncio.run(run_analysis())