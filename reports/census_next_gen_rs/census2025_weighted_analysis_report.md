# Census 2025 Weighted Analysis (Grok-Focused)

## Executive Summary

This report summarizes who is coming, who is returning, and how placed camps relate to retention in 2025 (weighted data). It is built for internal decision-making, with a brief public summary at the end.

## Data Hygiene

- Rows: `5028`
- Missing age: `0`
- Missing campPlaced: `15`
- Missing virgin: `0`

## Composition Baselines

- Under-30 share (weighted, <=29): **11.5%**

### Age Distribution (Weighted %)

| age_band | weighted_pct |
| --- | --- |
| <=22 | 0.8% |
| 23-28 | 7.8% |
| 29-34 | 19.8% |
| 35-39 | 21.8% |
| 40-49 | 26.1% |
| 50-59 | 15.6% |
| 60+ | 8.1% |

Chart: `reports/census2025_age_distribution.svg`

### Camp Placement (Weighted %)

| campPlaced | weighted_pct |
| --- | --- |
| yes | 73.9% |
| no | 21.5% |
| dontKnow | 4.4% |
| missing | 0.2% |

Chart: `reports/census2025_camp_placed_share.svg`

### Under-30 Share by Camp Placement (Weighted %)

| campPlaced | under30_pct |
| --- | --- |
| yes | 10.6% |
| no | 12.3% |

### Camp Placement by Age Band (Weighted %, within age band)

| age_band | campPlaced_yes | campPlaced_no |
| --- | --- | --- |
| <=22 | 76.1% | 23.9% |
| 23-28 | 75.1% | 24.9% |
| 29-34 | 77.3% | 22.7% |
| 35-39 | 78.8% | 21.2% |
| 40-49 | 77.3% | 22.7% |
| 50-59 | 79.9% | 20.1% |
| 60+ | 72.4% | 27.6% |

### Camp Placement by Under-30 vs 30+ (Weighted %, within group)

| age_group | campPlaced_yes | campPlaced_no |
| --- | --- | --- |
| under30 | 74.7% | 25.3% |
| 30plus | 77.8% | 22.2% |

## Crosstabs

See `reports/census2025_weighted_crosstabs.md` and CSV outputs in `reports/`.

## Retention: Return Next Year

The table below shows weighted return rates by age band and camp placement (yes/no). `dontKnow` and missing campPlaced are excluded from the comparison.

| age_band | campPlaced_clean | weighted_count | unweighted_n | weighted_return_rate |
| --- | --- | --- | --- | --- |
| <=22 | no | 1.6 | 1 | 0.000 |
| <=22 | yes | 13.9 | 9 | 0.881 |
| 23-28 | no | 34.3 | 23 | 0.835 |
| 23-28 | yes | 153.9 | 85 | 0.826 |
| 29-34 | no | 112.1 | 98 | 0.756 |
| 29-34 | yes | 430.4 | 358 | 0.809 |
| 35-39 | no | 131.8 | 123 | 0.657 |
| 35-39 | yes | 552.3 | 500 | 0.715 |
| 40-49 | no | 186.5 | 217 | 0.672 |
| 40-49 | yes | 703.0 | 823 | 0.728 |
| 50-59 | no | 96.3 | 100 | 0.692 |
| 50-59 | yes | 467.9 | 518 | 0.733 |
| 60+ | no | 83.2 | 142 | 0.664 |
| 60+ | yes | 207.0 | 448 | 0.785 |

Chart: `reports/census2025_return_rate_by_age_camp.svg`

## Inference (Weighted Logistic Regression)

Model: return-next-year ~ campPlaced + virgin + age_band (reference: <=22). Odds ratios are from a bootstrap (percentile) CI.

| term | odds_ratio | ci_low | ci_high |
| --- | --- | --- | --- |
| campPlaced_yes | 1.34 | 1.06 | 1.69 |
| virgin_yes | 1.00 | 1.00 | 1.00 |
| age_23-28 | 1.49 | 0.81 | 2.68 |
| age_29-34 | 1.23 | 0.81 | 1.94 |
| age_35-39 | 0.73 | 0.48 | 1.21 |
| age_40-49 | 0.77 | 0.51 | 1.24 |
| age_50-59 | 0.81 | 0.51 | 1.37 |
| age_60+ | 0.95 | 0.60 | 1.61 |

## Interpretation Framework

For each key metric, interpret using: What we see → Why it might matter → What it does not prove → Actionable question.

## Public Summary (Draft)

In 2025, the weighted census shows that younger participation is concentrated in the under‑30 band, and placed camps appear associated with higher return‑next‑year rates across most age groups. These patterns suggest camps are an important retention channel, though the analysis is associative rather than causal. The Census can use these insights to help camps benchmark their age mix and track newcomer retention over time.
