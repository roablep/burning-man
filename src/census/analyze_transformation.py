import asyncio
from collections import Counter
import analysis_utils as utils

async def run_analysis():
    print("Loading Transformation Data...")
    data_2024 = utils.load_data(2024, "Transformation")
    data_2025 = utils.load_data(2025, "Transformation")
    
    all_data = data_2024 + data_2025
    print(f"Total Transformation Records: {len(all_data)}")
    
    # Bucket by Cohort
    cohorts = {"Virgin": [], "Sophomore": [], "Veteran": [], "Elder": []}
    
    for row in all_data:
        status = row.get("Burn_Status", "Unknown")
        # Transformation Q5 is the key narrative question
        q5_text = row.get("Q5", "").strip()
        
        if status in cohorts and len(q5_text) > 10: # Filter empty/short answers
            cohorts[status].append(q5_text)
            
    # LLM Analysis
    # We will sample up to 50 responses per cohort to save time/tokens for this demo
    # but in full production we'd do all.
    SAMPLE_SIZE = 50
    
    cohort_themes = {}
    
    for cohort, responses in cohorts.items():
        print(f"Analyzing {cohort} ({len(responses)} responses)...")
        sample = responses[:SAMPLE_SIZE]
        
        prompt = """
        Analyze the following response to the question "Did Burning Man change you?".
        Extract 1 to 3 distinct themes (1-2 words each) representing the type of change.
        Format: Theme1, Theme2, Theme3
        Examples:
        - "Confidence, Community, Creativity"
        - "No Change"
        - "Open-mindedness, Social Skills"
        
        Response: "{{TEXT}}"
        """
        
        themes_raw = await utils.batch_process_with_llm(sample, prompt)
        
        # Tally themes
        theme_counter = Counter()
        for t_str in themes_raw:
            if not t_str or "ERROR" in t_str: continue
            # Split and clean
            themes = [t.strip().title() for t in t_str.split(",")]
            theme_counter.update(themes)
            
        cohort_themes[cohort] = theme_counter.most_common(10)

    # Generate Report
    report = ["# Module 1: The Pilgrim's Progress (Transformation)\n"]
    report.append("Analysis of how the narrative of change evolves by tenure.\n")
    
    for cohort, themes in cohort_themes.items():
        report.append(f"## {cohort} Themes")
        report.append("| Theme | Count |")
        report.append("| :--- | :--- |")
        for t, c in themes:
            report.append(f"| {t} | {c} |")
        report.append("\n")
        
        # Add a "Voice" section - pick a representative quote (longest usually good proxy for depth)
        if cohorts[cohort]:
            longest_response = max(cohorts[cohort][:SAMPLE_SIZE], key=len)
            voice_block = f"**Representative Voice:**\n> *\"{longest_response}\"*\n"
            report.append(voice_block)

    utils.save_report("module_1_transformation.md", "\n".join(report))

if __name__ == "__main__":
    asyncio.run(run_analysis())