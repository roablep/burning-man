import sys
import os
import re
import csv
import statistics
from collections import Counter

# Add parent directory to path to find analysis_utils
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import analysis_utils as utils

TOP_TERMS = 7
MIN_GROUP_RESPONSES_FOR_TERMS = 5

AGE_BUCKETS = [
    (0, 24, "Under 25"),
    (25, 34, "25-34"),
    (35, 44, "35-44"),
    (45, 54, "45-54"),
    (55, 64, "55-64"),
    (65, 200, "65+"),
]

BURN_COUNT_BUCKETS = [
    (0, 1, "1"),
    (2, 3, "2-3"),
    (4, 6, "4-6"),
    (7, 9, "7-9"),
    (10, 14, "10-14"),
    (15, 19, "15-19"),
    (20, 200, "20+"),
]

STOPWORDS = {
    "the", "and", "for", "with", "that", "this", "was", "were", "are",
    "but", "not", "you", "your", "our", "have", "had", "from", "they",
    "their", "them", "him", "her", "she", "his", "its", "it's", "into",
    "out", "about", "because", "what", "when", "where", "why", "how",
    "been", "being", "who", "which", "than", "then", "there", "here",
    "just", "like", "more", "less", "can", "could", "would", "should",
    "did", "does", "doing", "i", "me", "my", "we", "us", "in", "on",
    "at", "of", "to", "a", "an", "or", "as", "if", "so", "no", "yes",
    "also", "very", "much", "make", "made", "feel", "feels", "felt",
    "really", "get", "got", "burning", "man", "playa", "brc",
}

THEME_CONFIG = {
    2024: {
        "Transformation": {
            "filters": ["Transformation"],
            "questions": {
                "Q5": "Did Burning Man change you? When? How?",
                "Q9": "Which factor(s) contributed to the change you experienced?",
            },
        },
        "Symbolism": {
            "filters": ["Symbolism"],
            "questions": {
                "Q6": "What does the symbol of the Burning Man mean to you?",
                "Q7": "What does the Temple mean to you?",
            },
        },
        "Emotions": {
            "filters": ["Emotions"],
            "questions": {
                "Q5": "Which emotions do you experience in BRC?",
                "Q6": "What made you laugh today?",
                "Q7": "What made you cry this week?",
                "Q8": "What made you feel a sense of wonder?",
            },
        },
        "Boundaries of Humanity": {
            "filters": ["Boundaries of Humanity"],
            "questions": {
                "Q5": "What characteristics distinguish humans from other animals?",
                "Q6": "What distinguishes humans from AI?",
                "Q7": "Could a machine have the same moral worth as a human?",
                "Q8": "What about being human is unique?",
            },
        },
        "Dancing & Singing": {
            "filters": ["Singing & Dancing"],
            "questions": {
                "Q5": "Do you often dance and/or sing at Burning Man?",
                "Q6": "Do you dance and/or sing in the default world?",
                "Q7": "How does dancing and/or singing make you feel?",
                "Q8": "Does it feel differently alone vs with others?",
            },
        },
        "Costumes": {
            "filters": ["Costumes"],
            "questions": {
                "Q5": "Do you wear costumes at Burning Man? Why or why not?",
                "Q6": "How do you decide what to wear?",
                "Q7": "Does what you wear affect your interactions?",
            },
        },
        "Drinking & Smoking": {
            "filters": ["Drinking & Smoking"],
            "questions": {
                "Q5": "Do you drink and/or smoke at Burning Man?",
                "Q6": "If yes, what and how often?",
                "Q7": "What does drinking and smoking mean to you?",
                "Q8": "If cannabis were fully legal, what would change?",
                "Q9": "How does cannabis affect your use of other substances?",
            },
        },
        "Experiences": {
            "filters": ["Experiences"],
            "questions": {
                "Q5": "What has caused negative experiences at Burning Man?",
                "Q6": "What has caused positive experiences at Burning Man?",
            },
        },
        "Relationships": {
            "filters": ["Relationships"],
            "questions": {
                "Q5": "Have you met someone and fallen in love in BRC?",
                "Q6": "Committed relationship in BRC? What do you recommend?",
                "Q7": "How are relationships different on playa vs default world?",
            },
        },
        "Survival": {
            "filters": ["Survival"],
            "questions": {
                "Q5": "Single most important piece of equipment?",
                "Q6": "Most surprising or unconventional equipment?",
                "Q7": "How many days could you survive with what you brought?",
                "Q8": "How do you rely on community to survive?",
            },
            "numeric_questions": {"Q7"},
        },
        "Diversity & Inclusion": {
            "filters": ["Diversity & Inclusion"],
            "questions": {
                "Q5": "Does appearance/cultural identity impact interactions (default world)?",
                "Q6": "Modified appearance/cultural identifiers in default world?",
                "Q7": "Appearance/cultural identity impact interactions on playa?",
                "Q8": "Modified appearance/cultural identifiers on playa?",
            },
        },
        "Beyond Black Rock City": {
            "filters": ["Beyond Black Rock City"],
            "questions": {
                "Q5": "Has Burning Man influenced parts of your life outside BRC?",
                "Q6": "Have you incorporated any ten principles outside BRC?",
                "Q7": "Has Burning Man influenced actions/thoughts/behavior outside?",
            },
        },
        "Sustainability": {
            "filters": ["Sustainability"],
            "questions": {
                "Q5": "How did sustainability concerns factor into your choices?",
                "Q6": "Sustainable practices seen at Burning Man?",
                "Q7": "Interested in making next burn more sustainable?",
                "Q8": "Should BRC encourage sustainable behaviors?",
                "Q9": "Would sustainability focus improve perception of Burning Man?",
                "Q10": "Could sustainable practices help the default world?",
            },
        },
    },
    2025: {
        "Transformation": {
            "filters": ["Transformation"],
            "questions": {
                "Q5": "Did Burning Man change you? When? How?",
                "Q9": "Which factor(s) contributed to the change you experienced?",
            },
        },
        "Survival": {
            "filters": ["Survival"],
            "questions": {
                "Q5": "Single most important piece of equipment?",
                "Q6": "Most surprising or unconventional equipment?",
                "Q7": "How many days could you survive with what you brought?",
                "Q8": "How do you rely on community to survive?",
            },
            "numeric_questions": {"Q7"},
        },
        "Emotions & Experiences": {
            "filters": ["Emotions & Experiences"],
            "questions": {
                "Q5": "What has caused negative experiences at Burning Man?",
                "Q6": "What has caused positive experiences at Burning Man?",
                "Q7": "Which emotions do you experience in BRC?",
                "Q8": "What made you laugh today?",
                "Q9": "What made you cry this week?",
                "Q10": "What made you feel a sense of wonder?",
            },
        },
        "Boundaries of Humanity": {
            "filters": ["Boundaries of Humanity"],
            "questions": {
                "Q5": "What characteristics distinguish humans from other animals?",
                "Q6": "What distinguishes humans from AI?",
                "Q7": "Could a machine have the same moral worth as a human?",
                "Q8": "What about being human is unique?",
            },
        },
        "Relationships": {
            "filters": ["Relationships"],
            "questions": {
                "Q5": "Have you met someone and fallen in love in BRC?",
                "Q6": "Committed relationship in BRC? What do you recommend?",
                "Q7": "How are relationships different on playa vs default world?",
            },
        },
        "Diversity & Inclusion": {
            "filters": ["Diversity & Inclusion"],
            "questions": {
                "Q5": "Does appearance/cultural identity impact interactions (default world)?",
                "Q6": "Modified appearance/cultural identifiers in default world?",
                "Q7": "Appearance/cultural identity impact interactions on playa?",
                "Q8": "Modified appearance/cultural identifiers on playa?",
            },
        },
    },
}


def bucket_age(value):
    try:
        age = int(value)
    except (TypeError, ValueError):
        return "Unknown"
    for low, high, label in AGE_BUCKETS:
        if low <= age <= high:
            return label
    return "Unknown"


def bucket_burn_count(value):
    try:
        count = int(value)
    except (TypeError, ValueError):
        return "Unknown"
    for low, high, label in BURN_COUNT_BUCKETS:
        if low <= count <= high:
            return label
    return "Unknown"


def tokenize(text):
    words = re.split(r"[^A-Za-z']+", text.lower())
    cleaned = []
    for w in words:
        if not w or len(w) < 3:
            continue
        if w in STOPWORDS:
            continue
        cleaned.append(w)
    return cleaned


def top_terms(responses, top_n=TOP_TERMS):
    counter = Counter()
    for resp in responses:
        counter.update(tokenize(resp))
    return counter.most_common(top_n)


def parse_numeric_days(text):
    matches = re.findall(r"\b(\d{1,3})\b", text)
    if not matches:
        return None
    try:
        value = int(matches[0])
    except ValueError:
        return None
    if 0 <= value <= 60:
        return value
    return None


def group_value(row, dimension):
    if dimension == "Age Bucket":
        return bucket_age(row.get("Norm_Age"))
    if dimension == "Burn Count Bucket":
        return bucket_burn_count(row.get("Norm_Burn_Count"))
    if dimension == "Burn Status":
        return row.get("Burn_Status") or "Unknown"
    if dimension == "Gender":
        return row.get("Norm_Gender") or "Unknown"
    if dimension == "Region":
        return row.get("Norm_Region") or "Unknown"
    return "Unknown"


def filter_theme_rows(rows, filters):
    filtered = []
    for row in rows:
        subfolder = (row.get("Subfolder") or "").lower()
        if any(token.lower() in subfolder for token in filters):
            filtered.append(row)
    return filtered


def build_group_tables(rows, question_id, numeric=False):
    dimensions = [
        "Age Bucket",
        "Burn Count Bucket",
        "Burn Status",
        "Gender",
        "Region",
    ]

    output = []

    for dimension in dimensions:
        totals = Counter()
        responses_by_group = {}
        numeric_by_group = {}

        for row in rows:
            group = group_value(row, dimension)
            totals[group] += 1
            response = (row.get(question_id) or "").strip()
            if response:
                responses_by_group.setdefault(group, []).append(response)
                if numeric:
                    value = parse_numeric_days(response)
                    if value is not None:
                        numeric_by_group.setdefault(group, []).append(value)

        output.append(f"##### {dimension}")
        output.append("| Group | Total N | Response N | Response % | Top Terms |")
        output.append("| :--- | ---: | ---: | ---: | :--- |")

        for group, total in totals.most_common():
            responses = responses_by_group.get(group, [])
            response_n = len(responses)
            response_pct = (response_n / total * 100) if total else 0
            if response_n >= MIN_GROUP_RESPONSES_FOR_TERMS:
                top = ", ".join([t for t, _ in top_terms(responses)]) or "-"
            else:
                top = "n<5"
            output.append(
                f"| {group} | {total} | {response_n} | {response_pct:.1f}% | {top} |"
            )

        if numeric:
            output.append("\n**Numeric Summary (parsed days; 0-60)**")
            output.append("| Group | N | Mean | Median | Min | Max |")
            output.append("| :--- | ---: | ---: | ---: | ---: | ---: |")
            for group, total in totals.most_common():
                values = numeric_by_group.get(group, [])
                if values:
                    output.append(
                        f"| {group} | {len(values)} | {statistics.mean(values):.1f} | "
                        f"{statistics.median(values):.1f} | {min(values)} | {max(values)} |"
                    )
                else:
                    output.append(f"| {group} | 0 | - | - | - | - |")

        output.append("")

    return "\n".join(output)


def run_analysis():
    report = ["# Descriptive Statistics by Theme\n"]

    for year in [2024, 2025]:
        year_rows = utils.load_data(year)
        if not year_rows:
            report.append(f"## Year {year}\nNo data found.\n")
            continue

        report.append(f"## Year {year}\n")
        for theme, config in THEME_CONFIG.get(year, {}).items():
            theme_rows = filter_theme_rows(year_rows, config["filters"])
            if not theme_rows:
                report.append(f"### {theme}\nNo responses found.\n")
                continue

            report.append(f"### {theme}\n")
            report.append(f"**Total Responses:** {len(theme_rows)}\n")

            numeric_questions = config.get("numeric_questions", set())
            for question_id, question_text in config["questions"].items():
                responses = [
                    (row.get(question_id) or "").strip()
                    for row in theme_rows
                    if (row.get(question_id) or "").strip()
                ]
                response_n = len(responses)
                overall_top = ", ".join([t for t, _ in top_terms(responses)]) if responses else "-"

                report.append(f"#### {question_id}: {question_text}")
                report.append(f"- **Response N:** {response_n}\n- **Top Terms (Overall):** {overall_top}\n")

                report.append(build_group_tables(
                    theme_rows,
                    question_id,
                    numeric=question_id in numeric_questions,
                ))

    utils.save_report("descriptive_stats_by_theme.md", "\n".join(report))
    print("Report generated: descriptive_stats_by_theme.md")


if __name__ == "__main__":
    run_analysis()
