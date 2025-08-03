#!/usr/bin/env python3
"""
BoxRec Scraper - Consolidated high-performance scraper using Zyte API.
Replaces multiple scraper files with one optimized version.
"""

import os
import sys
import json
import time
import logging
import argparse
import csv
from pathlib import Path
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock, Semaphore
from urllib.parse import urlparse
from base64 import b64decode

# Load environment variables from .env file if it exists
def load_env():
    env_path = Path(__file__).parent.parent.parent.parent / '.env'
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

load_env()

# Configuration
ZYTE_API_KEY = os.getenv('ZYTE_API_KEY')
ZYTE_API_URL = "https://api.zyte.com/v1/extract"

# Default settings
DEFAULT_WORKERS = 5  # Reduced from 10 to avoid rate limits
DEFAULT_RATE_LIMIT = 5  # Reduced from 10 to 5 requests per second
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
            logging.FileHandler(log_dir / 'scraper.log'),
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

def create_filename_from_url(url: str) -> str:
    """Create a safe filename from a BoxRec URL."""
    parsed = urlparse(url)
    path_parts = parsed.path.strip('/').split('/')
    
    # Handle different URL formats
    if 'box-pro' in url:
        # Extract language and ID: /en/box-pro/123456
        if len(path_parts) >= 3:
            lang = path_parts[0] if path_parts[0] in ['en', 'es', 'fr', 'de', 'ru'] else 'en'
            boxer_id = path_parts[-1]
            return f"{lang}_box-pro_{boxer_id}.html"
    elif 'wiki' in url:
        # Extract ID from wiki URL
        import re
        id_match = re.search(r'Human:(\d+)', url)
        if id_match:
            return f"wiki_box-pro_{id_match.group(1)}.html"
    
    # Fallback: clean up the path
    filename_parts = []
    for part in path_parts:
        clean_part = part.replace('/', '_').replace('\\', '_').replace(':', '_')
        if clean_part:
            filename_parts.append(clean_part)
    
    filename = '_'.join(filename_parts) if filename_parts else 'index'
    return f"{filename[:100]}.html"  # Limit length

def fetch_url(url: str, output_dir: Path, rate_limit: float, max_age_days: int = None) -> dict:
    """Fetch a single URL with rate limiting and error handling."""
    try:
        import requests
    except ImportError:
        return {
            'url': url,
            'status': 'failed',
            'error': 'requests module not installed',
            'message': 'Run: pip install requests'
        }
    
    # Create filename from original URL (without allSports parameter)
    filename = create_filename_from_url(url)
    output_file = output_dir / filename
    
    # Add allSports=y parameter to get amateur data for box-pro URLs
    fetch_url = url
    if '/box-pro/' in url and '?' not in url:
        fetch_url = url + '?allSports=y'
    elif '/box-pro/' in url and '?' in url:
        fetch_url = url + '&allSports=y'
    
    # Always scrape - file existence checking disabled
    
    # Rate limiting
    rate_limited_request(rate_limit)
    
    try:
        # Make API request with the modified URL (includes allSports=y)
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
        
        # Save HTML
        html_content = b64decode(data["httpResponseBody"]).decode('utf-8')
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # Update stats
        with progress_lock:
            stats['completed'] += 1
            # More frequent updates - every 5 files instead of 10
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
            # Check if it's a rate limit error
            if e.response.status_code == 429:
                logging.warning(f"⚠️  Rate limited on {url} - too many requests")
            elif e.response.status_code == 403:
                logging.warning(f"⚠️  Access denied on {url} - might be login page")
        
        error_msg = f"HTTP {e.response.status_code}: {e}"
        logging.error(f"Failed to fetch {url}: {error_msg}")
        
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

def load_urls_from_csv(csv_file: Path) -> list:
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

def scrape_urls(urls: list, output_dir: Path, max_workers: int = DEFAULT_WORKERS, 
                rate_limit: float = DEFAULT_RATE_LIMIT, max_age_days: int = None) -> list:
    """Scrape multiple URLs concurrently."""
    if not ZYTE_API_KEY:
        logging.error("ZYTE_API_KEY not found in environment variables")
        logging.error("Please set ZYTE_API_KEY in your .env file or environment")
        return []
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Check how many files already exist
    existing_count = 0
    for url in urls:
        filename = create_filename_from_url(url)
        if (output_dir / filename).exists():
            existing_count += 1
    
    # Initialize stats
    stats['total'] = len(urls)
    stats['start_time'] = time.time()
    stats['completed'] = 0
    stats['failed'] = 0
    stats['skipped'] = 0
    
    logging.info(f"Starting scrape: {len(urls)} URLs with {max_workers} workers")
    logging.info(f"Rate limit: {rate_limit} requests/second")
    logging.info(f"Output directory: {output_dir}")
    logging.info(f"Already downloaded: {existing_count} files will be skipped")
    
    results = []
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_url = {
            executor.submit(fetch_url, url, output_dir, rate_limit, max_age_days): url 
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
    logging.info(f"🎉 SCRAPING COMPLETED")
    logging.info(f"{'='*60}")
    logging.info(f"⏱️  Total time: {elapsed/60:.1f} minutes")
    logging.info(f"📊 Results:")
    logging.info(f"   • Total URLs: {stats['total']}")
    logging.info(f"   • ✅ Successful: {stats['completed']} ({stats['completed']/stats['total']*100:.1f}%)")
    logging.info(f"   • ❌ Failed: {stats['failed']} ({stats['failed']/stats['total']*100:.1f}%)")
    logging.info(f"   • ⏭️  Skipped: {stats['skipped']} ({stats['skipped']/stats['total']*100:.1f}%)")
    logging.info(f"   • 🚀 Average speed: {stats['completed'] / elapsed:.2f} requests/second")
    logging.info(f"{'='*60}")
    
    return results

def save_results(results: list, output_dir: Path):
    """Save scraping results summary."""
    summary_file = output_dir / f'scrape_summary_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    
    summary = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'total_urls': stats['total'],
        'successful': stats['completed'],
        'failed': stats['failed'],
        'skipped': stats['skipped'],
        'duration_seconds': time.time() - stats['start_time'],
        'requests_per_second': stats['requests_per_second'],
        'results': results
    }
    
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2)
    
    logging.info(f"📊 Results summary saved: {summary_file}")
    return summary_file

def main():
    """Main entry point."""
    # Get absolute paths - handle different working directories
    script_dir = Path(__file__).resolve().parent
    # Go up from scripts/scrape to boxrec_scraper
    boxrec_root = script_dir.parent.parent
    
    default_csv = boxrec_root / 'data' / '10000boxers.csv'
    default_output = boxrec_root / 'data' / 'raw' / 'boxrec_html'
    
    parser = argparse.ArgumentParser(description='BoxRec Scraper - High-performance scraper using Zyte API')
    parser.add_argument('csv_file', nargs='?', default=str(default_csv), 
                       help='CSV file containing URLs to scrape')
    parser.add_argument('--workers', type=int, default=DEFAULT_WORKERS,
                       help=f'Number of concurrent workers (default: {DEFAULT_WORKERS})')
    parser.add_argument('--rate-limit', type=float, default=DEFAULT_RATE_LIMIT,
                       help=f'Requests per second limit (default: {DEFAULT_RATE_LIMIT})')
    parser.add_argument('--output', type=str, default=str(default_output),
                       help='Output directory for HTML files')
    parser.add_argument('--limit', type=int, help='Limit number of URLs to scrape')
    parser.add_argument('--max-age-days', type=int, 
                       help='Re-scrape files older than N days (default: skip all existing)')
    
    args = parser.parse_args()
    
    # Set up logging
    setup_logging()
    
    # Load URLs
    csv_file = Path(args.csv_file)
    if not csv_file.exists():
        logging.error(f"CSV file not found: {csv_file}")
        return 1
    
    urls = load_urls_from_csv(csv_file)
    if not urls:
        logging.error("No URLs loaded")
        return 1
    
    # Apply limit if specified
    if args.limit:
        urls = urls[:args.limit]
        logging.info(f"Limited to first {len(urls)} URLs")
    
    # Set up output directory
    output_dir = Path(args.output)
    
    # Run scraper
    results = scrape_urls(urls, output_dir, args.workers, args.rate_limit, args.max_age_days)
    
    # Save results
    save_results(results, output_dir)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())