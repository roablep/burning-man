import os
import csv
import time
from pathlib import Path

import google.generativeai as genai
from dotenv import load_dotenv
from PIL import Image
from pillow_heif import register_heif_opener

# 1. Setup

# env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise EnvironmentError(f"GEMINI_API_KEY not found in {env_path}")
IMAGE_FOLDER = "/Users/peter/Downloads/2025 Notes"
OUTPUT_CSV = "transcriptions.csv"

# Register HEIC opener
register_heif_opener()
genai.configure(api_key=API_KEY)

# Use Flash for speed/free limits (1500 req/day). 
# If handwriting is very messy, switch to 'gemini-1.5-pro' (limit 50/day free)
model = genai.GenerativeModel('gemini-1.5-flash')

def transcribe_image(image_path):
    try:
        # Open and resize if massive (Flash has a 4MB limit typically, resizing helps)
        img = Image.open(image_path)
        
        prompt = """
        Analyze this image. It is a survey response. 
        Extract the handwritten answers corresponding to the typed questions.
        Return ONLY a raw string in this format:
        Q1: [Answer] | Q2: [Answer] | Q3: [Answer]...
        """
        
        response = model.generate_content([prompt, img])
        return response.text.strip()
    except Exception as e:
        return f"Error: {e}"

# 2. Main Loop
with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["Filename", "Raw Transcription"]) # Header

    files = [
        os.path.join(root, f) 
        for root, dirs, filenames in os.walk(IMAGE_FOLDER) 
        for f in filenames 
        if f.lower().endswith(('.heic', '.jpg', '.png'))
    ]
    print(f"Found {len(files)} images. Starting batch processing...")

    for i, path in enumerate(files):
        print(f"Processing {i+1}/{len(files)}: {filename}")
        
        transcription = transcribe_image(path)
        writer.writerow([filename, transcription])
        
        # Polite sleep to avoid hitting rate limits (Flash is fast, but safe is better)
        time.sleep(2)

print(f"Done! Saved to {OUTPUT_CSV}")
