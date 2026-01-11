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
    
    man_res = await utils.batch_process_with_llm(man_resp, prompt, response_schema=SymbolAnalysis)
    temple_res = await utils.batch_process_with_llm(temple_resp, prompt, response_schema=SymbolAnalysis)
    
    def get_stats(results):
        valid = [r for r in results if "error" not in r]
        if not valid: return Counter(), 0
        c = Counter([r.get("primary_emotion") for r in valid])
        sent = sum([r.get("sentiment_score", 0) for r in valid]) / len(valid)
        return c, sent

    man_counts, man_score = get_stats(man_res)
    temple_counts, temple_score = get_stats(temple_res)
    
    # Dynamic Conclusion
    conclusion = []
    
    # Calculate percentages for key emotions to allow robust comparison
    def get_pct(counter, key, total):
        return (counter[key] / total) if total > 0 else 0

    man_total = sum(man_counts.values())
    temple_total = sum(temple_counts.values())
    
    man_grief_pct = get_pct(man_counts, 'Grief', man_total)
    temple_grief_pct = get_pct(temple_counts, 'Grief', temple_total)
    
    man_cel_pct = get_pct(man_counts, 'Celebration', man_total)
    temple_cel_pct = get_pct(temple_counts, 'Celebration', temple_total)

    # Temple Analysis
    if temple_grief_pct > 0.4:
        conclusion.append(f"**Temple as Grief Vessel:** The Temple is strongly associated with Grief ({temple_grief_pct:.1%}), significantly more than the Man ({man_grief_pct:.1%}).")
    elif temple_grief_pct > man_grief_pct:
        conclusion.append(f"**Temple leans towards Grief:** While present in both, Grief is more prevalent in Temple narratives ({temple_grief_pct:.1%} vs {man_grief_pct:.1%}).")
        
    # Man Analysis
    if man_cel_pct > 0.4:
        conclusion.append(f"**Man as Celebration:** The Man is primarily a symbol of Celebration ({man_cel_pct:.1%}), contrasting with the Temple's lower association ({temple_cel_pct:.1%}).")
    elif man_counts['Indifference'] > man_counts['Celebration']:
        conclusion.append("**Ambivalence toward the Man:** 'Indifference' is the most common reaction to the Man, suggesting a potential disconnect or routinization of the symbol.")
    else:
        conclusion.append(f"**Mixed Signals on the Man:** The Man evokes a broad range of emotions, with Celebration ({man_cel_pct:.1%}) being a leading but not dominant theme.")

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
