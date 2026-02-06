import csv
import re
import os

def normalize_age(val):
    """Parses '34', '34 years old', '34 yo', 'thirty four' into 34."""
    if not val: return None
    # Extract first digits
    match = re.search(r"(\d+)", val)
    if match:
        age = int(match.group(1))
        # Filter realistic human ages for Burning Man
        return age if 0 < age < 110 else None
    
    # Handle text numbers if common (basic set)
    text_nums = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, 
                 "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10}
    val_low = val.lower().strip()
    return text_nums.get(val_low)

def normalize_gender(val):
    """Maps free text to M, F, NB, Other."""
    if not val: return "U" # Unknown
    v = val.lower().strip()
    
    if v in ["m", "male", "man", "cis male", "he", "him", "masc", "guy", "boy"]:
        return "M"
    if v in ["f", "female", "woman", "cis female", "she", "her", "femme", "girl", "lady"]:
        return "F"
    if any(x in v for x in ["nonbinary", "non-binary", "nb", "enby", "fluid", "queer", "they"]):
        return "NB"
    
    return "O" # Other/Nuanced

def normalize_burn_count(val):
    """Converts 'Virgin', '1st', '10+' to integers."""
    if not val: return None
    v = val.lower().strip()
    
    if any(x in v for x in ["virgin", "first", "1st", "once"]):
        return 1
    
    # Extract digits
    match = re.search(r"(\d+)", v)
    if match:
        return int(match.group(1))
    
    return None

def normalize_location(val):
    """Simple region mapping."""
    if not val: return "Unknown"
    v = val.lower()
    
    if any(x in v for x in ["ca", "california", "san francisco", "sf", "oakland", "la", "los angeles", "reno", "nv", "nevada"]):
        return "Local/West"
    if any(x in v for x in ["uk", "london", "france", "germany", "europe", "australia", "canada", "israel", "brazil", "international", "nz"]):
        return "International"
    
    return "US Other"

def process_file(input_file, output_file):
    print(f"Normalizing demographics in {input_file}...")
    
    cleaned_rows = []
    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        # New columns to add
        new_cols = ["Norm_Age", "Norm_Gender", "Norm_Burn_Count", "Norm_Region", "Burn_Status"]
        
        for row in reader:
            # Demographics are always Q1-Q4 in both years
            row["Norm_Age"] = normalize_age(row.get("Q1"))
            row["Norm_Gender"] = normalize_gender(row.get("Q2"))
            row["Norm_Region"] = normalize_location(row.get("Q3"))
            row["Norm_Burn_Count"] = normalize_burn_count(row.get("Q4"))
            
            # Categorical Status
            count = row["Norm_Burn_Count"]
            if count is None: status = "Unknown"
            elif count == 1: status = "Virgin"
            elif count <= 3: status = "Sophomore"
            elif count <= 9: status = "Veteran"
            else: status = "Elder"
            row["Burn_Status"] = status
            
            cleaned_rows.append(row)

    output_fieldnames = fieldnames + new_cols
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=output_fieldnames)
        writer.writeheader()
        writer.writerows(cleaned_rows)
    
    print(f"Saved {len(cleaned_rows)} normalized rows to {output_file}")

def main():
    files = [
        ("2024-field-note-transcriptions-cleaned.csv", "2024-field-note-transcriptions-normalized.csv"),
        ("2025-field-note-transcriptions-cleaned.csv", "2025-field-note-transcriptions-normalized.csv")
    ]
    
    for in_f, out_f in files:
        if os.path.exists(in_f):
            process_file(in_f, out_f)
        else:
            print(f"Skipping {in_f} (not found)")

if __name__ == "__main__":
    main()
