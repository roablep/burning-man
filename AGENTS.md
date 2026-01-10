# Repository Guidelines

## Project Structure & Module Organization
- `src/bm/` contains the core Burning Man workflows and the Streamlit app (`bm_streamlit_app.py`).
- `src/census/` holds census ingestion, cleaning, and analysis scripts plus `data/` inputs (CSV/JSON/MD).
- `reports/` stores generated analysis reports and writeups; `analysis_cache/` holds cached analysis artifacts.
- `static/` contains static assets used by the app or reports (e.g., CSVs, images).

## Build, Test, and Development Commands
- `./build-dev.sh` sets up Python via `pyenv`, installs dependencies with Poetry, and creates `.venv`.
- `source .venv/bin/activate` or `source activate.sh` activates the local virtual environment.
- `poetry run streamlit run src/bm/bm_streamlit_app.py` runs the Streamlit UI locally.
- `poetry run python src/census/analyze_survival.py` (example) runs a single analysis script.

## Coding Style & Naming Conventions
- Use Python 3.11+, 4-space indentation, and PEP 8 conventions.
- Prefer `snake_case` for functions/variables and `PascalCase` for classes.
- Keep data files in `src/census/data/` and generated artifacts in `reports/` or `analysis_cache/`.

## Testing Guidelines
- Pytest is configured in `pyproject.toml`, but there is no dedicated test suite yet.
- When adding new logic, add tests under `tests/` (create if needed) and run `poetry run pytest`.
- Name tests as `test_<feature>.py` with `test_<behavior>()` functions.

## Commit & Pull Request Guidelines
- Follow existing commit style: short, present-tense messages like `moving files` or `Update analyze_transformation.py`.
- PRs should describe the change, how to run it, and include screenshots for Streamlit/UI changes.
- Link any relevant issues or report files (e.g., `reports/module_1_transformation.md`).

## Configuration & Data Notes
- Environment variables can be managed with `.env` (used by `python-dotenv`); document new keys in the PR.
- Large raw datasets should stay in `src/census/data/` with clear filenames (e.g., `2025-...-cleaned.csv`).
