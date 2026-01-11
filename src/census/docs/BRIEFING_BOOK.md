# The Burning Man Field Notes Project
## A Living Ethnography of Temporary Autonomous Zones (2024-2025)

> *"We are the archaeologists of our own ephemeral city, collecting the whispers of transformation before the dust settles and the playa erases all traces."*

---

## Executive Summary

This project represents a unique **ethnographic field study** conducted at Burning Man 2024 and 2025, capturing handwritten responses to deep philosophical, sociological, and practical questions from participants during the event. Using physical journals placed strategically across Black Rock City, we gathered **1,797 total responses** (1,658 in 2024, 139 in 2025) spanning 13 thematic question sets.

**What makes this dataset extraordinary:**
- **Unfiltered immediacy**: Participants wrote responses while *in the experience*, not months later through rose-tinted memory
- **Handwritten authenticity**: The raw, visceral nature of pen-on-paper in a dusty, challenging environment
- **Philosophical depth**: Questions ranged from survival logistics to the boundaries of humanity and consciousness
- **Temporal capture**: Responses frozen in the liminal space of Black Rock City, before reintegration into the "default world"

This is not survey data. This is **ethnographic testimony from a temporary society** that dissolves itself every year.

---

## The Burning Question: What Are We Actually Studying?

At its core, this project investigates:

### Primary Research Domains

1. **Transformation & Liminality**
   How does a week-long experiment in radical self-reliance and communal living alter human consciousness? Is the "Virgin" experience fundamentally different from the "Elder" Burner?

2. **Identity & Performance**
   In a place where costumes become "more real" than everyday clothes, what does authenticity mean? Are participants hiding behind masks or revealing their true selves?

3. **Survival vs. Transcendence**
   Does physical hardship (dust, heat, scarcity) *catalyze* or *inhibit* spiritual breakthrough? Testing Maslow's hierarchy in extremis.

4. **Community & The Other**
   How does "Radical Inclusion" work in practice? Do marginalized identities experience utopia differently than the majority?

5. **Symbol & Ritual**
   What do The Man (celebration/destruction) and The Temple (grief/healing) mean to different demographics? How does ritual create shared meaning?

6. **The Default World**
   Can temporary transformation become permanent change? Which of the Ten Principles survive reentry?

### The Meta-Question Underneath Everything

**"Who are we when the rules change?"**

Burning Man creates a temporary autonomous zone where capitalism, hierarchy, and spectacle are theoretically suspended. This dataset lets us measure whether the rhetoric matches the lived experience.

---

## Methodology: From Dust to Data

### Phase 1: Data Collection (On-Playa)

**The Instrument**: Physical journals with printed question sets
- Placed at camps, art installations, and common areas
- Participants self-selected which question set to answer
- No compensation, no coercion—pure voluntary participation
- Questions visible upfront (transparency over random assignment)

**Years Collected**:
- **2024**: 13 question sets (A-M), 1,658 responses
- **2025**: 6 question sets (A-F), 139 responses

**The Questions** (see `src/census/data/question-set-{year}.md` for full instruments):

| Set | Theme | Key Questions |
|-----|-------|--------------|
| **A** | Transformation | Did Burning Man change you? How? |
| **B** | Symbolism (2024) / Survival (2025) | What does The Man/Temple mean? / What do you bring to survive? |
| **C** | Emotions (2024) / Emotions & Experiences (2025) | What made you laugh, cry, wonder? |
| **D** | Boundaries of Humanity | What separates humans from animals/AI? |
| **E** | Dancing/Singing (2024) / Relationships (2025) | How does music/movement feel? / Playa love vs. default love? |
| **F** | Costumes (2024) / Diversity (2025) | Why do you wear costumes? / Does identity affect interactions? |
| **G-M** | (2024 only) | Drinking/Smoking, Relationships, Survival, Diversity, Beyond BRC, Sustainability |

**All question sets begin with the same 4 demographic questions**:
1. Age
2. Gender
3. Location (default world residence)
4. Burning Man tenure (number of burns)

### Phase 2: Image Extraction & Transcription

**Technical Pipeline**:

```
Physical Journals (HEIC/JPG photos)
         ↓
[img_extract.py / img_extract_async.py]
  • Google Gemini Vision API (gemini-2.0-flash-lite)
  • HEIC format handling (iPhone photos)
  • OCR of handwritten text
  • Safety settings disabled (some responses contain mature themes)
         ↓
Raw CSV with "Q1: answer | Q2: answer | ..." format
         ↓
[parse_questions.py]
  • Regex parsing of Q&A structure
  • Handling overflow (answers that span multiple questions)
         ↓
[clean_columns.py]
  • Merge fragmented answers
  • Standardize column structure
         ↓
Parsed CSV (one column per question)
```

**Output Files** (see `src/census/data/`):
- `{year}-field-note-transcriptions.csv` (raw transcription)
- `{year}-field-note-transcriptions-parsed.csv` (Q&A structured)
- `{year}-field-note-transcriptions-cleaned.csv` (overflow merged)
- `{year}-field-note-transcriptions-normalized.csv` (demographics processed)

### Phase 3: Demographic Normalization

**Challenge**: Free-text demographic responses are wildly inconsistent:
- Age: "34", "34 years old", "30s", "thirty four"
- Gender: "M", "Male", "He/Him", "Cis Male", "Masc", "Fluid"
- Location: "SF", "San Francisco, CA", "Bay Area", "California"
- Tenure: "Virgin", "First time", "10+", "15 burns"

**Solution** (`normalize_demographics.py`):

| Field | Normalization Strategy | Output |
|-------|------------------------|--------|
| **Age (Q1)** | Extract first numeric match, filter 0-110 range | `Norm_Age` (integer) |
| **Gender (Q2)** | Map to M/F/NB/O/U with keyword matching | `Norm_Gender` (category) |
| **Location (Q3)** | Region clustering (Local/West, US Other, International) | `Norm_Region` (category) |
| **Tenure (Q4)** | Extract numeric burn count + categorize | `Norm_Burn_Count` (int), `Burn_Status` (Virgin/Sophomore/Veteran/Elder) |

**Burn Status Taxonomy**:
- **Virgin**: 1 burn (first-timers)
- **Sophomore**: 2-3 burns (the "slump" phase)
- **Veteran**: 4-9 burns (experienced burners)
- **Elder**: 10+ burns (the architects and stewards)

### Phase 4: Analysis & Thematic Extraction

**Current Analytical Pipeline** (`analysis_utils.py`):

```python
# Shared utilities for all analysis modules
- load_data(year, survey_type): Load normalized CSV
- batch_process_with_llm(items, prompt): Async Gemini processing
  • Automatic caching (avoids re-running expensive API calls)
  • Rate limiting (1s delay between requests)
  • Error handling
- save_report(filename, content): Export markdown reports
```

**Analysis Modules Completed**:

1. **Module 1: Transformation by Tenure** (`analyze_transformation.py`)
   - Theme extraction using LLM (Gemini 2.0 Flash Lite)
   - Cohort comparison (Virgin vs. Sophomore vs. Veteran vs. Elder)
   - Output: `reports/module_1_transformation.md`

2. **Module 2: Survival as Catalyst** (`analyze_survival.py`)
   - Keyword detection for hardship vs. breakthrough
   - Testing "The Ordeal Hypothesis"
   - Output: `reports/module_2_survival.md`

3. **Basic Demographic Statistics** (`generate_basic_stats.py`)
   - Age, gender, region, tenure histograms
   - Output: `src/census/reports/basic_stats_report.md`

---

## Findings to Date: What the Dust Revealed

### Demographic Profile (2024, n=1,658)

- **Average Age**: 39.6 years (median 37)
- **Gender Split**: Nearly perfect balance (49% M, 42% F, 2% NB, 20% Other/Nuanced)
- **Burner Tenure**:
  - 29% Virgins (first burn)
  - 26% Sophomores (2-3 burns)
  - 23% Veterans (4-9 burns)
  - 11% Elders (10+)
  - Average: 13 burns
- **Geographic Origin**:
  - 45% Local/West (CA, NV)
  - 45% US Other
  - 5% International
  - 7% Unknown

### Demographic Profile (2025, n=139)

- **Average Age**: 38.1 years (median 39)
- **Higher Tenure**: Average 20.4 burns (more experienced sample)
- **Similar Gender Balance**: 45% M, 42% F, 2% NB, 22% Other
- **More Local**: 54% Local/West vs. 55% US Other

**Observation**: 2025 sample skews toward more experienced burners (Elders: 9% vs. 11%) and locals, suggesting journal placement or camp demographics influenced who responded.

### Module 1: The Pilgrim's Progress (Transformation by Tenure)

**Research Question**: Does the transformation narrative evolve from "Virgin shock" to "Elder service"?

**Key Findings**:

| Cohort | Top Themes (from LLM analysis) | Interpretation |
|--------|-------------------------------|----------------|
| **Virgin** | No Change, Anticipation, Perspective, Impact, Uncertainty | *Mixed signals*—some Virgins answering *during* their first burn reported "no change yet," showing the immediacy of data collection. Anticipation dominates. |
| **Sophomore** | Connection, Self-Expression, Idealism, Empathy, Disillusionment | *The Sophomore Slump is REAL*—themes shift from individual transformation to relational dynamics. First mentions of "Disillusionment." |
| **Veteran** | Creativity, Acceptance, Connection, Relationships, Awareness | *Maturation*—focus on skills (Creativity), community bonds, and self-awareness. Less ego, more integration. |
| **Elder** | Creativity, Community, Relationships, Openness, Generosity | *Stewardship Mode*—shift from "what Burning Man did for me" to "what I bring to Burning Man." Service-oriented language. |

**Representative Voices**:

- **Virgin**: *"I'm still navigating my 1st BURN - BUT I feel home partying with you all... 'joy as an act of resistance'"*
  → Emotional overwhelm, present-tense processing

- **Sophomore**: *"I realized that the reason people came here can't be put into words. I had a spiritual awareness with the right people."*
  → Grasping for meaning beyond the describable

- **Elder**: *"The people / community is the way I wish the default world could be. I feel free, happy; anything is possible. Pure magic exists here."*
  → Fully internalized the ethos

**Theoretical Validation**: The data **partially supports** Turner's liminality thesis—Virgins do express more disorientation/awe, while Elders show integration and service. However, the "Sophomore Slump" is an unexpected finding worthy of deeper investigation.

### Module 2: The Ordeal as Catalyst (Survival vs. Epiphany)

**Research Question**: Does physical hardship correlate with emotional breakthrough?

**Findings**: Only **2 participants** (out of 131 multi-column narratives analyzed) explicitly connected physical struggle to personal growth.

**Interpretation**:
- **Hypothesis mostly rejected**: Burners do NOT frame their transformation in terms of overcoming physical adversity
- **Alternative theory**: The transformation is *despite* the hardship, not *because* of it
- **OR**: Physical struggle is so normalized on playa that it's invisible (like water to fish)

**Critical Gap**: Need sentiment analysis on Survival vs. Transformation columns to test correlation more rigorously.

---

## Theoretical Frameworks: The Intellectual Scaffolding

The `analysis_plan.md` proposes five major theoretical lenses:

### 1. The Pilgrim's Progress (Victor Turner - Liminality)
**Discipline**: Anthropology, Developmental Psychology

**Core Idea**: Initiates pass through three phases:
1. **Separation** (leaving default world)
2. **Liminality** (ambiguous, transformative state)
3. **Re-incorporation** (returning changed)

**Test**: Does the transformation narrative evolve across burn count?
- Virgin = Pure liminality (ego death, shock)
- Sophomore = Re-evaluation (cynicism, disappointment)
- Veteran = Integration (balance between worlds)
- Elder = Service (building the liminal space for others)

**Status**: ✅ Partially validated (Module 1)

### 2. Maslow's Inverted Pyramid (Psychology)
**Core Idea**: Burning Man *removes* physiological safety (water, shelter, comfort) yet participants report self-actualization. Does hardship *enable* or *hinder* transcendence?

**Test**: Correlate mentions of physical struggle with sentiment in transformation responses.

**Status**: ⚠️ Preliminary analysis (Module 2) suggests hardship is NOT explicitly credited

### 3. The Mask vs. The Mirror (Erving Goffman - Dramaturgy)
**Discipline**: Sociology

**Core Idea**: In default world, we perform a "front stage" self (suit/uniform). At Burning Man, the costume becomes the "real" self.

**Test**: Do participants describe costumes as:
- **Type A**: Hiding/disguise (putting on a mask)
- **Type B**: Revealing/authenticity (taking off a mask)
- **Type C**: Play/exploration (no mask, just fun)

**Status**: ⏳ Pending (Costume question set analysis)

### 4. Sacred vs. Profane (Émile Durkheim - Sociology of Religion)
**Core Idea**: The Man (Dionysian celebration/destruction) and The Temple (Apollonian grief/healing) represent dual sacred axes.

**Test**:
- Semantic distance between Man and Temple responses
- Gender differences in symbolism interpretation
- Sentiment polarity (joy vs. sorrow)

**Status**: ⏳ Pending (Symbolism question set analysis)

### 5. The "Other" in Utopia (Critical Race Theory / Queer Theory)
**Core Idea**: Burning Man claims "Radical Inclusion," but lived experience may differ for marginalized identities.

**Test**:
- Do POC/LGBTQ+ respondents report different "friction" levels?
- Code-switching analysis (modifying behavior to fit in)
- Sentiment comparison (marginalized vs. majority experience)

**Status**: ⏳ Pending (Diversity question set analysis)

---

## Research Roadmap: The Unburned Questions

### Completed Analyses ✅
- [x] Demographic normalization
- [x] Basic descriptive statistics
- [x] Transformation by tenure (Module 1)
- [x] Survival as catalyst (Module 2)

### High-Priority Analyses 🔥

1. **Identity & Costume Analysis** (Module 3)
   - LLM classification: Hiding vs. Revealing vs. Play
   - Cross-reference with Diversity Q7 (interaction effects)
   - Gender differences in costume motivations

2. **Symbolism & Ritual** (Module 4)
   - Semantic clustering of Man vs. Temple responses
   - Sentiment analysis (celebration vs. grief)
   - Demographic segmentation (age, gender, tenure)

3. **Diversity & Inclusion** (Module 5)
   - Filter by self-identified marginalized groups
   - Pain point clustering (negative experiences)
   - Code-switching keyword detection

4. **Emotions & Wonder** (Combined C/E Analysis)
   - What triggers laughter, tears, and awe?
   - Positive vs. negative experience drivers
   - Dancing/singing as emotional regulation

5. **Relationships & Intimacy** (Module 6)
   - Playa love vs. default world love
   - Committed relationships under stress
   - Polyamory and boundary negotiation themes

### Advanced Methodological Improvements 🚀

1. **Semantic Embeddings + Clustering**
   - Use `text-embedding-3-small` or Sentence Transformers
   - HDBSCAN or K-Means for theme discovery
   - Dimensionality reduction (UMAP) for visualization

2. **Sentiment Scoring**
   - Apply to all open-ended responses
   - Correlate with demographics
   - Identify "joy points" vs. "pain points"

3. **Anomaly Detection**
   - Demographic outliers (e.g., 70+ year-old Virgins)
   - Semantic outliers (responses distant from all clusters)
   - These are often the best "field notes" stories

4. **Longitudinal Analysis** (2024 vs. 2025)
   - Did the 2024 mud year affect narratives?
   - Theme evolution over time
   - Pandemic recovery (if pre-2024 data exists)

5. **N-gram & TF-IDF Analysis**
   - Unique vocabulary by cohort (Virgin "I/me" vs. Elder "we/us")
   - Keyword frequency shifts
   - Linguistic markers of transformation

### Deliverables for Future Work 📊

- **Academic Paper**: "Liminality and Transformation in Temporary Autonomous Zones: A Mixed-Methods Analysis of Burning Man Field Notes (2024-2025)"
- **Data Visualization Dashboard**: Interactive exploration of themes, demographics, and correlations
- **Ethnographic Compendium**: Curated "greatest hits" of responses (with consent)
- **Methodology Whitepaper**: How to do ethnography at ephemeral events

---

## Creative Research Directions: Provocative Angles to Explore

Beyond the standard analyses, here are five high-impact research directions that could yield surprising insights:

### 1. The "Sophomore Slump" Deep Dive 📉

**What We've Seen**: Module 1 analysis revealed that 2nd/3rd-year burners express themes of "Disillusionment" alongside "Connection"—a stark contrast to Virgin "Anticipation" and Elder "Service."

**Research Question**: *"Is there a predictable arc of disenchantment → re-enchantment across the Burner lifecycle?"*

**Methodology**:
- Sentiment analysis on Transformation responses by exact burn count (not just cohorts)
- Plot sentiment scores (1st burn → 20th burn) to visualize the curve
- Identify the "trough" point: Is it burn #2? #3? #5?
- Qualitative theme extraction: What words appear in the slump that disappear later?

**Why It Matters**: This challenges the mythos of Burning Man as universally transformative. If there's a predictable disillusionment phase, the community should address it (or acknowledge it as part of the journey).

**Hypothesis**: The slump occurs when:
- The novelty wears off (not a Virgin anymore)
- Reality intrudes (logistics, dust, exhaustion)
- But the "Elder wisdom" hasn't developed yet (haven't found their role in the community)

### 2. The Language of Liminality: "I" vs. "We" 🗣️

**Observation**: Elders talk more about "community" and "service." Virgins focus on personal transformation.

**Research Question**: *"Do Burners linguistically shift from individual to collective identity as tenure increases?"*

**Methodology**:
- TF-IDF analysis by cohort on Transformation responses
- Count pronoun usage: "I/me/my/mine" vs. "we/us/our/ours"
- Track keywords:
  - **Virgin-specific**: "myself", "first time", "overwhelmed", "discovering"
  - **Elder-specific**: "contribute", "teach", "build", "gift", "steward"
- Sentiment + self-reference correlation: Are self-focused responses more positive or negative?

**Why It Matters**: If we can measure the linguistic shift, we can:
- Quantify the "ego death" phenomenon
- Predict when someone becomes a "true Burner" (not by years, but by language)
- Design interventions to accelerate the shift (if desirable)

**Bonus Analysis**: Apply this to the "Beyond BRC" question set—do people who use collective language also report taking principles home?

### 3. The Boundaries of Humanity: Burners vs. AI in 2024-2025 🤖

**Unique Opportunity**: Question Set D asks "What distinguishes humans from AI?" during the peak of ChatGPT/AI hype (2024-2025).

**Research Question**: *"How do Burners—a community centered on radical self-expression—conceptualize human uniqueness in the age of AI?"*

**Methodology**:
- Theme clustering on Q6: "What distinguishes humans from AI?"
- Demographic splits:
  - **Tech workers** (SF/Bay Area) vs. non-tech
  - **Age cohorts**: Gen Z digital natives vs. Boomers
  - **Burn tenure**: Do veterans think differently?
- Cross-reference with Q8: "What would AI never understand?"
- Sentiment analysis: Are responses fearful, optimistic, dismissive?

**Why It Matters**: Burning Man is a *highly* tech-heavy community (lots of Silicon Valley). Their answers reveal how people who *build* AI think about human identity.

**Provocative Sub-Questions**:
- Do tech workers actually have *different* answers than artists?
- Does psychedelic use correlate with different AI perspectives? (If we have data on Set G - Drinking/Smoking)
- Do responses reference consciousness, emotions, creativity, embodiment, or something else?

### 4. Gender & The Sacred: The Man vs. The Temple ⚧️🔥

**Observation**: The Man = destruction/celebration. The Temple = healing/grief. These seem gendered.

**Research Question**: *"Are Burning Man's two central rituals coded differently by gender? Is The Man masculine and The Temple feminine?"*

**Methodology**:
- Semantic analysis on Symbolism Set B (2024):
  - Q6: "What does the Burning Man mean to you?"
  - Q7: "What does the Temple mean to you?"
- Generate embeddings for each response
- Calculate "semantic distance" between Man and Temple responses
- Segment by gender (M, F, NB, O):
  - Do men describe The Man differently than women?
  - Do women engage more with The Temple?
  - How do non-binary folks describe these symbols?
- Keyword extraction: Look for gendered language (power, softness, aggression, nurturing)

**Why It Matters**: If the central rituals *are* gendered, this has implications for:
- Whose experiences are centered in Burning Man lore
- Why some people connect more with one ritual than the other
- Whether "Radical Inclusion" extends to symbolic architecture

**Bonus Analysis**: Cross-reference with Emotions Set C—do people who cry more go to The Temple? Do people who laugh more go to The Man burn?

### 5. The Radical Inclusion Stress Test: Whose Utopia? 🌈

**Critical Question**: Burning Man claims "Radical Inclusion," but does utopia feel utopian for everyone?

**Research Question**: *"Do marginalized identities (POC, LGBTQ+, disabled, etc.) report different experiences of 'freedom' and 'inclusion' than the majority?"*

**Methodology**:
- **Identify marginalized respondents** via Diversity Set K/F:
  - Q5: Self-report of identity impact in default world
  - Keywords: "Black", "Asian", "Trans", "Queer", "disabled", "fat", etc.
- **Compare their responses** to Transformation, Experiences, and Emotions sets:
  - Do they report *more* or *less* transformation?
  - Are their negative experiences different? (harassment vs. logistics)
  - Sentiment analysis: Is their playa experience as positive as the majority?
- **Code-Switching Analysis**:
  - Q6 & Q8: Do they modify appearance/behavior on playa vs. default world?
  - Hypothesis: If radical inclusion is real, modification should *decrease* on playa
  - Counter-hypothesis: Even in "utopia," marginalized folks still modify to stay safe
- **Language of Safety**:
  - Do keywords like "safe", "unsafe", "threatening", "free" appear more in marginalized responses?

**Why It Matters**: This is the most politically charged analysis—it tests whether Burning Man's rhetoric matches reality. If marginalized folks report *more* friction on playa, that's a major finding.

**Ethical Note**: This requires sensitivity. Consider:
- Not "outing" anyone's identity without consent
- Framing as "community learning" not "gotcha journalism"
- Sharing findings with diversity/inclusion camps at BRC

---

## Technical Architecture: The Code Behind the Curtain

### File Structure
```
burning-man/
├── src/
│   └── census/
│       ├── data/
│       │   ├── {year}-field-note-transcriptions-*.csv (data pipeline outputs)
│       │   ├── question-set-{year}.md (survey instruments)
│       ├── img_extract.py (synchronous image OCR)
│       ├── img_extract_async.py (async batch processing)
│       ├── parse_questions.py (Q&A parsing)
│       ├── clean_columns.py (overflow merging)
│       ├── normalize_demographics.py (demographic standardization)
│       ├── analysis_utils.py (shared LLM/caching utilities)
│       ├── generate_basic_stats.py (histogram reports)
│       ├── analyze_transformation.py (Module 1)
│       ├── analyze_survival.py (Module 2)
│       ├── analysis_plan.md (theoretical framework)
│       ├── analysis_execution_plan.md (project management)
│       └── reports/
│           ├── basic_stats_report.md
│           ├── module_1_transformation.md
├── reports/ (top-level consolidated reports)
│   ├── module_1_transformation.md
│   ├── module_2_survival.md
├── analysis_cache/ (LLM response cache to avoid re-runs)
│   └── {hash}.json
└── BRIEFING_BOOK.md (this document)
```

### Key Technologies

| Component | Technology | Notes |
|-----------|-----------|-------|
| **Image Processing** | PIL, pillow-heif | Handles HEIC (iPhone) format |
| **OCR** | Google Gemini Vision API (gemini-2.0-flash-lite) | Handwriting transcription |
| **Data Processing** | Python `csv`, `re` modules | Parsing and normalization |
| **LLM Analysis** | Google Gemini API (async) | Theme extraction, sentiment |
| **Caching** | JSON file-based cache (MD5 hashing) | Avoids redundant API calls |
| **Statistics** | Python `statistics`, `collections.Counter` | Basic descriptive stats |

### Environment Setup

**Dependencies** (via Poetry):
```bash
poetry install  # Installs google-genai, pillow, pillow-heif, python-dotenv
```

**API Keys** (`.env` file):
```bash
GEMINI_API_KEY=your_key_here
```

**Running Analyses**:
```bash
# Normalize demographics (if raw data changes)
python src/census/normalize_demographics.py

# Generate basic stats
python src/census/generate_basic_stats.py

# Run transformation analysis (Module 1)
python src/census/analyze_transformation.py

# Run survival analysis (Module 2)
python src/census/analyze_survival.py
```

---

## Critical Reflections: What This Dataset Can (and Cannot) Tell Us

### Strengths 💪

1. **Ecological Validity**: Captured *in situ*, not retrospectively
2. **Depth Over Breadth**: Open-ended responses vs. Likert scales
3. **Handwritten Authenticity**: The physical act of writing conveys commitment
4. **Diverse Question Sets**: 13 thematic areas (2024), multidimensional view
5. **Self-Selection Reveals Values**: Who chooses to answer which questions is data itself

### Limitations ⚠️

1. **Sampling Bias**:
   - Participants self-selected into journal writing (literacy, time, introspection)
   - English-language only (excludes non-English speakers)
   - Location bias (journals placed at specific camps/areas)
   - 2025 sample much smaller and skewed toward veterans

2. **Temporal Ambiguity**:
   - We don't know *when* during the week participants answered
   - Monday Virgin responses ≠ Sunday Virgin responses
   - Cannot track transformation *within* a single burn

3. **OCR Limitations**:
   - Handwriting transcription is imperfect (see "Representative Voices" in Module 1 for garbled text)
   - Some responses may be unreadable
   - Context clues may be lost (drawings, cross-outs, margin notes)

4. **Anonymity & Honesty**:
   - Lack of identifiers means no follow-up possible
   - But also enables radical honesty (no social desirability bias)

5. **Theoretical Priors**:
   - Our question design reflects our assumptions
   - We asked about "transformation" → participants felt obligated to report it
   - Leading questions (e.g., "Did BM change you?") vs. neutral probes

### Ethical Considerations 🤔

- **Consent**: Journals had visible disclaimer that responses may be used for research
- **Anonymity**: No identifying information collected (age/gender insufficient to de-anonymize)
- **Dust & Durability**: Physical journals are fragile—did some responses get lost to the elements?
- **Power Dynamics**: Researchers are also Burners—insider/outsider status affects interpretation

### Critical Data Quality Issues 🔍

**1. The 2024 vs. 2025 Sample Disparity**

The dramatic difference in sample size (1,658 vs. 139 responses) raises important questions:

**Possible Explanations**:
- **Journal placement strategy**: Were fewer journals deployed in 2025? Were they placed at different camps?
- **The 2024 "Mud Year" trauma**: The 2024 event was impacted by rain and mud, creating an unusually challenging year. Did this:
  - *Reduce* 2025 attendance overall?
  - *Change* who came back (more veterans, fewer virgins)?
  - *Affect* engagement with reflective activities?
- **Timing effects**: Were journals available for the full week in both years? Early departure in 2025?
- **Camp/demographic clustering**: If journals were hosted by specific camps, 2025 data may reflect that camp's demographics more than the broader population

**Research Implications**:
- **Cannot compare 2024 vs. 2025 as equivalent samples**—they represent different populations
- **2025 is NOT representative** of Burning Man broadly (54% local, 20.4 average burns vs. 13.0 in 2024)
- **Within-year analyses are valid**, between-year comparisons require caution
- **Opportunity**: If placement data exists, analyze how journal location affects response demographics

**Action Items**:
- Document journal placement strategy for both years (which camps, when deployed, how advertised)
- If future data collection occurs, implement systematic placement across diverse camps
- Consider weighting 2025 data if using both years in aggregate analyses

**2. OCR Quality and Transcription Fidelity**

As seen in Module 1 "Representative Voices," some transcriptions are heavily garbled:
> *"I MINK IT'S TOO SOON TO SAY. AT TIMES & wave REFLECTOR ON THE WORMS of EMPATHY..."*

**Assessment**:
- **Minor errors** (typos, word substitutions) are acceptable for thematic analysis
- **Severe garbling** may lose critical meaning, especially for nuanced responses
- **Visual context lost**: Drawings, diagrams, cross-outs, margin notes, emphasis (underlining/caps) not captured
- **Handwriting quality variation**: Some participants have clearer handwriting than others

**Solutions**:
- **Human verification pass**: For key analyses (e.g., academic publication), manually verify a random sample (10-20%) of transcriptions
- **Confidence scoring**: If Gemini provides confidence scores, filter low-confidence transcriptions for manual review
- **Re-run critical responses**: For responses cited in papers or reports, re-transcribe with higher-quality models (GPT-4 Vision, Claude 3.5 with vision)
- **Preserve originals**: Keep image files linked to transcriptions so researchers can review originals when meaning is unclear

**Current Status**: Transcription errors are acknowledged but not systematically addressed. Consider this a limitation in findings.

**3. Temporal Metadata: The "When" Problem**

**The Issue**: We captured responses *during* the burn, but don't know *when* during the week.

**Why This Matters**:
- **Virgin on Monday**: "Did Burning Man change you?" → "Not yet, I just got here"
- **Virgin on Saturday**: "Did Burning Man change you?" → "Yes, completely, here's a novel-length answer"
- **Elder on Tuesday**: Might be in setup mode, focused on logistics
- **Elder on Sunday**: Might be in teardown mode, reflective about closure

**Current Blind Spots**:
- Cannot track transformation *within* a single burn (arrival → midweek → departure)
- Cannot control for "peak experience" timing (first night vs. last night)
- Cannot separate early-week "anticipation" from late-week "integration"

**Potential Recovery**:
- **EXIF timestamp analysis**: Check if image files contain timestamp metadata
  - Problem: Timestamps might be when photo was taken (could be days after participant wrote)
  - Solution: Cluster by image timestamp as rough proxy for journal entry time
- **Content-based temporal inference**: Use LLM to infer timing from responses
  - Keywords like "just arrived", "first night", "leaving tomorrow", "last day"
  - References to specific art burns (Man burns Saturday, Temple burns Sunday)
- **Future data collection**: Add "What day is it?" or "How many days have you been here?" to demographic questions

**Recommendation**: Acknowledge this as a limitation but consider it a feature of ecological validity—we captured the *immediate* experience, not curated retrospectives.

---

## Future AI Onboarding: How to Pick Up This Project

**If you're an AI assistant encountering this project for the first time**, here's your quick-start guide:

### Orientation Checklist ✅

1. **Read this entire briefing book** (you're doing it!)
2. **Review the theoretical frameworks** in `src/census/analysis_plan.md`
3. **Examine the question instruments**: `src/census/data/question-set-{2024|2025}.md`
4. **Check project status**: `src/census/analysis_execution_plan.md` (task tracker)
5. **Inspect the data pipeline**:
   - Raw images → Transcription CSV → Parsed CSV → Cleaned CSV → Normalized CSV
6. **Run basic stats** to understand the sample:
   ```bash
   python src/census/generate_basic_stats.py
   ```
7. **Read existing reports** in `reports/` to see what's been discovered

### Understanding the Research Philosophy

This project sits at the intersection of:
- **Quantitative rigor** (demographics, clustering, sentiment scores)
- **Qualitative depth** (themes, narratives, voices)
- **Critical theory** (interrogating power, inclusion, identity)
- **Playful creativity** (it's Burning Man—embrace the weird!)

**We are not just counting responses. We are listening to a temporary city speak.**

### Common Tasks You Might Be Asked To Do

| Task | Where to Start |
|------|----------------|
| "Analyze the Costume responses" | `src/census/data/{year}-field-note-transcriptions-normalized.csv` → Filter `Subfolder` for "Costume" → Adapt `analyze_transformation.py` template |
| "Compare 2024 vs. 2025 themes" | Load both years, segment by `Subfolder`, run comparative LLM analysis |
| "Find the most 'Elder' response" | Filter `Burn_Status == "Elder"`, sort by response length or use LLM to score "wisdom" |
| "What do people say about AI?" | `question-set-2024.md` → Set D (Boundaries of Humanity) → Analyze Q6-Q8 |
| "Visualize age vs. transformation sentiment" | Normalize demographics → Apply sentiment scoring → Create scatter plot |
| "Is there a 'Sophomore Slump'?" | Module 1 already suggests yes—extend with sentiment analysis |

### Key Files Reference

| File | Purpose |
|------|---------|
| `BRIEFING_BOOK.md` | **This document** – Comprehensive overview |
| `src/census/analysis_plan.md` | Theoretical frameworks and research questions |
| `src/census/analysis_execution_plan.md` | Task tracker (what's done, what's next) |
| `src/census/analysis_utils.py` | Shared utilities (load data, call LLM, cache) |
| `src/census/data/{year}-field-note-transcriptions-normalized.csv` | **Primary dataset** |
| `src/census/data/question-set-{year}.md` | Survey instruments (what was asked) |
| `reports/` | Analysis outputs (markdown reports) |

---

## Philosophical Coda: Why This Matters

Burning Man is not just a festival. It is a **living laboratory** for alternative social organization. For one week, 70,000+ people create a city governed by ten principles instead of market capitalism. Then it vanishes.

Most attempts to study it are either:
- **Journalistic** (Hunter S. Thompson-style gonzo reporting)
- **Sociological** (external observer surveys, post-hoc interviews)
- **Anecdotal** (participant blogs and stories)

**This dataset is different.**

We captured **participants talking to themselves** (via journal prompts) **while inside the experiment**. This is ethnography as close to the bone as you can get without telepathy.

### The Questions That Haunt Us

- If Burning Man "changes" people, why does the default world stay the same?
- Can temporary utopia teach us anything about permanent society?
- Is radical self-expression truly radical if it requires $500+ tickets and a week off work?
- What do 1,797 people *really* mean when they say "community"?

**We don't have all the answers yet. But we have their words.**

---

## Research Team Notes & Context

**Project Lead**: Peter (GitHub: peter)
**Collection Years**: 2024, 2025
**Dataset Size**: 1,797 responses
**Status**: Early analysis phase (2 of 6+ modules complete)
**Next Steps**: Costume/Identity analysis, Symbolism analysis, Diversity analysis

**For Future Collaborators**:
- This is a **living project**—new data could be collected in future years
- The theoretical frameworks are **hypotheses**, not dogma—challenge them!
- The code is functional but not polished—refactor as needed
- The most important thing is to **listen** to what participants said, not just confirm our biases

**Contact/Contribution**:
- Issues and contributions welcome via GitHub
- Respect participant anonymity—no attempts to de-anonymize
- If publishing, acknowledge the Burning Man community

---

## Appendix A: The Ten Principles (For Context)

1. **Radical Inclusion**
   Anyone may be a part of Burning Man.

2. **Gifting**
   Giving without expectation of return.

3. **Decommodification**
   No commercial transactions (except ice and coffee).

4. **Radical Self-Reliance**
   Bring everything you need to survive.

5. **Radical Self-Expression**
   Be who you are, unapologetically.

6. **Communal Effort**
   Build together.

7. **Civic Responsibility**
   Take care of each other and the space.

8. **Leaving No Trace**
   Pack it in, pack it out.

9. **Participation**
   Do, don't just observe.

10. **Immediacy**
    Be present, now.

---

## Appendix B: Sample Responses (Illustrative)

**Transformation (Virgin)**:
*"From the 1st time I heard of it about 15 yr ago, so yeah... a calling that changed me and now that I'm here, MAKES SO MUCH SENSE - I need time to ponder on how it has changed me because I'm still navigating my 1st BURN - BUT I feel home partying with you all... 'joy as an act of resistance' in such a hurt world"*

**Symbolism (The Man)**:
*"The Man is the embodiment of our collective creative spirit—the celebration of building something beautiful just to watch it burn. It's about letting go."*

**Survival**:
*"Water. Everything else is negotiable. Water is life."*

**Diversity**:
*"In the default world, I code-switch constantly. Here, I can just... be. No one cares if I'm the only [identity] in the room."*

---

## Appendix C: Data Dictionary

### Normalized Demographics Columns

| Column | Type | Values | Description |
|--------|------|--------|-------------|
| `Norm_Age` | Integer | 0-110 | Participant age |
| `Norm_Gender` | Category | M, F, NB, O, U | M=Male, F=Female, NB=Non-binary, O=Other/Nuanced, U=Unknown |
| `Norm_Burn_Count` | Integer | 1-100+ | Number of Burning Man events attended |
| `Norm_Region` | Category | Local/West, US Other, International, Unknown | Geographic origin |
| `Burn_Status` | Category | Virgin, Sophomore, Veteran, Elder | Tenure categorization |

### Question Column Structure

- **Q1-Q4**: Demographics (consistent across all sets)
- **Q5+**: Thematic questions (vary by question set)
- **Folder**: Year (e.g., "2024 Field Notes Images")
- **Subfolder**: Question set (e.g., "A - Transformation", "J1 - Survival")
- **Filename**: Original image filename
- **EntryIndex**: Entry number within that image (if multiple responses per page)
- **Raw Transcription**: Original OCR output before parsing

---

**Document Version**: 1.0
**Last Updated**: January 2026
**Status**: Living Document (update as analysis progresses)

---

*"The playa provides. The dust teaches. The fire transforms. And we, the ethnographers, bear witness."*

**Welcome to the Field Notes. May the dust be kind to you.** 🔥🏜️✨
