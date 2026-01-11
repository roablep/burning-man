import argparse
import asyncio
import csv
import json
import os
import re
from typing import Dict, Iterable, List, Tuple

try:
    from .analysis_utils import batch_process_with_llm
except ImportError:
    try:
        from analysis_utils import batch_process_with_llm
    except ImportError:
        batch_process_with_llm = None

DEFAULT_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
DEFAULT_MAPPING = os.path.join(DEFAULT_DATA_DIR, "ocr_corrections.json")

DEFAULT_FILES = [
    (
        os.path.join(DEFAULT_DATA_DIR, "2024-field-note-transcriptions-cleaned.csv"),
        os.path.join(DEFAULT_DATA_DIR, "2024-field-note-transcriptions-ocr-cleaned.csv"),
    ),
    (
        os.path.join(DEFAULT_DATA_DIR, "2025-field-note-transcriptions-cleaned.csv"),
        os.path.join(DEFAULT_DATA_DIR, "2025-field-note-transcriptions-ocr-cleaned.csv"),
    ),
]


def parse_question_number(field: str) -> int | None:
    if not field.startswith("Q"):
        return None
    suffix = field[1:]
    if not suffix.isdigit():
        return None
    return int(suffix)


def load_mappings(path: str) -> List[Tuple[re.Pattern, str]]:
    with open(path, "r", encoding="utf-8") as f:
        mappings = json.load(f)

    compiled = []
    for item in mappings:
        pattern = item.get("pattern")
        replacement = item.get("replacement")
        if not pattern or replacement is None:
            continue
        compiled.append((re.compile(pattern, re.IGNORECASE), replacement))
    return compiled


def apply_case(original: str, replacement: str) -> str:
    if original.isupper():
        return replacement.upper()
    if original[:1].isupper():
        return replacement[:1].upper() + replacement[1:]
    return replacement.lower() if replacement.isupper() else replacement


def normalize_whitespace(text: str) -> str:
    text = text.replace("\r", " ").replace("\n", " ")
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"\s+([,.;:!?])", r"\1", text)
    text = re.sub(r"\(\s+", "(", text)
    text = re.sub(r"\s+\)", ")", text)
    return text


def clean_text(text: str, mappings: List[Tuple[re.Pattern, str]]) -> str:
    if not text:
        return text
    cleaned = normalize_whitespace(text)
    if cleaned in {"[Blank]", "N/A", "NA"}:
        return cleaned

    for pattern, replacement in mappings:
        cleaned = pattern.sub(lambda m: apply_case(m.group(0), replacement), cleaned)

    cleaned = normalize_whitespace(cleaned)
    return cleaned


def quality_score(text: str) -> float:
    if not text:
        return 1.0

    length = len(text)
    if length == 0:
        return 1.0

    letters = sum(ch.isalpha() for ch in text)
    digits = sum(ch.isdigit() for ch in text)
    spaces = sum(ch.isspace() for ch in text)
    punct = length - letters - digits - spaces

    tokens = re.findall(r"\b\S+\b", text)
    word_tokens = re.findall(r"\b[A-Za-z]{2,}\b", text)

    alpha_ratio = letters / length
    token_ratio = len(word_tokens) / max(1, len(tokens))
    punct_ratio = punct / length
    long_caps = len(re.findall(r"\b[A-Z]{6,}\b", text))

    score = (0.5 * alpha_ratio) + (0.3 * token_ratio) + (0.2 * (1 - punct_ratio))
    score -= 0.05 * long_caps
    return max(0.0, min(1.0, score))


def iter_input_output_pairs(args: argparse.Namespace) -> Iterable[Tuple[str, str]]:
    if args.input and args.output:
        return [(args.input, args.output)]
    if args.input or args.output:
        raise ValueError("Both --input and --output must be provided together.")
    return DEFAULT_FILES


def build_llm_prompt(text: str, subfolder: str, field: str) -> str:
    return (
        "You are cleaning OCR text from handwritten Burning Man field notes. "
        "Make the text minimally legible while preserving the original meaning. "
        "Only fix obvious OCR errors; do not add new content or interpret. "
        "If unsure, keep the original word. Return only the cleaned text.\n\n"
        f"Question set: {subfolder}\n"
        f"Field: {field}\n"
        f"Text: {text}"
    )


async def llm_clean_texts(texts: List[str]) -> List[str]:
    if batch_process_with_llm is None:
        raise RuntimeError("LLM utilities not available. Ensure analysis_utils is importable.")
    prompt_template = "{{TEXT}}"
    return await batch_process_with_llm(texts, prompt_template=prompt_template)


async def process_file(
    input_path: str,
    output_path: str,
    mapping_path: str,
    min_question: int,
    use_llm: bool,
    llm_threshold: float,
) -> None:
    mappings = load_mappings(mapping_path)

    with open(input_path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise ValueError(f"No header found in {input_path}")

        question_fields = [
            field
            for field in reader.fieldnames
            if (qn := parse_question_number(field)) is not None and qn >= min_question
        ]

        cleaned_fields = [f"Cleaned_{field}" for field in question_fields]
        score_fields = [f"Cleaning_Confidence_{field}" for field in question_fields]

        fieldnames = list(reader.fieldnames) + cleaned_fields + score_fields

        rows = list(reader)

    llm_inputs = []
    llm_targets = []

    for row in rows:
        subfolder = row.get("Subfolder", "")
        for field in question_fields:
            raw = row.get(field, "")
            cleaned = clean_text(raw, mappings)
            score = quality_score(cleaned)

            if use_llm and raw and score < llm_threshold:
                llm_inputs.append(build_llm_prompt(cleaned, subfolder, field))
                llm_targets.append((row, field))
            else:
                row[f"Cleaned_{field}"] = cleaned
                row[f"Cleaning_Confidence_{field}"] = f"{score:.3f}"

    if use_llm and llm_inputs:
        llm_outputs = await llm_clean_texts(llm_inputs)
        for (row, field), llm_text in zip(llm_targets, llm_outputs):
            cleaned = normalize_whitespace(llm_text)
            row[f"Cleaned_{field}"] = cleaned
            row[f"Cleaning_Confidence_{field}"] = f"{quality_score(cleaned):.3f}"

    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows to {output_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Clean OCR text in field note CSVs.")
    parser.add_argument("--input", help="Path to cleaned CSV input")
    parser.add_argument("--output", help="Path to write OCR-cleaned CSV")
    parser.add_argument(
        "--mapping",
        default=DEFAULT_MAPPING,
        help="Path to JSON mapping file with OCR corrections",
    )
    parser.add_argument(
        "--min-question",
        type=int,
        default=5,
        help="Only clean Q fields >= this number (default: 5)",
    )
    parser.add_argument(
        "--use-llm",
        action="store_true",
        help="Use LLM to clean low-quality rows (requires GEMINI_API_KEY)",
    )
    parser.add_argument(
        "--llm-threshold",
        type=float,
        default=0.55,
        help="Quality score threshold under which to call the LLM",
    )

    args = parser.parse_args()

    async def run_all():
        for input_path, output_path in iter_input_output_pairs(args):
            if not os.path.exists(input_path):
                print(f"Skipping missing file: {input_path}")
                continue
            await process_file(
                input_path=input_path,
                output_path=output_path,
                mapping_path=args.mapping,
                min_question=args.min_question,
                use_llm=args.use_llm,
                llm_threshold=args.llm_threshold,
            )

    asyncio.run(run_all())


if __name__ == "__main__":
    main()
