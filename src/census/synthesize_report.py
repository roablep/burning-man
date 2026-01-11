import os
import glob

def run_synthesis():
    print("Synthesizing Final Report...")
    
    report_files = sorted(glob.glob("reports/module_*.md"))
    
    final_report = ["# Burning Man Field Notes: Comprehensive Thematic Analysis\n"]
    final_report.append("## Executive Summary\n")
    final_report.append("This report synthesizes findings from a mixed-method analysis of 2024-2025 field notes.\n")
    
    # 1. Transformation
    final_report.append("### 1. The Arc of Transformation")
    final_report.append("- **Virgins** experience shock and anticipation.")
    final_report.append("- **Sophomores** experience a 'slump' or disillusionment.")
    final_report.append("- **Veterans/Elders** shift focus to service, community, and stewardship.\n")
    
    # 2. Survival
    final_report.append("### 2. The Role of Hardship")
    final_report.append("- Contrary to the 'Ordeal' hypothesis, physical hardship is **rarely** cited as the primary catalyst for growth.")
    final_report.append("- Transformation is driven by **Social Connection** and **Creative Freedom**, not suffering.\n")
    
    # 3. Identity
    final_report.append("### 3. The Function of Costumes")
    final_report.append("- Costumes are overwhelmingly a **Mirror** (Authenticity/Expression), not a Mask (Disguise).")
    final_report.append("- Participants feel *more* like themselves in costume than in default clothes.\n")
    
    # 4. Symbolism
    final_report.append("### 4. Sacred Geography")
    final_report.append("- **The Temple** is the emotional core of the city, associated with Grief and Release.")
    final_report.append("- **The Man** is a more ambiguous symbol, associated with Community but also Indifference.\n")
    
    # 5. Diversity
    final_report.append("### 5. The Friction of Utopia")
    final_report.append("- Radical Inclusion is not evenly distributed.")
    final_report.append("- Marginalized groups report high rates of **Negative** or **Mixed** experiences.")
    final_report.append("- Key friction points: **Racism, Exoticism, and Invisibility**.\n")
    
    final_report.append("---\n")
    
    # Append individual reports
    for f_path in report_files:
        with open(f_path, 'r', encoding='utf-8') as f:
            content = f.read()
            final_report.append(f"\n{content}\n")
            final_report.append("---\n")
            
    with open("FINAL_ANALYSIS_REPORT.md", "w", encoding='utf-8') as f:
        f.write("\n".join(final_report))
        
    print("Final Report Generated: FINAL_ANALYSIS_REPORT.md")

if __name__ == "__main__":
    run_synthesis()
