import sys
import os
import asyncio
from collections import Counter
from pydantic import BaseModel, Field
from typing import Literal

# Add parent directory to path to find analysis_utils
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import analysis_utils as utils

class DiversityExperience(BaseModel):
    identity_impact: Literal["Positive", "Negative", "Mixed", "None"] = Field(..., description="Impact of identity on experience.")
    key_theme: str = Field(..., description="Main theme (e.g. Racism, Exoticism).")
    code_switching: bool = Field(..., description="Did they modify behavior to fit in?")

class SentimentAnalysis(BaseModel):
    sentiment_score: float = Field(..., description="Score from -1.0 (very negative) to 1.0 (very positive).")
    mentions_friction: bool = Field(..., description="Does the response mention any social friction, exclusion, or discomfort?")

async def run_analysis():
    print("Loading Diversity and General Data...")
    
    # 1. Diversity-Specific Analysis (What they say about diversity)
    data_div = utils.load_data(2024, "Diversity")
    div_narratives = [r.get("Q5", "") + " " + r.get("Q7", "") for r in data_div if len(r.get("Q5", "")) > 20]
    
    div_prompt = "Analyze this response regarding diversity. Determine impact and themes.\nResponse: \"{{TEXT}}\""
    div_results = await utils.batch_process_with_llm(div_narratives, div_prompt, response_schema=DiversityExperience)
    
    # 2. General Experience Analysis (Do they have more friction in other areas?)
    # Load 'Experiences' and 'Emotions' to check for general friction
    general_data = utils.load_data(2024, "Experiences") + utils.load_data(2024, "Emotions")
    
    # Segment by Identity
    marginalized = [r for r in general_data if r.get("Norm_Gender") in ["NB", "O"]]
    majority = [r for r in general_data if r.get("Norm_Gender") == "M"] # Using Men as baseline
    
    async def get_group_sentiment(group_data, label):
        texts = [r.get("Q5", "") for r in group_data if len(r.get("Q5", "")) > 15]
        if not texts: return 0, 0
        prompt = "Score the sentiment and detect social friction in this Burning Man experience.\nResponse: \"{{TEXT}}\""
        results = await utils.batch_process_with_llm(texts[:200], prompt, response_schema=SentimentAnalysis)
        
        valid = [r for r in results if "error" not in r]
        if not valid: return 0, 0
        avg_sent = sum([r['sentiment_score'] for r in valid]) / len(valid)
        friction_pct = sum([1 for r in valid if r['mentions_friction']]) / len(valid)
        return avg_sent, friction_pct

    print("Analyzing sentiment for Majority (Men) baseline...")
    maj_sent, maj_friction = await get_group_sentiment(majority, "Majority")
    print("Analyzing sentiment for Marginalized (NB/Other) group...")
    marg_sent, marg_friction = await get_group_sentiment(marginalized, "Marginalized")

    # --- PROCESS DIVERSITY RESULTS ---
    stats = Counter([r.get("identity_impact") for r in div_results if "error" not in r])
    themes = Counter([r.get("key_theme") for r in div_results if "error" not in r])
    code_switch = sum([1 for r in div_results if "error" not in r and r.get("code_switching")])
    total_valid = len([r for r in div_results if "error" not in r])
    
    # Dynamic Conclusion
    conclusion = []
    if total_valid > 0:
        neg_pct = (stats['Negative'] + stats['Mixed']) / total_valid
        conclusion.append(f"**Experience Breakdown:** {stats['Positive']/total_valid:.1%} reported Positive experiences, while {neg_pct:.1%} reported Negative or Mixed impacts related to their identity.")
        
        # Add baseline comparison
        if marg_friction > maj_friction * 1.5:
            conclusion.append(f"**Cross-Set Validation:** Marginalized respondents reported **significantly higher friction** in general experience surveys ({marg_friction:.1%} vs {maj_friction:.1%} for the majority baseline).")
        else:
            conclusion.append(f"**Baseline Consistency:** General experience sentiment was relatively consistent between groups (Friction: {marg_friction:.1%} marginalized vs {maj_friction:.1%} majority).")
    else:
        conclusion.append("Insufficient data to draw conclusions.")

    # Report
    report = ["# Module 5: The 'Other' in Utopia (Diversity & Inclusion)\n"]
    report.append("**Research Question:** How does the marginalized experience differ from the 'Radical Inclusion' ideal?\n")
    report.append(f"**Methodology:** Comparative analysis of {total_valid} diversity narratives and cross-set sentiment analysis of {len(marginalized) + len(majority)} general responses.\n")
    
    report.append("## 1. Diversity Survey Results")
    if total_valid > 0:
        neg_pct = (stats['Negative'] + stats['Mixed']) / total_valid
        report.append(f"- **Negative/Mixed Impact:** {stats['Negative'] + stats['Mixed']} ({neg_pct:.1%})")
        report.append(f"- **Code Switching:** {code_switch} ({code_switch / total_valid:.1%})")
        report.append(f"- **Top Themes:** {', '.join([t for t,c in themes.most_common(3)])}")
    else:
        report.append("- No valid diversity narratives found.")
    
    report.append("\n## 2. General Experience Baseline (Cross-Set Analysis)")
    report.append("| Group | Avg Sentiment | Friction Rate |")
    report.append("| :--- | :--- | :--- |")
    report.append(f"| Majority (Men) | {maj_sent:.2f} | {maj_friction:.1%} |")
    report.append(f"| Marginalized (NB/O) | {marg_sent:.2f} | {marg_friction:.1%} |")
    
    report.append("\n## Conclusion")
    report.append(f"> {' '.join(conclusion)}")

    utils.save_report("module_5_diversity.md", "\n".join(report))

if __name__ == "__main__":
    asyncio.run(run_analysis())
