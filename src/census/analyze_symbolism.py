import asyncio
from collections import Counter
from pydantic import BaseModel, Field
from typing import Literal
import analysis_utils as utils

class SymbolAnalysis(BaseModel):
    sentiment_score: float = Field(..., description="Sentiment score from -1.0 (Negative) to 1.0 (Positive).")
    primary_emotion: Literal["Celebration", "Grief", "Awe", "Anger", "Indifference", "Community", "Rebirth", "Authority", "Other"] = Field(..., description="The primary emotion associated with this symbol.")
    keywords: str = Field(..., description="Comma-separated keywords.")

async def run_analysis():
    print("Loading Symbolism Data...")
    data_2024 = utils.load_data(2024, "Symbolism")
    # 2025 doesn't have a distinct Symbolism set in the prompt list provided earlier?
    # Checking analysis plan... 2025 Set D is Boundaries.
    # We will focus on 2024 Set B.
    
    man_responses = []
    temple_responses = []
    
    for row in data_2024:
        # Q6: The Man, Q7: The Temple
        m = row.get("Q6", "")
        t = row.get("Q7", "")
        if len(m) > 5: man_responses.append(m)
        if len(t) > 5: temple_responses.append(t)
            
    print(f"Man Responses: {len(man_responses)}")
    print(f"Temple Responses: {len(temple_responses)}")
    
    prompt = """
    Analyze this description of a Burning Man symbol.
    Determine the sentiment and primary emotion.
    
    Description: "{{TEXT}}"
    """
    
    print("Analyzing The Man...")
    man_results = await utils.batch_process_with_llm(
        man_responses[:100], 
        prompt, 
        response_schema=SymbolAnalysis
    )
    
    print("Analyzing The Temple...")
    temple_results = await utils.batch_process_with_llm(
        temple_responses[:100], 
        prompt, 
        response_schema=SymbolAnalysis
    )
    
    def summarize(results, name):
        stats = Counter()
        total_sent = 0
        valid = 0
        for r in results:
            if isinstance(r, dict) and "error" in r: continue
            stats[r.get("primary_emotion")] += 1
            total_sent += r.get("sentiment_score", 0)
            valid += 1
        
        avg_sent = total_sent / valid if valid else 0
        return avg_sent, stats

    man_sent, man_stats = summarize(man_results, "The Man")
    temple_sent, temple_stats = summarize(temple_results, "The Temple")

    # Generate Report
    report = ["# Module 4: Sacred vs. Profane (The Man vs. The Temple)\n"]
    
    report.append("### Sentiment Score (-1 to 1)")
    report.append(f"- **The Man:** {man_sent:.2f}")
    report.append(f"- **The Temple:** {temple_sent:.2f}")
    
    report.append("\n### Emotional Profile")
    report.append("| Emotion | The Man (Count) | The Temple (Count) |")
    report.append("| :--- | :--- | :--- |")
    
    all_emotions = set(man_stats.keys()) | set(temple_stats.keys())
    for em in sorted(all_emotions):
        report.append(f"| {em} | {man_stats[em]} | {temple_stats[em]} |")

    report.append("\n**Conclusion:**")
    if temple_stats['Grief'] > man_stats['Grief']:
        report.append("> **The Temple is the Vessel of Grief:** It carries a distinct emotional weight compared to the Man.")
    
    if man_stats['Authority'] > temple_stats['Authority'] or man_stats['Indifference'] > temple_stats['Indifference']:
        report.append("> **The Man is Complicated:** Participants show more ambivalence or association with authority/structure regarding The Man.")

    utils.save_report("module_4_symbolism.md", "\n".join(report))

if __name__ == "__main__":
    asyncio.run(run_analysis())
