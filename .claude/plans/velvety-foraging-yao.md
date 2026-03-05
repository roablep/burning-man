# Plan: Surface Census Reports via GitHub Pages

## Context

A large body of Burning Man census and field notes analysis exists in `reports/` but is not easily accessible — it's a mix of markdown, interactive HTML charts, and CSVs that require knowing where to look. The goal is to make key findings consumable at a glance, with progressive disclosure for those who want to dig in. The figures directory in particular has 10 charts, many redundant, so we'll surface only the 3 highest-impact ones prominently.

## Recommended Top 3 Charts

From `reports/census_next_gen_rs/figures/`, these three charts tell the most complete and actionable story:

1. **`under30_share_by_cohort.html`** — "Is Burning Man getting younger?" Tracks the under-30 share of each entry cohort over time. This is the headline recruitment question for long-term community health.

2. **`retention_by_age_band.html`** — "Who comes back?" Shows second-year return rates by age band with interactive cohort-year filters. Directly answers where retention is strong vs. weak.

3. **`retention_gap_line_last10.html`** — "Does camp placement matter?" Shows the gap in retention between camp-placed vs. unplaced burners by age band over the last 10 years. Most actionable for organizational decision-making (camp placement as a retention lever). For ≤22 year-olds the gap is +0.67 — that's compelling.

## Approach: Static GitHub Pages site in `docs/`

No build tool, no CI pipeline, no external dependencies. Pure HTML/CSS files in the existing `docs/` directory, which is the conventional GitHub Pages source folder. All chart HTML files are already self-contained (Plotly CDN + embedded data).

GitHub Pages can be enabled in repo Settings → Pages → Source: `docs/` folder on `main` branch after the feature branch is merged.

## Files to Create

### Structure
```
docs/
├── index.html                    # Landing page (new)
├── census-analysis.html          # Census deep-dive page (new)
├── field-notes.html              # Field notes page (new)
├── charts/                       # Copy of 3 key chart files (new dir)
│   ├── under30_share_by_cohort.html
│   ├── retention_by_age_band.html
│   └── retention_gap_line_last10.html
├── regional-burns-2026.html      # existing — leave alone
└── rising-sparks-brand-kit.md    # existing — leave alone
```

### `docs/index.html` — Landing page
- Clean header: "Burning Man Research Hub"
- Brief 2-sentence description of the research
- Two cards: **Census Analysis** (quantitative, 2025 weighted data) | **Field Notes** (qualitative, 2024–25 participant narratives)
- Stat callouts prominently shown: "5,028 respondents · 11.5% under 30 · 73.9% in placed camps"
- Simple dark/warm CSS theme (no framework, ~50 lines of inline style)

### `docs/census-analysis.html` — Census page
- Section 1: Key findings prose (3 bullet points from the briefing — retention trend, youth trend, camp placement effect)
- Section 2: "Three Key Charts" — each chart in an `<iframe>` (height: 480px, full width), with a 1-sentence caption below
- Section 3: "More Detail" — collapsible `<details>` element linking to all 10 charts in `reports/census_next_gen_rs/figures/` and key markdown reports
- Small-N caveat note

### `docs/field-notes.html` — Field Notes page
- Executive summary: the 6 module conclusions from `reports/field_notes/FINAL_ANALYSIS_REPORT.md`, formatted as a scannable card grid (module name → 1-sentence finding)
- "Dive Deeper" links to individual module markdown files in `reports/field_notes/`
- Key stat callouts: "154 transformation narratives · 8.4% mention hardship · 18.2% found new love on playa"

## Styling
- Single shared CSS block (inline, no external stylesheet needed)
- Clean academic style: white background (#ffffff), blue accent (#2563eb), Georgia serif headers, system-ui body
- Responsive single-column on mobile, two-column cards on desktop
- No JS except what's already in the chart files

## Field Notes Content Approach
Inline the key findings as HTML — embed executive summaries and module conclusions directly in `docs/field-notes.html`. Source content from `reports/field_notes/FINAL_ANALYSIS_REPORT.md` (executive summary section) and the 6 module conclusion blocks.

## Critical Files to Reference
- `reports/field_notes/FINAL_ANALYSIS_REPORT.md` — source for module summaries
- `reports/census_next_gen_rs/census2025_weighted_quick_stats.md` — source for stat callouts
- `reports/census_next_gen_rs/census2025_cohort_analysis_briefing.md` — source for key findings prose
- `reports/census_next_gen_rs/figures/*.html` — 3 chart files to copy into `docs/charts/`

## Verification

1. Open `docs/index.html` in a browser locally — confirm both cards link correctly
2. Open `docs/census-analysis.html` — confirm all 3 iframes load charts without errors (they use Plotly CDN, so need network)
3. Open `docs/field-notes.html` — confirm module summaries are readable and links resolve
4. After merge to main: enable GitHub Pages in repo Settings → Pages → Source: `docs/` folder
5. Check that the live site renders on `https://roablep.github.io/burning-man/`

## Out of Scope
- Converting markdown to HTML (linking to raw GitHub-rendered markdown is fine for "dig in" links)
- Any backend, database, or dynamic content
- Automated rebuild of reports
