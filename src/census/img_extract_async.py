import os
import csv
import asyncio
import time
from pathlib import Path

# --- LIBRARY IMPORTS ---
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from dotenv import load_dotenv

# --- IMAGE HANDLING IMPORTS ---
import PIL.PngImagePlugin
import PIL.JpegImagePlugin
import pillow_heif
from PIL import Image, ImageOps

# --- 1. SETUP ---
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
IMAGE_FOLDER = "/Users/peter/Downloads/2025 Notes"
OUTPUT_CSV = "transcriptions.csv"

# Configure settings
pillow_heif.register_heif_opener()
genai.configure(api_key=API_KEY)

# Use the lighter model for speed, but fallback aliases are safer
model = genai.GenerativeModel("gemini-2.5-flash-lite")

# Safety Settings
safety_settings = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
}


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
    """
    The main worker unit.
    1. Acquires semaphore (limit concurrency)
    2. Offloads image prep to thread
    3. Awaits API response
    4. Puts result in a queue for writing
    """
    p = Path(full_path)
    folder = Path(IMAGE_FOLDER).name # p.parent.parent.name
    filename = os.path.basename(full_path)
    subfolder = os.path.basename(os.path.dirname(full_path))
    unique_id = f"{folder}/{subfolder}/{filename}"

    if unique_id in processed_set:
        return

    async with sem:  # Limits active tasks
        print(f"Starting: {unique_id}")

        # STEP 1: Load Image (CPU Bound -> Thread)
        # We use asyncio.to_thread to run the blocking PIL code
        img_object = await asyncio.to_thread(load_and_prep_image_sync, full_path)

        if img_object is None:
            return

        # STEP 2: Transcribe (IO Bound -> Await)
        try:
            prompt = """
            Analyze this image. It is a survey response. 
            Extract the handwritten answers corresponding to the typed questions.
            Return ONLY a raw string in this format:
            Q1: [Answer] | Q2: [Answer] | Q3: [Answer] | ...
            If handwriting is illegible, write [Illegible].
            """

            # Use the NATIVE Async method
            response = await model.generate_content_async(
                [prompt, img_object], safety_settings=safety_settings
            )
            transcription = response.text.strip()

        except Exception as e:
            transcription = f"Error: {e}"
            # Simple rate limit backoff (very basic)
            if "429" in str(e) or "Quota" in str(e):
                print(f"Rate Limit Hit on {filename}. Cooling down...")
                await asyncio.sleep(10)

        # STEP 3: Send to CSV Writer (Safe)
        # We don't write to file here directly to avoid race conditions.
        # We put it in a queue and let a dedicated writer handle it.
        await writer_queue.put([folder, subfolder, filename, transcription])
        print(f"Finished: {unique_id}")


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
            writer.writerow(["Folder", "Subfolder", "Filename", "Raw Transcription"])

    # Gather all files
    all_files = [
        os.path.join(root, f)
        for root, dirs, filenames in os.walk(IMAGE_FOLDER)
        for f in filenames
        if f.lower().endswith((".heic", ".jpg", ".png"))
    ]

    # Filter out already done
    files_to_do = [
        f
        for f in all_files
        if f"{os.path.basename(os.path.dirname(f))}/{os.path.basename(f)}"
        not in processed_files
    ][:50]
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
