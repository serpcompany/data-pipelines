#!/usr/bin/env python3
"""
Enhanced BoxRec scraper that saves HTML to the three staging tables:
- boxrec_boxer
- boxrec_event  
- boxrec_bout
"""

import os
import sys
import time
import logging
import argparse
import csv
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from urllib.parse import urlparse
from base64 import b64decode
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import execute_batch
import requests
from bs4 import BeautifulSoup

# Load environment variables
load_dotenv('/Users/devin/repos/projects/data-pipelines/boxing/.env')

# Configuration
ZYTE_API_KEY = os.getenv('ZYTE_API_KEY')
ZYTE_API_URL = "https://api.zyte.com/v1/extract"

# PostgreSQL connection
POSTGRES_CONFIG = {
    'host': os.getenv('POSTGRES_HOST'),
    'port': os.getenv('POSTGRES_PORT'),
    'user': os.getenv('POSTGRES_USER'), 
    'password': os.getenv('POSTGRES_PASSWORD'),
    'database': os.getenv('POSTGRES_DEFAULT_DB')
}

# Default settings
DEFAULT_WORKERS = 15
DEFAULT_RATE_LIMIT = 1000
REQUEST_TIMEOUT = 30

# Rate limiting
request_lock = Lock()
last_request_time = 0

# Database connection pool
db_lock = Lock()
db_conn = None

# Progress tracking
progress_lock = Lock()
stats = {
    'total': 0,
    'completed': 0,
    'failed': 0,
    'skipped': 0,
    'saved_to_db': 0,
    'invalid_scrapes': 0,
    'start_time': None
}

def get_db_connection():
    """Get database connection with thread safety"""
    global db_conn
    with db_lock:
        if db_conn is None or db_conn.closed:
            db_conn = psycopg2.connect(**POSTGRES_CONFIG)
        return db_conn

def validate_html_content(html_content, url):
    """Validate HTML content for common issues"""
    issues = []
    
    # Check for login page
    if 'BoxRec: Login' in html_content or '<title>Login</title>' in html_content:
        issues.append('LOGIN_PAGE')
    
    # Check size
    if len(html_content) < 1000:
        issues.append(f'TOO_SMALL_{len(html_content)}_bytes')
    
    # Check for errors
    if '404 Not Found' in html_content or 'Page Not Found' in html_content:
        issues.append('404_ERROR')
    
    if '403 Forbidden' in html_content:
        issues.append('403_FORBIDDEN')
    
    if 'Rate Limit' in html_content or 'rate limit' in html_content.lower():
        issues.append('RATE_LIMITED')
    
    return issues

def extract_entity_info(url):
    """Extract entity type and ID from URL"""
    parsed = urlparse(url)
    path_parts = parsed.path.strip('/').split('/')
    
    entity_type = 'unknown'
    entity_id = None
    
    if 'box-pro' in url or 'proboxer' in url:
        entity_type = 'boxer'
        # Extract boxer ID
        for part in path_parts:
            if part.isdigit():
                entity_id = part
                break
    elif 'event' in url:
        # Check if it's a bout URL (has two IDs) or event URL (one ID)
        numeric_parts = [p for p in path_parts if p.isdigit()]
        if len(numeric_parts) >= 2:
            entity_type = 'bout'
            entity_id = f"{numeric_parts[0]}_{numeric_parts[1]}"  # event_id_bout_id
        else:
            entity_type = 'event'
            entity_id = numeric_parts[0] if numeric_parts else None
    elif 'venue' in url:
        entity_type = 'venue'
        for part in path_parts:
            if part.isdigit():
                entity_id = part
                break
    
    return entity_type, entity_id

def save_to_database(url, html_content, validation_issues):
    """Save HTML content to appropriate staging table"""
    entity_type, entity_id = extract_entity_info(url)
    
    if not entity_id:
        logging.error(f"Could not extract ID from URL: {url}")
        return False
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        if entity_type == 'boxer':
            # Save to boxrec_boxer table
            cur.execute("""
                INSERT INTO "data-pipelines-staging".boxrec_boxer 
                (boxrec_url, boxrec_id, html_file, scraped_at)
                VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (boxrec_id) DO UPDATE SET
                    html_file = EXCLUDED.html_file,
                    scraped_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
            """, (url, entity_id, html_content))
            
        elif entity_type == 'event':
            # Save to boxrec_event table
            cur.execute("""
                INSERT INTO "data-pipelines-staging".boxrec_event 
                (boxrec_url, boxrec_event_id, html_file, scraped_at)
                VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (boxrec_event_id) DO UPDATE SET
                    html_file = EXCLUDED.html_file,
                    scraped_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
            """, (url, entity_id, html_content))
            
        elif entity_type == 'bout':
            # Save to boxrec_bout table
            cur.execute("""
                INSERT INTO "data-pipelines-staging".boxrec_bout 
                (boxrec_url, boxrec_bout_id, html_file, scraped_at)
                VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (boxrec_bout_id) DO UPDATE SET
                    html_file = EXCLUDED.html_file,
                    scraped_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
            """, (url, entity_id, html_content))
        else:
            logging.warning(f"Unknown entity type for URL: {url}")
            return False
        
        conn.commit()
        
        with progress_lock:
            stats['saved_to_db'] += 1
            if validation_issues:
                stats['invalid_scrapes'] += 1
        
        return True
        
    except Exception as e:
        conn.rollback()
        logging.error(f"Database error for {url}: {e}")
        return False
    finally:
        cur.close()

def check_if_exists(url):
    """Check if URL already exists in database"""
    entity_type, entity_id = extract_entity_info(url)
    
    if not entity_id:
        return False, None
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        if entity_type == 'boxer':
            cur.execute("""
                SELECT scraped_at 
                FROM "data-pipelines-staging".boxrec_boxer 
                WHERE boxrec_id = %s
            """, (entity_id,))
        elif entity_type == 'event':
            cur.execute("""
                SELECT scraped_at 
                FROM "data-pipelines-staging".boxrec_event 
                WHERE boxrec_event_id = %s
            """, (entity_id,))
        elif entity_type == 'bout':
            cur.execute("""
                SELECT scraped_at 
                FROM "data-pipelines-staging".boxrec_bout 
                WHERE boxrec_bout_id = %s
            """, (entity_id,))
        else:
            return False, None
        
        result = cur.fetchone()
        if result:
            return True, {'scraped_at': result[0]}
        return False, None
        
    finally:
        cur.close()

def rate_limited_request(rate_limit: float):
    """Ensure we don't exceed rate limits"""
    global last_request_time
    
    request_interval = 1.0 / rate_limit
    
    with request_lock:
        current_time = time.time()
        time_since_last = current_time - last_request_time
        
        if time_since_last < request_interval:
            sleep_time = request_interval - time_since_last
            time.sleep(sleep_time)
        
        last_request_time = time.time()

def fetch_url(url: str, rate_limit: float, skip_existing: bool = True, max_age_days: int = None) -> dict:
    """Fetch a single URL, validate, and save to database"""
    
    # Check if already exists in database
    if skip_existing:
        exists, existing_data = check_if_exists(url)
        if exists:
            if max_age_days is not None and existing_data and existing_data['scraped_at']:
                # Check age
                age_days = (datetime.now(timezone.utc) - existing_data['scraped_at'].replace(tzinfo=timezone.utc)).days
                if age_days < max_age_days:
                    with progress_lock:
                        stats['skipped'] += 1
                    return {
                        'url': url,
                        'status': 'skipped',
                        'reason': f'recent_in_db ({age_days} days old)'
                    }
            else:
                # Skip all existing
                with progress_lock:
                    stats['skipped'] += 1
                return {
                    'url': url,
                    'status': 'skipped',
                    'reason': 'exists_in_db'
                }
    
    # Rate limiting
    rate_limited_request(rate_limit)
    
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
        
        # Extract HTML
        html_content = b64decode(data["httpResponseBody"]).decode('utf-8')
        
        # Validate content
        validation_issues = validate_html_content(html_content, url)
        
        # Save to database
        saved = save_to_database(url, html_content, validation_issues)
        
        if saved:
            with progress_lock:
                stats['completed'] += 1
                if stats['completed'] % 50 == 0:
                    elapsed = time.time() - stats['start_time']
                    req_per_sec = stats['completed'] / elapsed
                    completion_pct = (stats['completed'] / stats['total']) * 100
                    logging.info(f"Progress: {stats['completed']}/{stats['total']} "
                               f"({completion_pct:.1f}%) - {req_per_sec:.2f} req/s - "
                               f"DB saves: {stats['saved_to_db']}")
        
        entity_type, entity_id = extract_entity_info(url)
        
        return {
            'url': url,
            'status': 'success',
            'entity_type': entity_type,
            'entity_id': entity_id,
            'validation': 'invalid' if validation_issues else 'valid',
            'issues': validation_issues,
            'saved_to_db': saved
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

def load_urls_from_csv(csv_file: Path) -> list:
    """Load URLs from CSV file"""
    urls = []
    
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                url = row.get('url') or row.get('URL') or row.get('boxrec_url')
                if url:
                    urls.append(url)
        
        logging.info(f"Loaded {len(urls)} URLs from {csv_file}")
        return urls
        
    except Exception as e:
        logging.error(f"Error loading CSV file {csv_file}: {e}")
        return []

def scrape_urls(urls: list, max_workers: int = DEFAULT_WORKERS, 
                rate_limit: float = DEFAULT_RATE_LIMIT, 
                skip_existing: bool = True,
                max_age_days: int = None) -> list:
    """Scrape multiple URLs concurrently and save to database"""
    
    if not ZYTE_API_KEY:
        logging.error("ZYTE_API_KEY not found in environment variables")
        return []
    
    # Initialize stats
    stats['total'] = len(urls)
    stats['start_time'] = time.time()
    stats['completed'] = 0
    stats['failed'] = 0
    stats['skipped'] = 0
    stats['saved_to_db'] = 0
    stats['invalid_scrapes'] = 0
    
    # Count entity types
    entity_counts = {'boxer': 0, 'event': 0, 'bout': 0, 'unknown': 0}
    for url in urls:
        entity_type, _ = extract_entity_info(url)
        entity_counts[entity_type] += 1
    
    logging.info(f"Starting scrape: {len(urls)} URLs with {max_workers} workers")
    logging.info(f"Entity types: {entity_counts}")
    logging.info(f"Rate limit: {rate_limit} requests/second")
    logging.info(f"Skip existing: {skip_existing}")
    if max_age_days:
        logging.info(f"Re-scrape files older than {max_age_days} days")
    
    results = []
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_url = {
            executor.submit(fetch_url, url, rate_limit, skip_existing, max_age_days): url 
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
    
    logging.info(f"\n🎉 Scraping completed in {elapsed/60:.1f} minutes")
    logging.info(f"   Total: {stats['total']}")
    logging.info(f"   Successful: {stats['completed']}")
    logging.info(f"   Failed: {stats['failed']}")
    logging.info(f"   Skipped: {stats['skipped']}")
    logging.info(f"   Saved to DB: {stats['saved_to_db']}")
    logging.info(f"   Invalid scrapes: {stats['invalid_scrapes']}")
    logging.info(f"   Average: {stats['completed'] / elapsed:.2f} requests/second")
    
    return results

def setup_logging():
    """Set up logging configuration"""
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / 'scrape_to_staging_db.log'),
            logging.StreamHandler()
        ]
    )

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='BoxRec scraper that saves to staging database tables')
    parser.add_argument('csv_file', help='CSV file containing URLs to scrape')
    parser.add_argument('--workers', type=int, default=DEFAULT_WORKERS,
                       help=f'Number of concurrent workers (default: {DEFAULT_WORKERS})')
    parser.add_argument('--rate-limit', type=float, default=DEFAULT_RATE_LIMIT,
                       help=f'Requests per second limit (default: {DEFAULT_RATE_LIMIT})')
    parser.add_argument('--limit', type=int, help='Limit number of URLs to scrape')
    parser.add_argument('--max-age-days', type=int, 
                       help='Re-scrape entries older than N days')
    parser.add_argument('--force', action='store_true',
                       help='Force re-scrape all URLs (ignore existing)')
    
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
    
    # Run scraper
    skip_existing = not args.force
    results = scrape_urls(urls, args.workers, args.rate_limit, skip_existing, args.max_age_days)
    
    # Close database connection
    global db_conn
    if db_conn:
        db_conn.close()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())