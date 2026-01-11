import sys
import os
import asyncio
from collections import Counter
from pydantic import BaseModel, Field
from typing import Literal

# Add parent directory to path to find analysis_utils
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import analysis_utils as utils

class CostumeMotivation(BaseModel):
    motivation_type: Literal["Authenticity", "Play", "Disguise", "Conformity", "Comfort", "Other"] = Field(..., description="Primary reason for wearing costumes.")
    key_phrase: str = Field(..., description="Specific phrase indicating this.")

async def run_analysis():
    print("Loading Costume Data...")
    data = utils.load_data(2024, "Costumes")
    narratives = [row.get("Q5", "") for row in data if len(row.get("Q5", "")) > 10]
    
    prompt = "Analyze this response to 'Do you wear costumes at Burning Man?'. Categorize the motivation.\nResponse: \"{{TEXT}}\""
    
    results = await utils.batch_process_with_llm(narratives, prompt, response_schema=CostumeMotivation)
    
    stats = Counter([r.get("motivation_type") for r in results if "error" not in r])
    total = sum(stats.values())
    
    # Dynamic Conclusion Logic
    if total == 0:
        conclusion = ["No valid responses found."]
    else:
        # Sort stats to find top motivations
        sorted_stats = stats.most_common()
        top_type, top_count = sorted_stats[0]
        top_pct = top_count / total
        
        conclusion = []
        conclusion.append(f"**Motivation Profile:** The most common motivation for wearing costumes is **{top_type}** ({top_pct:.1%}).")
        
        if len(sorted_stats) > 1:
            second_type, second_count = sorted_stats[1]
            second_pct = second_count / total
            if (top_pct - second_pct) < 0.10:
                conclusion.append(f"Motivations are **highly distributed**, with {second_type} ({second_pct:.1%}) following closely behind.")
            else:
                conclusion.append(f"{top_type} is the clear primary driver, with {second_type} ({second_pct:.1%}) as a secondary theme.")
        
        # Specific Identity Insight
        auth_pct = stats.get('Authenticity', 0) / total
        disguise_pct = stats.get('Disguise', 0) / total
        if auth_pct > disguise_pct:
            conclusion.append(f"Data suggests the costume functions more as a **Mirror** (Authenticity: {auth_pct:.1%}) than a **Mask** (Disguise: {disguise_pct:.1%}).")
        else:
            conclusion.append(f"Data suggests the costume functions more as a **Mask** (Disguise: {disguise_pct:.1%}) than a **Mirror** (Authenticity: {auth_pct:.1%}).")

    # Report
    report = ["# Module 3: The Mask vs. The Mirror (Identity)\n"]
    report.append("**Research Question:** Do participants wear costumes to hide (Mask) or to reveal their true selves (Mirror)?\n")
    report.append(f"**Methodology:** Semantic classification of {total} responses regarding costume motivation from the 2024 dataset.\n")
    
    report.append("## Results & Analysis")
    for m_type, count in stats.most_common():
        report.append(f"- **{m_type}:** {count} ({count/total:.1%})")
    
    report.append("\n## Voices")
    for i, res in enumerate(results):
        if "error" in res: continue
        if res.get("motivation_type") == "Authenticity":
            report.append(f"- **Authenticity:** *\"{narratives[i]}\"*")
            break
            
    report.append("\n## Conclusion")
    report.append("> " + " ".join(conclusion))

    utils.save_report("module_3_identity.md", "\n".join(report))

if __name__ == "__main__":
    asyncio.run(run_analysis())