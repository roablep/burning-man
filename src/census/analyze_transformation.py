import asyncio
from collections import Counter
import analysis_utils as utils

async def run_analysis():
    print("Loading Transformation Data...")
    data_2024 = utils.load_data(2024, "Transformation")
    data_2025 = utils.load_data(2025, "Transformation")
    
    all_data = data_2024 + data_2025
    
    cohorts = {"Virgin": [], "Sophomore": [], "Veteran": [], "Elder": []}
    
    for row in all_data:
        status = row.get("Burn_Status", "Unknown")
        q5_text = row.get("Q5", "").strip()
        if status in cohorts and len(q5_text) > 10:
            cohorts[status].append(q5_text)
            
    # LLM Analysis
    SAMPLE_SIZE = 200
    cohort_themes = {}
    
    for cohort, responses in cohorts.items():
        sample = responses[:SAMPLE_SIZE]
        prompt = """
        Analyze the following response to the question "Did Burning Man change you?".
        Extract 1 to 3 distinct themes (1-2 words each) representing the type of change.
        Format: Theme1, Theme2, Theme3
        Response: "{{TEXT}}"
        """
        themes_raw = await utils.batch_process_with_llm(sample, prompt)
        
        theme_counter = Counter()
        for t_str in themes_raw:
            if not t_str or "ERROR" in t_str: continue
            themes = [t.strip().title() for t in t_str.split(",")]
            theme_counter.update(themes)
        cohort_themes[cohort] = theme_counter

    # Dynamic Conclusion Logic
    virgin_top = [t[0] for t in cohort_themes["Virgin"].most_common(5)]
    elder_top = [t[0] for t in cohort_themes["Elder"].most_common(5)]
    
    # Check overlap
    common_themes = set(virgin_top) & set(elder_top)
    distinct_virgin = set(virgin_top) - set(elder_top)
    distinct_elder = set(elder_top) - set(virgin_top)
    
    conclusion = []
    conclusion.append(f"**Thematic Overlap:** {len(common_themes)} of the top 5 themes are shared between Virgins and Elders ({', '.join(common_themes)}), indicating core structural similarities.")
    
    if len(common_themes) >= 4:
        conclusion.append("This suggests a **highly consistent** narrative of transformation regardless of tenure.")
    elif len(common_themes) <= 2:
        conclusion.append("However, there is a **notable shift** in focus.")
        if distinct_virgin:
            conclusion.append(f"Virgins prioritize **{', '.join(distinct_virgin)}**.")
        if distinct_elder:
            conclusion.append(f"Elders shift towards **{', '.join(distinct_elder)}**.")
    else:
        conclusion.append("The narrative evolves subtly, maintaining core themes while shifting emphasis.")

    # Generate Report
    report = ["# Module 1: The Pilgrim's Progress (Transformation)\n"]
    report.append("**Research Question:** How does the narrative of transformation evolve from Virgin to Veteran?\n")
    report.append(f"**Methodology:** Analyzed {len(all_data)} transformation narratives using TF-IDF style keyword extraction via LLM, segmented by Burn Tenure (Virgin, Sophomore, Veteran, Elder). Sample size for theme extraction: {SAMPLE_SIZE} per cohort.\n")
    
    report.append("## Results & Analysis")
    for cohort, counter in cohort_themes.items():
        top_3 = ", ".join([t[0] for t in counter.most_common(3)])
        report.append(f"- **{cohort}:** Top themes are *{top_3}*.")
    
    report.append("\n## Voices")
    for cohort in ["Virgin", "Sophomore", "Elder"]:
        if cohorts[cohort]:
            longest = max(cohorts[cohort][:SAMPLE_SIZE], key=len)
            voice_block = f"- **{cohort}:** *\"{longest[:300]}\"*"
            report.append(voice_block)

    report.append("\n## Conclusion")
    report.append("> " + " ".join(conclusion))

    utils.save_report("module_1_transformation.md", "\n".join(report))

if __name__ == "__main__":
    asyncio.run(run_analysis())