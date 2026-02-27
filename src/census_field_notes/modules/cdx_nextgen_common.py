from __future__ import annotations

import csv
import os
import re
from collections import Counter
from typing import Dict, Iterable, List

WORD_RE = re.compile(r"[A-Za-z][A-Za-z']+")
SUBFOLDER_RE = re.compile(r"([A-M])\d", re.IGNORECASE)

STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "but", "by", "for", "from",
    "has", "have", "he", "her", "hers", "him", "his", "i", "if", "in", "is",
    "it", "its", "me", "my", "of", "on", "or", "our", "ours", "she", "so",
    "that", "the", "their", "them", "they", "this", "to", "us", "we", "were",
    "what", "when", "where", "who", "why", "with", "you", "your", "yours", "am",
    "im", "ive", "dont", "didnt", "cant", "couldnt", "wouldnt", "wont", "yes",
    "no", "not", "just", "also", "because", "about", "into", "than", "burning",
    "man", "bm", "brc", "playa", "black", "rock", "city", "really", "very",
}

QUESTION_FAMILY_MAP = {
    2024: {
        "A": "Transformation",
        "B": "Symbolism",
        "C": "Emotions & Experiences",
        "D": "Boundaries of Humanity",
        "E": "Other",
        "F": "Other",
        "G": "Other",
        "H": "Emotions & Experiences",
        "I": "Relationships",
        "J": "Survival",
        "K": "Diversity & Inclusion",
        "L": "Other",
        "M": "Other",
    },
    2025: {
        "A": "Transformation",
        "B": "Survival",
        "C": "Emotions & Experiences",
        "D": "Boundaries of Humanity",
        "E": "Relationships",
        "F": "Diversity & Inclusion",
    },
}


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def safe_int(value: str | None) -> int | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        return int(float(text))
    except ValueError:
        return None


def age_band_nextgen(age: int | None) -> str:
    if age is None:
        return "Unknown"
    if age < 25:
        return "<25"
    if age < 30:
        return "25-29"
    if age < 35:
        return "30-34"
    if age < 40:
        return "35-39"
    return "40+"


def normalize_tenure(value: str | None) -> str:
    text = (value or "").strip()
    if text in {"Virgin", "Sophomore", "Veteran", "Elder"}:
        return text
    return "Unknown"


def extract_set_key(subfolder: str | None) -> str | None:
    if not subfolder:
        return None
    match = SUBFOLDER_RE.search(subfolder.strip())
    if not match:
        return None
    return match.group(1).upper()


def map_question_family(year: int, subfolder: str | None) -> str:
    key = extract_set_key(subfolder)
    if not key:
        return "Unknown"
    return QUESTION_FAMILY_MAP.get(year, {}).get(key, "Unknown")


def clean_text(text: str | None) -> str:
    if not text:
        return ""
    value = text.strip()
    if value.lower() in {"[blank]", "blank", "no entries found"}:
        return ""
    return value


def collect_open_ended_text(row: Dict[str, str], min_q: int = 5) -> tuple[str, int]:
    parts: List[str] = []
    non_empty = 0
    for key, value in row.items():
        if not key.startswith("Q") or not key[1:].isdigit():
            continue
        if int(key[1:]) < min_q:
            continue
        cleaned = clean_text(value)
        if cleaned:
            parts.append(cleaned)
            non_empty += 1
    return " ".join(parts).strip(), non_empty


def count_words(text: str) -> int:
    if not text:
        return 0
    return len(WORD_RE.findall(text))


def tokenize(text: str) -> List[str]:
    tokens = []
    for token in WORD_RE.findall(text.lower()):
        if token in STOPWORDS:
            continue
        if len(token) < 3:
            continue
        tokens.append(token)
    return tokens


def write_csv(path: str, rows: Iterable[Dict[str, object]], fieldnames: List[str]) -> None:
    ensure_dir(os.path.dirname(path))
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def read_csv(path: str) -> List[Dict[str, str]]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def top_terms(texts: Iterable[str], top_n: int = 20) -> List[tuple[str, int]]:
    counter = Counter()
    for text in texts:
        counter.update(tokenize(text))
    return counter.most_common(top_n)
