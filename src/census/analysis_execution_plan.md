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

- [x] **Module 1: The "Pilgrim's Progress" (Transformation)**
*Research Question:* How does the narrative of transformation evolve from Virgin to Veteran?

- [x] **Data Prep:** Filter "Transformation" (Set A) responses by Cohort (Virgin, Sophomore, Veteran, Elder).
- [x] **Analysis Script (`analyze_transformation.py`):**
    -   [x] **Keyword Extraction:** Identify top unique words for Virgins vs. Veterans.
    -   [x] **LLM Analysis:** Ask Gemini to summarize the "Core Driver of Change" for a sample of each cohort.
- [x] **Hypothesis Test:** Verify if "Ego Death" is a Virgin trait and "Service" is a Veteran trait.
- [x] **Output:** `reports/module_1_transformation.md`

- [x] **Module 2: Maslow’s Inverted Pyramid (Survival vs. Epiphany)**
*Research Question:* Does physical hardship correlate with emotional breakthrough?

- [x] **Data Prep:** Join "Survival" (Set J/B) and "Experiences" (Set H/C) data.
- [x] **Analysis Script (`analyze_survival.py`):**
    -   [x] **Hardship Index:** Score responses based on mentions of "Mud", "Dust", "Heat", "Hunger".
    -   [x] **Epiphany Index:** Score "Transformation" responses for "Life Changing" sentiment.
    -   [x] **Correlation:** Plot/Check overlap. Do those with high Hardship scores have high Epiphany scores?
- [x] **Output:** `reports/module_2_survival.md`

- [x] **Module 3: The Mask vs. The Mirror (Identity)**
*Research Question:* Is the costume a mask (hiding) or a mirror (revealing)?

- [x] **Data Prep:** Focus on "Costumes" (Set F) and "Diversity" (Set K/F).
- [x] **Analysis Script (`analyze_identity.py`):**
    -   [x] **Semantic Classification:** Classify "Why do you wear costumes?" answers into:
        -   *Type A: Hiding/Blending In*
        -   *Type B: Revealing/Authenticity*
        -   *Type C: Play/Fun*
    -   [x] **Cross-Reference:** Check if *Type B* respondents report higher "Positive Interactions" in Diversity Q7.
- [x] **Output:** `reports/module_3_identity.md`

- [x] **Module 4: Sacred vs. Profane (Symbolism)**
*Research Question:* How do "The Man" and "The Temple" differ in emotional coding?

- [x] **Data Prep:** Focus on "Symbolism" (Set B).
- [x] **Analysis Script (`analyze_symbolism.py`):**
    -   [x] **Sentiment Contrast:** Compare sentiment scores for "The Man" vs. "The Temple".
    -   [x] **Gender Split:** Analyze if Men vs. Women describe these icons differently.
- [x] **Output:** `reports/module_4_symbolism.md`

- [x] **Module 5: The "Other" in Utopia (Radical Inclusion)**
*Research Question:* How does the minority experience differ in Black Rock City?

- [x] **Data Prep:** Filter "Diversity" (Set K/F) for respondents indicating "Yes" to "Does your appearance impact interactions?"
- [x] **Analysis Script (`analyze_diversity.py`):**
    -   [x] **Pain Point Identification:** Cluster the "Negative" experiences for this group.
    -   [x] **Code Switching:** Analyze mentions of modifying behavior/appearance.
- [x] **Output:** `reports/module_5_diversity.md`

## 7. Final Synthesis
- [ ] **Compile:** Aggregate all module reports into a master `FINAL_ANALYSIS_REPORT.md`.
- [ ] **Executive Summary:** Write a "Field Notes" ethnographic summary based on the data.
