import sys
import os
import asyncio
from collections import Counter, defaultdict
from pydantic import BaseModel, Field
from typing import Literal

# Add parent directory to path to find analysis_utils
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import analysis_utils as utils

SAMPLE_SIZE = None  # Set to an integer (e.g., 100) for testing, or None for full dataset

INTENT_ORDER = ["explicit_yes", "implicit_yes", "neutral", "implicit_no", "explicit_no"]

class ReturnSignal(BaseModel):
    return_intent: Literal["explicit_yes", "explicit_no", "implicit_yes", "implicit_no", "neutral"] = Field(
        ..., description="Whether the respondent signals intent to return to Burning Man."
    )
    time_horizon: Literal["next_year", "someday", "never", "unclear"] = Field(
        ..., description="Time frame implied by the return intent."
    )
    key_phrase: str = Field(
        ..., description="The phrase most clearly indicating return intent (or lack thereof)."
    )
    barrier_type: Literal["cost", "logistics", "emotional", "social", "none"] = Field(
        ..., description="Type of barrier mentioned if return intent is negative or mixed. Use 'none' if not applicable."
    )


async def run_analysis():
    print("Loading Return Intent data (Transformation + Experiences/Emotions, 2024+2025)...")

    transformation_2024 = utils.load_data(2024, "Transformation")
    transformation_2025 = utils.load_data(2025, "Transformation")

    # "Emotions" survey types (Set C/H in 2024)
    emotions_2024 = utils.load_data(2024, "Emotions")
    emotions_2025 = utils.load_data(2025, "Emotions")

    # "Beyond" / "L" set (2024-only, life outside BRC)
    beyond_2024 = utils.load_data(2024, "L")

    all_data_with_type = (
        [(row, "Transformation") for row in transformation_2024 + transformation_2025]
        + [(row, "Emotions") for row in emotions_2024 + emotions_2025]
        + [(row, "Beyond") for row in beyond_2024]
    )

    age_groups = ["Under 30", "30-39", "40-49", "50+"]
    burn_statuses = ["Virgin", "Sophomore", "Veteran", "Elder"]
    age_keys = ["Under 30", "30+"]

    age_cohorts = {ag: [] for ag in age_groups}
    matrix = defaultdict(list)  # (age_key, burn_status) -> list of texts

    all_texts = []
    all_ages = []
    all_statuses = []

    for row, survey_type in all_data_with_type:
        text = row.get("Q5", "").strip()
        if len(text) < 15:
            continue
        age = utils.get_age_bucket(row.get("Norm_Age"))
        status = row.get("Burn_Status", "")
        age_key = "Under 30" if age == "Under 30" else "30+"

        all_texts.append(text)
        all_ages.append(age)
        all_statuses.append(status)

        if age in age_cohorts:
            age_cohorts[age].append(text)
        if status in burn_statuses:
            matrix[(age_key, status)].append(text)

    prompt = (
        "Analyze this Burning Man field notes response for signals about whether the person "
        "intends to return to Burning Man. Look for explicit statements, future-tense language, "
        "and phrases that imply intent. Also identify any barriers mentioned.\n"
        "Response: \"{{TEXT}}\""
    )

    print(f"Processing {len(all_texts)} responses for return intent...")
    sample = all_texts[:SAMPLE_SIZE] if SAMPLE_SIZE else all_texts
    results = await utils.batch_process_with_llm(sample, prompt, response_schema=ReturnSignal)

    # Per-age stats (cache hit — free)
    age_stats = {}
    for age in age_groups:
        texts = age_cohorts[age]
        if not texts:
            age_stats[age] = None
            continue
        s = texts[:SAMPLE_SIZE] if SAMPLE_SIZE else texts
        res = await utils.batch_process_with_llm(s, prompt, response_schema=ReturnSignal)
        valid = [r for r in res if "error" not in r]
        n = len(valid)
        if n == 0:
            age_stats[age] = None
            continue
        age_stats[age] = {
            "n": n,
            "intent": Counter(r.get("return_intent") for r in valid),
            "barrier": Counter(r.get("barrier_type") for r in valid if r.get("barrier_type") != "none"),
        }

    # 2×4 matrix stats
    matrix_stats = {}
    for age_key in age_keys:
        for status in burn_statuses:
            texts = matrix.get((age_key, status), [])
            if not texts:
                matrix_stats[(age_key, status)] = None
                continue
            s = texts[:SAMPLE_SIZE] if SAMPLE_SIZE else texts
            res = await utils.batch_process_with_llm(s, prompt, response_schema=ReturnSignal)
            valid = [r for r in res if "error" not in r]
            n = len(valid)
            if n == 0:
                matrix_stats[(age_key, status)] = None
                continue
            pos_count = sum(1 for r in valid if r.get("return_intent") in ("explicit_yes", "implicit_yes"))
            matrix_stats[(age_key, status)] = {
                "n": n,
                "pct_positive": pos_count / n,
                "intent": Counter(r.get("return_intent") for r in valid),
            }

    # Representative quotes: young first-timer returns vs doesn't
    return_voice = None
    no_return_voice = None
    for i, res in enumerate(results):
        if "error" in res:
            continue
        age = all_ages[i] if i < len(all_ages) else "Unknown"
        status = all_statuses[i] if i < len(all_statuses) else ""
        text = all_texts[i] if i < len(all_texts) else ""
        if age == "Under 30" and status in ("Virgin", "Sophomore") and len(text) > 50:
            if return_voice is None and res.get("return_intent") in ("explicit_yes", "implicit_yes"):
                return_voice = (text, res.get("key_phrase", ""))
            if no_return_voice is None and res.get("return_intent") in ("explicit_no", "implicit_no"):
                no_return_voice = (text, res.get("key_phrase", ""))
        if return_voice and no_return_voice:
            break

    # Build report
    sample_desc = f"{SAMPLE_SIZE}" if SAMPLE_SIZE else "Full Dataset"
    report = ["# Module 10: Return Intent Signals — Who Comes Back?\n"]
    report.append(
        "**Research Question:** From the qualitative text, who signals plans to return — "
        "and does this differ by age and experience level?\n"
    )
    report.append(
        f"**Methodology:** Analysis of {len(all_texts)} Q5 responses from Transformation, Emotions/Experiences, "
        f"and Beyond survey types (2024+2025), segmented by age group and Burn Status. Sample: {sample_desc}.\n"
    )

    report.append("## Return Intent by Age Group")
    report.append("| Age Group | n | Explicit Yes | Implicit Yes | Neutral | Implicit No | Explicit No |")
    report.append("| :--- | :--- | :--- | :--- | :--- | :--- | :--- |")
    for age in age_groups:
        s = age_stats.get(age)
        if not s:
            report.append(f"| {age} | 0 | — | — | — | — | — |")
        else:
            n = s["n"]
            cells = " | ".join(f"{s['intent'].get(k, 0) / n:.0%}" for k in INTENT_ORDER)
            report.append(f"| {age} | {n} | {cells} |")

    report.append("\n## Return Intent by Age × Burn Status (2×4 Matrix)")
    report.append("*% with positive intent (explicit_yes + implicit_yes)*")
    header = "| Age | " + " | ".join(burn_statuses) + " |"
    sep = "| :--- |" + " :--- |" * len(burn_statuses)
    report.append(header)
    report.append(sep)
    for age_key in age_keys:
        cells = []
        for status in burn_statuses:
            s = matrix_stats.get((age_key, status))
            if not s:
                cells.append("—")
            else:
                cells.append(f"{s['pct_positive']:.0%} (n={s['n']})")
        report.append(f"| {age_key} | " + " | ".join(cells) + " |")

    all_barriers = ["cost", "logistics", "emotional", "social"]
    report.append("\n## Barrier Types by Age Group")
    report.append("| Age Group | Cost | Logistics | Emotional | Social |")
    report.append("| :--- | :--- | :--- | :--- | :--- |")
    for age in age_groups:
        s = age_stats.get(age)
        if not s:
            report.append(f"| {age} | — | — | — | — |")
        else:
            total_barriers = sum(s["barrier"].values())
            if total_barriers == 0:
                report.append(f"| {age} | — | — | — | — |")
            else:
                cells = " | ".join(f"{s['barrier'].get(b, 0) / total_barriers:.0%}" for b in all_barriers)
                report.append(f"| {age} | {cells} |")

    report.append("\n## Voices — Young First-Timers (Under 30, Virgin/Sophomore)")
    if return_voice:
        text, phrase = return_voice
        report.append("\n**Signals Return:**")
        report.append(f"> *\"{text[:300]}\"*")
        if phrase:
            report.append(f"> Key phrase: *\"{phrase}\"*")
    else:
        report.append("*No representative quote found.*")

    if no_return_voice:
        text, phrase = no_return_voice
        report.append("\n**Does Not Signal Return:**")
        report.append(f"> *\"{text[:300]}\"*")
        if phrase:
            report.append(f"> Key phrase: *\"{phrase}\"*")
    else:
        report.append("\n*No negative-intent quote found among young first-timers.*")

    # Conclusion
    u30_virgin = matrix_stats.get(("Under 30", "Virgin"))
    older_virgin = matrix_stats.get(("30+", "Virgin"))

    conclusion = []
    if u30_virgin and older_virgin:
        diff = u30_virgin["pct_positive"] - older_virgin["pct_positive"]
        if diff < -0.05:
            conclusion.append(
                f"Under-30 Virgins signal return intent at a lower rate ({u30_virgin['pct_positive']:.0%}) "
                f"than older first-timers ({older_virgin['pct_positive']:.0%}), "
                "indicating a retention gap at the first-time boundary."
            )
        elif diff > 0.05:
            conclusion.append(
                f"Under-30 Virgins are actually *more* likely to signal return intent ({u30_virgin['pct_positive']:.0%}) "
                f"than older first-timers ({older_virgin['pct_positive']:.0%})."
            )
        else:
            conclusion.append(
                f"Return intent among first-timers is comparable across age groups "
                f"(Under 30: {u30_virgin['pct_positive']:.0%}, 30+: {older_virgin['pct_positive']:.0%})."
            )

    u30_stat = age_stats.get("Under 30")
    if u30_stat and u30_stat["barrier"]:
        top_barrier = u30_stat["barrier"].most_common(1)[0][0]
        conclusion.append(f"The most cited barrier for Under-30 non-returners is **{top_barrier}**.")

    report.append("\n## Conclusion")
    report.append("> " + " ".join(conclusion) if conclusion else "> Insufficient data for comparison.")

    utils.save_report("module_10_return_intent.md", "\n".join(report))


if __name__ == "__main__":
    asyncio.run(run_analysis())
