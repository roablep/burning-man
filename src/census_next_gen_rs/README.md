# Census Next Gen (2025 Weighted) - TL;DR

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

## Custom Input File / Sheet

If you need a specific XLSX or sheet name/index:
```bash
poetry run python src/census_next_gen_rs/scripts/census2025_cohort_all.py \
  --input /path/to/census2025_cleaned_weighted.xlsx \
  --sheet census2025_cleaned_weighted
```
