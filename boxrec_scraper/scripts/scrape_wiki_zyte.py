#!/usr/bin/env python3
"""
Scrape BoxRec wiki pages using Zyte API.
Wiki URLs follow pattern: https://boxrec.com/wiki/index.php?title=Human:{boxrec_id}
"""

import json
import os
import sys
import logging
import argparse
import time
from pathlib import Path
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from base64 import b64decode
from dotenv import load_dotenv
from datetime import datetime, timezone

# Load environment variables
load_dotenv()

# Configuration
ZYTE_API_KEY = os.getenv("ZYTE_API_KEY")
ZYTE_API_URL = "https://api.zyte.com/v1/extract"

# Default settings
DEFAULT_WORKERS = 15
DEFAULT_RATE_LIMIT = 1000  # No rate limits on Zyte plan
REQUEST_TIMEOUT = 30

# Rate limiting
request_lock = Lock()
last_request_time = 0

# Progress tracking
progress_lock = Lock()
stats = {
    'total': 0,
    'completed': 0,
    'failed': 0,
    'skipped': 0,
    'start_time': None,
    'requests_per_second': 0
}

# Set up logging
def setup_logging():
    """Set up logging configuration."""
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / 'wiki_scraper.log'),
            logging.StreamHandler()
        ]
    )

def rate_limited_request(rate_limit: float):
    """Ensure we don't exceed rate limits."""
    global last_request_time
    
    request_interval = 1.0 / rate_limit
    
    with request_lock:
        current_time = time.time()
        time_since_last = current_time - last_request_time
        
        if time_since_last < request_interval:
            sleep_time = request_interval - time_since_last
            time.sleep(sleep_time)
        
        last_request_time = time.time()

def print_progress():
    """Print progress statistics."""
    with progress_lock:
        elapsed = time.time() - stats['start_time'] if stats['start_time'] else 0
        if elapsed > 0:
            stats['requests_per_second'] = (stats['completed'] + stats['failed'] + stats['skipped']) / elapsed
        
        logging.info(
            f"Progress: {stats['completed'] + stats['failed'] + stats['skipped']}/{stats['total']} | "
            f"Completed: {stats['completed']} | Failed: {stats['failed']} | Skipped: {stats['skipped']} | "
            f"Rate: {stats['requests_per_second']:.1f} req/s"
        )

def load_blacklist(output_dir):
    """Load blacklist of empty wiki IDs to avoid re-scraping."""
    blacklist_path = output_dir.parent / 'empty_wiki_blacklist.json'
    if blacklist_path.exists():
        try:
            with open(blacklist_path, 'r') as f:
                data = json.load(f)
                return set(data.get('empty_wiki_ids', []))
        except Exception as e:
            logging.warning(f"Error loading blacklist: {e}")
    return set()

def get_wiki_url(boxrec_id):
    """Construct wiki URL from BoxRec ID."""
    return f"https://boxrec.com/wiki/index.php?title=Human:{boxrec_id}"

def fetch_wiki_page_zyte(boxrec_id, output_dir, rate_limit=DEFAULT_RATE_LIMIT, force=False, max_age_days=None, blacklist=None):
    """
    Fetch wiki page using Zyte API.
    Handles redirects automatically.
    """
    # Skip if in blacklist (known empty pages)
    if blacklist and boxrec_id in blacklist:
        with progress_lock:
            stats['skipped'] += 1
            logging.info(f"[SKIP] Blacklisted (empty wiki): {boxrec_id}")
        return True, boxrec_id, "blacklisted_empty"
    
    wiki_url = get_wiki_url(boxrec_id)
    output_file = output_dir / f"wiki_box-pro_{boxrec_id}.html"
    
    # Skip if already downloaded (unless force is True or file is too old)
    if output_file.exists() and not force:
        if max_age_days is not None:
            # Check file age
            file_age_days = (time.time() - output_file.stat().st_mtime) / (24 * 3600)
            if file_age_days < max_age_days:
                with progress_lock:
                    stats['skipped'] += 1
                    logging.info(f"[SKIP] Recent file ({file_age_days:.1f} days old): {output_file.name}")
                return True, boxrec_id, f"recent_file_{file_age_days:.1f}_days"
            # File is too old, re-scrape it
            logging.info(f"[RESCRAPE] File too old ({file_age_days:.1f} days): {output_file.name}")
        else:
            # No age limit specified, skip all existing files
            with progress_lock:
                stats['skipped'] += 1
                logging.info(f"[SKIP] Already exists: {output_file.name}")
            return True, boxrec_id, "already_exists"
    
    # Apply rate limiting
    rate_limited_request(rate_limit)
    
    try:
        # Prepare Zyte API request with proper redirect handling
        api_response = requests.post(
            ZYTE_API_URL,
            json={
                "url": wiki_url,
                "browserHtml": True,
                "actions": [
                    {
                        "action": "waitForTimeout",
                        "timeout": 3
                    }
                ]
            },
            auth=(ZYTE_API_KEY, ""),
            timeout=REQUEST_TIMEOUT
        )
        if api_response.status_code != 200:
            error_details = api_response.text[:500]  # Get first 500 chars of error
            with progress_lock:
                stats['failed'] += 1
                logging.error(f"[ERROR] HTTP {api_response.status_code} for ID {boxrec_id}: {error_details}")
            return False, boxrec_id, f"http_error_{api_response.status_code}"
        
        # Parse response
        data = api_response.json()
        
        # Check if we got redirected to a wiki page
        final_url = data.get("url", wiki_url)
        if '/wiki/index.php' not in final_url:
            with progress_lock:
                stats['failed'] += 1
                logging.warning(f"[FAIL] No wiki page for ID {boxrec_id} - redirected to: {final_url}")
            return False, boxrec_id, f"no_wiki_page_{final_url}"
        
        # Get HTML content from browserHtml
        html_content = data.get("browserHtml", "")
        
        # Save HTML
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        with progress_lock:
            stats['completed'] += 1
            if final_url != wiki_url:
                logging.info(f"[SUCCESS] Downloaded {boxrec_id}: {wiki_url} → {final_url}")
            else:
                logging.info(f"[SUCCESS] Downloaded {boxrec_id}: {wiki_url}")
        
        return True, boxrec_id, final_url
        
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            with progress_lock:
                stats['failed'] += 1
                logging.warning(f"[FAIL] No wiki page for ID {boxrec_id} (404)")
            return False, boxrec_id, "404_not_found"
        else:
            with progress_lock:
                stats['failed'] += 1
                logging.error(f"[ERROR] HTTP error for ID {boxrec_id}: {e}")
            return False, boxrec_id, f"http_error_{e.response.status_code}"
    except Exception as e:
        with progress_lock:
            stats['failed'] += 1
            logging.error(f"[ERROR] Error downloading wiki for ID {boxrec_id}: {e}")
        return False, boxrec_id, str(e)

def get_boxrec_ids_from_html(html_dir):
    """Extract BoxRec IDs from HTML filenames in directory."""
    html_path = Path(html_dir)
    boxer_ids = set()
    
    # Look for boxer profile HTML files
    html_files = list(html_path.glob('*_box-pro_*.html'))
    logging.info(f"Found {len(html_files)} HTML files matching pattern")
    
    for html_file in html_files:
        # Extract ID from filename like: en_box-pro_628407.html
        parts = html_file.stem.split('_')
        if len(parts) >= 3 and parts[1] == 'box-pro':
            boxer_ids.add(parts[2])
    
    logging.info(f"Extracted {len(boxer_ids)} unique boxer IDs from HTML files")
    return sorted(list(boxer_ids))

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
    setup_logging()
    
    if not ZYTE_API_KEY:
        logging.error("ZYTE_API_KEY environment variable not set.")
        logging.info("Please set ZYTE_API_KEY in your environment")
        sys.exit(1)
    
    parser = argparse.ArgumentParser(description='BoxRec Wiki Scraper - High-performance wiki scraper using Zyte API')
    parser.add_argument('source', help='Source: JSON directory or combined JSON file')
    parser.add_argument('--output', default='data/raw/boxrec_wiki', 
                       help='Output directory for wiki HTML files (default: data/raw/boxrec_wiki)')
    parser.add_argument('--workers', type=int, default=DEFAULT_WORKERS,
                       help=f'Number of concurrent workers (default: {DEFAULT_WORKERS})')
    parser.add_argument('--rate-limit', type=float, default=DEFAULT_RATE_LIMIT,
                       help=f'Requests per second limit (default: {DEFAULT_RATE_LIMIT})')
    parser.add_argument('--limit', type=int, help='Limit number of IDs to process')
    parser.add_argument('--force', action='store_true', help='Re-scrape existing files')
    parser.add_argument('--max-age-days', type=int, 
                       help='Re-scrape files older than N days (default: skip all existing)')
    
    args = parser.parse_args()
    
    source = Path(args.source)
    output_dir = Path(args.output)
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Get BoxRec IDs based on source type
    if source.is_file():
        logging.info(f"Reading BoxRec IDs from combined file: {source}")
        boxer_ids = get_boxrec_ids_from_combined(source)
    elif source.is_dir():
        # First try to get IDs from HTML files, then fall back to JSON
        html_ids = get_boxrec_ids_from_html(source)
        if html_ids:
            logging.info(f"Reading BoxRec IDs from HTML files in: {source}")
            boxer_ids = html_ids
        else:
            logging.info(f"No HTML files found, reading BoxRec IDs from JSON directory: {source}")
            boxer_ids = get_boxrec_ids_from_json(source)
    else:
        logging.error(f"Source not found: {source}")
        sys.exit(1)
    
    if not boxer_ids:
        logging.error("No BoxRec IDs found!")
        sys.exit(1)
    
    # Load blacklist of empty wiki IDs
    blacklist = load_blacklist(output_dir)
    logging.info(f"Loaded blacklist with {len(blacklist)} empty wiki IDs")
    
    # Apply limit if specified
    if args.limit:
        boxer_ids = boxer_ids[:args.limit]
    
    logging.info(f"Found {len(boxer_ids)} BoxRec IDs to process with {args.workers} workers")
    
    # Initialize stats
    stats['total'] = len(boxer_ids)
    stats['start_time'] = time.time()
    
    results = []
    
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        # Submit all tasks
        futures = {
            executor.submit(fetch_wiki_page_zyte, boxer_id, output_dir, args.rate_limit, args.force, args.max_age_days, blacklist): boxer_id 
            for boxer_id in boxer_ids
        }
        
        # Process completed tasks
        for i, future in enumerate(as_completed(futures), 1):
            success, boxer_id, result = future.result()
            results.append({
                'boxrec_id': boxer_id,
                'success': success,
                'result': result
            })
            
            # Print progress every 10 items
            if i % 10 == 0:
                print_progress()
    
    # Final summary
    print_progress()
    
    # Save results summary
    summary = {
        'total_ids': stats['total'],
        'completed': stats['completed'],
        'failed': stats['failed'],
        'skipped': stats['skipped'],
        'duration_seconds': time.time() - stats['start_time'],
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'results': results
    }
    
    summary_file = Path('logs') / 'wiki_scrape_summary.json'
    summary_file.parent.mkdir(exist_ok=True)
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    logging.info(f"Summary saved to: {summary_file}")

if __name__ == "__main__":
    main()