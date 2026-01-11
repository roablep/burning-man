import sys
import os
import asyncio
from collections import Counter, defaultdict
from pydantic import BaseModel, Field
from typing import Literal, List, Dict, Any, Iterable, Tuple

# Add parent directory to path to find analysis_utils
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import analysis_utils as utils

THEMES_Q5 = [
    "Vulnerability",
    "Authenticity",
    "Novelty",
    "Playfulness",
    "Community",
    "Connection",
    "Boundaries",
    "Consent",
    "Jealousy",
    "Compersion",
    "Loneliness",
    "Healing",
    "Freedom",
    "Uncertainty",
]

THEMES_Q6 = [
    "Communication",
    "Trust",
    "Boundaries",
    "Jealousy",
    "Compersion",
    "Logistics",
    "Consent",
    "Support",
    "Conflict",
    "Independence",
    "Growth",
    "Intimacy",
]

THEMES_Q7 = [
    "Authenticity",
    "Intensity",
    "Openness",
    "Vulnerability",
    "Boundaries",
    "Consent",
    "Communication",
    "Jealousy",
    "Compersion",
    "Community",
    "Ephemerality",
    "Time",
    "Logistics",
    "Safety",
]

COMPARISON_INTENSE = {"More Intense", "More Authentic"}


class Q5NewLoveAnalysis(BaseModel):
    experienced: Literal["Yes", "No", "Unclear"] = Field(
        ..., description="Whether they met someone new and fell in love in BRC."
    )
    rel_type: Literal["Romantic", "Platonic", "Other", "Unclear"] = Field(
        ..., description="Type of bond described."
    )
    duration: Literal["Fleeting", "Ongoing", "Deep", "Unclear"] = Field(
        ..., description="Implied duration or depth of the bond."
    )
    tone: Literal["Positive", "Neutral", "Negative", "Mixed"] = Field(
        ..., description="Overall emotional tone."
    )
    themes: List[str] = Field(
        ..., description=f"Use only themes from: {', '.join(THEMES_Q5)}."
    )


class Q6CommittedAnalysis(BaseModel):
    in_committed_relationship: Literal["Yes", "No", "Unclear"] = Field(
        ..., description="Whether they were in a committed relationship at BRC."
    )
    partner_present: Literal["Present", "Not Present", "Not Applicable", "Unclear"] = Field(
        ..., description="Was the partner present on playa."
    )
    impact: Literal["Strengthened", "Strained", "Mixed", "No Change", "Unclear"] = Field(
        ..., description="Effect on the relationship."
    )
    tone: Literal["Positive", "Neutral", "Negative", "Mixed"] = Field(
        ..., description="Overall emotional tone."
    )
    advice: List[str] = Field(
        ..., description="0-3 short recommendations or lessons for couples."
    )
    themes: List[str] = Field(
        ..., description=f"Use only themes from: {', '.join(THEMES_Q6)}."
    )


class Q7ComparisonAnalysis(BaseModel):
    comparison: Literal[
        "More Intense",
        "More Authentic",
        "More Challenging",
        "More Permissive",
        "More Ephemeral",
        "Similar",
        "Depends",
        "Unclear",
    ] = Field(..., description="How playa relationships compare to default world.")
    tone: Literal["Positive", "Neutral", "Negative", "Mixed"] = Field(
        ..., description="Overall emotional tone."
    )
    themes: List[str] = Field(
        ..., description=f"Use only themes from: {', '.join(THEMES_Q7)}."
    )


def normalize_theme_list(values: Iterable[str], allowed: List[str]) -> List[str]:
    allowed_map = {v.lower(): v for v in allowed}
    normalized = []
    for raw in values or []:
        if not isinstance(raw, str):
            continue
        key = raw.strip().lower()
        if key in allowed_map:
            normalized.append(allowed_map[key])
    return normalized


def count_normalized_themes(results: List[Dict[str, Any]], allowed: List[str]) -> Counter:
    theme_counter = Counter()
    for res in results:
        if "error" in res:
            continue
        themes = normalize_theme_list(res.get("themes", []), allowed)
        theme_counter.update(themes)
    return theme_counter


def pick_quotes(
    items: List[Dict[str, Any]],
    results: List[Dict[str, Any]],
    allowed: List[str],
    limit_per_theme: int = 1,
    min_len: int = 50,
) -> List[Tuple[str, str, int]]:
    quotes = []
    themes_to_find = [t for t, _ in count_normalized_themes(results, allowed).most_common(3)]
    for theme in themes_to_find:
        found = 0
        for item, res in zip(items, results):
            if "error" in res:
                continue
            themes = normalize_theme_list(res.get("themes", []), allowed)
            if theme in themes and len(item["text"]) >= min_len:
                quotes.append((theme, item["text"], item["year"]))
                found += 1
            if found >= limit_per_theme:
                break
    return quotes


def collect_relationship_items(
    rows: List[Dict[str, Any]], year: int
) -> Dict[str, List[Dict[str, Any]]]:
    items = {"Q5": [], "Q6": [], "Q7": []}
    for row in rows:
        age_bucket = utils.get_age_bucket(row.get("Norm_Age"))
        burn_status = row.get("Burn_Status", "Unknown")
        gender = row.get("Norm_Gender", "Unknown")
        region = row.get("Norm_Region", "Unknown")
        for q in ["Q5", "Q6", "Q7"]:
            text = (row.get(q) or "").strip()
            if text:
                items[q].append(
                    {
                        "year": year,
                        "text": text,
                        "age_bucket": age_bucket,
                        "burn_status": burn_status,
                        "gender": gender,
                        "region": region,
                    }
                )
    return items


def summarize_by_year(items: List[Dict[str, Any]]) -> Counter:
    return Counter([item["year"] for item in items])


def summarize_field(results: List[Dict[str, Any]], field: str) -> Counter:
    return Counter([r.get(field) for r in results if "error" not in r])


def compute_burn_status_rates(
    items: List[Dict[str, Any]],
    results: List[Dict[str, Any]],
    positive_values: set,
    field: str,
) -> Dict[str, float]:
    buckets = defaultdict(list)
    for item, res in zip(items, results):
        if "error" in res:
            continue
        status = item.get("burn_status", "Unknown")
        buckets[status].append(res.get(field))
    rates = {}
    for status, values in buckets.items():
        if not values:
            rates[status] = 0.0
            continue
        match = sum(1 for v in values if v in positive_values)
        rates[status] = match / len(values)
    return rates


async def run_analysis():
    print("Loading Relationship Data...")
    # Relationship data is in Set I (2024) and Set E (2025)
    data_2024 = utils.load_data(2024, "Relationships")
    data_2025 = utils.load_data(2025, "Relationships")

    items_2024 = collect_relationship_items(data_2024, 2024)
    items_2025 = collect_relationship_items(data_2025, 2025)

    q5_items = items_2024["Q5"] + items_2025["Q5"]
    q6_items = items_2024["Q6"] + items_2025["Q6"]
    q7_items = items_2024["Q7"] + items_2025["Q7"]

    if not q5_items and not q6_items and not q7_items:
        print("No relationship narratives found.")
        return

    prompt_q5 = """
    Analyze this response about meeting someone new and falling in love at Burning Man.
    Use only the provided theme list and keep advice empty.

    Response: "{{TEXT}}"
    """
    prompt_q6 = """
    Analyze this response about being in a committed relationship at Burning Man.
    Extract whether the partner was present, the relationship impact, and any short recommendations.
    Use only the provided theme list.

    Response: "{{TEXT}}"
    """
    prompt_q7 = """
    Analyze this response comparing playa relationships to the default world.
    Focus on the comparison label and themes only from the list.

    Response: "{{TEXT}}"
    """

    q5_texts = [item["text"] for item in q5_items]
    q6_texts = [item["text"] for item in q6_items]
    q7_texts = [item["text"] for item in q7_items]

    q5_results = (
        await utils.batch_process_with_llm(
            q5_texts, prompt_q5, response_schema=Q5NewLoveAnalysis
        )
        if q5_texts
        else []
    )
    q6_results = (
        await utils.batch_process_with_llm(
            q6_texts, prompt_q6, response_schema=Q6CommittedAnalysis
        )
        if q6_texts
        else []
    )
    q7_results = (
        await utils.batch_process_with_llm(
            q7_texts, prompt_q7, response_schema=Q7ComparisonAnalysis
        )
        if q7_texts
        else []
    )

    q5_total = len([r for r in q5_results if "error" not in r])
    q6_total = len([r for r in q6_results if "error" not in r])
    q7_total = len([r for r in q7_results if "error" not in r])

    q5_year_counts = summarize_by_year(q5_items)
    q6_year_counts = summarize_by_year(q6_items)
    q7_year_counts = summarize_by_year(q7_items)

    q5_experienced = summarize_field(q5_results, "experienced")
    q5_types = summarize_field(q5_results, "rel_type")
    q5_tones = summarize_field(q5_results, "tone")
    q5_themes = count_normalized_themes(q5_results, THEMES_Q5)

    q6_partner = summarize_field(q6_results, "partner_present")
    q6_impact = summarize_field(q6_results, "impact")
    q6_tones = summarize_field(q6_results, "tone")
    q6_themes = count_normalized_themes(q6_results, THEMES_Q6)

    q7_comparison = summarize_field(q7_results, "comparison")
    q7_tones = summarize_field(q7_results, "tone")
    q7_themes = count_normalized_themes(q7_results, THEMES_Q7)

    q7_burn_status = compute_burn_status_rates(
        q7_items, q7_results, COMPARISON_INTENSE, "comparison"
    )

    advice_counter = Counter()
    for res in q6_results:
        if "error" in res:
            continue
        for advice in res.get("advice", []) or []:
            if isinstance(advice, str) and advice.strip():
                advice_counter.update([advice.strip()])

    # Report
    report = ["# Module 6: Playa Love vs. Default Love (Relationships)\n"]
    report.append(
        "**Research Question:** How do relationship dynamics and intimacy differ in the temporary autonomous zone?\n"
    )
    report.append(
        "**Methodology:** Separate analyses of Q5 (new love), Q6 (committed relationships), and Q7 (playa vs. default comparison). Results are segmented by year and burn status where possible.\n"
    )
    report.append(
        "> **Note:** 2025 sample size is much smaller; avoid unweighted cross-year comparisons.\n"
    )

    report.append("## Q5: Meeting Someone New and Falling in Love")
    report.append(
        f"- **Total Responses:** {q5_total} (2024: {q5_year_counts.get(2024, 0)}, 2025: {q5_year_counts.get(2025, 0)})"
    )
    if q5_total:
        yes_pct = q5_experienced.get("Yes", 0) / q5_total
        report.append(f"- **Experienced Love on Playa:** {yes_pct:.1%}")
    report.append(
        f"- **Top Relationship Type:** {q5_types.most_common(1)[0][0] if q5_types else 'N/A'}"
    )
    report.append(
        f"- **Top Themes:** {', '.join([t for t, _ in q5_themes.most_common(4)]) if q5_themes else 'N/A'}"
    )
    report.append(
        f"- **Tone Split:** {', '.join([f'{k} ({v})' for k, v in q5_tones.most_common(3)]) if q5_tones else 'N/A'}"
    )

    report.append("\n## Q6: Committed Relationships on Playa")
    report.append(
        f"- **Total Responses:** {q6_total} (2024: {q6_year_counts.get(2024, 0)}, 2025: {q6_year_counts.get(2025, 0)})"
    )
    report.append(
        f"- **Partner Presence:** {', '.join([f'{k} ({v})' for k, v in q6_partner.most_common(3)]) if q6_partner else 'N/A'}"
    )
    report.append(
        f"- **Relationship Impact:** {', '.join([f'{k} ({v})' for k, v in q6_impact.most_common(3)]) if q6_impact else 'N/A'}"
    )
    report.append(
        f"- **Top Themes:** {', '.join([t for t, _ in q6_themes.most_common(4)]) if q6_themes else 'N/A'}"
    )

    report.append("\n### Advice for Couples (Q6)")
    if advice_counter:
        report.append("Top recommendations:")
        for advice, count in advice_counter.most_common(5):
            report.append(f"- {advice} ({count})")
    else:
        report.append("No explicit advice extracted.")

    report.append("\n## Q7: Playa vs. Default World Relationships")
    report.append(
        f"- **Total Responses:** {q7_total} (2024: {q7_year_counts.get(2024, 0)}, 2025: {q7_year_counts.get(2025, 0)})"
    )
    report.append(
        f"- **Top Comparison:** {q7_comparison.most_common(1)[0][0] if q7_comparison else 'N/A'}"
    )
    report.append(
        f"- **Top Themes:** {', '.join([t for t, _ in q7_themes.most_common(4)]) if q7_themes else 'N/A'}"
    )

    report.append("\n### Burn Status: Intense/Authentic Comparison Rate (Q7)")
    report.append("| Burn Status | Intense/Authentic % |")
    report.append("| :--- | :--- |")
    for status in ["Virgin", "Sophomore", "Veteran", "Elder", "Unknown"]:
        report.append(f"| {status} | {q7_burn_status.get(status, 0):.1%} |")

    report.append("\n## Voices")
    for theme, quote, year in pick_quotes(q5_items, q5_results, THEMES_Q5):
        report.append(f"- **Q5 ({year}) · {theme}:** *\"{quote}\"*")
    for theme, quote, year in pick_quotes(q6_items, q6_results, THEMES_Q6):
        report.append(f"- **Q6 ({year}) · {theme}:** *\"{quote}\"*")
    for theme, quote, year in pick_quotes(q7_items, q7_results, THEMES_Q7):
        report.append(f"- **Q7 ({year}) · {theme}:** *\"{quote}\"*")

    utils.save_report("module_6_relationships.md", "\n".join(report))


if __name__ == "__main__":
    asyncio.run(run_analysis())
