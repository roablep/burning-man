#!/usr/bin/env python3
"""Cohort-level cross-theme analysis without respondent linkage.

Builds theme clusters per question set using simple TF-IDF keyword theming,
then computes cohort-level theme prevalence and cross-set correlations.
"""

from __future__ import annotations

import csv
import math
import os
import re
from collections import Counter, defaultdict

os.environ.setdefault("LOKY_MAX_CPU_COUNT", "1")

import numpy as np
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer

DATA_DIR = "src/census/data"
REPORT_DIR = "reports/cross_theme"

MIN_SINGLE_N = 15
MIN_TWO_WAY_N = 15
MIN_CORR_COHORTS = 4

STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "but", "by", "for", "from",
    "has", "have", "he", "her", "hers", "him", "his", "i", "if", "in", "is",
    "it", "its", "me", "my", "of", "on", "or", "our", "ours", "she", "so",
    "that", "the", "their", "them", "they", "this", "to", "us", "we", "were",
    "what", "when", "where", "who", "why", "with", "you", "your", "yours",
    "im", "ive", "dont", "didnt", "cant", "couldnt", "wouldnt", "wont",
    "yes", "no", "not", "just", "also", "because", "about", "into", "than",
    "burning", "burn", "man", "temple", "bm", "brc", "playa", "city", "black",
    "rock", "burner", "burners", "people", "person", "thing", "things",
    "stuff", "really", "very", "like", "many", "lot", "lots", "everything",
    "nothing", "someone", "something", "anyone", "everyone", "day", "week",
    "year", "years", "time", "times", "made", "make", "making", "feel",
    "feels", "feeling", "feelings", "blank", "illegible", "unknown",
    "come", "coming", "go", "going", "went", "get", "got", "getting", "take",
    "took", "taking", "give", "gave", "giving", "see", "saw", "seen", "know",
    "knew", "think", "thought", "say", "said", "tell", "told", "want",
    "wanted", "need", "needed", "use", "used", "using", "put", "putting",
    "wear", "wearing", "have", "had", "having", "out", "in",
}

SET_NAMES_2024 = {
    "A": "Transformation",
    "B": "Symbolism",
    "C": "Emotions",
    "D": "Boundaries of Humanity",
    "E": "Singing & Dancing",
    "F": "Costumes",
    "G": "Drinking & Smoking",
    "H": "Experiences",
    "I": "Relationships",
    "J": "Survival",
    "K": "Diversity & Inclusion",
    "L": "Beyond Black Rock City",
    "M": "Sustainability",
}

SET_NAMES_2025 = {
    "A": "Transformation",
    "B": "Survival",
    "C": "Emotions & Experiences",
    "D": "Boundaries of Humanity",
    "E": "Relationships",
    "F": "Diversity & Inclusion",
}

THEME_TARGETS_2024 = {
    "A": 10,
    "B": 8,
    "C": 10,
    "D": 10,
    "E": 8,
    "F": 8,
    "G": 8,
    "H": 8,
    "I": 10,
    "J": 8,
    "K": 10,
    "L": 8,
    "M": 8,
}

THEME_TARGETS_2025 = {
    "A": 10,
    "B": 8,
    "C": 10,
    "D": 10,
    "E": 10,
    "F": 10,
}

TOKEN_RE = re.compile(r"[a-zA-Z]{3,}")
SUBFOLDER_RE = re.compile(r"([A-M])\d", re.IGNORECASE)


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def normalize_token(token: str) -> str:
    token = token.lower()
    if token.endswith("ing") and len(token) > 5:
        token = token[:-3]
    elif token.endswith("ed") and len(token) > 4:
        token = token[:-2]
    elif token.endswith("s") and len(token) > 4:
        token = token[:-1]
    return token


def tokenize(text: str) -> list[str]:
    tokens = []
    for match in TOKEN_RE.findall(text.lower()):
        if match in STOPWORDS:
            continue
        token = normalize_token(match)
        if token in STOPWORDS:
            continue
        tokens.append(token)
    return tokens


def age_band(age_value: str) -> str | None:
    if not age_value:
        return None
    try:
        age = int(float(age_value))
    except ValueError:
        return None
    if age < 30:
        return "<30"
    if age < 40:
        return "30s"
    if age < 50:
        return "40s"
    if age < 60:
        return "50s"
    return "60+"


def extract_set_key(subfolder: str) -> str | None:
    if not subfolder:
        return None
    match = SUBFOLDER_RE.search(subfolder.strip())
    if not match:
        return None
    return match.group(1).upper()


def build_records(year: int) -> list[dict]:
    path = os.path.join(DATA_DIR, f"{year}-field-note-transcriptions-normalized.csv")
    records = []
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            set_key = extract_set_key(row.get("Subfolder", ""))
            if not set_key:
                continue
            # Concatenate open-ended response columns (Q5+)
            responses = []
            for key, value in row.items():
                if key.startswith("Q") and key[1:].isdigit() and int(key[1:]) >= 5:
                    text = (value or "").strip()
                    if text:
                        responses.append(text)
            if not responses:
                continue
            text = " ".join(responses)
            record = {
                "year": year,
                "set_key": set_key,
                "text": text,
                "tokens": tokenize(text),
                "gender": (row.get("Norm_Gender") or "").strip() or None,
                "region": (row.get("Norm_Region") or "").strip() or None,
                "burn_status": (row.get("Burn_Status") or "").strip() or None,
                "age_band": age_band((row.get("Norm_Age") or "").strip()),
            }
            records.append(record)
    return records


def cluster_themes(records: list[dict], target_theme_count: int) -> dict:
    texts = [rec["text"] for rec in records]
    doc_count = len(texts)
    if doc_count < 2:
        for rec in records:
            rec["theme_id"] = "t0"
            rec["theme_label"] = "misc"
        return {"labels": {"t0": "misc"}, "theme_counts": Counter({"t0": doc_count})}

    cluster_count = min(target_theme_count, max(2, int(math.sqrt(doc_count))))
    vectorizer = TfidfVectorizer(
        stop_words=sorted(STOPWORDS),
        token_pattern=r"[a-zA-Z]{3,}",
        min_df=2,
        max_df=0.6,
    )

    try:
        matrix = vectorizer.fit_transform(texts)
    except ValueError:
        vectorizer = TfidfVectorizer(
            stop_words=sorted(STOPWORDS),
            token_pattern=r"[a-zA-Z]{3,}",
            min_df=1,
            max_df=0.8,
        )
        matrix = vectorizer.fit_transform(texts)

    if matrix.shape[1] == 0:
        for rec in records:
            rec["theme_id"] = "t0"
            rec["theme_label"] = "misc"
        return {"labels": {"t0": "misc"}, "theme_counts": Counter({"t0": doc_count})}

    kmeans = KMeans(n_clusters=cluster_count, n_init=10, random_state=42)
    labels = kmeans.fit_predict(matrix)

    terms = vectorizer.get_feature_names_out()
    label_map: dict[str, str] = {}
    for idx in range(cluster_count):
        centroid = kmeans.cluster_centers_[idx]
        top_indices = np.argsort(centroid)[-5:][::-1]
        top_terms = [terms[i] for i in top_indices if centroid[i] > 0]
        label_map[f"t{idx}"] = " / ".join(top_terms[:3]) or "misc"

    for rec, label in zip(records, labels, strict=False):
        theme_id = f"t{label}"
        rec["theme_id"] = theme_id
        rec["theme_label"] = label_map.get(theme_id, "misc")

    return {
        "labels": label_map,
        "theme_counts": Counter(rec["theme_id"] for rec in records),
    }


def build_theme_catalog(records: list[dict], set_name: str) -> list[dict]:
    by_theme = defaultdict(list)
    for rec in records:
        by_theme[rec["theme_id"]].append(rec)

    catalog = []
    total = len(records)
    for theme, group in sorted(by_theme.items(), key=lambda x: (-len(x[1]), x[0])):
        token_counts = Counter()
        for rec in group:
            token_counts.update(rec["tokens"])
        key_terms = [t for t, _ in token_counts.most_common(5)]
        example = next((rec["text"] for rec in group if rec["text"]), "")
        catalog.append({
            "set": set_name,
            "theme_id": theme,
            "theme_label": group[0].get("theme_label", "misc"),
            "count": len(group),
            "pct": round((len(group) / total) * 100.0, 2) if total else 0.0,
            "key_terms": ", ".join(key_terms),
            "example": example[:240],
        })
    return catalog


def cohort_prevalence(records: list[dict], cohort_key: str, min_n: int) -> list[dict]:
    cohort_theme_counts = defaultdict(Counter)
    cohort_totals = Counter()
    for rec in records:
        cohort_value = rec.get(cohort_key)
        if not cohort_value:
            continue
        cohort_totals[cohort_value] += 1
        cohort_theme_counts[cohort_value][rec["theme_id"]] += 1

    output = []
    for cohort_value, total in cohort_totals.items():
        if total < min_n:
            continue
        theme_counts = cohort_theme_counts[cohort_value]
        for theme, count in theme_counts.items():
            output.append({
                "cohort_type": cohort_key,
                "cohort": cohort_value,
                "theme_id": theme,
                "theme_label": "",
                "count": count,
                "cohort_n": total,
                "prevalence": round(count / total, 6),
            })
    return output


def pearson(values_a: list[float], values_b: list[float]) -> float | None:
    if len(values_a) < 3 or len(values_a) != len(values_b):
        return None
    mean_a = sum(values_a) / len(values_a)
    mean_b = sum(values_b) / len(values_b)
    num = sum((a - mean_a) * (b - mean_b) for a, b in zip(values_a, values_b))
    den_a = math.sqrt(sum((a - mean_a) ** 2 for a in values_a))
    den_b = math.sqrt(sum((b - mean_b) ** 2 for b in values_b))
    if den_a == 0 or den_b == 0:
        return None
    return num / (den_a * den_b)


def build_correlation_rows(prevalence_rows: list[dict], set_pairs: list[tuple], year: int) -> list[dict]:
    # Build lookup: (set, cohort_type, cohort) -> theme -> prevalence
    lookup = defaultdict(lambda: defaultdict(dict))
    for row in prevalence_rows:
        lookup[(row["set"], row["cohort_type"], row["cohort"])][row["theme_id"]] = row["prevalence"]

    # Gather cohorts per set/cohort_type
    cohorts_by_set_type = defaultdict(set)
    for row in prevalence_rows:
        cohorts_by_set_type[(row["set"], row["cohort_type"])].add(row["cohort"])

    correlations = []
    for set_a, set_b in set_pairs:
        for cohort_type in {"burn_status", "gender", "region", "age_band"}:
            cohorts = sorted(
                cohorts_by_set_type.get((set_a, cohort_type), set())
                & cohorts_by_set_type.get((set_b, cohort_type), set())
            )
            if len(cohorts) < MIN_CORR_COHORTS:
                continue

            # Collect themes per set
            themes_a = set()
            themes_b = set()
            for cohort in cohorts:
                themes_a.update(lookup[(set_a, cohort_type, cohort)].keys())
                themes_b.update(lookup[(set_b, cohort_type, cohort)].keys())

            for theme_a in themes_a:
                values_a = [lookup[(set_a, cohort_type, cohort)].get(theme_a, 0.0) for cohort in cohorts]
                for theme_b in themes_b:
                    values_b = [lookup[(set_b, cohort_type, cohort)].get(theme_b, 0.0) for cohort in cohorts]
                    corr = pearson(values_a, values_b)
                    if corr is None:
                        continue
                    correlations.append({
                        "year": year,
                        "cohort_type": cohort_type,
                        "set_a": set_a,
                        "theme_a_id": theme_a,
                        "set_b": set_b,
                        "theme_b_id": theme_b,
                        "n_cohorts": len(cohorts),
                        "correlation": round(corr, 4),
                    })
    return correlations


def write_csv(path: str, rows: list[dict], fieldnames: list[str]) -> None:
    ensure_dir(os.path.dirname(path))
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    ensure_dir(REPORT_DIR)

    all_catalog_rows = []
    all_prevalence_rows = []
    all_count_rows = []

    for year in (2024, 2025):
        records = build_records(year)
        if not records:
            continue

        set_names = SET_NAMES_2024 if year == 2024 else SET_NAMES_2025
        theme_targets = THEME_TARGETS_2024 if year == 2024 else THEME_TARGETS_2025

        records_by_set = defaultdict(list)
        for rec in records:
            if rec["set_key"] not in set_names:
                continue
            records_by_set[rec["set_key"]].append(rec)

        for set_key, set_records in records_by_set.items():
            target = theme_targets.get(set_key, 8)
            cluster_themes(set_records, target)

            set_label = f"{set_key} - {set_names[set_key]}"
            for rec in set_records:
                rec["set"] = set_label

            catalog = build_theme_catalog(set_records, set_label)
            all_catalog_rows.extend(catalog)

            for cohort_key in ("burn_status", "gender", "region", "age_band"):
                rows = cohort_prevalence(set_records, cohort_key, MIN_SINGLE_N)
                for row in rows:
                    row["year"] = year
                    row["set"] = set_label
                    row["theme_label"] = next(
                        (rec["theme_label"] for rec in set_records if rec["theme_id"] == row["theme_id"]),
                        "misc",
                    )
                all_prevalence_rows.extend(rows)

            # Optional two-way cohorts
            two_way_keys = [
                ("burn_status", "gender"),
                ("burn_status", "region"),
                ("gender", "region"),
            ]
            for key_a, key_b in two_way_keys:
                cohort_counts = Counter()
                theme_counts = defaultdict(Counter)
                for rec in set_records:
                    val_a = rec.get(key_a)
                    val_b = rec.get(key_b)
                    if not val_a or not val_b:
                        continue
                    cohort = f"{val_a} | {val_b}"
                    cohort_counts[cohort] += 1
                    theme_counts[cohort][rec["theme_id"]] += 1
                for cohort, total in cohort_counts.items():
                    if total < MIN_TWO_WAY_N:
                        continue
                    for theme, count in theme_counts[cohort].items():
                        all_prevalence_rows.append({
                            "year": year,
                            "set": set_label,
                            "cohort_type": f"{key_a}x{key_b}",
                            "cohort": cohort,
                            "theme_id": theme,
                            "theme_label": next(
                                (rec["theme_label"] for rec in set_records if rec["theme_id"] == theme),
                                "misc",
                            ),
                            "count": count,
                            "cohort_n": total,
                            "prevalence": round(count / total, 6),
                        })

            for theme, count in Counter(rec["theme_id"] for rec in set_records).items():
                all_count_rows.append({
                    "year": year,
                    "set": set_label,
                    "theme_id": theme,
                    "theme_label": next(
                        (rec["theme_label"] for rec in set_records if rec["theme_id"] == theme),
                        "misc",
                    ),
                    "count": count,
                })

    write_csv(
        os.path.join(REPORT_DIR, "theme_catalog.csv"),
        all_catalog_rows,
        ["set", "theme_id", "theme_label", "count", "pct", "key_terms", "example"],
    )

    write_csv(
        os.path.join(REPORT_DIR, "theme_prevalence.csv"),
        all_prevalence_rows,
        ["year", "set", "cohort_type", "cohort", "theme_id", "theme_label", "count", "cohort_n", "prevalence"],
    )

    write_csv(
        os.path.join(REPORT_DIR, "theme_counts.csv"),
        all_count_rows,
        ["year", "set", "theme_id", "theme_label", "count"],
    )

    # Cross-set correlations
    theme_label_lookup = {
        (row["set"], row["theme_id"]): row["theme_label"] for row in all_catalog_rows
    }
    set_pairs_2024 = [
        ("B - Symbolism", "C - Emotions"),
        ("B - Symbolism", "H - Experiences"),
        ("J - Survival", "A - Transformation"),
        ("J - Survival", "H - Experiences"),
        ("F - Costumes", "K - Diversity & Inclusion"),
        ("F - Costumes", "I - Relationships"),
        ("I - Relationships", "C - Emotions"),
        ("D - Boundaries of Humanity", "A - Transformation"),
        ("D - Boundaries of Humanity", "C - Emotions"),
        ("H - Experiences", "M - Sustainability"),
        ("G - Drinking & Smoking", "C - Emotions"),
        ("L - Beyond Black Rock City", "A - Transformation"),
        ("L - Beyond Black Rock City", "M - Sustainability"),
    ]

    set_pairs_2025 = [
        ("B - Survival", "A - Transformation"),
        ("B - Survival", "C - Emotions & Experiences"),
        ("E - Relationships", "C - Emotions & Experiences"),
        ("F - Diversity & Inclusion", "E - Relationships"),
        ("D - Boundaries of Humanity", "A - Transformation"),
        ("D - Boundaries of Humanity", "C - Emotions & Experiences"),
    ]

    correlations = []
    for year in (2024, 2025):
        rows = [row for row in all_prevalence_rows if row["year"] == year]
        pairs = set_pairs_2024 if year == 2024 else set_pairs_2025
        correlations.extend(build_correlation_rows(rows, pairs, year))

    for row in correlations:
        row["theme_a_label"] = theme_label_lookup.get((row["set_a"], row["theme_a_id"]), "misc")
        row["theme_b_label"] = theme_label_lookup.get((row["set_b"], row["theme_b_id"]), "misc")

    write_csv(
        os.path.join(REPORT_DIR, "cross_set_correlations.csv"),
        correlations,
        [
            "year",
            "cohort_type",
            "set_a",
            "theme_a_id",
            "theme_a_label",
            "set_b",
            "theme_b_id",
            "theme_b_label",
            "n_cohorts",
            "correlation",
        ],
    )

    # Summary markdown
    summary_path = os.path.join(REPORT_DIR, "summary.md")
    ensure_dir(REPORT_DIR)
    with open(summary_path, "w") as f:
        f.write("# Cross-Theme Cohort Analysis Summary\n\n")
        f.write("This analysis uses cohort-level joins (no respondent linkage). Correlations are ecological.\n\n")
        f.write("Theme labels are derived from top TF-IDF terms per cluster and are descriptive, not definitive.\n\n")

        for year in (2024, 2025):
            f.write(f"## {year}\n\n")
            year_rows = [r for r in correlations if r["year"] == year]
            if not year_rows:
                f.write("No correlations computed (insufficient cohort overlap).\n\n")
                continue
            # Top correlations by absolute value
            top = sorted(year_rows, key=lambda r: abs(r["correlation"]), reverse=True)[:20]
            f.write("Top correlations (by absolute value):\n\n")
            for row in top:
                theme_a = row["theme_a_label"]
                theme_b = row["theme_b_label"]
                f.write(
                    f"- {row['cohort_type']} | {row['set_a']}:{theme_a} "
                    f"vs {row['set_b']}:{theme_b} => r={row['correlation']} (n={row['n_cohorts']})\n"
                )
            f.write("\n")


if __name__ == "__main__":
    main()
