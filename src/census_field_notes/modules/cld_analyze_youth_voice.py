import sys
import os
import asyncio
from collections import Counter
from pydantic import BaseModel, Field
from typing import Literal

# Add parent directory to path to find analysis_utils
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import analysis_utils as utils

SAMPLE_SIZE = None  # Set to an integer (e.g., 100) for testing, or None for full dataset

class YouthTheme(BaseModel):
    primary_theme: str = Field(..., description="1-3 word theme extracted from the response.")
    sentiment: Literal["positive", "negative", "mixed"] = Field(..., description="Emotional tone of the response.")
    values_language: Literal["freedom", "community", "identity", "spirituality", "creativity", "survival", "other"] = Field(
        ..., description="Primary value system expressed in the response."
    )
    key_phrase: str = Field(..., description="Most distinctive phrase from the response.")


async def run_analysis():
    print("Loading Youth Voice data (all types, 2024+2025)...")
    data_2024 = utils.load_data(2024)
    data_2025 = utils.load_data(2025)
    all_data = data_2024 + data_2025

    age_groups = ["Under 30", "30-39", "40-49", "50+"]
    age_cohorts = {ag: [] for ag in age_groups}
    all_texts = []
    all_ages = []

    for row in all_data:
        text = row.get("Q5", "").strip()
        if len(text) < 15:
            continue
        age = utils.get_age_bucket(row.get("Norm_Age"))
        all_texts.append(text)
        all_ages.append(age)
        if age in age_cohorts:
            age_cohorts[age].append(text)

    prompt = (
        "Analyze this Burning Man field notes response. "
        "Extract the primary theme (1-3 words), emotional sentiment, "
        "primary value expressed, and the single most distinctive phrase.\n"
        "Response: \"{{TEXT}}\""
    )

    print(f"Processing {len(all_texts)} total Q5 responses...")
    sample = all_texts[:SAMPLE_SIZE] if SAMPLE_SIZE else all_texts
    results = await utils.batch_process_with_llm(sample, prompt, response_schema=YouthTheme)

    # Overall stats
    theme_counter = Counter(r.get("primary_theme", "").strip().title() for r in results if "error" not in r and r.get("primary_theme"))
    sentiment_counter = Counter(r.get("sentiment") for r in results if "error" not in r)
    total = sum(sentiment_counter.values())

    # Per-age stats (cache hit — free)
    age_stats = {}
    for age in age_groups:
        texts = age_cohorts[age]
        if not texts:
            age_stats[age] = {"themes": Counter(), "sentiment": Counter(), "values": Counter()}
            continue
        s = texts[:SAMPLE_SIZE] if SAMPLE_SIZE else texts
        res = await utils.batch_process_with_llm(s, prompt, response_schema=YouthTheme)
        age_stats[age] = {
            "themes": Counter(r.get("primary_theme", "").strip().title() for r in res if "error" not in r and r.get("primary_theme")),
            "sentiment": Counter(r.get("sentiment") for r in res if "error" not in r),
            "values": Counter(r.get("values_language") for r in res if "error" not in r),
        }

    # Representative quotes (one per age group)
    voices = {}
    for i, res in enumerate(results):
        if "error" in res:
            continue
        age = all_ages[i] if i < len(all_ages) else "Unknown"
        if age not in voices and len(all_texts[i]) > 40:
            voices[age] = (all_texts[i], res.get("key_phrase", ""))

    # Build report
    sample_desc = f"{SAMPLE_SIZE} per group" if SAMPLE_SIZE else "Full Dataset"
    report = ["# Module 7: Youth Voice — Language, Values & Sentiment by Age\n"]
    report.append("**Research Question:** How does Under-30 language, values, and emotional tone differ from older cohorts?\n")
    report.append(
        f"**Methodology:** Semantic classification of {total} Q5 responses (2024+2025, all survey types) "
        f"segmented by age group. Sample: {sample_desc}.\n"
    )

    report.append("## Top 10 Themes (Overall)")
    for theme, count in theme_counter.most_common(10):
        report.append(f"- **{theme}:** {count}")

    report.append("\n## Top Themes by Age Group")
    for age in age_groups:
        stats = age_stats[age]
        n = sum(stats["sentiment"].values())
        top = ", ".join(t for t, _ in stats["themes"].most_common(5))
        report.append(f"- **{age}** (n={n}): {top}")

    all_values = ["freedom", "community", "identity", "spirituality", "creativity", "survival", "other"]
    report.append("\n## Values Language Distribution by Age Group")
    header = "| Age Group | " + " | ".join(v.title() for v in all_values) + " |"
    sep = "| :--- |" + " :--- |" * len(all_values)
    report.append(header)
    report.append(sep)
    for age in age_groups:
        stats = age_stats[age]
        n = sum(stats["values"].values())
        if n == 0:
            row_cells = " | ".join("—" for _ in all_values)
        else:
            row_cells = " | ".join(f"{stats['values'].get(v, 0) / n:.0%}" for v in all_values)
        report.append(f"| {age} | {row_cells} |")

    report.append("\n## Sentiment by Age Group")
    report.append("| Age Group | Positive | Negative | Mixed | n |")
    report.append("| :--- | :--- | :--- | :--- | :--- |")
    for age in age_groups:
        stats = age_stats[age]
        n = sum(stats["sentiment"].values())
        if n == 0:
            report.append(f"| {age} | — | — | — | 0 |")
        else:
            pos = stats["sentiment"].get("positive", 0) / n
            neg = stats["sentiment"].get("negative", 0) / n
            mix = stats["sentiment"].get("mixed", 0) / n
            report.append(f"| {age} | {pos:.0%} | {neg:.0%} | {mix:.0%} | {n} |")

    report.append("\n## Voices — Representative Quotes by Age Group")
    for age in age_groups:
        if age in voices:
            text, phrase = voices[age]
            report.append(f"\n**{age}:** *\"{text[:250]}\"*")
            if phrase:
                report.append(f"> Key phrase: *\"{phrase}\"*")

    # Conclusion
    u30_stats = age_stats.get("Under 30", {"themes": Counter(), "values": Counter(), "sentiment": Counter()})
    older_themes = Counter()
    older_values = Counter()
    for age in ["30-39", "40-49", "50+"]:
        older_themes.update(age_stats[age]["themes"])
        older_values.update(age_stats[age]["values"])

    u30_top_themes = {t for t, _ in u30_stats["themes"].most_common(5)}
    older_top_themes = {t for t, _ in older_themes.most_common(5)}
    distinct_young = u30_top_themes - older_top_themes
    distinct_older = older_top_themes - u30_top_themes

    u30_n = sum(u30_stats["sentiment"].values())
    u30_top_val = u30_stats["values"].most_common(1)[0][0] if u30_stats["values"] else "N/A"
    older_top_val = older_values.most_common(1)[0][0] if older_values else "N/A"

    conclusion = []
    if distinct_young:
        conclusion.append(f"Under-30 voices emphasize **{', '.join(distinct_young)}** — themes largely absent from older cohorts.")
    if distinct_older:
        conclusion.append(f"Older cohorts lean toward **{', '.join(distinct_older)}**.")
    conclusion.append(
        f"Values language diverges: young respondents (n={u30_n}) most often express **{u30_top_val}**, "
        f"while older cohorts foreground **{older_top_val}**."
    )

    report.append("\n## Conclusion")
    report.append("> " + " ".join(conclusion) if conclusion else "> Insufficient data for comparison.")

    utils.save_report("module_7_youth_voice.md", "\n".join(report))


if __name__ == "__main__":
    asyncio.run(run_analysis())
