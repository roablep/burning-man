import os
import csv
import json
import time
import asyncio
import hashlib
from typing import List, Dict, Any
from google import genai
from dotenv import load_dotenv

# Load Env
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
CACHE_DIR = "analysis_cache"

# Initialize Client
client = genai.Client(api_key=API_KEY)
model_id = "gemini-2.0-flash-lite"

# Ensure cache dir exists
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

def load_data(year=2024, survey_type=None) -> List[Dict[str, Any]]:
    """
    Loads normalized data for a specific year.
    If survey_type (e.g., 'Transformation', 'A') is provided, filters by Subfolder.
    """
    # Look in the 'data' subdirectory relative to the script
    base_dir = os.path.dirname(os.path.abspath(__file__))
    filename = os.path.join(base_dir, "data", f"{year}-field-note-transcriptions-normalized.csv")
    if not os.path.exists(filename):
        print(f"File not found: {filename}")
        return []

    data = []
    with open(filename, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if survey_type:
                # Check if survey_type string is in the Subfolder column (case insensitive)
                if survey_type.lower() not in row.get('Subfolder', '').lower():
                    continue
            data.append(row)
    return data

def get_cache_path(key: str) -> str:
    """Generates a filename for the cache key."""
    hash_key = hashlib.md5(key.encode('utf-8')).hexdigest()
    return os.path.join(CACHE_DIR, f"{hash_key}.json")

async def batch_process_with_llm(
    items: List[str], 
    prompt_template: str, 
    batch_size: int = 10,
    rate_limit_delay: float = 1.0
) -> List[str]:
    """
    Processes a list of text items using the LLM with a given prompt.
    Handles caching and rate limiting.
    Returns a list of responses corresponding to the items.
    """
    results = [None] * len(items)
    uncached_indices = []

    # 1. Check Cache
    for i, item in enumerate(items):
        cache_key = f"{prompt_template}::{item}"
        cache_path = get_cache_path(cache_key)
        
        if os.path.exists(cache_path):
            with open(cache_path, 'r') as f:
                results[i] = json.load(f)['response']
        else:
            uncached_indices.append(i)
    
    if not uncached_indices:
        return results

    print(f"Processing {len(uncached_indices)} items with LLM...")

    # 2. Process Uncached
    # We'll use a semaphore for concurrency
    sem = asyncio.Semaphore(batch_size)

    async def _process(idx):
        item = items[idx]
        cache_key = f"{prompt_template}::{item}"
        cache_path = get_cache_path(cache_key)
        
        async with sem:
            try:
                full_prompt = prompt_template.replace("{{TEXT}}", item)
                response = await client.aio.models.generate_content(
                    model=model_id,
                    contents=full_prompt
                )
                result_text = response.text.strip()
                
                # Save to cache
                with open(cache_path, 'w') as f:
                    json.dump({'response': result_text}, f)
                
                results[idx] = result_text
                
            except Exception as e:
                print(f"Error processing item {idx}: {e}")
                results[idx] = "ERROR"
            
            # Rate limit chill
            await asyncio.sleep(rate_limit_delay)

    tasks = [_process(i) for i in uncached_indices]
    await asyncio.gather(*tasks)
    
    return results

def save_report(filename, content):
    """Saves a markdown report to the reports directory."""
    if not os.path.exists("reports"):
        os.makedirs("reports")
    
    path = os.path.join("reports", filename)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Report saved to {path}")
