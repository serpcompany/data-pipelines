#!/usr/bin/env python3
"""
Scrape BoxRec wiki pages using Zyte API.
Wiki URLs follow pattern: https://boxrec.com/wiki/index.php?title=Human:{boxrec_id}
"""

import json
import os
import sys
import logging
from pathlib import Path
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from base64 import b64decode
from dotenv import load_dotenv
#from tqdm import tqdm

# Load environment variables
env_path = Path('..') / '.env'
load_dotenv(dotenv_path=env_path)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Configuration
ZYTE_API_KEY = os.getenv("ZYTE_API_KEY")
if not ZYTE_API_KEY:
    logging.error("ZYTE_API_KEY environment variable not set.")
    logging.info("Please create a ../.env file with ZYTE_API_KEY=your_key")
    exit(1)

# Zyte API endpoint
ZYTE_API_URL = "https://api.zyte.com/v1/extract"

# Thread safety
lock = Lock()
progress_count = 0

def get_wiki_url(boxrec_id):
    """Construct wiki URL from BoxRec ID."""
    return f"https://boxrec.com/wiki/index.php?title=Human:{boxrec_id}"

def fetch_wiki_page_zyte(boxrec_id, output_dir):
    """
    Fetch wiki page using Zyte API.
    Handles redirects automatically.
    """
    wiki_url = get_wiki_url(boxrec_id)
    output_file = output_dir / f"wiki_box-pro_{boxrec_id}.html"
    
    # Skip if already downloaded
    if output_file.exists():
        with lock:
            logging.info(f"✅ Already exists: {output_file.name}")
        return True, boxrec_id, "already_exists"
    
    try:
        # Prepare Zyte API request
        api_response = requests.post(
            ZYTE_API_URL,
            json={
                "url": wiki_url,
                "httpResponseBody": True,
                "httpResponseHeaders": True
            },
            auth=(ZYTE_API_KEY, ""),
            timeout=120
        )
        api_response.raise_for_status()
        
        # Parse response
        data = api_response.json()
        
        # Check if we got redirected to a wiki page
        final_url = data.get("url", wiki_url)
        if '/wiki/index.php' not in final_url:
            with lock:
                logging.warning(f"❌ No wiki page for ID {boxrec_id} - redirected to: {final_url}")
            return False, boxrec_id, f"no_wiki_page_{final_url}"
        
        # Decode HTML content
        html_content = b64decode(data["httpResponseBody"]).decode('utf-8')
        
        # Save HTML
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        with lock:
            global progress_count
            progress_count += 1
            if final_url != wiki_url:
                logging.info(f"✅ [{progress_count}] Downloaded {boxrec_id}: {wiki_url} → {final_url}")
            else:
                logging.info(f"✅ [{progress_count}] Downloaded {boxrec_id}: {wiki_url}")
        
        return True, boxrec_id, final_url
        
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            with lock:
                logging.warning(f"❌ No wiki page for ID {boxrec_id} (404)")
            return False, boxrec_id, "404_not_found"
        else:
            with lock:
                logging.error(f"❌ HTTP error for ID {boxrec_id}: {e}")
            return False, boxrec_id, f"http_error_{e.response.status_code}"
    except Exception as e:
        with lock:
            logging.error(f"❌ Error downloading wiki for ID {boxrec_id}: {e}")
        return False, boxrec_id, str(e)

def get_boxrec_ids_from_json(json_dir):
    """Extract BoxRec IDs from existing JSON files."""
    json_path = Path(json_dir)
    boxer_ids = []
    
    for json_file in json_path.glob('*box-pro*.json'):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if 'boxrec_id' in data:
                    boxer_ids.append(data['boxrec_id'])
        except Exception as e:
            logging.error(f"Error reading {json_file}: {e}")
    
    return boxer_ids

def get_boxrec_ids_from_combined(combined_file):
    """Extract BoxRec IDs from combined JSON file."""
    try:
        with open(combined_file, 'r', encoding='utf-8') as f:
            content = f.read()
            # Handle the metadata + array format
            if content.startswith('{'):
                # Split by the comma after metadata
                parts = content.split('},\n[', 1)
                if len(parts) == 2:
                    # Parse just the array part
                    boxers = json.loads('[' + parts[1])
                else:
                    # Try parsing as regular JSON
                    data = json.loads(content)
                    boxers = data if isinstance(data, list) else []
            else:
                boxers = json.loads(content)
        
        return [boxer['boxrec_id'] for boxer in boxers if 'boxrec_id' in boxer]
    except Exception as e:
        logging.error(f"Error reading combined file: {e}")
        return []

def main():
    if len(sys.argv) < 2:
        print("Usage: python scrape_wiki_zyte.py <source> [output_dir]")
        print("\nSource can be:")
        print("  - Path to JSON directory (e.g., data/raw/boxrec_json_v2/)")
        print("  - Path to combined JSON file (e.g., outputs/combined_boxers.json)")
        print("\nOutput directory defaults to: data/raw/boxrec_wiki/")
        sys.exit(1)
    
    source = Path(sys.argv[1])
    output_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else Path('data/raw/boxrec_wiki')
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Get BoxRec IDs based on source type
    if source.is_file():
        logging.info(f"Reading BoxRec IDs from combined file: {source}")
        boxer_ids = get_boxrec_ids_from_combined(source)
    elif source.is_dir():
        logging.info(f"Reading BoxRec IDs from JSON directory: {source}")
        boxer_ids = get_boxrec_ids_from_json(source)
    else:
        logging.error(f"Source not found: {source}")
        sys.exit(1)
    
    if not boxer_ids:
        logging.error("No BoxRec IDs found!")
        sys.exit(1)
    
    logging.info(f"Found {len(boxer_ids)} BoxRec IDs to process")
    
    # Download wiki pages concurrently
    successful = 0
    failed = 0
    no_wiki = 0
    results = []
    
    # Use ThreadPoolExecutor for concurrent downloads
    max_workers = 5  # Zyte can handle more concurrent requests
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        futures = {executor.submit(fetch_wiki_page_zyte, boxer_id, output_dir): boxer_id 
                  for boxer_id in boxer_ids}
        
        # Process completed tasks
        for future in as_completed(futures):
            success, boxer_id, result = future.result()
            results.append({
                'boxrec_id': boxer_id,
                'success': success,
                'result': result
            })
            
            if success:
                successful += 1
            else:
                if "no_wiki_page" in result or "404" in result:
                    no_wiki += 1
                else:
                    failed += 1
    
    # Summary
    logging.info(f"\nWiki scraping complete:")
    logging.info(f"  Successful: {successful}")
    logging.info(f"  No wiki page: {no_wiki}")
    logging.info(f"  Failed: {failed}")
    logging.info(f"  Total: {len(boxer_ids)}")
    
    # Save results summary
    summary_file = output_dir / 'wiki_scrape_summary.json'
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump({
            'total_boxers': len(boxer_ids),
            'successful': successful,
            'no_wiki_page': no_wiki,
            'failed': failed,
            'results': results
        }, f, indent=2)
    
    logging.info(f"\nSummary saved to: {summary_file}")

if __name__ == "__main__":
    main()