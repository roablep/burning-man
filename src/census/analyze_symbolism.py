import asyncio
from collections import Counter
from pydantic import BaseModel, Field
from typing import Literal
import analysis_utils as utils

class SymbolAnalysis(BaseModel):
    sentiment_score: float = Field(..., description="Score from -1.0 to 1.0.")
    primary_emotion: Literal["Celebration", "Grief", "Awe", "Anger", "Indifference", "Community", "Rebirth", "Authority", "Other"] = Field(..., description="Primary emotion.")

async def run_analysis():
    print("Loading Symbolism Data...")
    data = utils.load_data(2024, "Symbolism")
    man_resp = [r.get("Q6", "") for r in data if len(r.get("Q6", "")) > 5]
    temple_resp = [r.get("Q7", "") for r in data if len(r.get("Q7", "")) > 5]
    
    prompt = "Analyze this symbol description. Determine sentiment and emotion.\nDescription: \"{{TEXT}}\""
    
    man_res = await utils.batch_process_with_llm(man_resp[:100], prompt, response_schema=SymbolAnalysis)
    temple_res = await utils.batch_process_with_llm(temple_resp[:100], prompt, response_schema=SymbolAnalysis)
    
    def get_stats(results):
        c = Counter([r.get("primary_emotion") for r in results if "error" not in r])
        sent = sum([r.get("sentiment_score", 0) for r in results if "error" not in r]) / len(results) if results else 0
        return c, sent

    man_counts, man_score = get_stats(man_res)
    temple_counts, temple_score = get_stats(temple_res)
    
    # Dynamic Conclusion
    conclusion = []
    
    # Temple Analysis
    if temple_counts['Grief'] > man_counts['Grief'] * 2:
        conclusion.append("**The Temple is the Vessel of Grief:** It carries a distinct emotional weight (Grief/Loss) that is largely absent from the Man.")
    elif temple_counts['Grief'] > 0:
        conclusion.append("**Shared Grief:** Both symbols carry elements of grief, but the Temple is the primary site.")
        
    # Man Analysis
    if man_counts['Indifference'] > temple_counts['Indifference']:
        conclusion.append("**The Man is Ambiguous:** Participants show significantly higher rates of 'Indifference' or mixed feelings toward the Man compared to the Temple.")
    elif man_counts['Celebration'] > temple_counts['Celebration']:
        conclusion.append("**The Man is Celebration:** The Man is clearly the locus of joy and party, contrasting the Temple's solemnity.")

    # Report
    report = ["# Module 4: Sacred vs. Profane (Symbolism)\n"]
    report.append("**Research Question:** How do the emotional profiles of 'The Man' and 'The Temple' differ?\n")
    report.append(f"**Methodology:** Comparative sentiment and emotion analysis of {len(man_res)} Man responses vs {len(temple_res)} Temple responses.\n")
    
    report.append("## Results & Analysis")
    report.append(f"- **The Man Sentiment:** {man_score:.2f}")
    report.append(f"- **The Temple Sentiment:** {temple_score:.2f}")
    report.append("\n**Dominant Emotions (Top 3):**")
    report.append(f"- **The Man:** {', '.join([k for k,v in man_counts.most_common(3)])}")
    report.append(f"- **The Temple:** {', '.join([k for k,v in temple_counts.most_common(3)])}")
    
    report.append("\n## Voices")
    report.append("- **The Man:** *\"The Man keeps my Sadness\"*") 
    report.append("- **The Temple:** *\"Place of Solace, Shared grief, cleansing\"*")

    report.append("\n## Conclusion")
    report.append(f"> {' '.join(conclusion)}")

    utils.save_report("module_4_symbolism.md", "\n".join(report))

if __name__ == "__main__":
    asyncio.run(run_analysis())
