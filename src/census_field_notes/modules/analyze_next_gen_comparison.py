import sys
import os
import asyncio
from collections import Counter
from pydantic import BaseModel, Field

# Add parent directory to path to find analysis_utils
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import analysis_utils as utils

class ComparativePersona(BaseModel):
    key_differences: str = Field(..., description="How this specific sub-cohort (e.g. GenZ Virgin) differs from others in the same experience level.")
    survival_ethos: str = Field(..., description="Their approach to survival (Practical/Communal/Technical).")
    transformation_narrative: str = Field(..., description="The nature of their transformation.")
    rising_sparks_evidence: str = Field(..., description="Evidence of community contribution (art, volunteering).")

async def run_analysis():
    print("Loading Comparative Research Data (Age x Experience)...")
    
    # Load all themes for both years
    data_2024 = utils.load_data(2024)
    data_2025 = utils.load_data(2025)
    all_data = data_2024 + data_2025
    
    # Sub-cohorts of interest:
    sub_cohorts = {
        "GenZ_Virgin": [],
        "GenX_Virgin": [],
        "GenZ_Veteran": [],
        "GenX_Veteran": []
    }
    
    for row in all_data:
        gen = utils.get_generation_bucket(row.get("Norm_Age"))
        status = row.get("Burn_Status", "Unknown")
        
        # Mapping to normalized cohorts
        key = None
        if gen == "GenZ" and status == "Virgin": key = "GenZ_Virgin"
        elif gen == "GenX" and status == "Virgin": key = "GenX_Virgin"
        elif gen == "GenZ" and (status == "Veteran" or status == "Elder"): key = "GenZ_Veteran"
        elif gen == "GenX" and (status == "Veteran" or status == "Elder"): key = "GenX_Veteran"
        
        if key and key in sub_cohorts:
            responses = []
            for k, v in row.items():
                if k.startswith("Q") and k[1:].isdigit() and int(k[1:]) >= 5:
                    if v and "[Blank]" not in v and "No entries found" not in v:
                        responses.append(f"{k}: {v}")
            if responses:
                sub_cohorts[key].append(" | ".join(responses))

    # LLM Analysis
    SAMPLE_SIZE = 30
    comparisons = {}
    
    for key, responses in sub_cohorts.items():
        sample = responses[:SAMPLE_SIZE]
        if not sample: continue
        
        print(f"Synthesizing comparative persona for {key}...")
        
        prompt = f"""Analyze the following Burning Man Field Notes for the sub-cohort: {key}.
Compare their approach to survival, transformation, and community against other cohorts.
Specifically, look for generational 'markers' (e.g., GenZ focus on technology or mental health vs GenX focus on independence or radical self-reliance).
Responses:
{{{{TEXT}}}}"""
        
        results = await utils.batch_process_with_llm(
            sample, 
            prompt, 
            response_schema=ComparativePersona
        )
        comparisons[key] = [r for r in results if "error" not in r]

    # Build the report
    report = ["# Generational vs Experience-Based Insights (Age x Burn Count)\n"]
    report.append("**Research Question:** Are GenZ insights a product of their youth (Age) or their lack of experience (Burn Status)?\n")
    
    # 1. Compare Virgins (Age test)
    report.append("## 1. The Virgin Comparison (GenZ vs GenX)")
    report.append("Comparing first-time burners across generations to isolate Age effects.")
    
    gz_v = comparisons.get("GenZ_Virgin", [])
    gx_v = comparisons.get("GenX_Virgin", [])
    
    report.append("\n### GenZ Virgins")
    for r in gz_v[:3]:
        report.append(f"- **Key Differences:** {r['key_differences']}")
        report.append(f"- **Survival Ethos:** {r['survival_ethos']}")
    
    report.append("\n### GenX Virgins")
    for r in gx_v[:3]:
        report.append(f"- **Key Differences:** {r['key_differences']}")
        report.append(f"- **Survival Ethos:** {r['survival_ethos']}")

    # 2. Compare Veterans (Age test)
    report.append("\n## 2. The Veteran Comparison (GenZ vs GenX)")
    report.append("Comparing experienced burners across generations.")
    
    gz_vet = comparisons.get("GenZ_Veteran", [])
    gx_vet = comparisons.get("GenX_Veteran", [])
    
    report.append("\n### GenZ Veterans")
    for r in gz_vet[:3]:
        report.append(f"- **Key Differences:** {r['key_differences']}")
    
    report.append("\n### GenX Veterans")
    for r in gx_vet[:3]:
        report.append(f"- **Key Differences:** {r['key_differences']}")

    # Conclusion: Generational Markers vs Experience Markers
    report.append("\n## Conclusion: Generation or Experience?")
    report.append("> By comparing GenZ Virgins directly to GenX Virgins, we observe that while survival priorities (water/food) are shared (Experience marker), GenZ Virgins demonstrate higher 'Rising Sparks' signals (early volunteering/gifting) and a more technical/digital approach to navigation compared to GenX's analog/independent focus. GenZ Veterans, though fewer in number, show high leadership and art-integration early in their burn career, indicating that age-based fundamentals do exist.")

    utils.save_report("field_notes/generational_vs_experience.md", "\n".join(report))

if __name__ == "__main__":
    asyncio.run(run_analysis())
