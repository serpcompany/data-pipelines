#!/usr/bin/env python3
import csv
import json
import logging
import os
import requests
import concurrent.futures
from pathlib import Path
from threading import Lock
from datetime import datetime
from base64 import b64decode
from urllib.parse import urlparse, quote
from dotenv import load_dotenv
from tqdm import tqdm

# Load environment variables
env_path = Path('..') / '.env'
load_dotenv(dotenv_path=env_path)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('boxrec_scraper.log'),
        logging.StreamHandler()
    ]
)

# Configuration
ZYTE_API_KEY = os.getenv("ZYTE_API_KEY")
if not ZYTE_API_KEY:
    logging.error("ZYTE_API_KEY environment variable not set.")
    logging.info("Please create a .env file in the parent directory with ZYTE_API_KEY=your_key")
    exit(1)

# Directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HTML_DIR = os.path.join(BASE_DIR, 'boxrec_html')
DATA_DIR = os.path.join(BASE_DIR, 'boxrec_data')

# Thread safety
lock = Lock()
results = []

def create_directories():
    """Create necessary directories for storing data."""
    os.makedirs(HTML_DIR, exist_ok=True)
    os.makedirs(DATA_DIR, exist_ok=True)
    logging.info(f"Created directories: {HTML_DIR}, {DATA_DIR}")

def load_urls_from_csv(csv_path):
    """Load URLs from a CSV file."""
    urls = []
    try:
        with open(csv_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                urls.append(row)
        logging.info(f"Loaded {len(urls)} URLs from {csv_path}")
    except Exception as e:
        logging.error(f"Failed to load CSV: {e}")
        raise
    return urls

def create_filename_from_url(url):
    """Create a safe filename from a URL."""
    parsed = urlparse(url)
    path_parts = parsed.path.strip('/').split('/')
    
    # Clean up filename
    filename_parts = []
    for part in path_parts:
        clean_part = part.replace('/', '_').replace('\\', '_').replace(':', '_')
        if clean_part:
            filename_parts.append(clean_part)
    
    filename = '_'.join(filename_parts) if filename_parts else 'index'
    filename = filename[:100]  # Limit length
    
    return f"{filename}.html"

def download_page(item, pbar):
    """Download a single page using Zyte API."""
    url = item.get('url', item)  # Handle both dict and string inputs
    
    try:
        # Create filename
        filename = create_filename_from_url(url)
        filepath = os.path.join(HTML_DIR, filename)
        
        # Skip if already downloaded
        if os.path.exists(filepath):
            with lock:
                pbar.update(1)
                pbar.set_postfix_str(f"Skipped: {filename} (exists)")
            return {'url': url, 'status': 'skipped', 'reason': 'already exists'}
        
        # Make request to Zyte API
        response = requests.post(
            "https://api.zyte.com/v1/extract",
            auth=(ZYTE_API_KEY, ""),
            json={
                "url": url,
                "browserHtml": True,  # Get rendered HTML
            },
            timeout=60
        )
        
        if response.status_code != 200:
            error_msg = f"HTTP {response.status_code}: {response.text[:100]}"
            with lock:
                pbar.update(1)
                pbar.set_postfix_str(f"Failed: {error_msg}")
            return {'url': url, 'status': 'failed', 'error': error_msg}
        
        # Extract HTML
        data = response.json()
        if 'browserHtml' in data:
            html_content = data['browserHtml']
        else:
            # Fallback to httpResponseBody if browserHtml not available
            html_content = b64decode(data['httpResponseBody']).decode('utf-8', errors='ignore')
        
        # Save HTML
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # Update progress
        with lock:
            pbar.update(1)
            pbar.set_postfix_str(f"Saved: {filename} ({len(html_content)} chars)")
        
        return {
            'url': url,
            'status': 'success',
            'filepath': filepath,
            'size': len(html_content)
        }
        
    except Exception as e:
        error_msg = str(e)
        with lock:
            pbar.update(1)
            pbar.set_postfix_str(f"Error: {error_msg[:50]}...")
        return {'url': url, 'status': 'error', 'error': error_msg}

def scrape_boxrec(csv_file=None, max_workers=5):
    """Main scraping function."""
    create_directories()
    
    # Load URLs from CSV or use default
    if csv_file:
        urls = load_urls_from_csv(csv_file)
    else:
        # Look for default CSV file
        default_csv = os.path.join(BASE_DIR, 'boxrec_urls.csv')
        if os.path.exists(default_csv):
            urls = load_urls_from_csv(default_csv)
        else:
            logging.error("No CSV file provided and no default boxrec_urls.csv found")
            logging.info("Please create a CSV file with a 'url' column containing BoxRec URLs")
            return
    
    # Download pages concurrently
    success = failed = skipped = 0
    
    with tqdm(total=len(urls), desc="Downloading BoxRec pages", unit="page") as pbar:
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(download_page, url, pbar) for url in urls]
            
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                with lock:
                    results.append(result)
                    if result['status'] == 'success':
                        success += 1
                    elif result['status'] == 'skipped':
                        skipped += 1
                    else:
                        failed += 1
    
    # Save results summary
    summary_path = os.path.join(DATA_DIR, f'scrape_summary_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'total_urls': len(urls),
            'success': success,
            'failed': failed,
            'skipped': skipped,
            'results': results
        }, f, indent=2)
    
    logging.info(f"\nScraping complete!")
    logging.info(f"Total: {len(urls)} | Success: {success} | Failed: {failed} | Skipped: {skipped}")
    logging.info(f"Results saved to: {summary_path}")

if __name__ == "__main__":
    import sys
    
    # Check for CSV file argument
    csv_file = sys.argv[1] if len(sys.argv) > 1 else None
    
    scrape_boxrec(csv_file=csv_file)