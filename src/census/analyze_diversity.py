import asyncio
from collections import Counter
from pydantic import BaseModel, Field
from typing import Literal
import analysis_utils as utils

class DiversityExperience(BaseModel):
    identity_impact: Literal["Positive", "Negative", "Mixed", "None"] = Field(..., description="Impact of identity on experience.")
    key_theme: str = Field(..., description="Main theme (e.g. Racism, Exoticism).")
    code_switching: bool = Field(..., description="Did they modify behavior to fit in?")

async def run_analysis():
    print("Loading Diversity Data...")
    data_2024 = utils.load_data(2024, "Diversity")
    data_2025 = utils.load_data(2025, "Diversity")
    narratives = [r.get("Q5", "") + " " + r.get("Q7", "") for r in (data_2024 + data_2025) if len(r.get("Q5", "")) > 20]
    
    prompt = "Analyze this response regarding diversity. Determine impact and themes.\nResponse: \"{{TEXT}}\""
    results = await utils.batch_process_with_llm(narratives, prompt, response_schema=DiversityExperience)
    
    stats = Counter([r.get("identity_impact") for r in results if "error" not in r])
    themes = Counter([r.get("key_theme") for r in results if "error" not in r])
    code_switch = sum([1 for r in results if "error" not in r and r.get("code_switching")])
    
    # Dynamic Conclusion
    total_valid = len([r for r in results if "error" not in r])
    if total_valid == 0:
        conclusion = ["No valid data points analyzed."]
    else:
        neg_count = stats['Negative']
        mixed_count = stats['Mixed']
        pos_count = stats['Positive']
        none_count = stats['None']
        
        negative_pct = (neg_count + mixed_count) / total_valid
        pos_pct = pos_count / total_valid
        code_switch_pct = code_switch / total_valid
        
        conclusion = []
        conclusion.append(f"**Experience Breakdown:** {pos_pct:.1%} reported Positive experiences, while {negative_pct:.1%} reported Negative or Mixed impacts related to their identity.")
        
        if negative_pct > 0.4:
            conclusion.append(f"**Significant Friction:** A substantial portion of marginalized participants ({negative_pct:.1%}) encountered challenges, citing themes like {', '.join([t for t,c in themes.most_common(2)])}.")
        elif negative_pct > 0.15:
            conclusion.append(f"**Uneven Utopia:** While the majority reported positive inclusion, a distinct minority ({negative_pct:.1%}) experienced exclusion or friction.")
        else:
            conclusion.append(f"**Largely Inclusive:** The vast majority ({pos_pct:.1%}) reported positive or neutral experiences, suggesting high efficacy of the Radical Inclusion principle.")
            
        if code_switch_pct > 0.15:
            conclusion.append(f"**The Cost of Adaptation:** {code_switch_pct:.1%} of respondents reported 'Code Switching' to navigate the space safely.")
        elif code_switch_pct > 0.05:
            conclusion.append(f"**Some Adaptation Required:** {code_switch_pct:.1%} felt the need to modify their behavior or appearance.")

    # Report
    report = ["# Module 5: The 'Other' in Utopia (Diversity & Inclusion)\n"]
    report.append("**Research Question:** How does the minority/marginalized experience differ from the 'Radical Inclusion' ideal?\n")
    report.append(f"**Methodology:** Analysis of {len(results)} narratives from participants who indicated their identity impacted their experience.\n")
    
    report.append("## Results & Analysis")
    report.append(f"- **Negative/Mixed Impact:** {stats['Negative'] + stats['Mixed']} ({negative_pct:.1%})")
    report.append(f"- **Code Switching:** {code_switch} ({code_switch_pct:.1%})")
    report.append(f"- **Top Themes:** {', '.join([t for t,c in themes.most_common(3)])}")
    
    report.append("\n## Voices")
    for i, res in enumerate(results):
        if "error" in res: continue
        if res.get("code_switching") and res.get("identity_impact") == "Negative":
            report.append(f"- *\"{narratives[i][:300]}...\"*")
            break

    report.append("\n## Conclusion")
    report.append(f"> {' '.join(conclusion)}")

    utils.save_report("module_5_diversity.md", "\n".join(report))

if __name__ == "__main__":
    asyncio.run(run_analysis())
