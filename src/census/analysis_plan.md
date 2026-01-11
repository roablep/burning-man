# Burning Man Field Notes Analysis Plan

This document outlines a mixed-method approach to analyzing the Burning Man Field Notes dataset (2024 & 2025). The goal is to move beyond simple transcription to deep semantic understanding, identifying key themes, patterns across demographics, and anomalies.

## 1. The "Who": Demographic Normalization
Before analyzing *what* participants said, we must clean and structure *who* they are. The first four questions of every survey are demographic.

*   **Goal:** Convert free-text demographic fields into structured, queryable data.
*   **Fields to Normalize:**
    *   **Age (Q1):** Parse strings ("34", "34 years old", "30s") into Integers.
    *   **Gender (Q2):** Map various free-text descriptions (e.g., "M", "Male", "He/Him", "Cis Male") into standard categories (M, F, NB, Fluid, etc.) while preserving the original nuance in a separate column.
    *   **Location (Q3):** Parse "City, State, Country" into standardized `Country` and `Region` fields to enable geographical analysis (e.g., "US vs. International").
    *   **Tenure (Q4):** Convert "Virgin", "First time", "10+", "15" into a numeric `Burn_Count` and a categorical `Burn_Status` (Virgin, Sophomore, Veteran, Elder).

## 2. The "What": Semantic Clustering (Thematic Analysis)
We will use Natural Language Processing (NLP) to discover the underlying themes in the open-ended answers.

*   **Technique:** LLM-Based Theme Extraction
*   **Process:**
    1.  **Select a Target:** Focus on high-value open-ended columns (e.g., *Transformation Q5: "Did Burning Man change you?"*).
    2.  **Extract:** Use an LLM to identify 1-3 distinct themes per response.
    3.  **Aggregate:** Count theme frequencies within demographic cohorts.
    4.  **Refine:** Use LLM to consolidate overlapping themes (e.g., "Community" and "Connection" -> "Social Bonds").
*   **Outcome:** A quantitative view of qualitative data (e.g., "40% of Virgins cited 'Community' as their primary transformation factor").

## 3. The "How": Sentiment & Emotion Analysis
Understanding the *tone* of the responses, particularly for topics like "Survival" and "Experiences."

*   **Technique:** LLM Sentiment Scoring
*   **Process:**
    *   Apply sentiment analysis (Range: -1.0 to +1.0) via LLM prompt to narrative answers.
    *   Correlate sentiment with demographics (e.g., "Do older burners have more positive 'Survival' experiences than younger ones?").
*   **Outcome:** Identification of "Pain Points" (clusters of negative sentiment) versus "Joy Points."

## 4. Anomaly Detection & Outliers
Finding the stories that don't fit the curve.

*   **Technique:** Outlier Analysis
*   **Process:**
    *   **Demographic Outliers:** (e.g., 70+ year old Virgins, International Virgins).
    *   **Semantic Outliers:** Responses that are statistically distant from all major clusters (the unique, singular experiences).
*   **Outcome:** These outliers are often the most compelling "Field Notes" stories for publication or qualitative review.

---

# Theoretical Research Framework

Drawing on Anthropology, Sociology, and Psychology, we can ask questions that go beyond "What did you bring?" and get to "Who are we when the rules change?"

## 1. The "Pilgrim's Progress": The Arc of Disenchantment & Re-enchantment
*Discipline: Developmental Psychology / Anthropology*

**The Theory:** Victor Turner’s concept of *Liminality* suggests that initiates go through a phase of ambiguity before re-entering society. But does this effect diminish with repetition? Does the "Virgin" experience a radical break, while the "Veteran" experiences a routine?

*   **The Query:** How does the narrative of "Transformation" (Question Set A) evolve as `Burn_Count` increases?
*   **Hypotheses to Test:**
    *   **The Virgin Peak:** Virgins use language of *shock, awe, and total ego-death*.
    *   **The Sophomore Slump:** 2nd/3rd timers express *cynicism, logistical focus, or disappointment*.
    *   **The Elder Wisdom:** 10+ year veterans shift from "Self-Transformation" to "Service/Stewardship".
*   **Methodology:** 
    *   Normalize `Burn_Count`.
    *   Segment respondents into cohorts: Virgin (1), Sophomore (2-3), Veteran (4-9), Elder (10+).
    *   **New Step:** Perform specific *Linguistic Analysis* via LLM to count pronoun usage (I/Me vs We/Us) to test the ego-death hypothesis directly.
    *   Extract LLM-based themes for each cohort.

## 2. Maslow’s Inverted Pyramid: Survival vs. Self-Actualization
*Discipline: Psychology / Human Factors*

**The Theory:** Maslow suggests we need physiological safety before we can achieve self-actualization. Burning Man *removes* physiological safety (heat, dust, thirst) yet participants claim high self-actualization.

*   **The Query:** Is there a correlation between physical struggle and emotional breakthrough?
*   **Hypotheses to Test:**
    *   Do people who list "hardships" (heat, dust, hunger) in *Survival* or *Experiences* question sets *also* report higher degrees of "Wonder" or "Transformation"?
    *   *The "Ordeal" Hypothesis:* Does the severity of the struggle predict the depth of the epiphany?
*   **Methodology:**
    *   **Cross-Reference Step:** Link `Transformation` respondents to their responses in `Survival` or `Experiences` sets (if identifiable/linked) or analyze the *internal* narrative of transformation for mentions of hardship.
    *   Use LLM to detect "Hardship" and "Breakthrough" concepts within the same narrative.
    *   Calculate the conditional probability: P(Breakthrough | Hardship).

## 3. The Mask vs. The Mirror: Identity & The "Default World"
*Discipline: Sociology (Erving Goffman)*

**The Theory:** Goffman argues we perform a "front stage" self for society. In the Default World, our "costume" is a suit/uniform (conformity). At Burning Man, the "costume" is the self-expression.

*   **The Query:** When participants answer `Costumes_Q5` ("Why do you wear costumes?"), do they describe it as *putting on a mask* (hiding) or *taking off a mask* (revealing the true self)?
*   **Hypotheses to Test:**
    *   **The Revelation Paradox:** People define their "Costume" as their "True Self" and their "Default Clothes" as the "Costume."
    *   **The Interaction Effect:** Does `Costumes_Q7` (Interaction effects) show that "Radical Self Expression" actually leads to *more* or *less* social friction?
*   **Methodology:**
    *   LLM Theme Extraction on `Costumes_Q5`.
    *   Look for opposing keyword clusters: "Hide/Disguise" vs. "Reveal/Express/True".
    *   Cross-reference with `Diversity_Q6` (Modifying appearance in default world).

## 4. Sacred vs. Profane: The Man vs. The Temple
*Discipline: Religious Studies / Sociology of Religion (Durkheim)*

**The Theory:** Durkheim distinguished between the Sacred (set apart, forbidden, awe-inspiring) and the Profane (mundane). Black Rock City creates two distinct axes of the Sacred: The Man (Celebration/Dionysian) and The Temple (Grief/Apollonian).

*   **The Query:** How does the semantic distance between "The Man" and "The Temple" differ?
*   **Hypotheses to Test:**
    *   **The Gender Split:** Do Men and Women interpret these symbols differently? (e.g., Is the Temple more gender-neutral in sentiment, while the Man is coded more masculine/patriarchal/authoritarian?)
    *   **The Emotional Barometer:** Is the Temple associated exclusively with "Grief" and "Loss," or is there a shift toward "Hope"?
*   **Methodology:**
    *   Use LLM to extract primary emotions and sentiment scores for `Symbolism_Q6` (The Man) and `Symbolism_Q7` (The Temple).
    *   **New Step:** Segment analysis by Gender (M vs F vs NB).
    *   Compare the *distribution* of emotions (e.g., "Grief" frequency) between Man and Temple.

## 5. The "Other" in Utopia: Radical Inclusion vs. Structural Reality
*Discipline: Critical Race Theory / Sociology*

**The Theory:** Burning Man posits "Radical Inclusion," yet it is a temporary city built largely by a specific demographic. How does the minority experience differ in a "Utopia"?

*   **The Query:** Do respondents who self-identify as POC or non-binary in `Diversity_Q5` report different "Survival" strategies or "Transformation" triggers?
*   **Hypotheses to Test:**
    *   **The Friction of Utopia:** Do marginalized groups report higher rates of *modifying their behavior* (`Diversity_Q6/Q8`) to fit in, even in a place designed for "Radical Self-Expression"?
    *   **Code-Switching:** How often does the concept of "Code-Switching" appear in the text for different demographics?
*   **Methodology:**
    *   Filter respondents based on `Diversity_Q5` keywords (e.g., "Black", "Asian", "Trans", "Queer").
    *   **New Step:** Compare their *general sentiment* across all questions against the baseline (White/Cis-Male) if data allows linking, OR strictly analyze the sentiment within the Diversity question set itself.
    *   Analyze `Diversity_Q8` (Modifying appearance on playa) for themes of "Safety" vs. "Celebration."

## Proposed Roadmap for Analysis Code

1.  **Script 1: `normalize_demographics.py`** - Clean Q1-Q4 to create the foundational "Person Object" for each row.
2.  **Script 2: `analyze_transformation.py`** - Module 1: Tenure cohorts + Pronoun analysis + Theme extraction.
3.  **Script 3: `analyze_survival.py`** - Module 2: Hardship vs Breakthrough correlation within narratives.
4.  **Script 4: `analyze_symbolism.py`** - Module 4: Emotion distribution by Gender for Man vs Temple.
5.  **Script 5: `analyze_diversity.py`** - Module 5: Code-switching and sentiment analysis for marginalized groups.
6.  **Script 6: `synthesize_report.py`** - Aggregate findings into a final markdown report.
