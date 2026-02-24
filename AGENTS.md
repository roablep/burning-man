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

## Skills
A skill is a set of local instructions to follow that is stored in a `SKILL.md` file. Below is the list of skills that can be used. Each entry includes a name, description, and file path so you can open the source for full instructions when using a specific skill.
### Available skills
- critical-thinker: Rigorous self-analysis and skeptical evaluation of a recently provided response. Use after substantial technical recommendations, architectural decisions, or complex problem-solving advice when you need to challenge assumptions, find weaknesses, and surface risks. (file: /Users/peter/.codex/skills/critical-thinker/SKILL.md)
- skill-creator: Guide for creating effective skills. This skill should be used when users want to create a new skill (or update an existing skill) that extends Codex's capabilities with specialized knowledge, workflows, or tool integrations. (file: /Users/peter/.codex/skills/.system/skill-creator/SKILL.md)
- skill-installer: Install Codex skills into $CODEX_HOME/skills from a curated list or a GitHub repo path. Use when a user asks to list installable skills, install a curated skill, or install a skill from another repo (including private repos). (file: /Users/peter/.codex/skills/.system/skill-installer/SKILL.md)
### How to use skills
- Discovery: The list above is the skills available in this session (name + description + file path). Skill bodies live on disk at the listed paths.
- Trigger rules: If the user names a skill (with `$SkillName` or plain text) OR the task clearly matches a skill's description shown above, you must use that skill for that turn. Multiple mentions mean use them all. Do not carry skills across turns unless re-mentioned.
- Missing/blocked: If a named skill isn't in the list or the path can't be read, say so briefly and continue with the best fallback.
- How to use a skill (progressive disclosure):
  1) After deciding to use a skill, open its `SKILL.md`. Read only enough to follow the workflow.
  2) When `SKILL.md` references relative paths (e.g., `scripts/foo.py`), resolve them relative to the skill directory listed above first, and only consider other paths if needed.
  3) If `SKILL.md` points to extra folders such as `references/`, load only the specific files needed for the request; don't bulk-load everything.
  4) If `scripts/` exist, prefer running or patching them instead of retyping large code blocks.
  5) If `assets/` or templates exist, reuse them instead of recreating from scratch.
- Coordination and sequencing:
  - If multiple skills apply, choose the minimal set that covers the request and state the order you'll use them.
  - Announce which skill(s) you're using and why (one short line). If you skip an obvious skill, say why.
- Context hygiene:
  - Keep context small: summarize long sections instead of pasting them; only load extra files when needed.
  - Avoid deep reference-chasing: prefer opening only files directly linked from `SKILL.md` unless you're blocked.
  - When variants exist (frameworks, providers, domains), pick only the relevant reference file(s) and note that choice.
- Safety and fallback: If a skill can't be applied cleanly (missing files, unclear instructions), state the issue, pick the next-best approach, and continue.
