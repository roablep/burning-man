import asyncio
from collections import Counter
from pydantic import BaseModel, Field
from typing import Literal
import analysis_utils as utils

class CostumeMotivation(BaseModel):
    motivation_type: Literal["Authenticity", "Play", "Disguise", "Conformity", "Comfort", "Other"] = Field(..., description="Primary reason for wearing costumes.")
    key_phrase: str = Field(..., description="Specific phrase indicating this.")

async def run_analysis():
    print("Loading Costume Data...")
    data = utils.load_data(2024, "Costumes")
    narratives = [row.get("Q5", "") for row in data if len(row.get("Q5", "")) > 10]
    
    prompt = "Analyze this response to 'Do you wear costumes at Burning Man?'. Categorize the motivation.\nResponse: \"{{TEXT}}\""
    
    results = await utils.batch_process_with_llm(narratives[:150], prompt, response_schema=CostumeMotivation)
    
    stats = Counter([r.get("motivation_type") for r in results if "error" not in r])
    total = sum(stats.values())
    
    # Dynamic Conclusion Logic
    auth_score = stats['Authenticity']
    disguise_score = stats['Disguise']
    play_score = stats['Play']
    
    conclusion = []
    if auth_score > disguise_score * 2:
        conclusion.append("**The Mirror Wins:** Participants overwhelmingly view costumes as a tool for revealing their true selves ('Radical Self Expression') rather than hiding.")
    elif disguise_score > auth_score:
        conclusion.append("**The Mask Wins:** Participants primarily use costumes to escape their identity.")
    elif play_score > (auth_score + disguise_score):
        conclusion.append("**It's Just a Game:** The dominant motivation is 'Play', suggesting costumes are less about deep identity work and more about situational fun.")
    else:
        conclusion.append("**It's Complicated:** The function of the costume is split between revelation, play, and escapism with no dominant narrative.")

    # Report
    report = ["# Module 3: The Mask vs. The Mirror (Identity)\n"]
    report.append("**Research Question:** Do participants wear costumes to hide (Mask) or to reveal their true selves (Mirror)?\n")
    report.append(f"**Methodology:** Semantic classification of {len(results)} responses regarding costume motivation.\n")
    
    report.append("## Results & Analysis")
    report.append(f"- **Play/Fun:** {stats['Play']} ({stats['Play']/total:.1%})")
    report.append(f"- **Authenticity (Mirror):** {stats['Authenticity']} ({stats['Authenticity']/total:.1%})")
    report.append(f"- **Disguise (Mask):** {stats['Disguise']} ({stats['Disguise']/total:.1%})")
    
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
