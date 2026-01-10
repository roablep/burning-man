import os
import csv
import json
import asyncio
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import random
from collections import defaultdict

# --- LIBRARY IMPORTS ---
from google import genai
from google.genai import types
from dotenv import load_dotenv

# --- IMAGE HANDLING IMPORTS ---
import PIL.PngImagePlugin
import pillow_heif
from PIL import Image, ImageOps

# --- 1. SETUP ---
load_dotenv()
ALLOWED_EXTS = (".heic", ".heif", ".jpg", ".jpeg", ".png")
API_KEY = os.getenv("GEMINI_API_KEY")
IMAGE_FOLDER = "/Users/peter/Downloads/2024 Field Notes Images Pt 2"
OUTPUT_CSV = "2024-field-note-transcriptions-pt2.csv"
LIMIT_FILES = None  # Set to an integer for testing

# Configure settings
pillow_heif.register_heif_opener()
client = genai.Client(api_key=API_KEY)

# Use the lighter model for speed, but fallback aliases are safer
model_id = "gemini-2.0-flash-lite"


# class SurveyEntry(BaseModel):
#     page_index: Optional[int] = Field(
#         None,
#         description="Page number within the image (1-based), if known."
#     )
#     entry_index: Optional[int] = Field(
#         None,
#         description="Entry order within the page (1-based), if known."
#     )
#     response: List[str] = Field(
#         ...,
#         description="Survey responses serialized as strings: 'Q1: ... | Q2: ... | Q3: ...'",
#         examples=["Q1: <answer> | Q2: [Blank] | Q3: [Illegible]"],
#     )


class SurveyExtraction(BaseModel):
    entries: List[str] = Field(
        ...,
        description="Survey responses serialized as strings: 'Q1: ... | Q2: ... | Q3: ...'",
    )


# Safety Settings
config = types.GenerateContentConfig(
    response_mime_type="application/json",
    response_schema=SurveyExtraction,
    safety_settings=[
        types.SafetySetting(category='HARM_CATEGORY_HARASSMENT', threshold='BLOCK_NONE'),
        types.SafetySetting(category='HARM_CATEGORY_HATE_SPEECH', threshold='BLOCK_NONE'),
        types.SafetySetting(category='HARM_CATEGORY_SEXUALLY_EXPLICIT', threshold='BLOCK_NONE'),
        types.SafetySetting(category='HARM_CATEGORY_DANGEROUS_CONTENT', threshold='BLOCK_NONE'),
    ]
)

def choose_random_files_for_testing(
    image_folder: str,
    limit_files: int,
    seed: int | None = 1337,
) -> list[str]:
    """
    Randomly pick subfolders within IMAGE_FOLDER, and randomly pick files within those
    subfolders, until we have up to `limit_files` total files.

    - Fair-ish distribution across subfolders (does not just sample globally).
    - If there are fewer total images than limit_files, returns them all.
    """
    rng = random.Random(seed)

    # Collect direct child subfolders that contain images (recursively)
    subfolder_to_files: dict[str, list[str]] = defaultdict(list)

    for root, dirs, filenames in os.walk(image_folder):
        # Define "subfolder" as the first path segment under IMAGE_FOLDER
        rel = os.path.relpath(root, image_folder)
        top = rel.split(os.sep)[0] if rel != "." else ""  # "" = root itself

        for fn in filenames:
            if fn.lower().endswith(ALLOWED_EXTS):
                full_path = os.path.join(root, fn)
                subfolder_to_files[top].append(full_path)

    # Drop empty buckets
    subfolder_to_files = {k: v for k, v in subfolder_to_files.items() if v}
    if not subfolder_to_files:
        return []

    # Shuffle files within each bucket so per-bucket pops are random
    for k in subfolder_to_files:
        rng.shuffle(subfolder_to_files[k])

    # Randomize bucket order for "randomly pick subfolders"
    buckets = list(subfolder_to_files.keys())
    rng.shuffle(buckets)

    picked: list[str] = []

    # Round-robin across randomly ordered buckets until we hit the limit
    while len(picked) < limit_files:
        progressed = False
        for b in buckets:
            if len(picked) >= limit_files:
                break
            if subfolder_to_files[b]:
                picked.append(subfolder_to_files[b].pop())
                progressed = True
        if not progressed:
            break  # all buckets exhausted

    return picked

def parse_and_validate(raw_text: str) -> SurveyExtraction:
    cleaned = raw_text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[-1].rsplit("```", 1)[0]

    return SurveyExtraction.model_validate_json(cleaned)
# --- 2. BLOCKING HELPER FUNCTIONS (Run in ThreadPool) ---
def load_and_prep_image_sync(image_path):
    """
    Standard synchronous image loading logic.
    We will run this in a separate thread so it doesn't block the async loop.
    """
    try:
        img = None
        if image_path.lower().endswith((".heic", ".heif")):
            heif_file = pillow_heif.read_heif(image_path)
            img = Image.frombytes(
                heif_file.mode,
                heif_file.size,
                heif_file.data,
                "raw",
            )
        else:
            img = Image.open(image_path)

        img.load()  # Force load
        if img.mode != "RGB":
            img = img.convert("RGB")
        img = ImageOps.exif_transpose(img)
        img.thumbnail((1024, 1024))
        return img
    except Exception as e:
        print(f"FAILED to load {image_path}: {e}")
        return None


# --- 3. ASYNC WORKER ---
async def process_single_image(sem, full_path, writer_queue, processed_set):
    p = Path(full_path)
    folder = Path(IMAGE_FOLDER).name 
    filename = os.path.basename(full_path)
    subfolder = os.path.basename(os.path.dirname(full_path))
    unique_id = f"{folder}/{subfolder}/{filename}"

    if unique_id in processed_set:
        return

    async with sem:
        entries: List[str] = []
        print(f"Starting: {unique_id}")

        img_object = await asyncio.to_thread(load_and_prep_image_sync, full_path)

        if img_object is None:
            return

        try:
            # --- IMPROVED PROMPT ---
            # We explicitly ask for a list of entries to handle multiple people per page
            prompt = """
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

            response = await client.aio.models.generate_content(
                model=model_id,
                contents=[prompt, img_object],
                config=config
            )
            
            # --- PARSING LOGIC ---
            try:

                extraction = parse_and_validate(response.text)
                entries = extraction.entries
                if not extraction.entries:
                    # Fallback if empty
                    entries = ["No entries found"]
            except Exception as e:
                print(f"Pydantic Parsing failed: {e}")

                try:

                    # Gemini usually returns raw text, but with response_mime_type="application/json"
                    # it should be valid JSON.
                    data = json.loads(response.text)
                    entries = data.get("entries", [])
                    if not entries:
                        # Fallback if empty
                        entries = ["No entries found"]
   
                except json.JSONDecodeError:
                    print("Fallback JSON parsing also failed.")
                    entries = [response.text.strip()]

                    if not entries:
                        # Fallback if empty
                        entries = ["No entries found"]

            # --- WRITE LOOP ---
            # Now we loop through the found entries and write 1 row per entry
            for i, entry_text in enumerate(entries, start=1):
                # Structure: Folder, Subfolder, Filename, Entry_ID, Transcription
                await writer_queue.put([folder, subfolder, filename, i, entry_text])

        except Exception as e:
            error_msg = f"Error: {e}"
            if "429" in str(e) or "Quota" in str(e):
                print(f"Rate Limit Hit on {filename}. Cooling down...")
                await asyncio.sleep(10)
            
            # Log the error as a single row
            await writer_queue.put([folder, subfolder, filename, 0, error_msg])

        print(f"Finished: {unique_id} ({len(entries)} entries found)")

# --- 4. CSV WRITER COROUTINE ---
async def csv_writer_worker(queue, filename):
    """
    Listens to the queue and writes rows to CSV sequentially.
    This ensures thread-safe file writing.
    """
    with open(filename, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        while True:
            row = await queue.get()
            if row is None:  # Sentinel value to stop
                break
            writer.writerow(row)
            f.flush()  # Ensure it hits disk immediately
            queue.task_done()


# --- 5. MAIN ENTRY POINT ---
async def main():
    # Load existing progress
    processed_files = set()
    if os.path.exists(OUTPUT_CSV):
        with open(OUTPUT_CSV, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            try:
                next(reader)
                for row in reader:
                    if len(row) > 1:
                        processed_files.add(f"{row[0]}/{row[1]}/{row[2]}")
            except StopIteration:
                pass
    print(f"Found {len(processed_files)} previously processed.")

    # Write Header if new
    if not os.path.exists(OUTPUT_CSV):
        with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Folder", "Subfolder", "Filename", "EntryIndex", "Raw Transcription"])



    # Gather all files (for normal full run)
    all_files = [
        os.path.join(root, f)
        for root, dirs, filenames in os.walk(IMAGE_FOLDER)
        for f in filenames
        if f.lower().endswith(ALLOWED_EXTS)
    ]

    # Filter out already done (NOTE: your processed_files uses folder/subfolder/filename)
    def make_unique_id(path: str) -> str:
        p = Path(path)
        folder = Path(IMAGE_FOLDER).name
        subfolder = p.parent.name
        filename = p.name
        return f"{folder}/{subfolder}/{filename}"

    remaining_files = [f for f in all_files if make_unique_id(f) not in processed_files]

    # If LIMIT_FILES is set, randomly choose subfolders + files within them
    if isinstance(LIMIT_FILES, int) and LIMIT_FILES > 0:
        # Choose from remaining_files only:
        # We'll temporarily point the sampler at a dict built from remaining_files
        # by using a tiny override approach.

        # Build buckets from remaining_files
        buckets: dict[str, list[str]] = defaultdict(list)
        for f in remaining_files:
            p = Path(f)
            rel = os.path.relpath(p.parent, IMAGE_FOLDER)
            top = rel.split(os.sep)[0] if rel != "." else ""
            buckets[top].append(f)

        rng = random.Random(1337)
        for k in list(buckets.keys()):
            if not buckets[k]:
                del buckets[k]
            else:
                rng.shuffle(buckets[k])

        bucket_keys = list(buckets.keys())
        rng.shuffle(bucket_keys)

        files_to_do: list[str] = []
        while len(files_to_do) < LIMIT_FILES:
            progressed = False
            for k in bucket_keys:
                if len(files_to_do) >= LIMIT_FILES:
                    break
                if buckets[k]:
                    files_to_do.append(buckets[k].pop())
                    progressed = True
            if not progressed:
                break

    else:
        files_to_do = remaining_files

    print(f"Processing {len(files_to_do)} new images...")

    # CONFIGURATION
    # Semaphore = How many concurrent API calls?
    # Gemini Flash has high throughput, but start with 5-10 to be safe.
    sem = asyncio.Semaphore(10)
    queue = asyncio.Queue()

    # Start the Writer
    writer_task = asyncio.create_task(csv_writer_worker(queue, OUTPUT_CSV))

    # Create worker tasks
    tasks = [process_single_image(sem, f, queue, processed_files) for f in files_to_do]

    # Run all image tasks
    await asyncio.gather(*tasks)

    # Stop the writer
    await queue.put(None)  # Signal stop
    await writer_task
    print("All done.")


if __name__ == "__main__":
    asyncio.run(main())
