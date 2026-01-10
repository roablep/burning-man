import csv
import os
from collections import Counter
import statistics


def generate_ascii_histogram(data, title, width=50):
    if not data:
        return f"No data for {title}"

    counts = Counter(data)
    if not counts:
        return f"No data for {title}"

    sorted_keys = sorted(counts.keys())
    # Handle mixed types if necessary, though demographics should be consistent
    # Age is int, others are str

    max_val = max(counts.values())
    output = [f"### {title}"]
    output.append("```")

    for k in sorted_keys:
        count = counts[k]
        bar_len = int((count / max_val) * width)
        bar = "#" * bar_len
        output.append(f"{str(k):<15} | {count:<4} {bar}")

    output.append("```\n")
    return "\n".join(output)


def analyze_file(filename, year):
    print(f"Analyzing {year}...")
    ages = []
    genders = []
    regions = []
    statuses = []
    burn_counts = []

    with open(filename, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
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

            # Burn Count (for numeric stats)
            bc = row.get("Norm_Burn_Count")
            if bc:
                burn_counts.append(int(bc))

    report = []
    report.append(f"## Year {year} Analysis")
    report.append(
        f"**Total Responses:** {len(ages)}"
    )  # Approximation based on age, or row count

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
    # Bin Ages for cleaner histogram
    age_bins = [f"{i}-{i + 9}" for i in range(10, 80, 10)] + ["80+"]
    binned_ages = []
    for a in ages:
        if a < 10:
            binned_ages.append("0-9")
        elif a >= 80:
            binned_ages.append("80+")
        else:
            binned_ages.append(f"{int(a / 10) * 10}-{int(a / 10) * 10 + 9}")

    report.append(generate_ascii_histogram(binned_ages, "Age Distribution"))
    report.append(generate_ascii_histogram(genders, "Gender Distribution"))
    report.append(generate_ascii_histogram(statuses, "Burner Status (Tenure)"))
    report.append(generate_ascii_histogram(regions, "Region Distribution"))

    return "\n".join(report)


def main():
    files = [
        ("2024-field-note-transcriptions-normalized.csv", 2024),
        ("2025-field-note-transcriptions-normalized.csv", 2025),
    ]

    full_report = ["# Burning Man Field Notes: Basic Demographic Statistics\n"]

    for f, year in files:
        if os.path.exists(f):
            full_report.append(analyze_file(f, year))

    with open("basic_stats_report.md", "w") as f:
        f.write("\n".join(full_report))

    print("Report generated: basic_stats_report.md")


if __name__ == "__main__":
    main()
