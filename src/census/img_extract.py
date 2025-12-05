import os
import csv
import time
from pathlib import Path

import google.generativeai as genai
from dotenv import load_dotenv
from PIL import Image
from pillow_heif import register_heif_opener
from google.api_core import exceptions

# 1. Setup
load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise EnvironmentError("GEMINI_API_KEY not found")

IMAGE_FOLDER = "/Users/peter/Downloads/2025 Notes"
OUTPUT_CSV = "transcriptions.csv"

register_heif_opener()
genai.configure(api_key=API_KEY)

model = genai.GenerativeModel("gemini-1.5-flash")

# DISABLE SAFETY FILTERS
# Handwriting often triggers false positives (e.g., seeing "nude" instead of "node")
safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]


def transcribe_image(image_path):
    try:
        img = Image.open(image_path)

        # OPTIMIZATION: Resize image to max 1024px on long side.
        # Saves bandwidth and speeds up processing without losing OCR legibility.
        img.thumbnail((1024, 1024))

        prompt = """
        Analyze this image. It is a survey response. 
        Extract the handwritten answers corresponding to the typed questions.
        Return ONLY a raw string in this format:
        Q1: [Answer] | Q2: [Answer] | Q3: [Answer]
        If handwriting is illegible, write [Illegible].
        """

        # Added safety_settings here
        response = model.generate_content(
            [prompt, img], safety_settings=safety_settings
        )
        return response.text.strip()

    except exceptions.ResourceExhausted:
        return "Error: 429 Quota Exceeded"
    except ValueError:
        # This catches when safety filters block the response despite settings
        return "Error: Blocked by Safety Filters (or empty response)"
    except Exception as e:
        return f"Error: {e}"


# 2. Main Loop
with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(
        ["Subfolder", "Filename", "Raw Transcription"]
    )  # Added Subfolder column

    # Recursive search
    files = [
        os.path.join(root, f)
        for root, dirs, filenames in os.walk(IMAGE_FOLDER)
        for f in filenames
        if f.lower().endswith((".heic", ".jpg", ".png"))
    ]

    print(f"Found {len(files)} images. Starting batch processing...")

    for i, full_path in enumerate(files[:]):
        # Extract just the filename and subfolder for cleaner CSV logging
        filename = os.path.basename(full_path)
        subfolder = os.path.basename(os.path.dirname(full_path))

        print(f"Processing {i+1}/{len(files)}: {subfolder}/{filename}")

        # PATH FIX: Use full_path directly, do not join again
        transcription = transcribe_image(full_path)

        writer.writerow([subfolder, filename, transcription])

        # If we hit a rate limit error, pause longer
        if "Quota Exceeded" in transcription:
            print("Quota hit. Sleeping for 30 seconds...")
            time.sleep(30)
        else:
            time.sleep(2)

print(f"Done! Saved to {OUTPUT_CSV}")
