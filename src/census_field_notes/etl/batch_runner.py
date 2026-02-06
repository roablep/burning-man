import os
import csv
import json
import asyncio
import time
import io
from pathlib import Path
from typing import List
import logging

# --- LIBRARY IMPORTS ---
from google import genai
from google.genai import types
from dotenv import load_dotenv
import pillow_heif
from PIL import Image, ImageOps

# --- SETUP ---
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
# Using the same folder as img_extract_async.py
IMAGE_FOLDER = "/Users/peter/Downloads/2025 Field Notes Images"
OUTPUT_CSV = "transcriptions_batch.csv"
BATCH_HISTORY_FILE = "batch_history.json"
ALLOWED_EXTS = (".heic", ".heif", ".jpg", ".jpeg", ".png")

# Initialize Client
client = genai.Client(api_key=API_KEY)
model_id = "gemini-2.0-flash-lite"

# Register HEIF opener
pillow_heif.register_heif_opener()

# Prompt exactly as in img_extract_async.py
PROMPT_TEXT = """
Analyze this photo of handwritten survey responses.

Each image may contain:
- ONE OR MORE handwritten survey responses
- An open notebook showing TWO DISTINCT PAGES
- Pages arranged LEFT/RIGHT or TOP/BOTTOM
- Text that may be ROTATED (90, 180, or 270 degrees)

Each survey response corresponds to the same questions (Q1...QN).

TASK (follow this order strictly):
1. If the image is rotated, mentally rotate it to its natural (EN-US) reading orientation.
2. Identify each distinct PAGE shown in the image.
3. Within each page, identify each distinct survey response block.
4. Extract the handwritten answers for EACH response block separately.

IMPORTANT:
- Do NOT merge answers from different people or different sections.
- If two sets of numbered questions appear, they MUST be returned as two separate entries.
- Each response block counts as exactly ONE entry.

OUTPUT FORMAT:
Return a JSON object with a single key "entries".
"entries" must be a LIST of STRINGS.

Each entry must include answers for ALL questions in order, using this format:
"Q1: ... | Q2: ... | Q3: ... | ..."

Example output:
{
  "entries": [
    "Q1: 46 | Q2: Male | Q3: NYC | Q4: ...",
    "Q1: 40 | Q2: Female | Q3: London | Q4: ..."
  ]
}

RULES:
- If only one response block is present, return a single-item list.
- Preserve punctuation and short phrases as written.
- If an answer is missing, use [Blank].
- If handwriting cannot be read with confidence, use [Illegible].
"""

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def upload_images(image_paths: List[str]):
    """Uploads local images to Gemini File API and returns a mapping of path -> file_uri."""
    path_to_uri = {}
    logging.info(f"Starting upload for {len(image_paths)} images...")
    # Semaphore to limit concurrent uploads
    sem = asyncio.Semaphore(10)

    async def _upload(path):
        async with sem:
            try:
                # Load and convert HEIC/HEIF to JPEG for File API
                if path.lower().endswith((".heic", ".heif")):
                    img = Image.open(path)
                    img = ImageOps.exif_transpose(img)
                    img.thumbnail((2048, 2048))
                    buf = io.BytesIO()
                    img.save(buf, format="JPEG", quality=85)
                    buf.seek(0)
                    
                    file_obj = await client.aio.files.upload(
                        file=buf,
                        config=types.UploadFileConfig(
                            mime_type="image/jpeg",
                            display_name=os.path.basename(path)
                        )
                    )
                else:
                    # Direct upload for supported formats (jpg, png)
                    file_obj = await client.aio.files.upload(path=path)
                
                logging.info(f"Uploaded: {os.path.basename(path)}")
                return path, file_obj.uri
            except Exception as e:
                logging.error(f"Failed to upload {path}: {e}")
                return path, None

    tasks = [_upload(p) for p in image_paths]
    results = await asyncio.gather(*tasks)
    
    for path, uri in results:
        if uri:
            path_to_uri[path] = uri
            
    return path_to_uri

async def submit_batch_job(image_folder: str, limit_files: int = None):
    # 1. Gather files
    all_files = []
    for root, _, filenames in os.walk(image_folder):
        for f in filenames:
            if f.lower().endswith(ALLOWED_EXTS):
                all_files.append(os.path.join(root, f))
    
    if limit_files:
        all_files = all_files[:limit_files]

    if not all_files:
        logging.warning("No files found.")
        return

    # 2. Upload Images
    path_to_uri = await upload_images(all_files)
    if not path_to_uri:
        logging.error("No images uploaded successfully.")
        return

    # 3. Create Batch Requests
    batch_requests = []
    for path, file_uri in path_to_uri.items():
        # Custom ID to identify the image in the results
        subfolder = os.path.basename(os.path.dirname(path))
        filename = os.path.basename(path)
        folder_name = Path(image_folder).name
        custom_id = f"{folder_name}/{subfolder}/{filename}"
        
        request = types.BatchJobRequest(
            custom_id=custom_id,
            model=model_id,
            contents=[
                PROMPT_TEXT, 
                types.Part.from_uri(file_uri, mime_type="image/jpeg")
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                safety_settings=[
                    types.SafetySetting(category='HARM_CATEGORY_HARASSMENT', threshold='BLOCK_NONE'),
                    types.SafetySetting(category='HARM_CATEGORY_HATE_SPEECH', threshold='BLOCK_NONE'),
                    types.SafetySetting(category='HARM_CATEGORY_SEXUALLY_EXPLICIT', threshold='BLOCK_NONE'),
                    types.SafetySetting(category='HARM_CATEGORY_DANGEROUS_CONTENT', threshold='BLOCK_NONE'),
                ]
            )
        )
        batch_requests.append(request)

    # 4. Submit Job
    logging.info("Submitting batch job...")
    job = await client.aio.batches.create(
        model=model_id,
        requests=batch_requests
    )
    
    logging.info(f"Batch Job Created! ID: {job.name}")
    save_batch_history(job.name)

async def retrieve_batch_results(job_name: str):
    logging.info(f"Checking status for job: {job_name}")
    job = await client.aio.batches.get(name=job_name)
    
    logging.info(f"Job Status: {job.state}")
    
    if job.state == "COMPLETED":
        logging.info("Job completed. Downloading results...")
        
        file_exists = os.path.isfile(OUTPUT_CSV)
        with open(OUTPUT_CSV, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["Folder", "Subfolder", "Filename", "EntryIndex", "Raw Transcription"])

            # Use list_results to iterate over items
            async for item in client.aio.batches.list_results(name=job_name):
                custom_id = item.custom_id
                parts = custom_id.split("/")
                # Handle cases where custom_id might not have exactly 3 parts if folder name has /
                if len(parts) >= 3:
                    folder, subfolder, filename = parts[0], parts[1], parts[2]
                else:
                    folder, subfolder, filename = "Unknown", "Unknown", custom_id

                try:
                    # In Batch results, response is nested
                    response_text = item.response.candidates[0].content.parts[0].text
                    data = json.loads(response_text)
                    entries = data.get("entries", ["No entries found"])
                    
                    for i, entry in enumerate(entries, 1):
                        writer.writerow([folder, subfolder, filename, i, entry])
                except Exception as e:
                    logging.error(f"Error parsing result for {custom_id}: {e}")
                    writer.writerow([folder, subfolder, filename, 0, f"Error: {e}"])
        
        logging.info(f"Results written to {OUTPUT_CSV}")
    elif job.state == "FAILED":
        logging.error(f"Job Failed: {job.error}")
    else:
        logging.info(f"Job is still {job.state}. Check back later using: python src/census/batch_runner.py --retrieve {job_name}")

def save_batch_history(job_name):
    history = []
    if os.path.exists(BATCH_HISTORY_FILE):
        with open(BATCH_HISTORY_FILE, "r") as f:
            history = json.load(f)
    history.append({"job_name": job_name, "created_at": time.time(), "status": "SUBMITTED"})
    with open(BATCH_HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Gemini Batch API Runner")
    parser.add_argument("--submit", action="store_true", help="Submit a new batch job")
    parser.add_argument("--retrieve", type=str, help="Retrieve results for a specific Job ID")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of files for testing")
    args = parser.parse_args()

    if args.submit:
        asyncio.run(submit_batch_job(IMAGE_FOLDER, args.limit))
    elif args.retrieve:
        asyncio.run(retrieve_batch_results(args.retrieve))
    else:
        print("Please specify --submit or --retrieve <job_id>")
