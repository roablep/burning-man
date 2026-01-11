import csv
import re
import os

def parse_transcription(raw_text):
    """
    Parses the raw transcription string into a dictionary of questions and answers.
    Expected format: "Q1: Answer 1 | Q2: Answer 2 | ..."
    """
    if not raw_text or raw_text.strip().lower() in ["no entries found", ""]:
        return {}

    # Regex to identify the start of a question: Q followed by digits, then optional whitespace, then colon or dot or just space
    q_pattern = re.compile(r"^\s*Q(\d+)[:\.]?\s*(.*)", re.IGNORECASE | re.DOTALL)

    parts = raw_text.split('|')
    entries = {}
    current_q_num = None
    
    for part in parts:
        # Check if this part starts a new question
        match = q_pattern.match(part.strip())
        if match:
            q_num = match.group(1)
            val = match.group(2).strip()
            entries[f"Q{q_num}"] = val
            current_q_num = q_num
        else:
            # It's a continuation of the previous value (e.g. contains a pipe)
            if current_q_num:
                entries[f"Q{current_q_num}"] += " | " + part.strip()
            else:
                # Part before any Q? or malformed.
                # If we haven't seen a Q yet, maybe it's just raw text without labels.
                # But we'll ignore for now or log? 
                # Let's assign to "Notes" or similar if we really wanted, but for Q columns we need Qs.
                pass
                
    return entries

def process_file(input_file, output_file):
    print(f"Processing {input_file} -> {output_file}")
    
    all_rows = []
    all_q_nums = set()
    
    with open(input_file, 'r', encoding='utf-8', errors='replace') as f:
        reader = csv.DictReader(f)
        # Normalize fieldnames to strip BOM if present or weird spaces
        fieldnames = [fn.strip() for fn in reader.fieldnames] if reader.fieldnames else []
        
        # Create a new reader with clean fieldnames to access rows easier if needed, 
        # but DictReader uses the original file content for keys. 
        # We'll just use the row dict as provided.
        
        for row in reader:
            # Clean keys in row just in case
            clean_row = {k.strip(): v for k, v in row.items() if k}
            
            raw = clean_row.get('Raw Transcription', '')
            parsed_data = parse_transcription(raw)
            
            # Track which Q numbers we've seen
            for k in parsed_data.keys():
                # Extract number from Q1, Q12 etc
                if k.startswith('Q') and k[1:].isdigit():
                    all_q_nums.add(int(k[1:]))
            
            clean_row.update(parsed_data)
            all_rows.append(clean_row)
            
    # Sort Q keys numerically
    sorted_q_nums = sorted(list(all_q_nums))
    q_keys = [f"Q{n}" for n in sorted_q_nums]
    
    # Define new header
    # Ensure standard fields are first
    standard_fields = ['Folder', 'Subfolder', 'Filename', 'EntryIndex', 'Raw Transcription']
    # Filter out any that weren't in original but keep order
    base_fields = [fn for fn in fieldnames if fn in standard_fields]
    # Add any extra fields from original that aren't standard (if any)
    extra_fields = [fn for fn in fieldnames if fn not in standard_fields]
    
    new_fieldnames = base_fields + extra_fields + q_keys
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=new_fieldnames)
        writer.writeheader()
        writer.writerows(all_rows)
    
    print(f"Done. Found questions: {q_keys}")

def main():
    files = [
        ("2024-field-note-transcriptions.csv", "2024-field-note-transcriptions-parsed.csv"),
        ("2025-field-note-transcriptions.csv", "2025-field-note-transcriptions-parsed.csv")
    ]
    
    for in_file, out_file in files:
        if os.path.exists(in_file):
            process_file(in_file, out_file)
        else:
            print(f"File not found: {in_file}")

if __name__ == "__main__":
    main()
