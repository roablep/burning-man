import csv
import os
import re

# 2024 Mapping
SURVEY_LIMITS_2024 = {
    'A': 9,  # Transformation
    'B': 7,  # Symbolism
    'C': 8,  # Emotions
    'D': 9,  # Boundaries of Humanity
    'E': 8,  # Dancing & Singing
    'F': 7,  # Costumes
    'G': 9,  # Drinking and Smoking
    'H': 6,  # Experiences
    'I': 7,  # Relationships
    'J': 8,  # Survival
    'K': 8,  # Diversity and Inclusion
    'L': 7,  # Beyond Black Rock City
    'M': 10  # Sustainability
}

# 2025 Mapping
SURVEY_LIMITS_2025 = {
    'A': 9,  # Transformation
    'B': 8,  # Survival
    'C': 10, # Emotions and Experiences
    'D': 9,  # Boundaries of Humanity
    'E': 7,  # Relationships
    'F': 8,  # Diversity and Inclusion
}

def get_max_questions(subfolder_name, year):
    """
    Extracts the survey code (A, B, C...) from the subfolder name
    and returns the max question count based on the year.
    """
    if not subfolder_name:
        return 0
    
    limits = SURVEY_LIMITS_2025 if year == 2025 else SURVEY_LIMITS_2024

    # Match the first letter if it looks like "A1", "B2", "C - Emotions" etc.
    match = re.match(r"^([A-Z])\d*\s*-", subfolder_name, re.IGNORECASE)
    if match:
        code = match.group(1).upper()
        return limits.get(code, 0)
    
    # Fallback by name if code fails (though code is preferred)
    name_lower = subfolder_name.lower()
    
    if year == 2025:
        if 'transformation' in name_lower: return 9
        if 'survival' in name_lower: return 8
        if 'emotions' in name_lower or 'experiences' in name_lower: return 10
        if 'boundaries' in name_lower: return 9
        if 'relationships' in name_lower: return 7
        if 'diversity' in name_lower: return 8
    else:
        # 2024 Fallbacks
        if 'transformation' in name_lower: return 9
        if 'symbolism' in name_lower: return 7
        if 'emotions' in name_lower: return 8
        if 'boundaries' in name_lower: return 9
        if 'dancing' in name_lower or 'singing' in name_lower: return 8
        if 'costumes' in name_lower: return 7
        if 'drinking' in name_lower or 'smoking' in name_lower: return 9
        if 'experiences' in name_lower: return 6
        if 'relationships' in name_lower: return 7
        if 'survival' in name_lower: return 8
        if 'diversity' in name_lower: return 8
        if 'beyond' in name_lower: return 7
        if 'sustainability' in name_lower: return 10
    
    return 0

def clean_file(input_file, output_file, year):
    print(f"Cleaning {input_file} -> {output_file} (Year: {year})")
    
    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    cleaned_rows = []
    
    for row in rows:
        subfolder = row.get('Subfolder', '')
        max_q = get_max_questions(subfolder, year)
        
        if max_q == 0:
            # Could not identify survey type, keep row as is
            cleaned_rows.append(row)
            continue
            
        # Clean the row
        cleaned_row = row.copy()
        
        # Check for overflow
        overflow_text = []
        for q in range(max_q + 1, 31): # Check up to Q30
            col_name = f"Q{q}"
            if col_name in row and row[col_name] and row[col_name].strip():
                overflow_text.append(row[col_name].strip())
                cleaned_row[col_name] = "" # Clear the invalid column
        
        # Append overflow to the last valid question
        if overflow_text:
            last_valid_col = f"Q{max_q}"
            current_val = cleaned_row.get(last_valid_col, "") or ""
            merged_val = (current_val + " " + " ".join(overflow_text)).strip()
            cleaned_row[last_valid_col] = merged_val
            
        cleaned_rows.append(cleaned_row)

    # Write output
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(cleaned_rows)
        
    print(f"Finished cleaning {len(cleaned_rows)} rows.")

def main():
    files = [
        ("2024-field-note-transcriptions-parsed.csv", "2024-field-note-transcriptions-cleaned.csv", 2024),
        ("2025-field-note-transcriptions-parsed.csv", "2025-field-note-transcriptions-cleaned.csv", 2025)
    ]
    
    for in_f, out_f, yr in files:
        if os.path.exists(in_f):
            clean_file(in_f, out_f, yr)
        else:
            print(f"Skipping {in_f} (not found)")

if __name__ == "__main__":
    main()