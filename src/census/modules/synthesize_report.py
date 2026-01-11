import sys
import os
import glob
import re

# Add parent directory to path to find analysis_utils
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import analysis_utils as utils

def extract_conclusion(content):
    """Extracts the text under '## Conclusion'."""
    match = re.search(r"## Conclusion\s*(.*)", content, re.DOTALL)
    if match:
        # Clean up block quotes and extra whitespace
        text = match.group(1).strip()
        text = text.replace("> ", "").strip()
        return text
    return "Conclusion not found."

def run_synthesis():
    print("Synthesizing Final Report (Dynamic).")
    
    # Check for reports in project root
    # Assuming script is run from project root, or we need to find root relative to this script
    # This script is in src/census/modules/
    # Reports are in reports/ (project root)
    
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
    reports_dir = os.path.join(project_root, "reports")
    
    report_files = sorted(glob.glob(os.path.join(reports_dir, "module_*.md")))
    
    if not report_files:
        print(f"No reports found in {reports_dir}")
        return

    # Header
    final_report = ["# Burning Man Field Notes: Comprehensive Thematic Analysis\n"]
    final_report.append("## Executive Summary\n")
    final_report.append("This report synthesizes findings from a mixed-method analysis of 2024-2025 field notes. The conclusions below are derived directly from the semantic analysis of participant narratives.\n")
    
    # Dynamic Executive Summary
    for f_path in report_files:
        module_name = os.path.basename(f_path).replace("module_", "").replace(".md", "").replace("_", " ").title()
        
        with open(f_path, 'r', encoding='utf-8') as f:
            content = f.read()
            conclusion = extract_conclusion(content)
            
            # Add to Executive Summary
            final_report.append(f"### {module_name}")
            final_report.append(f"{conclusion}\n")

    final_report.append("---\n")
    final_report.append("# Detailed Findings\n")
    
    # Append individual detailed reports
    for f_path in report_files:
        with open(f_path, 'r', encoding='utf-8') as f:
            content = f.read()
            final_report.append(f"\n{content}\n")
            final_report.append("---\n")
            
    utils.save_report("FINAL_ANALYSIS_REPORT.md", "\n".join(final_report))
        
    print("Final Report Generated: FINAL_ANALYSIS_REPORT.md")

if __name__ == "__main__":
    run_synthesis()
