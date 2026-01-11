import sys
import os
import asyncio
from collections import Counter
from pydantic import BaseModel, Field

# Add parent directory to path to find analysis_utils
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import analysis_utils as utils

class PronounAnalysis(BaseModel):
    self_refs: int = Field(..., description="Count of first-person singular pronouns (I, me, my, mine, myself).")
    collective_refs: int = Field(..., description="Count of first-person plural pronouns (we, us, our, ours, ourselves).")

async def run_analysis():
    print("Loading Transformation Data...")
    data_2024 = utils.load_data(2024, "Transformation")
    data_2025 = utils.load_data(2025, "Transformation")
    
    all_data = data_2024 + data_2025
    
    cohorts = {"Virgin": [], "Sophomore": [], "Veteran": [], "Elder": []}
    age_cohorts = {"Under 30": [], "30-39": [], "40-49": [], "50+": []}
    
    for row in all_data:
        q5_text = row.get("Q5", "").strip()
        if len(q5_text) > 10:
            # Tenure Cohorts
            status = row.get("Burn_Status", "Unknown")
            if status in cohorts:
                cohorts[status].append(q5_text)
            
            # Age Cohorts
            age_bucket = utils.get_age_bucket(row.get("Norm_Age"))
            if age_bucket in age_cohorts:
                age_cohorts[age_bucket].append(q5_text)
            
    # LLM Analysis
    SAMPLE_SIZE = None # Set to an integer (e.g., 200) for testing, or None for full dataset
    
    # --- Tenure Analysis ---
    cohort_themes = {}
    cohort_pronouns = {}
    
    for cohort, responses in cohorts.items():
        sample = responses[:SAMPLE_SIZE] if SAMPLE_SIZE else responses
        if not sample: continue
        
        # Theme Extraction
        theme_prompt = (
            "Analyze the following response to the question \"Did Burning Man change you?\".\n"
            "Extract 1 to 3 distinct themes (1-2 words each) representing the type of change.\n"
            "Format: Theme1, Theme2, Theme3\n"
            "Response: \"{{TEXT}}\""
        )
        themes_raw = await utils.batch_process_with_llm(sample, theme_prompt)
        
        theme_counter = Counter()
        for t_str in themes_raw:
            if not t_str or "ERROR" in t_str: continue
            themes = [t.strip().title() for t in t_str.split(",")]
            theme_counter.update(themes)
        cohort_themes[cohort] = theme_counter
        
        # Pronoun Analysis
        pronoun_prompt = (
            "Analyze the grammatical structure of this response.\n"
            "Count the number of self-references (I, me, my) vs collective references (we, us, our).\n"
            "Response: \"{{TEXT}}\""
        )
        pronoun_results = await utils.batch_process_with_llm(sample, pronoun_prompt, response_schema=PronounAnalysis)
        
        total_self = sum([r.get('self_refs', 0) for r in pronoun_results if "error" not in r])
        total_collective = sum([r.get('collective_refs', 0) for r in pronoun_results if "error" not in r])
        cohort_pronouns[cohort] = {"I": total_self, "We": total_collective}

    # --- Age Analysis ---
    age_themes = {}
    age_pronouns = {}
    
    for age_group, responses in age_cohorts.items():
        sample = responses[:SAMPLE_SIZE] if SAMPLE_SIZE else responses
        if not sample: continue
        
        # Reuse prompts (themes)
        themes_raw = await utils.batch_process_with_llm(sample, theme_prompt)
        theme_counter = Counter()
        for t_str in themes_raw:
            if not t_str or "ERROR" in t_str: continue
            themes = [t.strip().title() for t in t_str.split(",")]
            theme_counter.update(themes)
        age_themes[age_group] = theme_counter
        
        # Reuse prompts (pronouns)
        pronoun_results = await utils.batch_process_with_llm(sample, pronoun_prompt, response_schema=PronounAnalysis)
        total_self = sum([r.get('self_refs', 0) for r in pronoun_results if "error" not in r])
        total_collective = sum([r.get('collective_refs', 0) for r in pronoun_results if "error" not in r])
        age_pronouns[age_group] = {"I": total_self, "We": total_collective}

    # Dynamic Conclusion Logic
    if "Virgin" not in cohort_themes or "Elder" not in cohort_themes:
        conclusion = ["Insufficient data for comparison."]
    else:
        virgin_top = [t[0] for t in cohort_themes["Virgin"].most_common(5)]
        elder_top = [t[0] for t in cohort_themes["Elder"].most_common(5)]
        
        # Check overlap
        common_themes = set(virgin_top) & set(elder_top)
        distinct_virgin = set(virgin_top) - set(elder_top)
        distinct_elder = set(elder_top) - set(virgin_top)
        
        # Pronoun Conclusion
        v_p = cohort_pronouns.get("Virgin", {"I": 0, "We": 0})
        e_p = cohort_pronouns.get("Elder", {"I": 0, "We": 0})
        
        virgin_ratio = v_p["I"] / v_p["We"] if v_p["We"] > 0 else 0
        elder_ratio = e_p["I"] / e_p["We"] if e_p["We"] > 0 else 0
        
        conclusion = []
        conclusion.append(f"**Thematic Overlap:** {len(common_themes)} of the top 5 themes are shared between Virgins and Elders ({', '.join(common_themes)}), indicating core structural similarities.")
        
        if virgin_ratio > elder_ratio * 1.5:
             conclusion.append(f"**Linguistic Shift:** There is a marked shift from self-focus to collective-focus. Virgins use {virgin_ratio:.1f} 'I's per 'We', while Elders drop to {elder_ratio:.1f}.")
        else:
             conclusion.append(f"**Linguistic Stability:** Both groups maintain a similar balance of self-vs-collective language (Virgin: {virgin_ratio:.1f}, Elder: {elder_ratio:.1f}).")

        if len(common_themes) >= 4:
            conclusion.append("Thematically, the narrative is highly consistent regardless of tenure.")
        elif len(common_themes) <= 2:
            conclusion.append("However, there is a **notable thematic shift**.")
            if distinct_virgin:
                conclusion.append(f"Virgins prioritize **{', '.join(distinct_virgin)}**.")
            if distinct_elder:
                conclusion.append(f"Elders shift towards **{', '.join(distinct_elder)}**.")
        else:
            conclusion.append("The narrative evolves subtly, maintaining core themes while shifting emphasis.")

    # Generate Report
    sample_desc = f"{SAMPLE_SIZE} per cohort" if SAMPLE_SIZE else "Full Dataset"
    report = ["# Module 1: The Pilgrim's Progress (Transformation)\n"]
    report.append("**Research Question:** How does the narrative of transformation evolve from Virgin to Veteran?\n")
    report.append(f"**Methodology:** Analyzed {len(all_data)} transformation narratives using **LLM-based Semantic Theme Extraction** and **Linguistic Pronoun Analysis**, segmented by **Burn Tenure** and **Age**. Sample size for theme extraction: {sample_desc}.\n")
    
    report.append("## Results & Analysis (By Tenure)")
    
    report.append("### Linguistic Analysis (The 'Ego Death' Test)")
    report.append("| Cohort | Self Refs (I/Me) | Collective Refs (We/Us) | Ratio (I:We) |")
    report.append("| :--- | :--- | :--- | :--- |")
    for cohort in ["Virgin", "Sophomore", "Veteran", "Elder"]:
        stats = cohort_pronouns.get(cohort, {"I": 0, "We": 0})
        ratio = stats["I"] / stats["We"] if stats["We"] > 0 else stats["I"]
        report.append(f"| {cohort} | {stats['I']} | {stats['We']} | {ratio:.2f} |")
        
    report.append("\n### Thematic Analysis")
    for cohort, counter in cohort_themes.items():
        top_3 = ", ".join([t[0] for t in counter.most_common(3)])
        report.append(f"- **{cohort}:** Top themes are *{top_3}*.")
        
    report.append("\n## Results & Analysis (By Age)")
    report.append("### Linguistic Analysis")
    report.append("| Age Group | Self Refs | Collective Refs | Ratio (I:We) |")
    report.append("| :--- | :--- | :--- | :--- |")
    for age in ["Under 30", "30-39", "40-49", "50+"]:
        stats = age_pronouns.get(age, {"I": 0, "We": 0})
        ratio = stats["I"] / stats["We"] if stats["We"] > 0 else 0
        report.append(f"| {age} | {stats['I']} | {stats['We']} | {ratio:.2f} |")
        
    report.append("\n### Thematic Analysis")
    for age, counter in age_themes.items():
        top_3 = ", ".join([t[0] for t in counter.most_common(3)])
        report.append(f"- **{age}:** *{top_3}*")
    
    report.append("\n## Voices")
    for cohort in ["Virgin", "Sophomore", "Elder"]:
        if cohorts.get(cohort):
            responses = cohorts[cohort]
            longest = max(responses[:SAMPLE_SIZE] if SAMPLE_SIZE else responses, key=len)
            voice_block = f"- **{cohort}:** *\"{longest[:300]}\"*"
            report.append(voice_block)

    report.append("\n## Conclusion")
    report.append("> " + " ".join(conclusion))

    utils.save_report("module_1_transformation.md", "\n".join(report))

if __name__ == "__main__":
    asyncio.run(run_analysis())
