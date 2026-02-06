import sys
import os
import asyncio
from collections import Counter
from pydantic import BaseModel, Field
from typing import Literal

# Add parent directory to path to find analysis_utils
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import analysis_utils as utils

class SymbolAnalysis(BaseModel):
    sentiment_score: float = Field(..., description="Score from -1.0 to 1.0.")
    primary_emotion: Literal["Celebration", "Grief", "Awe", "Anger", "Indifference", "Community", "Rebirth", "Authority", "Other"] = Field(..., description="Primary emotion.")

async def run_analysis():
    print("Loading Symbolism Data...")
    data = utils.load_data(2024, "Symbolism")
    
    # Segment by Gender
    cohorts = {"M": [], "F": []}
    
    # Segment by Age
    age_cohorts = {"Under 30": [], "30-39": [], "40-49": [], "50+": []}
    
    for r in data:
        # Gender
        gender = r.get("Norm_Gender", "U")
        if gender in ["M", "F"]:
            cohorts[gender].append(r)
            
        # Age
        age = utils.get_age_bucket(r.get("Norm_Age"))
        if age in age_cohorts:
            age_cohorts[age].append(r)
            
    # Prepare lists for batch processing (Gender)
    man_resp_m = [r.get("Q6", "") for r in cohorts["M"] if len(r.get("Q6", "")) > 5]
    man_resp_f = [r.get("Q6", "") for r in cohorts["F"] if len(r.get("Q6", "")) > 5]
    temple_resp_m = [r.get("Q7", "") for r in cohorts["M"] if len(r.get("Q7", "")) > 5]
    temple_resp_f = [r.get("Q7", "") for r in cohorts["F"] if len(r.get("Q7", "")) > 5]

    # LLM Analysis
    SAMPLE_SIZE = None # Set to an integer (e.g., 200) for testing, or None for full dataset

    prompt = "Analyze this symbol description. Determine sentiment and emotion.\nDescription: \"{{TEXT}}\""
    
    # Run Gender batches
    print("Analyzing Men on The Man...")
    man_res_m = await utils.batch_process_with_llm(man_resp_m[:SAMPLE_SIZE] if SAMPLE_SIZE else man_resp_m, prompt, response_schema=SymbolAnalysis)
    print("Analyzing Women on The Man...")
    man_res_f = await utils.batch_process_with_llm(man_resp_f[:SAMPLE_SIZE] if SAMPLE_SIZE else man_resp_f, prompt, response_schema=SymbolAnalysis)
    print("Analyzing Men on The Temple...")
    temple_res_m = await utils.batch_process_with_llm(temple_resp_m[:SAMPLE_SIZE] if SAMPLE_SIZE else temple_resp_m, prompt, response_schema=SymbolAnalysis)
    print("Analyzing Women on The Temple...")
    temple_res_f = await utils.batch_process_with_llm(temple_resp_f[:SAMPLE_SIZE] if SAMPLE_SIZE else temple_resp_f, prompt, response_schema=SymbolAnalysis)
    
    # Run Age batches
    age_stats = {}
    print("Analyzing Age Cohorts...")
    for age, rows in age_cohorts.items():
        # The Man
        man_texts = [r.get("Q6", "") for r in rows if len(r.get("Q6", "")) > 5]
        # The Temple
        temple_texts = [r.get("Q7", "") for r in rows if len(r.get("Q7", "")) > 5]
        
        # Reuse cache
        sample_man = man_texts[:SAMPLE_SIZE] if SAMPLE_SIZE else man_texts
        sample_temple = temple_texts[:SAMPLE_SIZE] if SAMPLE_SIZE else temple_texts
        
        man_res = await utils.batch_process_with_llm(sample_man, prompt, response_schema=SymbolAnalysis)
        temple_res = await utils.batch_process_with_llm(sample_temple, prompt, response_schema=SymbolAnalysis)
        
        man_counts = Counter([r.get("primary_emotion") for r in man_res if "error" not in r])
        temple_counts = Counter([r.get("primary_emotion") for r in temple_res if "error" not in r])
        
        age_stats[age] = {"Man": man_counts, "Temple": temple_counts}
    
    def get_stats(results):
        valid = [r for r in results if "error" not in r]
        if not valid: return Counter(), 0
        c = Counter([r.get("primary_emotion") for r in valid])
        sent = sum([r.get("sentiment_score", 0) for r in valid]) / len(valid)
        return c, sent

    man_counts_m, man_score_m = get_stats(man_res_m)
    man_counts_f, man_score_f = get_stats(man_res_f)
    temple_counts_m, temple_score_m = get_stats(temple_res_m)
    temple_counts_f, temple_score_f = get_stats(temple_res_f)
    
    # Aggregate for general stats
    man_counts_all = man_counts_m + man_counts_f
    temple_counts_all = temple_counts_m + temple_counts_f
    
    # Dynamic Conclusion
    conclusion = []
    
    # Helper to calculate percentages
    def get_pct(counter, key, total):
        return (counter[key] / total) if total > 0 else 0

    man_total = sum(man_counts_all.values())
    temple_total = sum(temple_counts_all.values())
    
    # General Symbolism Conclusions
    temple_grief_pct = get_pct(temple_counts_all, 'Grief', temple_total)
    man_grief_pct = get_pct(man_counts_all, 'Grief', man_total)
    man_cel_pct = get_pct(man_counts_all, 'Celebration', man_total)
    temple_cel_pct = get_pct(temple_counts_all, 'Celebration', temple_total)

    if temple_grief_pct > 0.4:
        conclusion.append(f"**Temple as Grief Vessel:** The Temple is strongly associated with Grief ({temple_grief_pct:.1%}), significantly more than the Man ({man_grief_pct:.1%}).")
    elif temple_grief_pct > man_grief_pct:
        conclusion.append(f"**Temple leans towards Grief:** While present in both, Grief is more prevalent in Temple narratives ({temple_grief_pct:.1%} vs {man_grief_pct:.1%}).")
        
    if man_cel_pct > 0.4:
        conclusion.append(f"**Man as Celebration:** The Man is primarily a symbol of Celebration ({man_cel_pct:.1%}), contrasting with the Temple's lower association ({temple_cel_pct:.1%}).")
    elif man_counts_all['Indifference'] > man_counts_all['Celebration']:
        conclusion.append("**Ambivalence toward the Man:** 'Indifference' is the most common reaction to the Man, suggesting a potential disconnect or routinization of the symbol.")
    else:
        conclusion.append(f"**Mixed Signals on the Man:** The Man evokes a broad range of emotions, with Celebration ({man_cel_pct:.1%}) being a leading but not dominant theme.")

    # Gender Conclusion
    conclusion.append("\n\n**Gender Analysis:**")
    
    # Compare Grief in Temple (M vs F)
    m_temple_grief = get_pct(temple_counts_m, 'Grief', sum(temple_counts_m.values()))
    f_temple_grief = get_pct(temple_counts_f, 'Grief', sum(temple_counts_f.values()))
    
    if abs(m_temple_grief - f_temple_grief) < 0.05:
        conclusion.append(f"**Universal Grief:** Men and Women relate to the Temple with nearly identical levels of Grief ({m_temple_grief:.1%} vs {f_temple_grief:.1%}), suggesting the ritual transcends gender.")
    elif f_temple_grief > m_temple_grief:
        conclusion.append(f"**Female Resonance with Grief:** Women are more likely ({f_temple_grief:.1%} vs {m_temple_grief:.1%}) to explicitly describe the Temple as a place of grief.")
    else:
        conclusion.append(f"**Male Resonance with Grief:** Men are more likely ({m_temple_grief:.1%} vs {f_temple_grief:.1%}) to explicitly describe the Temple as a place of grief.")

    # Report
    sample_desc = f"{SAMPLE_SIZE}" if SAMPLE_SIZE else "Full Dataset"
    report = ["# Module 4: Sacred vs. Profane (Symbolism & Gender)\n"]
    report.append("**Research Question:** How do the emotional profiles of 'The Man' and 'The Temple' differ, and is there a gender divide?\n")
    report.append(f"**Methodology:** Comparative sentiment and emotion analysis of {man_total} Man responses vs {temple_total} Temple responses, segmented by Gender and **Age**. Sample size: {sample_desc}.\n")
    
    report.append("## Results & Analysis")
    report.append(f"- **The Man Sentiment (M/F):** {man_score_m:.2f} / {man_score_f:.2f}")
    report.append(f"- **The Temple Sentiment (M/F):** {temple_score_m:.2f} / {temple_score_f:.2f}")
    
    report.append("\n**Dominant Emotions (Top 3):**")
    report.append(f"- **The Man (All):** {', '.join([k for k,v in man_counts_all.most_common(3)])}")
    report.append(f"- **The Temple (All):** {', '.join([k for k,v in temple_counts_all.most_common(3)])}")
    
    report.append("\n### Gender Breakdown (Temple Grief)")
    report.append(f"- **Men:** {m_temple_grief:.1%}")
    report.append(f"- **Women:** {f_temple_grief:.1%}")
    
    report.append("\n### Age Analysis: Evolution of Meaning")
    report.append("| Age Group | Man: Celebration % | Temple: Grief % |")
    report.append("| :--- | :--- | :--- |")
    for age in ["Under 30", "30-39", "40-49", "50+"]:
        stats = age_stats.get(age, {"Man": Counter(), "Temple": Counter()})
        man_tot = sum(stats["Man"].values())
        temple_tot = sum(stats["Temple"].values())
        
        man_cel = stats["Man"]['Celebration'] / man_tot if man_tot > 0 else 0
        temple_grf = stats["Temple"]['Grief'] / temple_tot if temple_tot > 0 else 0
        report.append(f"| {age} | {man_cel:.1%} | {temple_grf:.1%} |")

    report.append("\n## Voices")
    
    # Helper to find a representative quote
    def find_quote(texts, results, target_emotion):
        for i, res in enumerate(results):
            if "error" in res: continue
            if res.get("primary_emotion") == target_emotion and len(texts[i]) > 40:
                return texts[i]
        return "No quote found."

    # Find dominant emotions
    top_man_emotion = man_counts_all.most_common(1)[0][0] if man_counts_all else "Indifference"
    top_temple_emotion = temple_counts_all.most_common(1)[0][0] if temple_counts_all else "Grief"
    
    # Get quotes (using the gender lists we processed earlier)
    # Combine M/F lists for search
    all_man_texts = man_resp_m + man_resp_f
    all_man_res = man_res_m + man_res_f
    
    all_temple_texts = temple_resp_m + temple_resp_f
    all_temple_res = temple_res_m + temple_res_f
    
    man_quote = find_quote(all_man_texts, all_man_res, top_man_emotion)
    temple_quote = find_quote(all_temple_texts, all_temple_res, top_temple_emotion)
    
    report.append(f"- **The Man ({top_man_emotion}):** *\"{man_quote}\"*") 
    report.append(f"- **The Temple ({top_temple_emotion}):** *\"{temple_quote}\"*")

    report.append("\n## Conclusion")
    report.append(f"> {' '.join(conclusion)}")

    utils.save_report("module_4_symbolism.md", "\n".join(report))

if __name__ == "__main__":
    asyncio.run(run_analysis())