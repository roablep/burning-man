import sys
import os
import asyncio
import re
import statistics
from collections import Counter
from pydantic import BaseModel, Field
from typing import Literal, Iterable, Dict, List, Tuple

# Add parent directory to path to find analysis_utils
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import analysis_utils as utils

class SurvivalAnalysis(BaseModel):
    mentions_hardship: bool = Field(..., description="Does the participant mention physical hardships like mud, heat, dust, hunger, or exhaustion?")
    hardship_level: Literal["None", "Low", "Medium", "High"] = Field(..., description="The intensity of the physical ordeal described.")
    describes_breakthrough: bool = Field(..., description="Does the participant describe a significant emotional or spiritual breakthrough?")
    hardship_was_catalyst: bool = Field(..., description="Is the physical hardship explicitly described as the cause or catalyst for the breakthrough?")

INVALID_EQUIPMENT = {"", "[blank]", "blank", "n/a", "na", "none", "null", "idk", "?"}

EQUIPMENT_CATEGORY_RULES: List[Tuple[str, List[str]]] = [
    ("bathroom/hygiene hacks", [r"\bpee\b", r"urinal", r"bidet", r"toilet paper", r"\btp\b", r"wash basin", r"sponge bath", r"rosewater"]),
    ("food/cooking", [r"watermelon", r"\bcooker\b", r"\bcook\b", r"deep fryer", r"fryer"]),
    ("tools/repair", [r"rebar", r"stake", r"impact driver", r"\bdriver\b", r"\bsaw\b", r"chain lube", r"nail clippers", r"goggles"]),
    ("power/tech", [r"solar", r"generator", r"starlink", r"battery"]),
    ("art/play/music", [r"accordion", r"flow", r"lamp", r"dance", r"watercolou?r", r"paint", r"wizard", r"crystal", r"orb"]),
    ("comfort/warmth", [r"onesie", r"blanket", r"hoodie", r"chair", r"shoes", r"cot"]),
    ("substances/medicine", [r"mushroom", r"psychedelic", r"tequila", r"pepto", r"insulin", r"\bmed\b"]),
]

Q8_THEME_RULES: List[Tuple[str, List[str]]] = [
    ("material support", [r"meal", r"food", r"water", r"shade", r"supplies", r"generator", r"power", r"camp", r"infrastructure"]),
    ("emotional support", [r"emotional", r"moral", r"support", r"kindness", r"friend", r"family", r"connection", r"community"]),
    ("knowledge/teaching", [r"teach", r"learn", r"tips", r"advice", r"help me", r"show", r"guide", r"how things work"]),
    ("labor/coordination", [r"setup", r"breakdown", r"work", r"hands", r"participation", r"roles", r"checkins", r"check-ins"]),
    ("self-reliance", [r"self-reliance", r"solo", r"on my own", r"i dont ask", r"i don't ask", r"pride myself"]),
]

def normalize_equipment(text: str) -> str:
    lowered = text.lower().strip()
    lowered = re.sub(r"[\"'`]+", "", lowered)
    lowered = re.sub(r"\s+", " ", lowered)
    lowered = re.sub(r"[^a-z0-9\s/&+-]", "", lowered)
    return lowered.strip()

def is_invalid_equipment(text: str) -> bool:
    normalized = normalize_equipment(text)
    if normalized in INVALID_EQUIPMENT:
        return True
    if not normalized or normalized.isdigit():
        return True
    if len(normalized) <= 2:
        return True
    return normalized in {"yes", "id"}

def categorize_equipment(text: str) -> str:
    normalized = normalize_equipment(text)
    for label, patterns in EQUIPMENT_CATEGORY_RULES:
        for pattern in patterns:
            if re.search(pattern, normalized):
                return label
    return "other"

def get_surprising_equipment(rows: Iterable[Dict[str, str]]) -> List[str]:
    items = []
    for row in rows:
        text = (row.get("Q6") or "").strip()
        if not text or is_invalid_equipment(text):
            continue
        items.append(text)
    return items

def equipment_stats(items: Iterable[str]) -> Dict[str, object]:
    normalized = [normalize_equipment(item) for item in items]
    counts = Counter(normalized)
    total = len(normalized)
    unique_once = sum(1 for count in counts.values() if count == 1)
    top_share = (counts.most_common(1)[0][1] / total) if total else 0
    categories = Counter()
    examples = {}
    for item in items:
        category = categorize_equipment(item)
        categories[category] += 1
        if category not in examples:
            examples[category] = item
    return {
        "total": total,
        "unique_rate": (unique_once / total) if total else 0,
        "top_share": top_share,
        "top_exact": counts.most_common(8),
        "categories": categories,
        "examples": examples,
    }

def md_escape(text: str) -> str:
    return text.replace("|", "/")

def get_equipment_items(rows: Iterable[Dict[str, str]], field: str) -> List[str]:
    items = []
    for row in rows:
        text = (row.get(field) or "").strip()
        if not text or is_invalid_equipment(text):
            continue
        items.append(text)
    return items

def parse_survival_days(text: str) -> float | None:
    lowered = text.lower()
    numbers = [float(n) for n in re.findall(r"\d+(?:\.\d+)?", lowered)]
    if not numbers:
        return None
    if "week" in lowered:
        value = sum(numbers) / len(numbers)
        return value * 7
    if "month" in lowered:
        value = sum(numbers) / len(numbers)
        return value * 30
    return sum(numbers) / len(numbers)

def percentile(values: List[float], pct: float) -> float | None:
    if not values:
        return None
    values = sorted(values)
    k = (len(values) - 1) * pct
    f = int(k)
    c = min(f + 1, len(values) - 1)
    if f == c:
        return values[f]
    return values[f] + (values[c] - values[f]) * (k - f)

def analyze_q7(rows: Iterable[Dict[str, str]]) -> Dict[str, float]:
    values = []
    for row in rows:
        raw = (row.get("Q7") or "").strip()
        if not raw:
            continue
        parsed = parse_survival_days(raw)
        if parsed is None:
            continue
        if parsed > 90:
            continue
        values.append(parsed)
    if not values:
        return {}
    return {
        "count": len(values),
        "mean": statistics.mean(values),
        "median": statistics.median(values),
        "min": min(values),
        "max": max(values),
        "p10": percentile(values, 0.1),
        "p90": percentile(values, 0.9),
    }

def analyze_q8_themes(rows: Iterable[Dict[str, str]]) -> Counter:
    theme_counts = Counter()
    for row in rows:
        text = (row.get("Q8") or "").strip().lower()
        if not text:
            continue
        matched = False
        for theme, patterns in Q8_THEME_RULES:
            if any(re.search(pattern, text) for pattern in patterns):
                theme_counts[theme] += 1
                matched = True
        if not matched:
            theme_counts["other/unclear"] += 1
    return theme_counts

async def run_analysis():
    print("Loading Survival and Transformation Data...")
    
    # 1. Establish Hardship Baseline (from Survival question sets)
    # Question set J (2024) is Survival
    survival_data = utils.load_data(2024, "Survival")
    survival_data_2025 = utils.load_data(2025, "Survival")
    
    # Analyze general hardship prevalence by Age
    age_baselines = {"Under 30": [], "30-39": [], "40-49": [], "50+": []}
    for row in survival_data:
        text = row.get("Q5", "") + " " + row.get("Q6", "")
        if len(row.get("Q5", "")) > 10:
            age = utils.get_age_bucket(row.get("Norm_Age"))
            if age in age_baselines:
                age_baselines[age].append(text)
    
    # LLM Analysis
    SAMPLE_SIZE = None # Set to an integer (e.g., 200) for testing, or None for full dataset

    baseline_stats = {}
    baseline_prompt = "Identify if this person mentions physical hardship (mud, heat, dust). Intensity: None, Low, Medium, High.\nText: \"{{TEXT}}\""
    
    print("Analyzing Baseline Hardship by Age...")
    for age, texts in age_baselines.items():
        if not texts:
            baseline_stats[age] = 0
            continue
        # Limit sample for baseline to save tokens/time
        sample = texts[:SAMPLE_SIZE] if SAMPLE_SIZE else texts
        res = await utils.batch_process_with_llm(sample, baseline_prompt, response_schema=SurvivalAnalysis)
        valid = [r for r in res if "error" not in r]
        pct = sum([1 for r in valid if r.get("mentions_hardship")]) / len(valid) if valid else 0
        baseline_stats[age] = pct

    # Overall Baseline (for original report section)
    all_survival_texts = [t for sublist in age_baselines.values() for t in sublist]
    # We already have age-specific stats, can weigh them or just use the aggregate logic if we want total. 
    # Let's keep the logic consistent with the previous version for the main section, or just aggregate.
    # To save re-running, let's just use the age stats to infer total if needed, but the original code re-ran a batch.
    # We'll just skip the redundant total run and use the aggregate of the age runs for the total stats? 
    # Or just keep the age analysis additive.
    
    # 2. Analyze Transformation narratives for the "Link"
    trans_data = utils.load_data(2024, "Transformation") + utils.load_data(2025, "Transformation")
    test_subjects = [] # List of (age, narrative)
    
    for row in trans_data:
        narrative = " ".join([row.get(f"Q{i}", "") for i in range(5, 10)])
        if len(narrative.strip()) > 30:
            age = utils.get_age_bucket(row.get("Norm_Age"))
            test_subjects.append((age, narrative))

    print(f"Total transformation narratives: {len(test_subjects)}")
    prompt = "Analyze this Burning Man transformation narrative. Determine if physical hardship played a role.\nNarrative: \"{{TEXT}}\""
    
    # We need to process them, then bucket the results by age
    if SAMPLE_SIZE:
        test_subjects = test_subjects[:SAMPLE_SIZE]
        
    narratives_only = [x[1] for x in test_subjects]
    results = await utils.batch_process_with_llm(narratives_only, prompt, response_schema=SurvivalAnalysis)
    
    # Tally Results by Age
    age_link_stats = {a: {"Hardship": 0, "Linked": 0, "Total": 0} for a in age_baselines.keys()}
    
    # Tally Results (Overall)
    stats = Counter()
    valid_results = 0
    
    for i, res in enumerate(results):
        if isinstance(res, dict) and "error" in res: continue
        valid_results += 1
        
        age_group = test_subjects[i][0]
        
        # Overall Stats
        if res.get("mentions_hardship"): stats["Hardship"] += 1
        if res.get("describes_breakthrough"): stats["Breakthrough"] += 1
        if res.get("hardship_was_catalyst"): stats["Linked"] += 1
        level = res.get("hardship_level", "None")
        stats[f"Level_{level}"] += 1
        
        # Age Stats
        if age_group in age_link_stats:
            age_link_stats[age_group]["Total"] += 1
            if res.get("mentions_hardship"): age_link_stats[age_group]["Hardship"] += 1
            if res.get("hardship_was_catalyst"): age_link_stats[age_group]["Linked"] += 1

    # Dynamic Conclusion Logic
    total = valid_results
    if total == 0:
        conclusion = ["No valid narratives found."]
        baseline_hardship_pct = 0 # Fallback
    else:
        linked_pct = stats['Linked'] / total
        hardship_mention_pct = stats['Hardship'] / total
        # Calculate weighted average for total baseline or just take mean of age baselines
        baseline_hardship_pct = sum(baseline_stats.values()) / 4 # Rough approx
        
        conclusion = []
        conclusion.append(f"**The Ordeal Gap:** Hardship is prevalent (Baseline ~{baseline_hardship_pct:.1%}), but only {hardship_mention_pct:.1%} of transformation narratives mention it.")
        
        if linked_pct > 0.15:
            conclusion.append(f"**Direct Link:** For {linked_pct:.1%} of participants, the 'Ordeal' is the explicit engine of their transformation.")
        elif linked_pct > 0.05:
            conclusion.append(f"**Normalization:** Hardship is common but rarely cited as the primary driver of epiphany, suggesting it is normalized as 'background noise' on the playa.")
        else:
            conclusion.append("**Hypothesis Weakened:** The 'Ordeal Hypothesis' is largely unsupported by the data; participants describe transformation through social and creative lenses, not physical survival.")

    survival_rows = survival_data + survival_data_2025
    q5_items = get_equipment_items(survival_rows, "Q5")
    q6_items = get_surprising_equipment(survival_rows)
    q5_stats = equipment_stats(q5_items)
    q6_stats = equipment_stats(q6_items)
    q6_2024 = get_surprising_equipment(survival_data)
    q6_2025 = get_surprising_equipment(survival_data_2025)
    stats_2024 = equipment_stats(q6_2024)
    stats_2025 = equipment_stats(q6_2025)
    stats_combined = equipment_stats(q6_items)

    q5_unique = set(normalize_equipment(item) for item in q5_items)
    q6_unique = set(normalize_equipment(item) for item in q6_items)
    overlap_unique = q5_unique & q6_unique
    overlap_share = (len(overlap_unique) / len(q6_unique)) if q6_unique else 0

    q7_summary = analyze_q7(survival_rows)
    q8_themes = analyze_q8_themes(survival_rows)
    q8_total_mentions = sum(q8_themes.values()) or 0

    cohort_rows = {}
    for row in survival_rows:
        status = (row.get("Burn_Status") or "Unknown").strip()
        cohort_rows.setdefault(status, []).append(row)

    cohort_q7 = {}
    cohort_q6_uniqueness = {}
    cohort_q8_top = {}
    for status, rows in cohort_rows.items():
        q7_stats = analyze_q7(rows)
        cohort_q7[status] = q7_stats
        q6_items_cohort = get_surprising_equipment(rows)
        q6_stats_cohort = equipment_stats(q6_items_cohort)
        cohort_q6_uniqueness[status] = q6_stats_cohort["unique_rate"]
        q8_counts = analyze_q8_themes(rows)
        if q8_counts:
            top_theme = q8_counts.most_common(1)[0][0]
        else:
            top_theme = "n/a"
        cohort_q8_top[status] = top_theme

    # Generate Report
    sample_desc = f"{SAMPLE_SIZE}" if SAMPLE_SIZE else "Full Dataset"
    report = ["# Module 2: The 'Ordeal' as Catalyst (Survival vs. Epiphany)\n"]
    report.append(f"**Methodology:** Comparative analysis of survival responses (Baseline) vs {total} transformation narratives, segmented by **Age**. Sample size: {sample_desc}.\n")
    
    report.append("### Findings")
    report.append(f"- **Transformation Narratives Mentioning Hardship:** {hardship_mention_pct:.1%}")
    report.append(f"- **Hardship as Explicit Catalyst:** {linked_pct:.1%}")
    
    report.append("\n### Hardship Intensity (Transformation Set)")
    report.append("| Level | Count |")
    report.append("| :--- | :--- |")
    for level in ["High", "Medium", "Low", "None"]:
        report.append(f"| {level} | {stats[f'Level_{level}']} |")
        
    report.append("\n### Age Analysis: Who Suffers, Who Grows?")
    report.append("| Age Group | Baseline Hardship % | Transf. Hardship % | Catalyst Rate (Linked) |")
    report.append("| :--- | :--- | :--- | :--- |")
    
    for age in ["Under 30", "30-39", "40-49", "50+"]:
        base = baseline_stats.get(age, 0)
        group_data = age_link_stats.get(age, {"Total": 0})
        tot = group_data["Total"]
        
        if tot > 0:
            trans_hard = group_data["Hardship"] / tot
            cat_rate = group_data["Linked"] / tot
        else:
            trans_hard = 0
            cat_rate = 0
            
        report.append(f"| {age} | {base:.1%} | {trans_hard:.1%} | {cat_rate:.1%} |")

    report.append("\n## Equipment Contrast (Q5 vs Q6)")
    report.append(
        f"- **Q5 (most important) items:** n={q5_stats['total']} | **Q6 (surprising) items:** n={q6_stats['total']}."
    )
    report.append(
        f"- **Exact overlap (unique items):** {len(overlap_unique)} of {len(q6_unique)} Q6 items also appear in Q5 ({overlap_share:.1%})."
    )
    report.append("\n### Category Mix: Q5 vs Q6")
    report.append("| Category | Q5 Share | Q6 Share |")
    report.append("| :--- | :--- | :--- |")
    categories = set(q5_stats["categories"].keys()) | set(q6_stats["categories"].keys())
    for category in sorted(categories):
        q5_share = (q5_stats["categories"][category] / q5_stats["total"]) if q5_stats["total"] else 0
        q6_share = (q6_stats["categories"][category] / q6_stats["total"]) if q6_stats["total"] else 0
        report.append(f"| {category} | {q5_share:.1%} | {q6_share:.1%} |")

    report.append("\n## Survival Days (Q7)")
    if q7_summary:
        report.append(
            f"- **Count:** {q7_summary['count']} | **Median:** {q7_summary['median']:.1f} | **Mean:** {q7_summary['mean']:.1f} | **P10/P90:** {q7_summary['p10']:.1f}/{q7_summary['p90']:.1f} | **Range:** {q7_summary['min']:.1f}-{q7_summary['max']:.1f}"
        )
    else:
        report.append("- No parseable Q7 responses found.")

    report.append("\n### Survival Days by Burn Status")
    report.append("| Burn Status | Count | Median Days | Mean Days |")
    report.append("| :--- | :--- | :--- | :--- |")
    for status in sorted(cohort_q7.keys()):
        stats = cohort_q7[status]
        if not stats:
            report.append(f"| {status} | 0 | n/a | n/a |")
            continue
        report.append(
            f"| {status} | {stats['count']} | {stats['median']:.1f} | {stats['mean']:.1f} |"
        )

    report.append("\n## Community Reliance Themes (Q8)")
    report.append("- Multi-label keyword tagging; counts can exceed response count.")
    report.append("| Theme | Count | Share of Mentions |")
    report.append("| :--- | :--- | :--- |")
    for theme, count in q8_themes.most_common():
        share = (count / q8_total_mentions) if q8_total_mentions else 0
        report.append(f"| {theme} | {count} | {share:.1%} |")

    report.append("\n### Cohort Highlights")
    report.append("| Burn Status | Q6 Uniqueness | Top Q8 Theme |")
    report.append("| :--- | :--- | :--- |")
    for status in sorted(cohort_q6_uniqueness.keys()):
        report.append(
            f"| {status} | {cohort_q6_uniqueness[status]:.1%} | {cohort_q8_top[status]} |"
        )

    report.append("\n## Surprising/Unconventional Gear (Q6)")
    report.append(
        f"**Sample sizes (non-blank Q6):** 2024 n={stats_2024['total']}, 2025 n={stats_2025['total']}, combined n={stats_combined['total']}."
    )
    report.append(
        f"- **Uniqueness rate:** 2024 {stats_2024['unique_rate']:.1%}, 2025 {stats_2025['unique_rate']:.1%}, combined {stats_combined['unique_rate']:.1%}."
    )
    report.append(
        f"- **Most common item share:** 2024 {stats_2024['top_share']:.1%}, 2025 {stats_2025['top_share']:.1%}, combined {stats_combined['top_share']:.1%}."
    )

    report.append("\n### Most Common Exact Items (Combined)")
    report.append("| Item | Count |")
    report.append("| :--- | :--- |")
    for item, count in stats_combined["top_exact"]:
        report.append(f"| {md_escape(item)} | {count} |")

    report.append("\n### Category Mix (Combined)")
    report.append("| Category | Count | Share | Example |")
    report.append("| :--- | :--- | :--- | :--- |")
    for category, count in stats_combined["categories"].most_common():
        share = count / stats_combined["total"] if stats_combined["total"] else 0
        example = md_escape(stats_combined["examples"].get(category, ""))
        report.append(f"| {category} | {count} | {share:.1%} | {example} |")

    report.append("\n## Conclusion")
    report.append("> " + " ".join(conclusion))

    utils.save_report("module_2_survival.md", "\n".join(report))

if __name__ == "__main__":
    asyncio.run(run_analysis())
