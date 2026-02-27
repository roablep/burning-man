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

class BelongingSignal(BaseModel):
    belonging_source: Literal[
        "theme_camp", "strangers", "friends_brought", "romantic", "art_community", "solo", "none"
    ] = Field(..., description="Primary source of belonging or connection described in the response.")
    camp_explicitly_mentioned: bool = Field(
        ..., description="True if the respondent explicitly mentions a theme camp, their camp, or camp community."
    )
    integration_level: Literal["isolated", "peripheral", "integrated", "central"] = Field(
        ..., description="How integrated the respondent seems in the Burning Man community."
    )
    sentiment: Literal["positive", "negative", "mixed"] = Field(
        ..., description="Emotional tone regarding belonging and connection."
    )
    barrier_mentioned: bool = Field(
        ..., description="True if the respondent mentions difficulty connecting, feeling excluded, or social barriers."
    )


async def run_analysis():
    print("Loading Belonging data (Survival + Transformation, 2024+2025)...")

    # Survival set: Q8 = "How do you rely on community to survive?"
    survival_2024 = utils.load_data(2024, "Survival")
    survival_2025 = utils.load_data(2025, "Survival")

    # Transformation set: Q8 = "Did BM change the way you relate to other people?"
    transformation_2024 = utils.load_data(2024, "Transformation")
    transformation_2025 = utils.load_data(2025, "Transformation")

    age_groups = ["Under 30", "30-39", "40-49", "50+"]
    age_cohorts = {ag: [] for ag in age_groups}
    all_texts = []
    all_ages = []

    def collect(dataset):
        for row in dataset:
            text = row.get("Q8", "").strip()
            if len(text) < 15:
                continue
            age = utils.get_age_bucket(row.get("Norm_Age"))
            all_texts.append(text)
            all_ages.append(age)
            if age in age_cohorts:
                age_cohorts[age].append(text)

    collect(survival_2024)
    collect(survival_2025)
    collect(transformation_2024)
    collect(transformation_2025)

    prompt = (
        "Analyze this Burning Man field notes response about community, connection, and belonging. "
        "Identify the primary source of belonging, whether a theme camp is explicitly mentioned, "
        "the respondent's level of social integration, the emotional sentiment, "
        "and whether they mention barriers to connecting.\n"
        "Response: \"{{TEXT}}\""
    )

    print(f"Processing {len(all_texts)} belonging-related responses...")
    sample = all_texts[:SAMPLE_SIZE] if SAMPLE_SIZE else all_texts
    results = await utils.batch_process_with_llm(sample, prompt, response_schema=BelongingSignal)

    # Overall stats
    total_valid = [r for r in results if "error" not in r]
    total_n = len(total_valid)
    overall_camp_rate = sum(1 for r in total_valid if r.get("camp_explicitly_mentioned")) / total_n if total_n else 0
    overall_barrier_rate = sum(1 for r in total_valid if r.get("barrier_mentioned")) / total_n if total_n else 0

    # Per-age stats (cache hit — free)
    age_stats = {}
    for age in age_groups:
        texts = age_cohorts[age]
        if not texts:
            age_stats[age] = None
            continue
        s = texts[:SAMPLE_SIZE] if SAMPLE_SIZE else texts
        res = await utils.batch_process_with_llm(s, prompt, response_schema=BelongingSignal)
        valid = [r for r in res if "error" not in r]
        n = len(valid)
        if n == 0:
            age_stats[age] = None
            continue
        age_stats[age] = {
            "n": n,
            "source_counter": Counter(r.get("belonging_source") for r in valid),
            "camp_rate": sum(1 for r in valid if r.get("camp_explicitly_mentioned")) / n,
            "integration_counter": Counter(r.get("integration_level") for r in valid),
            "barrier_rate": sum(1 for r in valid if r.get("barrier_mentioned")) / n,
            "sentiment_counter": Counter(r.get("sentiment") for r in valid),
        }

    # Representative quotes: belonging vs isolation
    belonging_voices = {}
    isolation_voices = {}
    for i, res in enumerate(results):
        if "error" in res:
            continue
        age = all_ages[i] if i < len(all_ages) else "Unknown"
        text = all_texts[i] if i < len(all_texts) else ""
        if len(text) < 40:
            continue
        if res.get("integration_level") in ("integrated", "central") and res.get("sentiment") == "positive":
            if age not in belonging_voices:
                belonging_voices[age] = text
        if res.get("integration_level") == "isolated" or res.get("barrier_mentioned"):
            if age not in isolation_voices:
                isolation_voices[age] = text

    # Build report
    sample_desc = f"{SAMPLE_SIZE}" if SAMPLE_SIZE else "Full Dataset"
    report = ["# Module 9: Belonging & Camp Effect — Social Integration by Age\n"]
    report.append(
        "**Research Question:** What do younger attendees say about social integration — "
        "and how often does camp affiliation appear as a belonging mechanism?\n"
    )
    report.append(
        f"**Methodology:** Analysis of {total_n} Q8 responses from Survival and Transformation surveys "
        f"(2024+2025), segmented by age group. Sample: {sample_desc}.\n"
    )

    all_sources = ["theme_camp", "strangers", "friends_brought", "romantic", "art_community", "solo", "none"]
    report.append("## Belonging Source by Age Group")
    header = "| Age Group | n | " + " | ".join(s.replace("_", " ").title() for s in all_sources) + " |"
    sep = "| :--- | :--- |" + " :--- |" * len(all_sources)
    report.append(header)
    report.append(sep)
    for age in age_groups:
        s = age_stats.get(age)
        if not s:
            report.append(f"| {age} | 0 |" + " — |" * len(all_sources))
        else:
            cells = " | ".join(f"{s['source_counter'].get(src, 0) / s['n']:.0%}" for src in all_sources)
            report.append(f"| {age} | {s['n']} | {cells} |")

    report.append("\n## Camp Mention Rate by Age Group")
    report.append("*(Proxy for camp as a belonging mechanism in qualitative data)*")
    report.append("| Age Group | n | Camp Mentioned |")
    report.append("| :--- | :--- | :--- |")
    for age in age_groups:
        s = age_stats.get(age)
        if not s:
            report.append(f"| {age} | 0 | — |")
        else:
            report.append(f"| {age} | {s['n']} | {s['camp_rate']:.0%} |")
    report.append(f"\n*Overall camp mention rate: {overall_camp_rate:.0%} (n={total_n})*")

    all_integration = ["isolated", "peripheral", "integrated", "central"]
    report.append("\n## Integration Level by Age Group")
    header2 = "| Age Group | " + " | ".join(l.title() for l in all_integration) + " |"
    sep2 = "| :--- |" + " :--- |" * len(all_integration)
    report.append(header2)
    report.append(sep2)
    for age in age_groups:
        s = age_stats.get(age)
        if not s:
            report.append(f"| {age} |" + " — |" * len(all_integration))
        else:
            cells = " | ".join(f"{s['integration_counter'].get(lv, 0) / s['n']:.0%}" for lv in all_integration)
            report.append(f"| {age} | {cells} |")

    report.append("\n## Barrier Mention Rate by Age Group")
    report.append("*(Who struggles most to connect?)*")
    report.append("| Age Group | n | Barrier Mentioned |")
    report.append("| :--- | :--- | :--- |")
    for age in age_groups:
        s = age_stats.get(age)
        if not s:
            report.append(f"| {age} | 0 | — |")
        else:
            report.append(f"| {age} | {s['n']} | {s['barrier_rate']:.0%} |")
    report.append(f"\n*Overall barrier mention rate: {overall_barrier_rate:.0%} (n={total_n})*")

    report.append("\n## Voices — Belonging vs. Isolation by Age Group")
    for age in age_groups:
        if age in belonging_voices or age in isolation_voices:
            report.append(f"\n**{age}**")
        if age in belonging_voices:
            report.append(f"- *Belonging:* \"{belonging_voices[age][:260]}\"")
        if age in isolation_voices:
            report.append(f"- *Isolation/Barrier:* \"{isolation_voices[age][:260]}\"")

    # Conclusion
    u30 = age_stats.get("Under 30")
    older_camp_rates = [age_stats[a]["camp_rate"] for a in ["30-39", "40-49", "50+"] if age_stats.get(a)]
    avg_older_camp = sum(older_camp_rates) / len(older_camp_rates) if older_camp_rates else 0

    conclusion = []
    if u30:
        if u30["camp_rate"] > avg_older_camp + 0.05:
            conclusion.append(
                f"Under-30 attendees mention theme camps at a higher rate ({u30['camp_rate']:.0%}) "
                f"than older cohorts (avg {avg_older_camp:.0%}), suggesting camp membership is particularly "
                "central to young attendees' belonging narratives."
            )
        elif u30["camp_rate"] < avg_older_camp - 0.05:
            conclusion.append(
                f"Older attendees reference camps more often (avg {avg_older_camp:.0%}) than Under-30s "
                f"({u30['camp_rate']:.0%}), suggesting younger attendees find belonging through other channels."
            )
        else:
            conclusion.append(
                f"Camp mention rates are comparable across age groups (~{u30['camp_rate']:.0%} for Under-30 vs "
                f"avg {avg_older_camp:.0%} for older cohorts)."
            )

        max_barrier_age = max(
            (a for a in age_groups if age_stats.get(a)),
            key=lambda a: age_stats[a]["barrier_rate"]
        )
        report_barrier = age_stats[max_barrier_age]["barrier_rate"] if age_stats.get(max_barrier_age) else 0
        conclusion.append(
            f"Social barriers are most commonly reported by **{max_barrier_age}** ({report_barrier:.0%})."
        )

    report.append("\n## Conclusion")
    report.append("> " + " ".join(conclusion) if conclusion else "> Insufficient data for comparison.")

    utils.save_report("module_9_belonging.md", "\n".join(report))


if __name__ == "__main__":
    asyncio.run(run_analysis())
