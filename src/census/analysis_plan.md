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

*   **Technique:** Text Embeddings + Clustering
*   **Process:**
    1.  **Select a Target:** Focus on high-value open-ended columns (e.g., *Transformation Q5: "Did Burning Man change you?"* or *Sustainability Q6: "Sustainable practices observed"*).
    2.  **Embed:** Generate vector embeddings for every response using a model like `text-embedding-3-small` or a local Sentence Transformer.
    3.  **Cluster:** Use algorithms like **K-Means** or **HDBSCAN** to group semantically similar answers.
    4.  **Label:** Use an LLM to generate a descriptive "Theme Name" for each cluster (e.g., "Restored Faith in Humanity" vs. "Personal Confidence").
*   **Outcome:** A quantitative view of qualitative data (e.g., "40% of Virgins cited 'Community' as their primary transformation factor").

## 3. The "How": Sentiment & Emotion Analysis
Understanding the *tone* of the responses, particularly for topics like "Survival" and "Experiences."

*   **Technique:** Sentiment Scoring
*   **Process:**
    *   Apply sentiment analysis (Range: -1.0 to +1.0) to narrative answers.
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
    *   **The Sophomore Slump:** 2nd/3rd timers express *cynicism, logistical focus, or disappointment* (the "magic" is gone, replaced by the reality of the dust).
    *   **The Elder Wisdom:** 10+ year veterans shift from "Self-Transformation" to "Service/Stewardship" (e.g., "I come to build for others").
*   **Methodology:** 
    *   Normalize `Burn_Count`.
    *   Segment respondents into cohorts: Virgin (1), Sophomore (2-3), Veteran (4-9), Elder (10+).
    *   Perform Sentiment Analysis on `Transformation_Q5` ("Did Burning Man change you?").
    *   Extract TF-IDF Keywords for each cohort to see linguistic shifts (e.g., "Me/I" vs. "We/Us").

## 2. Maslow’s Inverted Pyramid: Survival vs. Self-Actualization
*Discipline: Psychology / Human Factors*

**The Theory:** Maslow suggests we need physiological safety before we can achieve self-actualization. Burning Man *removes* physiological safety (heat, dust, thirst) yet participants claim high self-actualization.

*   **The Query:** Is there a correlation between physical struggle and emotional breakthrough?
*   **Hypotheses to Test:**
    *   Do people who list "hardships" (heat, dust, hunger) in `Survival_Q6` (Surprising things) or `Experiences_Q5` (Negative experiences) *also* report higher degrees of "Wonder" or "Transformation"?
    *   *The "Ordeal" Hypothesis:* Does the severity of the struggle predict the depth of the epiphany?
*   **Methodology:**
    *   Code `Experiences_Q5` (Negative) for physical hardship markers (dust, heat, hunger).
    *   Correlate the presence of these markers with the Sentiment Score of `Transformation_Q5`.
    *   Look for the "complaint-to-breakthrough" ratio.

## 3. The Mask vs. The Mirror: Identity & The "Default World"
*Discipline: Sociology (Erving Goffman)*

**The Theory:** Goffman argues we perform a "front stage" self for society. In the Default World, our "costume" is a suit/uniform (conformity). At Burning Man, the "costume" is the self-expression.

*   **The Query:** When participants answer `Costumes_Q5` ("Why do you wear costumes?"), do they describe it as *putting on a mask* (hiding) or *taking off a mask* (revealing the true self)?
*   **Hypotheses to Test:**
    *   **The Revelation Paradox:** People define their "Costume" as their "True Self" and their "Default Clothes" as the "Costume."
    *   **The Interaction Effect:** Does `Costumes_Q7` (Interaction effects) show that "Radical Self Expression" actually leads to *more* or *less* social friction?
*   **Methodology:**
    *   Semantic Clustering on `Costumes_Q5`.
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
    *   Generate Embeddings for `Symbolism_Q6` (The Man) and `Symbolism_Q7` (The Temple).
    *   Calculate "Semantic Distance" between the two sets of answers.
    *   Break down sentiment by Gender categories.

## 5. The "Other" in Utopia: Radical Inclusion vs. Structural Reality
*Discipline: Critical Race Theory / Sociology*

**The Theory:** Burning Man posits "Radical Inclusion," yet it is a temporary city built largely by a specific demographic. How does the minority experience differ in a "Utopia"?

*   **The Query:** Do respondents who self-identify as POC or non-binary in `Diversity_Q5` report different "Survival" strategies or "Transformation" triggers?
*   **Hypotheses to Test:**
    *   **The Friction of Utopia:** Do marginalized groups report higher rates of *modifying their behavior* (`Diversity_Q6/Q8`) to fit in, even in a place designed for "Radical Self-Expression"?
    *   **Code-Switching:** How often does the concept of "Code-Switching" appear in the text for different demographics?
*   **Methodology:**
    *   Filter respondents based on `Diversity_Q5` keywords (e.g., "Black", "Asian", "Trans", "Queer").
    *   Compare their Sentiment Scores in `Experiences_Q5` (Negative) against the baseline (White/Cis-Male).
    *   Analyze `Diversity_Q8` (Modifying appearance on playa) for themes of "Safety" vs. "Celebration."

## Proposed Roadmap for Analysis Code

1.  **Script 1: `normalize_demographics.py`** - Clean Q1-Q4 to create the foundational "Person Object" for each row.
2.  **Script 2: `cluster_themes.py`** - Generate embeddings and clusters for selected Question columns to answer "The What".
3.  **Script 3: `hypothesis_tester.py`** - Specifically run correlations (e.g., Tenure vs. Sentiment) to answer "The Why".
4.  **Script 4: `report_generator.py`** - output a markdown report summarizing the findings.