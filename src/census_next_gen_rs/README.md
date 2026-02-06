# Census Next Gen (2025 Weighted) - TL;DR

## Goals & Objectives

**Goals**
- Reverse or better understand the decline in under-30 participation by identifying how theme camps influence recruitment, acculturation, and retention.
- Treat the Census as a partner for cultural sustainability research, not just a data source.

**Objectives**
- Diagnose the problem: separate recruitment vs. retention dynamics for younger participants.
- Quantify the camp effect: measure under-30 participation and return rates by placed vs. non-placed camps.
- Provide actionable benchmarks: anonymized metrics camps can compare to citywide averages (e.g., % under-30, % virgins, retention).
- Inform program design: identify factors that correlate with stronger retention to guide next-gen engagement.
- Set up future research: move toward longitudinal and on-playa methods (EMA/intercepts) that capture belonging and return intent.

## Quick Start (Recommended Order)

1. **Run the quick stats overview first**
   ```bash
   poetry run python src/census_next_gen_rs/scripts/quick_stats_2025_weighted.py
   ```

2. **Run the full cohort pipeline**
   ```bash
   poetry run python src/census_next_gen_rs/scripts/census2025_cohort_all.py
   ```

3. **Open outputs**
   - Tables: `reports/census_next_gen_rs/census2025_cohort_retention.csv`
   - Trends: `reports/census_next_gen_rs/census2025_cohort_trends.csv`
   - Under-30 share: `reports/census_next_gen_rs/census2025_under30_share.csv`
   - First-timer camp share: `reports/census_next_gen_rs/census2025_firsttimer_camp_share.csv`
   - Multi-year retention (pooled): `reports/census_next_gen_rs/census2025_multiyear_retention.csv`
   - Briefing prompt: `reports/census_next_gen_rs/census2025_cohort_analysis_briefing.md`
   - Visuals (Plotly HTML): `reports/census_next_gen_rs/figures/`

## If You Need To Run Steps Manually

1. **Cohort retention (base table + summary)**
   ```bash
   poetry run python src/census_next_gen_rs/scripts/census2025_cohort_retention.py
   ```

2. **Cohort trends + under-30 share**
   ```bash
   poetry run python src/census_next_gen_rs/scripts/census2025_cohort_trends.py
   ```

3. **Visuals (Plotly HTML)**
   ```bash
   poetry run python src/census_next_gen_rs/scripts/census2025_cohort_visuals.py
   ```

4. **Briefing (human-analysis prompt)**
   ```bash
   poetry run python src/census_next_gen_rs/scripts/census2025_cohort_briefing.py
   ```

## Cohort Retention Methodology (Summary)

- The script scans columns named `attendedYears.YYYY`. If multiple columns exist for the same year
  (e.g., `attendedYears.1990Baker`, `attendedYears.1990BlackRock`), it collapses them by taking the
  max across those columns, so any attendance counts as attended.
- `cohort_year` is the first year with attended == 1.
- `return_next_year` is whether attended == 1 for `cohort_year + 1`. If that year column does not
  exist, the value is treated as missing and excluded from results.
- Rows are filtered to valid `age` (bucketed into fixed age bands) and `campPlaced` in {yes, no}.
- Return rates are weighted: sum(weights * return_next_year) / sum(weights).
- Important: This is computed from the 2025 census respondent sample only. For recent
  cohorts (e.g., cohort_year = 2024), return_next_year is right-censored and biased upward
  because the sample already consists of 2025 attendees. Near-100% return rates for the
  most recent cohort are a sampling artifact, not population retention.
- Outputs:
  - Cohort table: `cohort_year x age_band x campPlaced`
  - Aggregated table: `age_band x campPlaced`

## Custom Input File / Sheet

If you need a specific XLSX or sheet name/index:
```bash
poetry run python src/census_next_gen_rs/scripts/census2025_cohort_all.py \
  --input /path/to/census2025_cleaned_weighted.xlsx \
  --sheet census2025_cleaned_weighted
```
