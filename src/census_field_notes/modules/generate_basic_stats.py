import sys
import os
import csv
from collections import Counter
import statistics

# Add parent directory to path to find analysis_utils
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import analysis_utils as utils

def generate_ascii_histogram(data, title, width=50):
    if not data:
        return f"No data for {title}"

    counts = Counter(data)
    if not counts:
        return f"No data for {title}"

    sorted_keys = sorted(counts.keys())
    max_val = max(counts.values())
    output = [f"### {title}"]
    output.append("```")

    for k in sorted_keys:
        count = counts[k]
        bar_len = int((count / max_val) * width) if max_val > 0 else 0
        bar = "#" * bar_len
        output.append(f"{str(k):<15} | {count:<4} {bar}")

    output.append("```\n")
    return "\n".join(output)

def analyze_year_data(data, year):
    print(f"Generating stats for {year}...")
    ages = []
    genders = []
    regions = []
    statuses = []
    burn_counts = []

    for row in data:
        # Age
        age_str = row.get("Norm_Age")
        if age_str:
            ages.append(int(age_str))

        # Gender
        g = row.get("Norm_Gender")
        if g and g != "U":
            genders.append(g)

        # Region
        r = row.get("Norm_Region")
        if r:
            regions.append(r)

        # Status
        s = row.get("Burn_Status")
        if s and s != "Unknown":
            statuses.append(s)

        # Burn Count
        bc = row.get("Norm_Burn_Count")
        if bc:
            burn_counts.append(int(bc))

    report = []
    report.append(f"## Year {year} Analysis")
    report.append(f"**Total Responses:** {len(data)}")

    # Numeric Stats
    if ages:
        mean_age = statistics.mean(ages)
        median_age = statistics.median(ages)
        report.append(f"- **Average Age:** {mean_age:.1f}")
        report.append(f"- **Median Age:** {median_age}")

    if burn_counts:
        mean_burns = statistics.mean(burn_counts)
        report.append(f"- **Average Burn Count:** {mean_burns:.1f}")

    report.append("\n")

    # Histograms
    age_bins = []
    for a in ages:
        if a < 10: age_bins.append("0-9")
        elif a >= 80: age_bins.append("80+")
        else: age_bins.append(f"{int(a / 10) * 10}-{int(a / 10) * 10 + 9}")

    report.append(generate_ascii_histogram(age_bins, "Age Distribution"))
    report.append(generate_ascii_histogram(genders, "Gender Distribution"))
    report.append(generate_ascii_histogram(statuses, "Burner Status (Tenure)"))
    report.append(generate_ascii_histogram(regions, "Region Distribution"))

    return "\n".join(report)

def run_analysis():
    full_report = ["# Burning Man Field Notes: Basic Demographic Statistics\n"]
    
    for year in [2024, 2025]:
        data = utils.load_data(year)
        if data:
            full_report.append(analyze_year_data(data, year))
        else:
            full_report.append(f"## Year {year} Analysis\nNo data found.")

    utils.save_report("basic_stats_report.md", "\n".join(full_report))
    print("Report generated: basic_stats_report.md")

if __name__ == "__main__":
    run_analysis()