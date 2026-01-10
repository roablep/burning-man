# Analysis Execution Plan: Burning Man Field Notes

This document serves as the master project management tool for the thematic analysis of the Burning Man Field Notes dataset (2024 & 2025).

**Objective:** Conduct a mixed-method analysis (quantitative & qualitative) using the "Theoretical Research Framework" to uncover deep insights into participant experiences.

**Status Legend:**
- [ ] Pending
- [x] Completed
- [~] In Progress

---

## 1. Setup & Infrastructure
Before diving into specific modules, ensure the data is ready and the toolkit is built.

- [x] **Data Cleaning:** Parse questions into columns (`parse_questions.py`).
- [x] **Data Cleaning:** Merge overflowing answers (`clean_columns.py`).
- [x] **Demographics:** Normalize Age, Gender, Tenure, Region (`normalize_demographics.py`).
- [x] **Baseline Stats:** Generate histograms for Age, Gender, Tenure (`generate_basic_stats.py`).
- [ ] **Infrastructure:** Create `analysis_utils.py` shared library.
    -   Function to load normalized data.
    -   Function to call Gemini API for batch processing (Sentiment/Tagging) with rate limit handling.
    -   Function to cache LLM results (to avoid re-running costs).

## 2. Module 1: The "Pilgrim's Progress" (Transformation)
*Research Question:* How does the narrative of transformation evolve from Virgin to Veteran?

- [ ] **Data Prep:** Filter "Transformation" (Set A) responses by Cohort (Virgin, Sophomore, Veteran, Elder).
- [ ] **Analysis Script (`analyze_transformation.py`):**
    -   **Keyword Extraction:** Identify top unique words for Virgins vs. Veterans.
    -   **LLM Analysis:** Ask Gemini to summarize the "Core Driver of Change" for a sample of each cohort.
- [ ] **Hypothesis Test:** Verify if "Ego Death" is a Virgin trait and "Service" is a Veteran trait.
- [ ] **Output:** `reports/module_1_transformation.md`

## 3. Module 2: Maslow’s Inverted Pyramid (Survival vs. Epiphany)
*Research Question:* Does physical hardship correlate with emotional breakthrough?

- [ ] **Data Prep:** Join "Survival" (Set J/B) and "Experiences" (Set H/C) data.
- [ ] **Analysis Script (`analyze_survival.py`):**
    -   **Hardship Index:** Score responses based on mentions of "Mud", "Dust", "Heat", "Hunger".
    -   **Epiphany Index:** Score "Transformation" responses for "Life Changing" sentiment.
    -   **Correlation:** Plot/Check overlap. Do those with high Hardship scores have high Epiphany scores?
- [ ] **Output:** `reports/module_2_survival.md`

## 4. Module 3: The Mask vs. The Mirror (Identity)
*Research Question:* Is the costume a mask (hiding) or a mirror (revealing)?

- [ ] **Data Prep:** Focus on "Costumes" (Set F) and "Diversity" (Set K/F).
- [ ] **Analysis Script (`analyze_identity.py`):**
    -   **Semantic Classification:** Classify "Why do you wear costumes?" answers into:
        -   *Type A: Hiding/Blending In*
        -   *Type B: Revealing/Authenticity*
        -   *Type C: Play/Fun*
    -   **Cross-Reference:** Check if *Type B* respondents report higher "Positive Interactions" in Diversity Q7.
- [ ] **Output:** `reports/module_3_identity.md`

## 5. Module 4: Sacred vs. Profane (Symbolism)
*Research Question:* How do "The Man" and "The Temple" differ in emotional coding?

- [ ] **Data Prep:** Focus on "Symbolism" (Set B).
- [ ] **Analysis Script (`analyze_symbolism.py`):**
    -   **Sentiment Contrast:** Compare sentiment scores for "The Man" vs. "The Temple".
    -   **Gender Split:** Analyze if Men vs. Women describe these icons differently.
- [ ] **Output:** `reports/module_4_symbolism.md`

## 6. Module 5: The "Other" in Utopia (Radical Inclusion)
*Research Question:* How does the minority experience differ in Black Rock City?

- [ ] **Data Prep:** Filter "Diversity" (Set K/F) for respondents indicating "Yes" to "Does your appearance impact interactions?"
- [ ] **Analysis Script (`analyze_diversity.py`):**
    -   **Pain Point Identification:** Cluster the "Negative" experiences for this group.
    -   **Code Switching:** Analyze mentions of modifying behavior/appearance.
- [ ] **Output:** `reports/module_5_diversity.md`

## 7. Final Synthesis
- [ ] **Compile:** Aggregate all module reports into a master `FINAL_ANALYSIS_REPORT.md`.
- [ ] **Executive Summary:** Write a "Field Notes" ethnographic summary based on the data.
