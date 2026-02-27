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

FLUENCY_ORDER = ["novice", "learning", "fluent", "teaching"]

class AcculturationSignal(BaseModel):
    cultural_fluency: Literal["novice", "learning", "fluent", "teaching"] = Field(
        ..., description="Level of cultural integration expressed in the response."
    )
    principles_referenced: bool = Field(
        ..., description="True if any of the 10 Burning Man principles are mentioned or clearly invoked."
    )
    belonging_expressed: bool = Field(
        ..., description="True if the respondent expresses finding their tribe, fitting in, or feeling at home."
    )
    overwhelm_expressed: bool = Field(
        ..., description="True if the respondent mentions sensory, social, or logistical overwhelm."
    )
    community_role: Literal["recipient", "participant", "contributor", "leader", "none"] = Field(
        ..., description="The role the respondent describes themselves as playing in the community."
    )


def _age_group(row):
    return utils.get_age_bucket(row.get("Norm_Age"))


def _experience_group(row):
    status = row.get("Burn_Status", "")
    if status in ("Virgin", "Sophomore"):
        return "Novice"
    if status in ("Veteran", "Elder"):
        return "Veteran"
    return None


async def run_analysis():
    print("Loading Acculturation data (Transformation, 2024+2025)...")
    data_2024 = utils.load_data(2024, "Transformation")
    data_2025 = utils.load_data(2025, "Transformation")
    all_data = data_2024 + data_2025

    # Build 2×2 matrix: age_group × experience_group
    matrix = {
        ("Under 30", "Novice"): [],
        ("Under 30", "Veteran"): [],
        ("30+", "Novice"): [],
        ("30+", "Veteran"): [],
    }

    texts_list = []
    text_cells = []  # which cell each text belongs to

    for row in all_data:
        q5 = row.get("Q5", "").strip()
        q9 = row.get("Q9", "").strip()
        combined = " | ".join(t for t in [q5, q9] if len(t) > 5)
        if not combined:
            continue

        age = _age_group(row)
        age_key = "Under 30" if age == "Under 30" else "30+"
        exp_key = _experience_group(row)
        if exp_key is None:
            continue

        cell = (age_key, exp_key)
        matrix[cell].append(combined)
        texts_list.append(combined)
        text_cells.append(cell)

    prompt = (
        "Analyze this Burning Man attendee response about their transformation experience. "
        "Assess their cultural fluency level, whether they reference any of the 10 Principles, "
        "whether they express belonging/finding their tribe, whether they mention overwhelm, "
        "and what community role they describe for themselves.\n"
        "Response: \"{{TEXT}}\""
    )

    print(f"Processing {len(texts_list)} Transformation responses...")
    sample = texts_list[:SAMPLE_SIZE] if SAMPLE_SIZE else texts_list
    results = await utils.batch_process_with_llm(sample, prompt, response_schema=AcculturationSignal)

    # Aggregate per cell (cache hit expected)
    cell_stats = {}
    for cell, texts in matrix.items():
        if not texts:
            cell_stats[cell] = None
            continue
        s = texts[:SAMPLE_SIZE] if SAMPLE_SIZE else texts
        res = await utils.batch_process_with_llm(s, prompt, response_schema=AcculturationSignal)
        valid = [r for r in res if "error" not in r]
        n = len(valid)
        if n == 0:
            cell_stats[cell] = None
            continue

        avg_fluency_idx = sum(
            FLUENCY_ORDER.index(r.get("cultural_fluency", "novice")) for r in valid if r.get("cultural_fluency") in FLUENCY_ORDER
        ) / n
        avg_fluency = FLUENCY_ORDER[round(avg_fluency_idx)]

        cell_stats[cell] = {
            "n": n,
            "avg_fluency": avg_fluency,
            "pct_belonging": sum(1 for r in valid if r.get("belonging_expressed")) / n,
            "pct_overwhelm": sum(1 for r in valid if r.get("overwhelm_expressed")) / n,
            "pct_principles": sum(1 for r in valid if r.get("principles_referenced")) / n,
            "top_role": Counter(r.get("community_role") for r in valid).most_common(1)[0][0],
        }

    # Representative voices per quadrant
    voices = {}
    for i, res in enumerate(results):
        if "error" in res:
            continue
        cell = text_cells[i] if i < len(text_cells) else None
        if cell and cell not in voices and len(texts_list[i]) > 50:
            voices[cell] = (texts_list[i], res.get("cultural_fluency", ""))

    # Build report
    sample_desc = f"{SAMPLE_SIZE}" if SAMPLE_SIZE else "Full Dataset"
    report = ["# Module 8: Acculturation Journey — Young Novices, Young Veterans, and Beyond\n"]
    report.append(
        "**Research Question:** How does cultural learning and integration differ for young first-timers "
        "vs young veterans vs older cohorts at the same experience level?\n"
    )
    report.append(
        f"**Methodology:** Analysis of {len(texts_list)} Transformation survey responses (2024+2025, Q5+Q9 combined) "
        f"segmented by age (Under 30 vs 30+) and experience (Novice=Virgin/Sophomore vs Veteran/Elder). "
        f"Sample: {sample_desc}.\n"
    )

    report.append("## 2×2 Acculturation Matrix")
    report.append("| Quadrant | n | Avg Fluency | % Belonging | % Overwhelm | % Principles | Top Role |")
    report.append("| :--- | :--- | :--- | :--- | :--- | :--- | :--- |")
    for age_key in ["Under 30", "30+"]:
        for exp_key in ["Novice", "Veteran"]:
            cell = (age_key, exp_key)
            s = cell_stats.get(cell)
            label = f"{age_key} / {exp_key}"
            if not s:
                report.append(f"| {label} | 0 | — | — | — | — | — |")
            else:
                report.append(
                    f"| {label} | {s['n']} | {s['avg_fluency']} | "
                    f"{s['pct_belonging']:.0%} | {s['pct_overwhelm']:.0%} | "
                    f"{s['pct_principles']:.0%} | {s['top_role']} |"
                )

    quadrant_labels = {
        ("Under 30", "Novice"): "Young Virgin — The Threshold Crosser",
        ("Under 30", "Veteran"): "Young Veteran — The Rising Spark",
        ("30+", "Novice"): "Older Virgin — The Late Arrival",
        ("30+", "Veteran"): "Older Veteran — The Keeper of the Flame",
    }
    report.append("\n## Quadrant Narratives")
    for cell, title in quadrant_labels.items():
        s = cell_stats.get(cell)
        report.append(f"\n### {title}")
        if not s:
            report.append("*No data available.*")
            continue
        report.append(
            f"n={s['n']}. Average cultural fluency: **{s['avg_fluency']}**. "
            f"{s['pct_belonging']:.0%} express belonging, "
            f"{s['pct_overwhelm']:.0%} express overwhelm, "
            f"{s['pct_principles']:.0%} reference the Principles. "
            f"Most common community role: **{s['top_role']}**."
        )
        if cell in voices:
            text, fluency = voices[cell]
            report.append(f"\n> *\"{text[:280]}\"* *(fluency: {fluency})*")

    # Conclusion
    young_novice = cell_stats.get(("Under 30", "Novice"))
    young_vet = cell_stats.get(("Under 30", "Veteran"))
    older_vet = cell_stats.get(("30+", "Veteran"))

    conclusion = []
    if young_novice and young_vet:
        fluency_gain = FLUENCY_ORDER.index(young_vet["avg_fluency"]) - FLUENCY_ORDER.index(young_novice["avg_fluency"])
        if fluency_gain > 0:
            conclusion.append(
                f"Among Under-30 attendees, tenure meaningfully advances fluency: "
                f"Novices average **{young_novice['avg_fluency']}** while Veterans reach **{young_vet['avg_fluency']}**."
            )
        else:
            conclusion.append("Under-30 fluency does not clearly advance with tenure in this dataset.")

        overwhelm_drop = young_novice["pct_overwhelm"] - young_vet["pct_overwhelm"]
        if overwhelm_drop > 0.05:
            conclusion.append(
                f"Overwhelm drops from {young_novice['pct_overwhelm']:.0%} to {young_vet['pct_overwhelm']:.0%} "
                "as young attendees gain experience."
            )

    if young_vet and older_vet:
        if young_vet["avg_fluency"] == older_vet["avg_fluency"]:
            conclusion.append("Young and older Veterans reach comparable fluency — tenure closes the acculturation gap.")
        else:
            conclusion.append(
                f"Older Veterans (**{older_vet['avg_fluency']}**) still outpace Young Veterans "
                f"(**{young_vet['avg_fluency']}**) in fluency."
            )

    report.append("\n## Conclusion")
    report.append("> " + " ".join(conclusion) if conclusion else "> Insufficient data for comparison.")

    utils.save_report("module_8_acculturation.md", "\n".join(report))


if __name__ == "__main__":
    asyncio.run(run_analysis())
