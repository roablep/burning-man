# cdx Next Gen / Rising Sparks Exploratory Memo

## What This Package Contains
- `cdx_nextgen_pooled_base.csv`: pooled and harmonized records (2024+2025 by default)
- `cdx_nextgen_engagement_summary.md` + `cdx_nextgen_engagement_tables.csv`: composition and response-depth cuts
- `cdx_nextgen_acculturation_summary.md` + `cdx_nextgen_acculturation_scores.csv`: proxy acculturation index
- `cdx_nextgen_theme_deltas.md` + `cdx_nextgen_theme_deltas.csv`: language and theme deltas
- `cdx_nextgen_pathways.md` + `cdx_nextgen_pathways.csv`: hardship-to-growth pathway rates

## How To Use
1. Start with engagement summary to identify viable segments (n and low-n suppression).
2. Read acculturation summary by question family and age/tenure segment.
3. Use theme deltas to translate findings into messaging/program hypotheses.
4. Validate intervention ideas against pathway rates and low-n caveats.

## Caveats
- This output is exploratory and descriptive, not causal.
- Cross-year pooling uses harmonized families; non-overlapping sets remain contextual.
- LLM validation is optional and may be skipped when no API key is configured.