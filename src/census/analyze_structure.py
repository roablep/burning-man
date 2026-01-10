import csv
from collections import defaultdict
import os

def analyze_csv(filename):
    print(f"\n--- Analyzing {filename} ---")
    if not os.path.exists(filename):
        print("File not found.")
        return

    # Store max populated question index per subfolder
    # subfolder -> { q_num: count }
    stats = defaultdict(lambda: defaultdict(int))
    
    with open(filename, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            subfolder = row.get('Subfolder', 'Unknown')
            # Check Q1...Q30
            for i in range(1, 31):
                col = f"Q{i}"
                if row.get(col) and row[col].strip():
                    stats[subfolder][i] += 1

    # Print summary
    print(f"{'Subfolder':<40} | {'Likely Max Q':<15} | {'Outliers (Q# : count)'}")
    print("-" * 100)
    
    for sub in sorted(stats.keys()):
        counts = stats[sub]
        if not counts:
            continue
            
        # Find the question number where the drop-off happens
        # Heuristic: If Q(N) has 100 answers and Q(N+1) has 5, N is likely the limit.
        
        sorted_qs = sorted(counts.keys())
        max_q = sorted_qs[-1]
        
        # Simple heuristic: Look for the last Q that has > 20% of the row count of Q1
        # (Assuming Q1 is almost always present)
        base_count = counts.get(1, 0)
        likely_limit = max_q
        
        for q in range(1, max_q + 1):
            if counts.get(q, 0) < (base_count * 0.2) and q > 1:
                # This q has very few responses compared to Q1, might be the cutoff
                # But let's be careful, some surveys have optional last questions.
                # Let's just print the raw data for you to decide.
                pass

        # Format outlier string
        outliers = []
        for q in sorted_qs:
            if counts[q] < base_count * 0.1 and base_count > 5: # Threshold for "outlier" 
                 outliers.append(f"Q{q}:{counts[q]}")
        
        # Estimate the "Real" max Q by finding the highest Q with substantial data
        # (Arbitrary threshold: > 50% of entries have it, or just the highest non-outlier)
        real_max = 0
        for q in sorted_qs:
            if counts[q] > base_count * 0.15: 
                real_max = q
        
        outlier_str = ", ".join(outliers)
        print(f"{sub:<40} | {real_max:<15} | {outlier_str}")

if __name__ == "__main__":
    analyze_csv("2024-field-note-transcriptions-parsed.csv")
    analyze_csv("2025-field-note-transcriptions-parsed.csv")
