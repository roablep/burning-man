# Census 2025 Cohort Trends

- Source file: `/Users/peter/Downloads/census2025_cleaned_weighted.xlsx`
- Rows: `5028`
- Attended years: `1986-2025`

## Data Hygiene

- Missing cohort year: `2`
- Missing return-next-year: `1510`
- Excluded campPlaced (dontKnow/missing): `201`

## Trend Table

Saved to CSV with columns: `cohort_year`, `segment`, `campPlaced`, `weighted_count`, `weighted_return_rate`, `unweighted_n`.
- Rows: `227`

## Age ≤28 Share Table

**What this measures:** The proportion of each cohort that is age 28 or younger. This is a composition metric (what % of the cohort is young), NOT a retention metric. Age ≤28 includes age bands `<=22` and `23-28`.

Saved to CSV with columns: `cohort_year`, `campPlaced`, `under30_weighted_count`, `total_weighted_count`, `under30_share`, `unweighted_n`.
- Rows: `97`

_Note: The variable is named 'under30' in the code for historical reasons, but actually measures age ≤28 based on the age band definitions._

## First-Timer Camp Placement Share

Saved to CSV with columns: `cohort_year`, `age_band`, `weighted_yes_count`, `weighted_no_count`, `weighted_total_count`, `camp_placed_share`, `unweighted_n`.
- Rows: `7`

## Multi-Year Retention (Pooled Across Cohorts)

Saved to CSV with columns: `segment`, `campPlaced`, `metric`, `weighted_count`, `weighted_return_rate`, `unweighted_n`.
- Rows: `18`

| segment | campPlaced | metric | weighted_count | weighted_return_rate | unweighted_n |
|---|---|---|---|---|---|
| age30plus | no | return_1yr | 609.94 | 0.6859 | 680 |
| age30plus | no | return_2yr | 447.20 | 0.6529 | 556 |
| age30plus | no | return_3plus | 506.76 | 0.9778 | 588 |
| age30plus | yes | return_1yr | 2360.49 | 0.7455 | 2647 |
| age30plus | yes | return_2yr | 1773.93 | 0.7057 | 2220 |
| age30plus | yes | return_3plus | 1997.48 | 0.9806 | 2314 |
| overall | no | return_1yr | 645.79 | 0.6921 | 704 |
| overall | no | return_2yr | 472.20 | 0.6649 | 572 |
| overall | no | return_3plus | 533.07 | 0.9759 | 603 |
| overall | yes | return_1yr | 2528.30 | 0.7512 | 2741 |
| overall | yes | return_2yr | 1877.60 | 0.7126 | 2282 |
| overall | yes | return_3plus | 2085.18 | 0.9798 | 2363 |
| under30 | no | return_1yr | 35.86 | 0.7976 | 24 |
| under30 | no | return_2yr | 25.01 | 0.8791 | 16 |
| under30 | no | return_3plus | 26.31 | 0.9396 | 15 |
| under30 | yes | return_1yr | 167.82 | 0.8305 | 94 |
| under30 | yes | return_2yr | 103.67 | 0.8315 | 62 |
| under30 | yes | return_3plus | 87.70 | 0.9625 | 49 |