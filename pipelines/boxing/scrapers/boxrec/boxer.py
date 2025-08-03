#!/usr/bin/env python3
"""
BoxRec Scraper using Zyte API.
Fetches HTML pages and stores them temporarily before validation.
"""

import json
import time
import logging
import csv
from pathlib import Path
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from urllib.parse import urlparse
from base64 import b64decode
from typing import List, Dict, Optional

try:
    import requests
except ImportError:
    raise ImportError("Please install requests: pip install requests")

from ...utils.config import (
    ZYTE_API_KEY, ZYTE_API_URL, PENDING_HTML_DIR, LOG_DIR,
    DEFAULT_WORKERS, DEFAULT_RATE_LIMIT, REQUEST_TIMEOUT
)
from ...utils.filename_utils import create_filename_from_url

# Rate limiting
request_lock = Lock()
last_request_time = 0

# Progress tracking
progress_lock = Lock()
stats = {
    'total': 0,
    'completed': 0,
    'failed': 0,
    'start_time': None,
    'requests_per_second': 0
}

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / 'scraper.log'),
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



def fetch_url(url: str, rate_limit: float, max_age_days: Optional[int] = None) -> Dict:
    """Fetch a single URL with rate limiting and error handling."""
    
    # Create filename
    filename = create_filename_from_url(url)
    output_file = PENDING_HTML_DIR / filename
    
    # Check if file exists and is recent enough
    if output_file.exists() and max_age_days is not None:
        file_age_days = (time.time() - output_file.stat().st_mtime) / (24 * 3600)
        if file_age_days < max_age_days:
            with progress_lock:
                stats['completed'] += 1  # Count as completed since we have it
            return {
                'url': url,
                'status': 'skipped',
                'filename': filename,
                'age_days': file_age_days
            }
    
    # Use URL as-is (no allSports parameter needed anymore)
    fetch_url = url
    
    # Rate limiting
    rate_limited_request(rate_limit)
    
    try:
        # Make API request
        response = requests.post(
            ZYTE_API_URL,
            json={
                "url": fetch_url,
                "httpResponseBody": True,
                "httpResponseHeaders": True
            },
            auth=(ZYTE_API_KEY, ""),
            timeout=REQUEST_TIMEOUT
        )
        
        response.raise_for_status()
        data = response.json()
        
        # Save HTML to temp directory
        html_content = b64decode(data["httpResponseBody"]).decode('utf-8')
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # Update stats
        with progress_lock:
            stats['completed'] += 1
            if stats['completed'] % 5 == 0 or stats['completed'] == 1:
                elapsed = time.time() - stats['start_time']
                stats['requests_per_second'] = stats['completed'] / elapsed
                completion_pct = (stats['completed'] / stats['total']) * 100
                eta_seconds = (stats['total'] - stats['completed']) / stats['requests_per_second'] if stats['requests_per_second'] > 0 else 0
                eta_minutes = eta_seconds / 60
                
                logging.info(f"Progress: {stats['completed']}/{stats['total']} "
                           f"({completion_pct:.1f}%) - {stats['requests_per_second']:.2f} req/s - "
                           f"ETA: {eta_minutes:.1f} minutes")
        
        return {
            'url': url,
            'status': 'success',
            'filename': filename,
            'size': len(html_content)
        }
        
    except requests.exceptions.HTTPError as e:
        with progress_lock:
            stats['failed'] += 1
            if e.response.status_code == 429:
                logging.warning(f"⚠️  Rate limited on {url} - too many requests")
            elif e.response.status_code == 403:
                logging.warning(f"⚠️  Access denied on {url} - might be login page")
        
        return {
            'url': url,
            'status': 'failed',
            'error': f"HTTP {e.response.status_code}",
            'message': str(e)
        }
        
    except Exception as e:
        with progress_lock:
            stats['failed'] += 1
        
        logging.error(f"Exception fetching {url}: {type(e).__name__}: {e}")
        
        return {
            'url': url,
            'status': 'failed',
            'error': 'exception',
            'message': str(e)
        }


def load_urls_from_csv(csv_file: Path) -> List[str]:
    """Load URLs from CSV file."""
    urls = []
    
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Handle different CSV formats
                url = row.get('url') or row.get('URL')
                if url:
                    urls.append(url)
        
        logging.info(f"Loaded {len(urls)} URLs from {csv_file}")
        return urls
        
    except Exception as e:
        logging.error(f"Error loading CSV file {csv_file}: {e}")
        return []


def scrape_urls(urls: List[str], max_workers: int = DEFAULT_WORKERS, 
                rate_limit: float = DEFAULT_RATE_LIMIT, max_age_days: Optional[int] = None) -> List[Dict]:
    """Scrape multiple URLs concurrently."""
    if not ZYTE_API_KEY:
        logging.error("ZYTE_API_KEY not found in environment variables")
        logging.error("Please set ZYTE_API_KEY in your .env file")
        return []
    
    # Initialize stats
    stats['total'] = len(urls)
    stats['start_time'] = time.time()
    stats['completed'] = 0
    stats['failed'] = 0
    
    logging.info(f"Starting scrape: {len(urls)} URLs with {max_workers} workers")
    logging.info(f"Rate limit: {rate_limit} requests/second")
    logging.info(f"Output directory: {PENDING_HTML_DIR}")
    if max_age_days:
        logging.info(f"Skipping files newer than {max_age_days} days")
    
    results = []
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_url = {
            executor.submit(fetch_url, url, rate_limit, max_age_days): url 
            for url in urls
        }
        
        # Process completed tasks
        for future in as_completed(future_to_url):
            url = future_to_url[future]
            try:
                result = future.result()
                results.append(result)
                
            except Exception as e:
                logging.error(f"Unexpected error for {url}: {e}")
                results.append({
                    'url': url,
                    'status': 'failed',
                    'error': 'future_exception',
                    'message': str(e)
                })
                with progress_lock:
                    stats['failed'] += 1
    
    # Final stats
    elapsed = time.time() - stats['start_time']
    
    logging.info(f"\n{'='*60}")
    logging.info(f"SCRAPING COMPLETED")
    logging.info(f"{'='*60}")
    logging.info(f"Total time: {elapsed/60:.1f} minutes")
    logging.info(f"Results:")
    logging.info(f"  • Total URLs: {stats['total']}")
    logging.info(f"  • Successful: {stats['completed']} ({stats['completed']/stats['total']*100:.1f}%)")
    logging.info(f"  • Failed: {stats['failed']} ({stats['failed']/stats['total']*100:.1f}%)")
    logging.info(f"  • Average speed: {stats['completed'] / elapsed:.2f} requests/second")
    logging.info(f"{'='*60}")
    
    return results




if __name__ == "__main__":
    import argparse
    import sys
    from ...utils.config import INPUT_DIR
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Scrape BoxRec URLs from CSV file')
    parser.add_argument('csv_filename', nargs='?', help='CSV filename in data/input/ directory (e.g., test_boxers.csv)')
    parser.add_argument('--workers', type=int, default=None, 
                       help=f'Number of concurrent workers (default: {DEFAULT_WORKERS})')
    parser.add_argument('--rate-limit', type=float, default=None,
                       help=f'Requests per second (default: {DEFAULT_RATE_LIMIT})')
    parser.add_argument('--max-age-days', type=int, 
                       help='Skip files newer than N days')
    
    args = parser.parse_args()
    
    # If no filename provided, show available files and prompt
    if not args.csv_filename:
        csv_files = list(INPUT_DIR.glob('*.csv'))
        
        if not csv_files:
            print(f"No CSV files found in {INPUT_DIR}")
            print("Please add a CSV file with URLs to the input directory.")
            exit(1)
        
        print(f"\nAvailable CSV files in {INPUT_DIR}:")
        for i, f in enumerate(csv_files, 1):
            print(f"  {i}. {f.name}")
        
        # Prompt for selection
        while True:
            choice = input(f"\nEnter filename or number (1-{len(csv_files)}): ").strip()
            
            # Check if it's a number
            if choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(csv_files):
                    args.csv_filename = csv_files[idx].name
                    break
                else:
                    print(f"Invalid number. Please enter 1-{len(csv_files)}")
            # Check if it's a filename
            elif any(f.name == choice for f in csv_files):
                args.csv_filename = choice
                break
            # Check if they forgot .csv extension
            elif any(f.name == f"{choice}.csv" for f in csv_files):
                args.csv_filename = f"{choice}.csv"
                break
            else:
                print(f"File not found. Please try again.")
    
    # Build full path to CSV file
    csv_file = INPUT_DIR / args.csv_filename
    
    if not csv_file.exists():
        print(f"Error: CSV file not found: {csv_file}")
        print(f"Available CSV files in {INPUT_DIR}:")
        for f in INPUT_DIR.glob('*.csv'):
            print(f"  - {f.name}")
        exit(1)
    
    # Prompt for workers if not provided
    if args.workers is None:
        while True:
            workers_input = input(f"\nNumber of concurrent workers (default {DEFAULT_WORKERS}): ").strip()
            if not workers_input:
                args.workers = DEFAULT_WORKERS
                break
            try:
                args.workers = int(workers_input)
                if args.workers > 0:
                    break
                else:
                    print("Workers must be greater than 0")
            except ValueError:
                print("Please enter a valid number")
    
    # Prompt for rate limit if not provided
    if args.rate_limit is None:
        while True:
            rate_input = input(f"Requests per second (default {DEFAULT_RATE_LIMIT}): ").strip()
            if not rate_input:
                args.rate_limit = DEFAULT_RATE_LIMIT
                break
            try:
                args.rate_limit = float(rate_input)
                if args.rate_limit > 0:
                    break
                else:
                    print("Rate limit must be greater than 0")
            except ValueError:
                print("Please enter a valid number")
    
    # Load and scrape URLs
    urls = load_urls_from_csv(csv_file)
    
    if urls:
        results = scrape_urls(urls, args.workers, args.rate_limit, args.max_age_days)
        print(f"\nScraped HTML files saved to: {PENDING_HTML_DIR}")
    else:
        print("No URLs found in CSV file")
        exit(1)