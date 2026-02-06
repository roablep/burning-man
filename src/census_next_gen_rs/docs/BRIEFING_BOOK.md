# **Data Request: Theme Camps & Age Demographics**

## **Purpose**

This request supports an intergenerational engagement initiative aimed at addressing the sharp decline in younger participants at Burning Man  \-  from \~30% under-30 in 2014 to \~12% today. The initiative explores the role of **theme camps as recruitment, acculturation, and retention engines** for younger burners.

## **Goals & Objectives**

**Goals**
- Reverse or better understand the decline in under-30 participation by identifying how theme camps influence recruitment, acculturation, and retention.
- Treat the Census as a partner for cultural sustainability research, not just a data source.

**Objectives**
- Diagnose the problem: separate recruitment vs. retention dynamics for younger participants.
- Quantify the camp effect: measure under-30 participation and return rates by placed vs. non-placed camps.
- Provide actionable benchmarks: anonymized metrics camps can compare to citywide averages (e.g., % under-30, % virgins, retention).
- Inform program design: identify factors that correlate with stronger retention to guide next-gen engagement.
- Set up future research: move toward longitudinal and on-playa methods (EMA/intercepts) that capture belonging and return intent.

## **Why This Matters**

- **Sustainability of Culture:** Camps rely on new members to survive; younger participants bring energy, longevity, and fresh perspectives.  
- **Lower Barriers to Entry:** Camps provide shared infrastructure that makes attending Burning Man more accessible for those with fewer resources.  
- **Cultural Transmission:** Camps act as “high-trust, high-accountability micro-communities” that help newcomers integrate into Burning Man culture more effectively than solo attendance.  
- **Retention & Churn Analysis:** Understanding which demographics return year over year helps identify where interventions might sustain participation.

Our (Peter’s) working hypothesis is that **theme camps are critical infrastructure for acculturating and retaining the next generation of Burners.**

They function as *acculturation incubators* by:

- **Lowering Barriers to Entry:** Providing essential infrastructure (power, water, meals) reduces the logistical and financial burden for first-timers.  
- **Providing Social Infrastructure:** Camps create intimate, high-trust environments that model Burning Man’s principles and foster deeper cultural understanding.

---

## **Revised Vision: From Data Request to Partnership**

Initially, the intention was to request data to ensure that we are:

1. **Solving the right problem** (e.g. recruitment vs. retention)  
2. **Measuring initiative effectiveness** (seeing the right KPIs move).  
3. **Developing data “products”** that encourage next-gen engagement awareness by theme camps (Provide camps with anonymized benchmarks vs. city averages for % of birgins, % under-30, and retention rates.)  
4. **Informing the initiative roadmap** (i.e. helping identify geographic or structural factors that correlate with higher young-burner retention.)

However, my thinking has evolved. The **Burning Man Census is not just a data source \- it’s the closest thing the community has to market research, social science, and public voice.**

I’d like to explore how this project could deepen partnership with the Census team to:

- **Co-design meaningful metrics** for cultural sustainability and intergenerational health.  
- **Develop participatory research approaches** (e.g., intercept surveys, focus groups, design jams) that amplify the voices of younger and first-time Burners.  
- **Pilot new feedback loops** that turn Census insights into real-world community action \- such as helping camps recruit inclusively, measure belonging, and reduce newcomer drop-off.

In short: this is an invitation for **Census to be an active co-researcher and cultural design partner**, not merely a passive data provider.

---

## **Requested Data (Phase 1\)**

Anonymized, aggregated data sufficient to understand age dynamics and camp participation patterns.

### 1\. Crosstab

| Variable | Description |
| :---- | :---- |
| `# of Burns attended` | 0, 1, 2, 3, 4, 5+ |
| `Age group` | ≤22, 23–28, 29–34, etc. |
| `Placed camp` | Yes/No (as captured by Census) |

### 2\. Longitudinal View

Replicate the crosstab across multiple years to observe under-30 participation trends in placed camps.

### 3\. Cohort / Retention Analysis

| Variable | Description |
| :---- | :---- |
| `year` | Year of participation |
| `age_band` | ≤22, 23–28, 29–34, 35–39, 40–49, 50–59, 60+ |
| `placed_camp` | Yes/No |
| `previous_burns` | 0, 1, 2, 3, 4, 5+ |

**Proposed Plots**

- Second-year return rate by age band, segmented by placed vs. non-placed camps.  
- Longitudinal changes in under-30 share by camp type.

---

## **Future Research Directions**

### **Longitudinal Cohort Study**

Investigate “churn”:

- Among first-time Burners in a given year, what percentage return?  
- How does return rate differ by age cohort or placed-camp status?

### **On-Playa Research Integration**

Pilot *Ecological Momentary Assessment (EMA)* approaches \- short, anonymous, geo-tagged intercept surveys in collaboration with PEERS or Census routes. Capture data on:

- Age band & first-timer status  
- Placed camp membership  
- How participants found their camp  
- Perceived welcome / belonging  
- Likelihood to return

Primary output: **aggregate “belonging & retention” maps** to inform cultural stewardship and next-gen engagement.

---

## **Closing Thought**

The Census already plays a foundational role in documenting who we are as a community.  
This project proposes a natural extension of that mission:  
→ to **listen actively, engage continuously, and design intentionally** for the cultural resilience of Burning Man’s future generations.
---

## **2025 Weighted Raw Data**

A data dictionary for the newly available weighted raw dataset is available here:

- `reports/census_next_gen_rs/census2025_weighted_data_dictionary.md`

It summarizes column names, data types, missingness, unique counts, and a few sample values.

Initial weighted distributions are here:

- `reports/census_next_gen_rs/census2025_weighted_quick_stats.md`

---

## **Key Fields For 2025 Analysis (Draft)**

This is a compact, analysis-focused subset of the weighted dataset. Columns are from the raw file unless noted as derived.

| Field | Type | Notes |
|---|---|---|
| `weights` | numeric | Survey weights; use for population-weighted stats. |
| `age` | integer | Respondent age in years. |
| `age_band` (derived) | categorical | Bins used for initial analysis: `<=22`, `23-28`, `29-34`, `35-39`, `40-49`, `50-59`, `60+`. |
| `campPlaced` | string | Placed camp membership (values seen: `yes`, `no`, `dontKnow`). |
| `nburns` | numeric | Number of Burns attended (as reported). |
| `virgin` | string | First-time indicator (values seen: `virgin`, `not virgin`). |
| `campAddressStreet` | string | Camp address street (sparse). |
| `campCenterCampRadial` | string | Camp radial (very sparse). |
| `campStreetSide` | string | Camp street side (sparse). |
| `campKStreetSide` | string | Camp K street side (sparse). |

Additional candidate fields can be promoted once we lock cohort/retention definitions.
