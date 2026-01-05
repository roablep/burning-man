import os
import csv
import time
from pathlib import Path

# --- LIBRARY IMPORTS ---
from google import genai
from google.genai import types
from dotenv import load_dotenv

# --- IMAGE HANDLING IMPORTS ---
# We explicitly import these plugins to prevent "module has no attribute" errors
import PIL.PngImagePlugin
import PIL.JpegImagePlugin
import pillow_heif
from PIL import Image, ImageOps

# --- 1. SETUP ---
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
IMAGE_FOLDER = "/Users/peter/Downloads/2025 Notes"
OUTPUT_CSV = "transcriptions.csv"

# Configure the HEIC opener
pillow_heif.register_heif_opener()

client = genai.Client(api_key=API_KEY)
model_id = "gemini-2.0-flash-lite" # Updated to a valid model name for the new SDK

print("Available Models:")
for m in client.models.list():
    print(f"- {m.name}")

# --- SAFETY SETTINGS (NEW SDK FORMAT) ---
config = types.GenerateContentConfig(
    safety_settings=[
        types.SafetySetting(category='HARM_CATEGORY_HARASSMENT', threshold='BLOCK_NONE'),
        types.SafetySetting(category='HARM_CATEGORY_HATE_SPEECH', threshold='BLOCK_NONE'),
        types.SafetySetting(category='HARM_CATEGORY_SEXUALLY_EXPLICIT', threshold='BLOCK_NONE'),
        types.SafetySetting(category='HARM_CATEGORY_DANGEROUS_CONTENT', threshold='BLOCK_NONE'),
    ]
)


# --- 2. ROBUST IMAGE LOADER ---
def load_and_prep_image(image_path):
    """
    Robust loader that handles HEIC/PNG/JPG and fixes orientation/mode.
    """
    try:
        img = None

        # MANUAL HEIC DECODE (Bypasses lazy-loading bugs)
        if image_path.lower().endswith((".heic", ".heif")):
            heif_file = pillow_heif.read_heif(image_path)
            img = Image.frombytes(
                heif_file.mode,
                heif_file.size,
                heif_file.data,
                "raw",
            )
        else:
            # Standard Open
            img = Image.open(image_path)

        # Force Loading: Copies image to memory and closes file pointer
        img.load()

        # 1. Convert to RGB (Fixes 'no attribute _im' and Alpha channel issues)
        if img.mode != "RGB":
            img = img.convert("RGB")

        # 2. Fix Orientation (EXIF rotation)
        img = ImageOps.exif_transpose(img)

        # 3. Resize (Max 1024px)
        img.thumbnail((1024, 1024))

        return img

    except Exception as e:
        print(f"FAILED to load {image_path}: {e}")
        return None


def transcribe_image(img_object):
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

        response = client.models.generate_content(
            model=model_id,
            contents=[prompt, img_object],
            config=config
        )
        return response.text.strip()

    except Exception as e:
        # Catch-all for API errors
        return f"Error: {e}"


# --- 3. MAIN EXECUTION ---
# Check existing progress to allow resuming
processed_files = set()
if os.path.exists(OUTPUT_CSV):
    with open(OUTPUT_CSV, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        try:
            next(reader)  # Skip header
            for row in reader:
                if len(row) > 1:
                    # Store "Subfolder/Filename" unique ID
                    processed_files.add(f"{row[0]}/{row[1]}/{row[2]}")
        except StopIteration:
            pass

print(f"Resuming... {len(processed_files)} images already processed.")

# Append mode 'a'
write_header = not os.path.exists(OUTPUT_CSV)
with open(OUTPUT_CSV, "a", newline="", encoding="utf-8") as csvfile:
    writer = csv.writer(csvfile)
    if write_header:
        writer.writerow(["Folder", "Subfolder", "Filename", "Raw Transcription"])

    # Recursive file search
    files = [
        os.path.join(root, f)
        for root, dirs, filenames in os.walk(IMAGE_FOLDER)
        for f in filenames
        if f.lower().endswith((".heic", ".jpg", ".png"))
    ]
    print(f"Found {len(files)} total images.")

    process_files = files[:1]
    print(f"Using {len(process_files)} total images.")

    for i, full_path in enumerate(process_files):
        p = Path(full_path)
        folder = Path(IMAGE_FOLDER).name # p.parent.parent.name
        filename = os.path.basename(full_path)
        subfolder = os.path.basename(os.path.dirname(full_path))
        unique_id = f"{folder}/{subfolder}/{filename}"

        if unique_id in processed_files:
            continue

        print(f"Processing {i+1}/{len(files)}: {unique_id}")

        clean_image = load_and_prep_image(full_path)
        transcription = transcribe_image(clean_image)

        writer.writerow([folder, subfolder, filename, transcription])

        # Simple rate limiting
        if "Quota" in transcription:
            print("Quota hit. Sleeping 30s...")
            time.sleep(30)
        else:
            time.sleep(2)  # 2 seconds between calls is safe for Flash

print("Done.")
