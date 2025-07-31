#!/usr/bin/env python3
"""
Optimized concurrent scraper for BoxRec using Zyte API.
Designed for high-throughput scraping with proper rate limiting.
"""

import os
import sys
import json
import time
import logging
import requests
from pathlib import Path
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock, Semaphore
from queue import Queue
import csv
from base64 import b64decode
from urllib.parse import urlparse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
ZYTE_API_KEY = os.getenv('ZYTE_API_KEY')
ZYTE_API_URL = "https://api.zyte.com/v1/extract"

# Optimized concurrency settings
MAX_WORKERS = 20  # Zyte typically allows 20-100 concurrent requests
RATE_LIMIT = 10   # Requests per second (adjust based on your plan)
REQUEST_TIMEOUT = 30  # Seconds

# Rate limiting
rate_limiter = Semaphore(RATE_LIMIT)
last_request_time = 0
request_interval = 1.0 / RATE_LIMIT
request_lock = Lock()

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
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/concurrent_scrape.log'),
        logging.StreamHandler()
    ]
)


def rate_limited_request():
    """Ensure we don't exceed rate limits."""
    global last_request_time
    
    with request_lock:
        current_time = time.time()
        time_since_last = current_time - last_request_time
        
        if time_since_last < request_interval:
            sleep_time = request_interval - time_since_last
            time.sleep(sleep_time)
        
        last_request_time = time.time()


def fetch_url(url: str, output_dir: Path) -> dict:
    """Fetch a single URL with rate limiting."""
    # Determine output filename
    parsed = urlparse(url)
    if 'box-pro' in url:
        match = parsed.path.strip('/').split('/')
        filename = f"{match[0]}_{'_'.join(match[1:])}.html"
    elif 'wiki' in url:
        # Extract ID from wiki URL
        import re
        id_match = re.search(r'Human:(\d+)', url)
        if id_match:
            filename = f"wiki_box-pro_{id_match.group(1)}.html"
        else:
            filename = f"wiki_{parsed.path.replace('/', '_')}.html"
    else:
        filename = parsed.path.strip('/').replace('/', '_') + '.html'
    
    output_file = output_dir / filename
    
    # Skip if already exists
    if output_file.exists():
        return {
            'url': url,
            'status': 'skipped',
            'reason': 'already_exists',
            'filename': filename
        }
    
    # Rate limiting
    rate_limited_request()
    
    try:
        # Make API request
        response = requests.post(
            ZYTE_API_URL,
            json={
                "url": url,
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
            if stats['completed'] % 100 == 0:
                elapsed = time.time() - stats['start_time']
                stats['requests_per_second'] = stats['completed'] / elapsed
                logging.info(f"Progress: {stats['completed']}/{stats['total']} "
                           f"({stats['requests_per_second']:.2f} req/s)")
        
        return {
            'url': url,
            'status': 'success',
            'filename': filename,
            'size': len(html_content)
        }
        
    except requests.exceptions.HTTPError as e:
        with progress_lock:
            stats['failed'] += 1
        
        return {
            'url': url,
            'status': 'failed',
            'error': f"HTTP {e.response.status_code}",
            'message': str(e)
        }
        
    except Exception as e:
        with progress_lock:
            stats['failed'] += 1
        
        return {
            'url': url,
            'status': 'failed',
            'error': 'exception',
            'message': str(e)
        }


def scrape_urls(urls: list, output_dir: Path, max_workers: int = MAX_WORKERS) -> list:
    """Scrape multiple URLs concurrently."""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize stats
    stats['total'] = len(urls)
    stats['start_time'] = time.time()
    stats['completed'] = 0
    stats['failed'] = 0
    stats['skipped'] = 0
    
    logging.info(f"Starting concurrent scrape of {len(urls)} URLs with {max_workers} workers")
    
    results = []
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_url = {
            executor.submit(fetch_url, url, output_dir): url 
            for url in urls
        }
        
        # Process completed tasks
        for future in as_completed(future_to_url):
            url = future_to_url[future]
            try:
                result = future.result()
                results.append(result)
                
                if result['status'] == 'skipped':
                    with progress_lock:
                        stats['skipped'] += 1
                
            except Exception as e:
                logging.error(f"Unexpected error for {url}: {e}")
                results.append({
                    'url': url,
                    'status': 'failed',
                    'error': 'future_exception',
                    'message': str(e)
                })
    
    # Final stats
    elapsed = time.time() - stats['start_time']
    logging.info(f"\nScraping completed in {elapsed:.1f} seconds")
    logging.info(f"Total: {stats['total']}")
    logging.info(f"Completed: {stats['completed']}")
    logging.info(f"Failed: {stats['failed']}")
    logging.info(f"Skipped: {stats['skipped']}")
    logging.info(f"Average: {stats['completed'] / elapsed:.2f} requests/second")
    
    return results


def scrape_from_csv(csv_file: Path, output_dir: Path, max_workers: int = MAX_WORKERS):
    """Scrape URLs from a CSV file."""
    # Load URLs
    urls = []
    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if 'url' in row:
                urls.append(row['url'])
    
    logging.info(f"Loaded {len(urls)} URLs from {csv_file}")
    
    # Scrape
    results = scrape_urls(urls, output_dir, max_workers)
    
    # Save results
    summary_file = output_dir / 'scrape_summary.json'
    with open(summary_file, 'w') as f:
        json.dump({
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'total_urls': len(urls),
            'stats': stats,
            'results': results
        }, f, indent=2)
    
    logging.info(f"Summary saved to {summary_file}")
    return results


def scrape_boxer_profiles_and_wikis(boxer_ids: list, base_dir: Path, max_workers: int = MAX_WORKERS):
    """Scrape both profile and wiki pages for boxers."""
    # Generate URLs
    profile_urls = [f"https://boxrec.com/en/box-pro/{boxer_id}" for boxer_id in boxer_ids]
    wiki_urls = [f"https://boxrec.com/wiki/index.php?title=Human:{boxer_id}" for boxer_id in boxer_ids]
    
    # Scrape profiles
    logging.info(f"\n{'='*60}")
    logging.info("Scraping boxer profiles...")
    logging.info(f"{'='*60}")
    profile_results = scrape_urls(profile_urls, base_dir / 'boxrec_html', max_workers)
    
    # Scrape wikis
    logging.info(f"\n{'='*60}")
    logging.info("Scraping boxer wiki pages...")
    logging.info(f"{'='*60}")
    wiki_results = scrape_urls(wiki_urls, base_dir / 'boxrec_wiki', max_workers)
    
    return {
        'profiles': profile_results,
        'wikis': wiki_results
    }


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Concurrent BoxRec scraper')
    parser.add_argument('--csv', type=str, help='CSV file with URLs')
    parser.add_argument('--boxer-ids', type=str, help='Comma-separated boxer IDs')
    parser.add_argument('--workers', type=int, default=MAX_WORKERS, help='Number of concurrent workers')
    parser.add_argument('--output', type=str, default='data/raw', help='Output directory')
    
    args = parser.parse_args()
    
    if not ZYTE_API_KEY:
        logging.error("ZYTE_API_KEY not found in environment variables")
        sys.exit(1)
    
    output_dir = Path(args.output)
    
    if args.csv:
        # Scrape from CSV
        scrape_from_csv(Path(args.csv), output_dir, args.workers)
    
    elif args.boxer_ids:
        # Scrape specific boxer IDs
        boxer_ids = args.boxer_ids.split(',')
        scrape_boxer_profiles_and_wikis(boxer_ids, output_dir, args.workers)
    
    else:
        # Test with a few boxers
        test_ids = ['628407', '348759', '474', '352', '000180']
        logging.info(f"Testing with {len(test_ids)} boxers")
        scrape_boxer_profiles_and_wikis(test_ids, output_dir, args.workers)


if __name__ == "__main__":
    main()