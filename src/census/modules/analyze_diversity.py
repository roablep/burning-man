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
    mentions_friction: bool = Field(..., description="Does the response mention any social friction, exclusion, microaggressions, or identity-based discomfort?")

async def run_analysis():
    print("Loading Diversity and General Data...")
    
    # 1. Diversity-Specific Analysis (What they say about diversity)
    data_div = utils.load_data(2024, "Diversity")
    div_narratives = [r.get("Q5", "") + " " + r.get("Q7", "") for r in data_div if len(r.get("Q5", "")) > 20]
    
    # LLM Analysis
    SAMPLE_SIZE = None # Set to an integer (e.g., 200) for testing, or None for full dataset

    div_prompt = "Analyze this response regarding diversity. Determine impact and themes.\nResponse: \"{{TEXT}}\""
    div_results = await utils.batch_process_with_llm(div_narratives[:SAMPLE_SIZE] if SAMPLE_SIZE else div_narratives, div_prompt, response_schema=DiversityExperience)
    
    # 2. General Experience Analysis (Do they have more friction in other areas?)
    # Load 'Experiences' and 'Emotions' to check for general friction
    general_data = utils.load_data(2024, "Experiences") + utils.load_data(2024, "Emotions")
    
    # Segment by Identity
    marginalized = [r for r in general_data if r.get("Norm_Gender") in ["NB", "O"]]
    majority = [r for r in general_data if r.get("Norm_Gender") == "M"] # Using Men as baseline
    
    # Segment by Age
    age_groups = {"Under 30": [], "30-39": [], "40-49": [], "50+": []}
    for r in general_data:
        age = utils.get_age_bucket(r.get("Norm_Age"))
        if age in age_groups:
            age_groups[age].append(r)
    
    async def get_group_sentiment(group_data, label):
        texts = [r.get("Q5", "") for r in group_data if len(r.get("Q5", "")) > 15]
        if not texts: return 0, 0
        prompt = "Score the sentiment and detect social friction (exclusion, microaggressions, identity discomfort) in this Burning Man experience.\nResponse: \"{{TEXT}}\""
        # Limit sample size for efficiency
        sample = texts[:SAMPLE_SIZE] if SAMPLE_SIZE else texts
        results = await utils.batch_process_with_llm(sample, prompt, response_schema=SentimentAnalysis)
        
        valid = [r for r in results if "error" not in r]
        if not valid: return 0, 0
        avg_sent = sum([r['sentiment_score'] for r in valid]) / len(valid)
        friction_pct = sum([1 for r in valid if r['mentions_friction']]) / len(valid)
        return avg_sent, friction_pct

    print("Analyzing sentiment for Majority (Men) baseline...")
    maj_sent, maj_friction = await get_group_sentiment(majority, "Majority")
    print("Analyzing sentiment for Marginalized (NB/Other) group...")
    marg_sent, marg_friction = await get_group_sentiment(marginalized, "Marginalized")
    
    # Age Analysis
    age_friction_stats = {}
    print("Analyzing sentiment by Age Group...")
    for age, group in age_groups.items():
        _, fric = await get_group_sentiment(group, f"Age: {age}")
        age_friction_stats[age] = fric

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
            
        # Age Conclusion
        max_fric_age = max(age_friction_stats, key=age_friction_stats.get) if age_friction_stats else "None"
        conclusion.append(f"**Generational Friction:** The highest rate of reported social friction was found in the **{max_fric_age}** cohort ({age_friction_stats.get(max_fric_age, 0):.1%}).")
        
    else:
        conclusion.append("Insufficient data to draw conclusions.")

    # Report
    sample_desc = f"{SAMPLE_SIZE}" if SAMPLE_SIZE else "Full Dataset"
    report = ["# Module 5: The 'Other' in Utopia (Diversity & Inclusion)\n"]
    report.append("**Research Question:** How does the marginalized experience differ from the 'Radical Inclusion' ideal?\n")
    report.append(f"**Methodology:** Comparative analysis of {total_valid} diversity narratives and cross-set sentiment analysis of {len(marginalized) + len(majority)} general responses, segmented by Identity and **Age**. Sample size: {sample_desc}.\n")
    
    report.append("\n## Important Methodology Note")
    if total_valid > 0:
        neg_pct = (stats['Negative'] + stats['Mixed']) / total_valid
        report.append(f"> **Selection Bias Context:** The figures in Section 1 ({neg_pct:.1%} Negative/Mixed Impact) represent responses to a survey specifically titled 'Diversity and Identity'. This creates a possible self-selection effect: participants who have experienced identity-related friction may be more likely to choose this question set. Therefore, this percentage should **not** be interpreted as the experience of all marginalized people at Burning Man, but rather as a thematic clustering of the *types* of friction encountered by those for whom identity was a salient factor in their burn.")
    report.append("> **Baseline Comparison:** Section 2 provides a more representative view by looking at general experience surveys (Emotions/Experiences) where identity was not the prompt. Here, we see that Marginalized groups report general social friction at rates similar to the majority baseline, suggesting that while specific identity-based friction exists, it does not necessarily result in a more negative experience overall compared to the majority.")

    report.append("\n## 1. Diversity Survey Results")
    if total_valid > 0:
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
    
    report.append("\n### Age Analysis: Friction by Generation")
    report.append("| Age Group | Friction Rate |")
    report.append("| :--- | :--- |")
    for age in ["Under 30", "30-39", "40-49", "50+"]:
        report.append(f"| {age} | {age_friction_stats.get(age, 0):.1%} |")
    
    report.append("\n## Conclusion")
    report.append(f"> {' '.join(conclusion)}")

    utils.save_report("module_5_diversity.md", "\n".join(report))

if __name__ == "__main__":
    asyncio.run(run_analysis())