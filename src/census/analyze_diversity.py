import asyncio
from collections import Counter
from pydantic import BaseModel, Field
from typing import Literal
import analysis_utils as utils

class DiversityExperience(BaseModel):
    identity_impact: Literal["Positive", "Negative", "Mixed", "None"] = Field(..., description="Does the participant feel their identity impacts their experience positively or negatively?")
    key_theme: str = Field(..., description="Main theme (e.g. 'Racism', 'Ageism', 'Liberation', 'Exoticism', 'Invisibility').")
    code_switching: bool = Field(..., description="Does the participant describe modifying their behavior/appearance to fit in or be safe?")

async def run_analysis():
    print("Loading Diversity Data...")
    # 2024 Set K, 2025 Set F
    data_2024 = utils.load_data(2024, "Diversity")
    data_2025 = utils.load_data(2025, "Diversity")
    
    all_data = data_2024 + data_2025
    print(f"Total Diversity Records: {len(all_data)}")
    
    narratives = []
    for row in all_data:
        # Q5: Does appearance impact interactions?
        # Q7: Same for playa
        n = row.get("Q5", "") + " " + row.get("Q7", "")
        if len(n) > 20:
            narratives.append(n)
            
    print(f"Qualitative Responses: {len(narratives)}")
    
    prompt = """
    Analyze this response regarding diversity and inclusion at Burning Man vs Default World.
    
    Response: "{{TEXT}}"
    """
    
    results = await utils.batch_process_with_llm(
        narratives[:100], 
        prompt, 
        response_schema=DiversityExperience
    )
    
    stats = Counter()
    themes = Counter()
    
    for res in results:
        if isinstance(res, dict) and "error" in res: continue
        stats[res.get("identity_impact")] += 1
        themes[res.get("key_theme")] += 1
        if res.get("code_switching"): stats["Code_Switching"] += 1

    # Generate Report
    report = ["# Module 5: The 'Other' in Utopia (Diversity & Inclusion)\n"]
    
    report.append("### Impact of Identity on Experience")
    report.append("| Impact | Count |")
    report.append("| :--- | :--- |")
    for k, v in stats.most_common():
        if k != "Code_Switching":
            report.append(f"| {k} | {v} |")
            
    report.append(f"\n**Code Switching Reported:** {stats['Code_Switching']} / {len(results)} ({stats['Code_Switching']/len(results):.1%})")
    
    report.append("\n### Top Themes")
    for t, c in themes.most_common(10):
        report.append(f"- **{t}:** {c}")

    utils.save_report("module_5_diversity.md", "\n".join(report))

if __name__ == "__main__":
    asyncio.run(run_analysis())
