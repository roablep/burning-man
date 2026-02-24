# Plan: Next-Gen / Rising Sparks Field Notes Analysis

## Context

The existing field notes pipeline (`src/census_field_notes/`) has 8 analysis modules focused on broad themes (Transformation, Survival, Identity, etc.) that treat age as a secondary segmentation variable. The quantitative `census_next_gen_rs` workstream has surfaced a clear story — declining under-30 participation, camp placement driving retention — but has no qualitative layer explaining *why*.

This plan creates 4 new age-first analysis modules and a standalone `run_nextgen_pipeline.py` that can be run independently of the main pipeline. All modules follow the exact same pattern as existing ones: `analysis_utils.load_data()` → text filtering → `batch_process_with_llm()` with Pydantic schemas → `save_report()`.

**Data available:**
- `src/census_field_notes/data/2024-field-note-transcriptions-normalized.csv` (1,937 rows)
- `src/census_field_notes/data/2025-field-note-transcriptions-normalized.csv` (181 rows)
- Key columns: `Norm_Age`, `Norm_Gender`, `Norm_Burn_Count`, `Norm_Region`, `Burn_Status`, `Subfolder`, `Q1`–`Q15`
- `utils.get_age_bucket()` returns: `"Under 30"`, `"30-39"`, `"40-49"`, `"50+"`

---

## Files to Create

```
src/census_field_notes/modules/analyze_youth_voice.py       # Module 7
src/census_field_notes/modules/analyze_acculturation.py     # Module 8
src/census_field_notes/modules/analyze_belonging.py         # Module 9
src/census_field_notes/modules/analyze_return_intent.py     # Module 10
src/census_field_notes/run_nextgen_pipeline.py              # Orchestrator
```

Reports will be written to `reports/` by `utils.save_report()`.

---

## Module 7: Youth Voice (`analyze_youth_voice.py`)

**Research question:** How does Under-30 language, values, and emotional tone differ from older cohorts across all survey topics?

**Approach:**
- Load all data (both years, no subfolder filter): `utils.load_data(2024)` + `utils.load_data(2025)`
- Pool Q5 responses across all survey types (the primary open-ended question in every set)
- Segment by `get_age_bucket()` → 4 age groups
- LLM extracts per response:

```python
class YouthTheme(BaseModel):
    primary_theme: str  # 1-3 word theme
    sentiment: Literal["positive", "negative", "mixed"]
    values_language: Literal["freedom", "community", "identity", "spirituality", "creativity", "survival", "other"]
    key_phrase: str  # most distinctive phrase from the response
```

**Output report** (`module_7_youth_voice.md`):
- Top 10 themes per age group with counts
- Values language distribution table (age group × value type)
- Sentiment comparison table
- "Voices" section: 1 representative quote per age group
- Conclusion: What is distinctly young vs distinctly older in this data

---

## Module 8: Acculturation Journey (`analyze_acculturation.py`)

**Research question:** How does cultural learning and integration differ for young first-timers vs young veterans vs older cohorts at the same experience level?

**Approach:**
- Load "Transformation" survey type (Set A, both years): contains questions about change, expectation, factors
- Build a **2×2 matrix**: Age (`Under 30` vs `30+`) × Experience (`Virgin/Sophomore` vs `Veteran/Elder`)
- Combine Q5 + Q9 text per respondent ("Did BM change you?" + "Which factors contributed?")
- LLM extracts per response:

```python
class AcculturationSignal(BaseModel):
    cultural_fluency: Literal["novice", "learning", "fluent", "teaching"]
    principles_referenced: bool      # any of the 10 principles mentioned
    belonging_expressed: bool        # language of fitting in / finding tribe
    overwhelm_expressed: bool        # sensory/social overwhelm
    community_role: Literal["recipient", "participant", "contributor", "leader", "none"]
```

**Output report** (`module_8_acculturation.md`):
- 2×2 matrix table: each cell shows average fluency level, % belonging, % overwhelm, % principles
- Narrative description of each quadrant (Young Virgin, Young Veteran, Older Virgin, Older Veteran)
- Conclusion: Does camp/tenure close the acculturation gap for younger attendees?

---

## Module 9: Belonging & Camp Effect (`analyze_belonging.py`)

**Research question:** What do younger attendees say about social integration and community — and how often do they mention camp affiliation as a belonging mechanism?

**Approach:**
- Load two survey types that contain community/belonging questions:
  - "Survival" set (Q8: "How do you rely on community to survive?"): `utils.load_data(year, "Survival")`
  - "Transformation" set (Q8: "Did BM change the way you relate to other people?"): Q8 field
- For each response, extract belonging signal:

```python
class BelongingSignal(BaseModel):
    belonging_source: Literal["theme_camp", "strangers", "friends_brought", "romantic", "art_community", "solo", "none"]
    camp_explicitly_mentioned: bool
    integration_level: Literal["isolated", "peripheral", "integrated", "central"]
    sentiment: Literal["positive", "negative", "mixed"]
    barrier_mentioned: bool          # mentions difficulty connecting
```

- Segment by age group
- Compute: camp_mention rate, integration distribution, barrier rate per age group

**Output report** (`module_9_belonging.md`):
- Belonging source distribution by age group (table)
- Camp mention rate by age group (proxy for camp effect in qualitative data)
- Integration level by age group
- Barrier mention rate by age group (who struggles most to connect?)
- Representative quotes per age group showing belonging vs isolation
- Conclusion: Does camp membership appear differently in young vs old narratives?

---

## Module 10: Return Intent Signals (`analyze_return_intent.py`)

**Research question:** From the qualitative text, who signals plans to return — and does this differ by age and experience level?

**Approach:**
- Load "Transformation" (Q5: "Did BM change you?") and "Experiences" (Q5/Q6: positive/negative) survey types
  - These are the richest sources of intent language — change narratives often contain future framing
- Also load 2024-only "Beyond" / "L" survey set if present (Q5: "Has BM influenced your life outside BRC?")
- LLM extracts per response:

```python
class ReturnSignal(BaseModel):
    return_intent: Literal["explicit_yes", "explicit_no", "implicit_yes", "implicit_no", "neutral"]
    time_horizon: Literal["next_year", "someday", "never", "unclear"]
    key_phrase: str     # the phrase most indicating intent
    barrier_type: Literal["cost", "logistics", "emotional", "social", "none"]  # if negative intent
```

- Segment by age group AND by `Burn_Status` (Virgin/Sophomore/Veteran/Elder)
- Focus comparison: Under-30 Virgins vs 30+ Virgins (who returns after their first time?)

**Output report** (`module_10_return_intent.md`):
- Return intent distribution by age group (table)
- Return intent by Burn_Status × Age (2×4 matrix)
- Barrier types mentioned by Under-30 vs others
- Representative quotes: young first-timer who signals return vs one who doesn't
- Conclusion: What qualitative signals predict who comes back?

---

## Pipeline: `run_nextgen_pipeline.py`

Located at `src/census_field_notes/run_nextgen_pipeline.py`. Same orchestration pattern as `run_pipeline.py`:

```python
# Run with: poetry run python src/census_field_notes/run_nextgen_pipeline.py

from modules import (
    analyze_youth_voice,
    analyze_acculturation,
    analyze_belonging,
    analyze_return_intent
)

steps = [
    ("Module 7: Youth Voice", analyze_youth_voice.run_analysis),
    ("Module 8: Acculturation Journey", analyze_acculturation.run_analysis),
    ("Module 9: Belonging & Camp Effect", analyze_belonging.run_analysis),
    ("Module 10: Return Intent Signals", analyze_return_intent.run_analysis),
]
# sequential execution with try/except per step, asyncio.run(main())
```

---

## Reused Patterns (from existing modules)

| Pattern | Source |
|---------|--------|
| `sys.path.append(...)` + `import analysis_utils as utils` | All existing modules |
| `utils.load_data(year, survey_type)` for data loading | `analyze_transformation.py` |
| `utils.get_age_bucket(row.get("Norm_Age"))` | All age-segmented modules |
| `utils.batch_process_with_llm(items, prompt, response_schema=Schema)` | `analyze_identity.py` |
| Re-calling LLM on subsets (cache hit = free) | `analyze_identity.py:50-57` |
| `utils.save_report("filename.md", "\n".join(report))` | All modules |
| `if __name__ == "__main__": asyncio.run(run_analysis())` | All modules |

---

## Verification

```bash
# Run the full next-gen pipeline
poetry run python src/census_field_notes/run_nextgen_pipeline.py

# Or run a single module for quick testing
poetry run python src/census_field_notes/modules/analyze_youth_voice.py

# Check outputs
ls reports/module_7_youth_voice.md
ls reports/module_8_acculturation.md
ls reports/module_9_belonging.md
ls reports/module_10_return_intent.md
```

Each module should produce a markdown report. If LLM quota is a concern, add `SAMPLE_SIZE = 100` temporarily (same pattern as existing modules).
