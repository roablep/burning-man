import os
import csv
import time
from pathlib import Path

import google.generativeai as genai
from dotenv import load_dotenv
from PIL import Image, ImageOps
from pillow_heif import register_heif_opener
from google.api_core import exceptions

# --- 1. SETUP ---
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
IMAGE_FOLDER = "/Users/peter/Downloads/2025 Notes"
OUTPUT_CSV = "transcriptions.csv"

register_heif_opener()
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]


# --- 2. HELPER FUNCTION ---
def load_and_prep_image(image_path):
    """
    Handles opening, converting HEIC->RGB, fixing rotation,
    and resizing. Returns a clean PIL Image object.
    """
    try:
        # Open the file (Pillow handles HEIC due to register_heif_opener)
        img = Image.open(image_path)

        # 1. Force Convert to RGB. This fixes the 'no attribute _im' error
        #    and ensures compatibility for HEIC, PNG, and RGBA files.
        img = img.convert("RGB")

        # 2. Fix Orientation (Phone photos are often rotated in metadata)
        img = ImageOps.exif_transpose(img)

        # 3. Resize (Optimize for API speed/cost)
        #    Max 1024px on the longest side is plenty for handwriting OCR
        img.thumbnail((1024, 1024))

        return img
    except Exception as e:
        print(f"Failed to prep image {image_path}: {e}")
        return None


def transcribe_image(img_object):
    """
    Takes a prepped PIL Image object and sends it to Gemini.
    """
    try:
        if img_object is None:
            return "Error: Image load failure"

        prompt = """
        Analyze this image. It is a survey response. 
        Extract the handwritten answers corresponding to the typed questions.
        Return ONLY a raw string in this format:
        Q1: [Answer] | Q2: [Answer] | Q3: [Answer]
        If handwriting is illegible, write [Illegible].
        """

        response = model.generate_content(
            [prompt, img_object], safety_settings=safety_settings
        )
        return response.text.strip()

    except exceptions.ResourceExhausted:
        return "Error: 429 Quota Exceeded"
    except ValueError:
        return "Error: Blocked by Safety Filters"
    except Exception as e:
        return f"Error: {e}"


# --- 3. MAIN EXECUTION ---
with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["Subfolder", "Filename", "Raw Transcription"])

    # Gather files
    files = [
        os.path.join(root, f)
        for root, dirs, filenames in os.walk(IMAGE_FOLDER)
        for f in filenames
        if f.lower().endswith((".heic", ".jpg", ".png"))
    ]
    print(f"Found {len(files)} images. Starting...")

    for i, full_path in enumerate(files):
        filename = os.path.basename(full_path)
        subfolder = os.path.basename(os.path.dirname(full_path))

        print(f"Processing {i+1}/{len(files)}: {subfolder}/{filename}")

        # STEP 1: Load & Prep (The new helper function)
        clean_image = load_and_prep_image(full_path)

        # STEP 2: Transcribe
        transcription = transcribe_image(clean_image)

        writer.writerow([subfolder, filename, transcription])

        if "Quota Exceeded" in transcription:
            time.sleep(30)
        else:
            time.sleep(2)

print("Done.")
