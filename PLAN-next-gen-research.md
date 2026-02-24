# Analysis & Reasoning

The user wants to analyze "Next Gen / Rising Sparks" engagement using Burning Man Field Notes data (2024-2025). The goal is to advance understanding of younger cohorts (GenZ, Millennials) in terms of their acculturation, participation, and sentiment.

Current analysis modules (`analyze_transformation.py`, `analyze_survival.py`, etc.) are theme-centric. A cross-theme, cohort-centric approach is needed to synthesize a holistic "Next Gen" profile.

**Key Findings from Exploration:**
- Data includes `Norm_Age`, `Norm_Burn_Count`, `Burn_Status`.
- Questions cover Transformation, Survival, Emotions, Relationships, and Diversity.
- `analysis_utils.py` provides `batch_process_with_llm` and `get_age_bucket`, which can be extended for generational cohorts.
- `analyze_cross_theme.py` already computes theme prevalence by age bands but uses generic buckets (`<30`, `30s`, etc.).

**Proposed Solution:**
Create a specialized module `analyze_next_gen.py` that aggregates responses from *all* themes for the GenZ cohort and compares them to older generations. We will use LLM-based summarization to extract "Next Gen" specific narratives.

# Plan: Next Gen / Rising Sparks Research Analysis

## 1. Goal
Advance the "Next Gen / Rising Sparks" initiative by performing cross-theme exploratory analysis of GenZ and younger Millennial burners, focusing on acculturation, survival priorities, and emotional engagement.

## 2. Analysis
- **Current State**: Existing modules analyze individual themes by age, but don't synthesize a cross-theme "Next Gen" persona.
- **Files Involved**:
  - `src/census_field_notes/modules/analyze_next_gen.py` (New)
  - `src/census_field_notes/analysis_utils.py` (Helper extension)
  - `src/census_field_notes/run_pipeline.py` (Orchestration)

## 3. Design
- **Cohort Definition**:
  - **GenZ**: Age < 28 (Born 1997-2012)
  - **Millennials**: Age 28-43 (Born 1981-1996)
  - **GenX**: Age 44-59 (Born 1965-1980)
  - **Boomers+**: Age 60+
- **Metrics/Dimensions**:
  - **Engagement**: Burn Status (Virgin vs Veteran) distribution by Gen.
  - **Acculturation**: Survival (Set B) equipment priorities (Tech/Digital vs Physical/Analog).
  - **Transformation**: Nature of change (Set A) - "Sudden" vs "Gradual" for younger cohorts.
  - **Emotional Profile**: Set C analysis for positive/negative triggers in younger burners.
  - **Identity**: Set F - impact of appearance on/off playa for GenZ.
- **Synthesized Narrative**: Use LLM to generate a "GenZ Burner Narrative" by summarizing their responses across all themes.

## 4. Implementation Steps
1. [x] **Update `analysis_utils.py`**: Add `get_generation_bucket(age)` to return "GenZ", "Millennial", "GenX", "Boomer+".
2. [x] **Create `src/census_field_notes/modules/analyze_next_gen.py`**:
    - Load data for 2024 and 2025.
    - Group all responses by Generation.
    - Extract thematic "Top Keywords" for GenZ across Survival and Transformation.
    - Perform LLM-based "Sentiment Comparison" between GenZ and GenX.
    - Identify "Rising Sparks" signals: look for responses mentioning "Art", "Volunteering", "Giving", "Community".
3. [x] **Integrate into `run_pipeline.py`**: Add the new module to the execution flow.
4. [x] **Generate Report**: Produce `reports/module_7_next_gen.md` and synthesize into `FINAL_ANALYSIS_REPORT.md`.

## 5. Approval
- [x] User Approval Received
