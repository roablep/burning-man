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
    results = await utils.batch_process_with_llm(narratives[:100], prompt, response_schema=DiversityExperience)
    
    stats = Counter([r.get("identity_impact") for r in results if "error" not in r])
    themes = Counter([r.get("key_theme") for r in results if "error" not in r])
    code_switch = sum([1 for r in results if "error" not in r and r.get("code_switching")])
    
    # Dynamic Conclusion
    negative_pct = (stats['Negative'] + stats['Mixed']) / len(results) if results else 0
    code_switch_pct = code_switch / len(results) if results else 0
    
    conclusion = []
    if negative_pct > 0.5:
        conclusion.append(f"**The Utopia Has Friction:** A majority ({negative_pct:.1%}) of marginalized participants report Negative or Mixed experiences, challenging the 'Radical Inclusion' ideal.")
    else:
        conclusion.append(f"**Inclusion is Working:** The majority of marginalized participants report Positive or Neutral experiences, suggesting the principle of Radical Inclusion is effective.")
        
    if code_switch_pct > 0.1:
        conclusion.append(f"**The Cost of Entry:** {code_switch_pct:.1%} of respondents report 'Code Switching' (modifying behavior/appearance) to feel safe or accepted.")

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
