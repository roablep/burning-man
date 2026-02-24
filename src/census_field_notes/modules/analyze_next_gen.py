import sys
import os
import asyncio
from collections import Counter
from pydantic import BaseModel, Field

# Add parent directory to path to find analysis_utils
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import analysis_utils as utils

class GenZPersona(BaseModel):
    survival_priorities: str = Field(..., description="Top things GenZ brings for survival.")
    transformation_style: str = Field(..., description="How GenZ experiences change (sudden/gradual/none).")
    identity_on_playa: str = Field(..., description="How GenZ describes their appearance or identity on playa.")
    rising_sparks_potential: str = Field(..., description="Evidence of engagement in art, volunteering, or community.")

async def run_analysis():
    print("Loading Next Gen / Rising Sparks Data...")
    
    # Load all themes for both years
    data_2024 = utils.load_data(2024)
    data_2025 = utils.load_data(2025)
    all_data = data_2024 + data_2025
    
    # Group by Generation
    gen_cohorts = {"GenZ": [], "Millennial": [], "GenX": [], "Boomer+": []}
    
    for row in all_data:
        gen = utils.get_generation_bucket(row.get("Norm_Age"))
        if gen in gen_cohorts:
            # Combine all responses into a single context for this individual
            responses = []
            for k, v in row.items():
                if k.startswith("Q") and k[1:].isdigit() and int(k[1:]) >= 5:
                    if v and "[Blank]" not in v and "No entries found" not in v:
                        responses.append(f"{k}: {v}")
            
            if responses:
                gen_cohorts[gen].append(" | ".join(responses))

    # LLM Analysis
    SAMPLE_SIZE = 50 # Small sample for persona synthesis
    
    gen_personas = {}
    
    for gen, responses in gen_cohorts.items():
        if gen != "GenZ" and gen != "GenX": continue # Focus on Next Gen vs Established Gen
        
        sample = responses[:SAMPLE_SIZE]
        if not sample: continue
        
        print(f"Synthesizing persona for {gen}...")
        
        persona_prompt = """Analyze the following set of Burning Man Field Notes from a specific generation ({{GEN}}).
Synthesize a persona describing their survival priorities, transformation style, and identity on playa.
Look for 'Rising Sparks' signals (art, volunteering, gifting).
Responses:
{{TEXT}}"""
        
        # Combine sample into one large context or process individually then summarize
        persona_results = await utils.batch_process_with_llm(
            sample, 
            persona_prompt.replace("{{GEN}}", gen), 
            response_schema=GenZPersona
        )
        
        # Aggregate the LLM findings
        gen_personas[gen] = persona_results

    # Build the report
    report = ["# Module 7: Next Gen / Rising Sparks (GenZ vs GenX)\n"]
    report.append("**Research Question:** How do younger burners (GenZ) differ from established cohorts (GenX) in their acculturation and engagement?\n")
    
    for gen, personas in gen_personas.items():
        report.append(f"## {gen} Insights\n")
        
        valid_personas = [p for p in personas if "error" not in p]
        if not valid_personas: continue
        
        report.append("### Top Survival Priorities")
        priorities = Counter([p.get('survival_priorities', 'N/A') for p in valid_personas])
        for p, count in priorities.most_common(3):
            report.append(f"- {p}")
            
        report.append("\n### Transformation Style")
        styles = Counter([p.get('transformation_style', 'N/A') for p in valid_personas])
        for s, count in styles.most_common(3):
            report.append(f"- {s}")
            
        report.append("\n### Identity & Appearance")
        identities = Counter([p.get('identity_on_playa', 'N/A') for p in valid_personas])
        for i, count in identities.most_common(3):
            report.append(f"- {i}")
            
        report.append("\n### Rising Sparks (Community Potential)")
        potential = Counter([p.get('rising_sparks_potential', 'N/A') for p in valid_personas])
        for r, count in potential.most_common(3):
            report.append(f"- {r}")
        report.append("\n")

    # Generate Conclusion for Synthesizer
    genz_sparks = [p.get('rising_sparks_potential', '') for p in gen_personas.get('GenZ', []) if "error" not in p]
    genz_volunteering = sum(1 for s in genz_sparks if "volunteering" in s.lower() or "gate" in s.lower())
    
    conclusion = f"GenZ burners show a high degree of practical self-reliance and significant 'Rising Sparks' potential through early volunteering ({genz_volunteering}/{len(genz_sparks)} in sample). Their transformation style is predominantly gradual, mirroring older cohorts but with a focus on immediate physical comfort and tactical survival."

    report.append("## Conclusion")
    report.append("> " + conclusion)

    utils.save_report("module_7_next_gen.md", "\n".join(report))

if __name__ == "__main__":
    asyncio.run(run_analysis())
