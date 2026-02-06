# Cohort Analysis Plan (Census 2025 Weighted)

**Summary**
We will build a cohort retention analysis using the weighted 2025 dataset. Cohorts are defined by **first burn year** inferred from `attendedYears.*` columns. The primary outcome is **return the next year**. Core segmentation is **age band + campPlaced** with `dontKnow` excluded. All metrics will be **survey‑weighted**.

## Scope And Outputs
- Compute **cohort year** for each respondent from the earliest `attendedYears.<YYYY> == 1`.
- Compute **return next year** indicator based on `attendedYears.<YYYY+1> == 1`.
- Segment results by:
  - `age_band` derived from `age` using bins: `<=22`, `23-28`, `29-34`, `35-39`, `40-49`, `50-59`, `60+`
  - `campPlaced` mapped to `yes/no`, excluding `dontKnow` and missing
- Produce:
  - A cohort table with weighted return rates by `cohort_year`, `age_band`, `campPlaced`
  - Aggregated plots/tables for:
    - Second‑year return rate by age band, split by campPlaced
    - Cohort‑year trend lines for under‑30 share by campPlaced (optional add‑on)

## Data Inputs
- Weighted dataset described in `src/census_next_gen_rs/docs/census2025_weighted_data_dictionary.md`
- Primary columns:
  - `weights`
  - `age`
  - `campPlaced`
  - `attendedYears.<YYYY>` (multiple columns)
  - Optional `virgin` not used in first pass

## Definitions (Decision Complete)
- **Cohort year**: min year where `attendedYears.<YYYY> == 1`.
- **Return next year**: `attendedYears.<cohort_year+1> == 1`.
- **Age band**: derived from `age` into bins in `src/census_next_gen_rs/docs/BRIEFING_BOOK.md`.
- **campPlaced handling**:
  - Keep `yes` and `no` as is.
  - Exclude rows with `campPlaced == dontKnow` or missing from campPlaced analyses.
- **Weights**: Use `weights` for all proportions/rates; compute weighted counts.

## Edge Cases And Data Hygiene
- If a respondent has no `attendedYears.* == 1`, exclude from cohort analysis.
- If cohort year is the latest year in the dataset (no `cohort_year+1` column), exclude from next‑year return metric.
- Validate that `attendedYears.*` columns are treated as numeric/binary (0/1).
- Ensure `age` is present; if missing or out of reasonable range, exclude from age‑banded analyses (log counts dropped).

## Implementation Steps
1. **Column discovery**
   - Programmatically collect all `attendedYears.<YYYY>` columns; parse years into integers.
2. **Derive fields**
   - `cohort_year` via earliest year attended.
   - `return_next_year` via `cohort_year + 1` column.
   - `age_band` via `age` bins.
3. **Filter**
   - Keep only rows with valid `cohort_year` and `return_next_year`.
   - For campPlaced‑segmented outputs, drop `dontKnow` and missing.
4. **Aggregate (weighted)**
   - For each group (`cohort_year`, `age_band`, `campPlaced`), compute:
     - weighted count (`sum(weights)`)
     - weighted return rate (`sum(weights * return_next_year) / sum(weights)`)
5. **Reporting**
   - Save a cohort table to `reports/census_next_gen_rs/` (CSV + brief markdown summary).
   - Produce 1–2 plots (optional if matplotlib/plotly already in project).

## Public Interfaces / Files
- New analysis script in `src/census_next_gen_rs/` (exact filename TBD).
- New output files in `reports/census_next_gen_rs/` (e.g., `reports/census_next_gen_rs/census2025_cohort_retention.md`, `reports/census_next_gen_rs/census2025_cohort_retention.csv`).

## Tests
- Add `tests/test_cohort_retention.py` with:
  - A tiny synthetic dataframe for attendedYears logic
  - Assert correct `cohort_year` inference
  - Assert correct `return_next_year` calculation
  - Assert campPlaced exclusion behavior
  - Assert weighted rate math

## Assumptions And Defaults
- Use only the 2025 weighted dataset described in `src/census_next_gen_rs/docs/census2025_weighted_data_dictionary.md`.
- All metrics are weighted (no unweighted outputs).
- `campPlaced` segmentation excludes `dontKnow` and missing.
- Primary metric is **return the next year**.
