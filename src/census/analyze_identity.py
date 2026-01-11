import asyncio
from collections import Counter
from pydantic import BaseModel, Field
from typing import Literal
import analysis_utils as utils

class CostumeMotivation(BaseModel):
    motivation_type: Literal["Authenticity", "Play", "Disguise", "Conformity", "Comfort", "Other"] = Field(
        ..., 
        description="The primary reason the participant wears costumes. Authenticity=To show true self. Play=For fun/creativity. Disguise=To hide/be someone else. Conformity=To fit in. Comfort=Practicality."
    )
    key_phrase: str = Field(..., description="The specific 3-5 word phrase that indicates this motivation.")

async def run_analysis():
    print("Loading Costume Data for Identity Analysis...")
    data_2024 = utils.load_data(2024, "Costumes")
    data_2025 = utils.load_data(2025, "Costumes") # Note: 2025 might map F to Diversity, need to check mapping
    
    # 2025 Set F is "Diversity", Set ?? is Costumes?
    # Checking analysis_plan.md... Wait, 2025 doesn't have a dedicated Costume set?
    # Let's check 2025 question set.
    # Set F in 2025 is Diversity. There is no Costume set in 2025 based on previous context.
    # We will stick to 2024 Set F (Costumes) for this analysis.
    
    narratives = []
    for row in data_2024:
        # Q5: Do you wear costumes? Why?
        q5 = row.get("Q5", "")
        if len(q5) > 10:
            narratives.append(q5)
            
    print(f"Total Costume narratives: {len(narratives)}")
    
    prompt = """
    Analyze this response to 'Do you wear costumes at Burning Man? Why or why not?'.
    Categorize the motivation.
    
    Response: "{{TEXT}}"
    """
    
    results = await utils.batch_process_with_llm(
        narratives[:150], 
        prompt, 
        response_schema=CostumeMotivation
    )
    
    stats = Counter()
    examples = {"Authenticity": [], "Play": [], "Disguise": []}
    
    for i, res in enumerate(results):
        if isinstance(res, dict) and "error" in res: continue
        
        mot = res.get("motivation_type", "Other")
        stats[mot] += 1
        
        if mot in examples and len(examples[mot]) < 3:
            examples[mot].append(f"\"{narratives[i]}\" -> *{res.get('key_phrase')}*")

    # Generate Report
    report = ["# Module 3: The Mask vs. The Mirror (Identity)\n"]
    report.append(f"**Research Question:** Is the costume a mask (hiding) or a mirror (revealing)?\n")
    report.append(f"**Sample:** {len(results)} responses from 2024.\n")
    
    report.append("### Motivation Distribution")
    report.append("| Motivation | Count | Percentage |")
    report.append("| :--- | :--- | :--- |")
    
    total = sum(stats.values())
    for k, v in stats.most_common():
        report.append(f"| {k} | {v} | {v/total:.1%} |")
        
    report.append("\n### Voices")
    for cat, items in examples.items():
        if items:
            report.append(f"\n**{cat}:**")
            for item in items:
                report.append(f"- {item}")

    report.append("\n**Conclusion:**")
    auth_score = stats['Authenticity']
    disguise_score = stats['Disguise']
    
    if auth_score > disguise_score * 2:
        report.append("> **The Mirror Wins:** Participants overwhelmingly view costumes as a tool for revealing their true selves ('Radical Self Expression') rather than hiding.")
    elif disguise_score > auth_score:
        report.append("> **The Mask Wins:** Participants primarily use costumes to escape their identity.")
    else:
        report.append("> **It's Complicated:** The function of the costume is split between revelation and escapism.")

    utils.save_report("module_3_identity.md", "\n".join(report))

if __name__ == "__main__":
    asyncio.run(run_analysis())
