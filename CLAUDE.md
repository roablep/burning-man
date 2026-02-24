# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python data analysis project focused on Burning Man research — specifically theme camp dues structures and participant census data. There are three largely independent workstreams:

1. **Theme Camp Dues App** (`src/bm/`) — Streamlit interactive dashboard analyzing camp budget and contribution data
2. **Census Field Notes** (`src/census_field_notes/`) — ETL pipeline using Google Gemini to OCR handwritten field notes and run thematic analysis modules
3. **Census Next-Gen Research** (`src/census_next_gen_rs/`) — Standalone scripts analyzing 2025 weighted census XLSX data for under-30 recruitment/retention

## Environment Setup

```bash
./build-dev.sh          # sets up Python via pyenv, installs deps with Poetry, creates .venv
source activate.sh      # activate the virtual environment
```

Run commands with `poetry run <command>` or activate the venv first.

## Key Commands

**Run the Streamlit app:**
```bash
poetry run streamlit run src/bm/bm_streamlit_app.py
```

**Run census field notes full pipeline:**
```bash
cd src/census_field_notes && poetry run python run_pipeline.py
poetry run python src/census_field_notes/run_pipeline.py --skip-cross-theme
```

**Run census next-gen pipeline:**
```bash
# Quick stats overview first
poetry run python src/census_next_gen_rs/scripts/quick_stats_2025_weighted.py

# Full cohort pipeline (retention, trends, visuals, briefing)
poetry run python src/census_next_gen_rs/scripts/census2025_cohort_all.py \
  --input /path/to/census2025_cleaned_weighted.xlsx

# Individual steps
poetry run python src/census_next_gen_rs/scripts/census2025_cohort_retention.py
poetry run python src/census_next_gen_rs/scripts/census2025_cohort_trends.py
poetry run python src/census_next_gen_rs/scripts/census2025_cohort_visuals.py
poetry run python src/census_next_gen_rs/scripts/census2025_cohort_briefing.py
```

**Run tests:**
```bash
poetry run pytest
```

## Architecture

### Theme Camp Dues App (`src/bm/bm_streamlit_app.py`)
Single-file Streamlit app. Loads `static/Theme Camp Dues!.csv` at startup, performs all data munging at module level (one-hot encoding amenities and fee structures into binary columns), then builds interactive Altair/Plotly/Matplotlib charts in the UI. The `streamlit_app.py` file appears to be an older version.

### Census Field Notes (`src/census_field_notes/`)
Two-stage pipeline:
- **ETL** (`etl/`) — Uses Google Gemini (`gemini-2.0-flash-lite`) to OCR handwritten images (HEIC/PNG/JPG) from a local folder, clean text, and parse structured data. Requires `GEMINI_API_KEY` in `.env`.
- **Analysis modules** (`modules/`) — Each module (`analyze_transformation.py`, `analyze_survival.py`, etc.) runs independently via `run_analysis()`. They use `analysis_utils.py` which provides a shared Gemini client, age bucketing helpers, and a JSON-based `analysis_cache/` for avoiding redundant LLM calls.
- `run_pipeline.py` orchestrates all modules sequentially with async support.

### Census Next-Gen Research (`src/census_next_gen_rs/`)
Standalone scripts; no shared utilities with the other workstreams. Input is a weighted XLSX file (default: `~/Downloads/census2025_cleaned_weighted.xlsx`). Outputs go to `reports/census_next_gen_rs/`. Scripts accept `--input` and `--sheet` CLI args.

## Data Locations

| Data type | Location |
|-----------|----------|
| Theme camp dues survey | `static/Theme Camp Dues!.csv` |
| Census XLSX input | `~/Downloads/census2025_cleaned_weighted.xlsx` (external, not in repo) |
| Analysis cache (LLM responses) | `analysis_cache/*.json` |
| Generated reports | `reports/` |
| Census next-gen outputs | `reports/census_next_gen_rs/` |

## External Dependencies

- `GEMINI_API_KEY` — required for `census_field_notes` ETL and analysis modules; set in `.env`
- Raw image inputs for field notes pipeline are loaded from a local path (`/Users/peter/Downloads/2025 Notes` in current code — may need updating)
- Census XLSX file is not committed; passed via `--input` flag
