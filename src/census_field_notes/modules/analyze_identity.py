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
    
    narratives = []
    age_cohorts = {"Under 30": [], "30-39": [], "40-49": [], "50+": []}
    
    for row in data:
        text = row.get("Q5", "")
        if len(text) > 10:
            narratives.append(text)
            age = utils.get_age_bucket(row.get("Norm_Age"))
            if age in age_cohorts:
                age_cohorts[age].append(text)
    
    # LLM Analysis
    SAMPLE_SIZE = None # Set to an integer (e.g., 200) for testing, or None for full dataset

    prompt = "Analyze this response to 'Do you wear costumes at Burning Man?'. Categorize the motivation.\nResponse: \"{{TEXT}}\""
    
    results = await utils.batch_process_with_llm(narratives[:SAMPLE_SIZE] if SAMPLE_SIZE else narratives, prompt, response_schema=CostumeMotivation)
    
    stats = Counter([r.get("motivation_type") for r in results if "error" not in r])
    total = sum(stats.values())
    
    # Process Age Segments (Map global results back to age buckets)
    # Since 'narratives' aligns with 'results', we need to track indices if we want to map back.
    # OR we can re-process age cohorts.
    # Optimization: Use a map of {text_hash: result} to avoid re-calling LLM if we re-loop.
    # But batch_process_with_llm caches by text content anyway! 
    # So we can just call it again on age cohorts and it will be instant (cache hit).
    
    age_stats = {}
    print("Analyzing Age Cohorts...")
    for age, texts in age_cohorts.items():
        if not texts:
            age_stats[age] = Counter()
            continue
        # Cache hit expected
        sample = texts[:SAMPLE_SIZE] if SAMPLE_SIZE else texts
        res = await utils.batch_process_with_llm(sample, prompt, response_schema=CostumeMotivation)
        age_stats[age] = Counter([r.get("motivation_type") for r in res if "error" not in r])

    # Dynamic Conclusion Logic
    if total == 0:
        conclusion = ["No valid responses found."]
    else:
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
        
        auth_pct = stats.get('Authenticity', 0) / total
        disguise_pct = stats.get('Disguise', 0) / total
        
        if auth_pct > disguise_pct:
            conclusion.append(f"Data suggests the costume functions more as a **Mirror** (Authenticity: {auth_pct:.1%}) than a **Mask** (Disguise: {disguise_pct:.1%}).")
        else:
            conclusion.append(f"Data suggests the costume functions more as a **Mask** (Disguise: {disguise_pct:.1%}) than a **Mirror** (Authenticity: {auth_pct:.1%}).")

    # Report
    sample_desc = f"{SAMPLE_SIZE}" if SAMPLE_SIZE else "Full Dataset"
    report = ["# Module 3: The Mask vs. The Mirror (Identity)\n"]
    report.append("**Research Question:** Do participants wear costumes to hide (Mask) or to reveal their true selves (Mirror)?\n")
    report.append(f"**Methodology:** Semantic classification of {total} responses regarding costume motivation from the 2024 dataset, segmented by **Age**. Sample size: {sample_desc}.\n")
    
    report.append("## Results & Analysis")
    for m_type, count in stats.most_common():
        report.append(f"- **{m_type}:** {count} ({count/total:.1%})")
        
    report.append("\n### Age Analysis: Mask vs. Mirror")
    report.append("| Age Group | Authenticity (Mirror) | Disguise (Mask) | Play |")
    report.append("| :--- | :--- | :--- | :--- |")
    
    for age in ["Under 30", "30-39", "40-49", "50+"]:
        c = age_stats.get(age, Counter())
        tot = sum(c.values())
        if tot > 0:
            auth = c['Authenticity'] / tot
            disg = c['Disguise'] / tot
            play = c['Play'] / tot
        else:
            auth = disg = play = 0
        report.append(f"| {age} | {auth:.1%} | {disg:.1%} | {play:.1%} |")
    
    report.append("\n## Voices")
    
    # Dynamic Voice Selection
    top_motivation = sorted_stats[0][0] if sorted_stats else "Play"
    
    for i, res in enumerate(results):
        if "error" in res: continue
        if res.get("motivation_type") == top_motivation and len(narratives[i]) > 50:
            report.append(f"- **{top_motivation}:** *\"{narratives[i]}\"*")
            break
            
    report.append("\n## Conclusion")
    report.append("> " + " ".join(conclusion))

    utils.save_report("module_3_identity.md", "\n".join(report))

if __name__ == "__main__":
    asyncio.run(run_analysis())