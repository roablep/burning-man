# Census 2025 Weighted Cohort Retention

- Source file: `/Users/peter/Downloads/census2025_cleaned_weighted.xlsx`
- Rows: `5028`
- Attended years: `1986-2025`

## Data Hygiene

- Missing cohort year: `1248`
- Missing return-next-year: `1510`
- Missing/invalid age band: `0`
- Excluded campPlaced (dontKnow/missing): `201`

## Second-Year Return Rate By Age Band (campPlaced)

| age_band | campPlaced | weighted_count | weighted_return_rate | unweighted_n |
|---|---|---|---|---|
| <=22 | no | 1.59 | 0.0000 | 1 |
| <=22 | yes | 13.92 | 0.8813 | 9 |
| 23-28 | no | 34.27 | 0.8347 | 23 |
| 23-28 | yes | 153.89 | 0.8258 | 85 |
| 29-34 | no | 112.13 | 0.7556 | 98 |
| 29-34 | yes | 430.36 | 0.8092 | 358 |
| 35-39 | no | 131.84 | 0.6568 | 123 |
| 35-39 | yes | 552.25 | 0.7146 | 500 |
| 40-49 | no | 186.51 | 0.6716 | 217 |
| 40-49 | yes | 702.96 | 0.7277 | 823 |
| 50-59 | no | 96.29 | 0.6915 | 100 |
| 50-59 | yes | 467.89 | 0.7328 | 518 |
| 60+ | no | 83.16 | 0.6637 | 142 |
| 60+ | yes | 207.03 | 0.7848 | 448 |

## Cohort Table

Full cohort table saved to CSV. Columns: `cohort_year`, `age_band`, `campPlaced`, `weighted_count`, `weighted_return_rate`, `unweighted_n`.
- Rows: `248`