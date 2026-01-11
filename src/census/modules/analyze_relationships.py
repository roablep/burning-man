import sys
import os
import asyncio
from collections import Counter
from pydantic import BaseModel, Field
from typing import Literal

# Add parent directory to path to find analysis_utils
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import analysis_utils as utils

class RelationshipAnalysis(BaseModel):
    rel_type: Literal["Romantic", "Platonic", "Communal", "Self", "Other"] = Field(..., description="The type of relationship being discussed.")
    playa_vs_default: Literal["More Intense", "More Authentic", "Similar", "More Challenging", "None"] = Field(..., description="Comparison of playa relationships to default world.")
    key_theme: str = Field(..., description="Main theme (e.g. Vulnerability, Boundaries, Gifting).")

async def run_analysis():
    print("Loading Relationship Data...")
    # Relationship data is in Set H (2024) and Set E (2025)
    data_2024 = utils.load_data(2024, "Relationships")
    data_2025 = utils.load_data(2025, "Relationships")
    
    all_data = data_2024 + data_2025
    narratives = []
    age_cohorts = {"Under 30": [], "30-39": [], "40-49": [], "50+": []}
    
    for row in all_data:
        text = row.get("Q5", "") + " " + row.get("Q6", "")
        if len(row.get("Q5", "")) > 10:
            narratives.append(text)
            age = utils.get_age_bucket(row.get("Norm_Age"))
            if age in age_cohorts:
                age_cohorts[age].append(text)
    
    if not narratives:
        print("No relationship narratives found.")
        return

    prompt = """
    Analyze this response about relationships at Burning Man. 
    Compare the quality of connection to the 'default world'.
    
    Response: "{{TEXT}}"
    """
    
    results = await utils.batch_process_with_llm(narratives, prompt, response_schema=RelationshipAnalysis)
    
    stats = Counter([r.get("rel_type") for r in results if "error" not in r])
    comparison = Counter([r.get("playa_vs_default") for r in results if "error" not in r])
    themes = Counter([r.get("key_theme") for r in results if "error" not in r])
    
    total = len([r for r in results if "error" not in r])
    
    # Process Age Segments
    age_stats = {}
    print("Analyzing Age Cohorts...")
    for age, texts in age_cohorts.items():
        if not texts:
            age_stats[age] = 0
            continue
        # Reuse cache via batch process
        res = await utils.batch_process_with_llm(texts, prompt, response_schema=RelationshipAnalysis)
        c = Counter([r.get("playa_vs_default") for r in res if "error" not in r])
        tot = sum(c.values())
        if tot > 0:
            age_stats[age] = (c['More Intense'] + c['More Authentic']) / tot
        else:
            age_stats[age] = 0

    # Dynamic Conclusion
    if total == 0:
        conclusion = ["No valid data points found."]
    else:
        intense_pct = (comparison['More Intense'] + comparison['More Authentic']) / total
        top_theme = themes.most_common(1)[0][0] if themes else "None"
        
        conclusion = []
        conclusion.append(f"**Connection Intensity:** {intense_pct:.1%} of respondents report that playa relationships are more intense or authentic than those in the default world.")
        
        # Age Conclusion
        max_age = max(age_stats, key=age_stats.get) if age_stats else "None"
        min_age = min(age_stats, key=age_stats.get) if age_stats else "None"
        
        conclusion.append(f"**Generational Connection:** The perception of heightened intimacy peaks in the **{max_age}** cohort ({age_stats.get(max_age, 0):.1%}) and is lowest among **{min_age}** participants ({age_stats.get(min_age, 0):.1%}).")

    # Report
    report = ["# Module 6: Playa Love vs. Default Love (Relationships)\n"]
    report.append("**Research Question:** How do relationship dynamics and intimacy differ in the temporary autonomous zone?\n")
    report.append(f"**Methodology:** Analysis of {total} narratives regarding relationships and intimacy, segmented by **Age**.\n")
    
    report.append("## Results & Analysis")
    report.append(f"- **Top Relationship Type:** {stats.most_common(1)[0][0] if stats else 'N/A'}")
    report.append(f"- **More Intense/Authentic:** {intense_pct:.1%}")
    report.append(f"- **Top Themes:** {', '.join([t for t,c in themes.most_common(3)])}")
    
    report.append("\n### Age Analysis: Intensity of Connection")
    report.append("| Age Group | Reported High Intensity % |")
    report.append("| :--- | :--- |")
    for age in ["Under 30", "30-39", "40-49", "50+"]:
        report.append(f"| {age} | {age_stats.get(age, 0):.1%} |")
    
    report.append("\n## Voices")
    # Find a quote about intensity
    for i, res in enumerate(results):
        if "error" in res: continue
        if res.get("playa_vs_default") in ["More Intense", "More Authentic"] and len(narratives[i]) > 50:
            report.append(f"- **Intensity:** *\"{narratives[i]}\"*")
            break
    
    report.append("\n## Conclusion")
    report.append(f"> {' '.join(conclusion)}")

    utils.save_report("module_6_relationships.md", "\n".join(report))

if __name__ == "__main__":
    asyncio.run(run_analysis())
