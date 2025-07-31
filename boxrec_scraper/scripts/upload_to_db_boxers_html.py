#!/usr/bin/env python3
"""
Upload HTML files to staging database tables.
Separates the database upload logic from scraping.
"""

import os
import sys
import logging
import argparse
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from urllib.parse import urlparse
from dotenv import load_dotenv
import psycopg2
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

# Load environment variables
load_dotenv('/Users/devin/repos/projects/data-pipelines/boxing/.env')

# PostgreSQL connection
POSTGRES_CONFIG = {
    'host': os.getenv('POSTGRES_HOST'),
    'port': os.getenv('POSTGRES_PORT'),
    'user': os.getenv('POSTGRES_USER'), 
    'password': os.getenv('POSTGRES_PASSWORD'),
    'database': os.getenv('POSTGRES_DEFAULT_DB')
}

# Thread-safe database connection
db_lock = Lock()
db_conn = None

# Progress tracking
progress_lock = Lock()
stats = {
    'total': 0,
    'uploaded': 0,
    'failed': 0,
    'skipped': 0
}

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def get_db_connection():
    """Get database connection with thread safety"""
    global db_conn
    with db_lock:
        if db_conn is None or db_conn.closed:
            db_conn = psycopg2.connect(**POSTGRES_CONFIG)
        return db_conn

def parse_filename(filename):
    """Parse entity info from filename format: lang_type_id.html"""
    parts = filename.replace('.html', '').split('_')
    if len(parts) >= 3:
        return {
            'language': parts[0],
            'entity_type': parts[1],
            'entity_id': parts[2]
        }
    return None

def determine_entity_from_url(url):
    """Determine entity type and ID from URL"""
    parsed = urlparse(url)
    path_parts = [p for p in parsed.path.split('/') if p]
    
    if 'box-pro' in path_parts:
        idx = path_parts.index('box-pro')
        if idx + 1 < len(path_parts):
            return 'boxer', path_parts[idx + 1]
    elif 'event' in path_parts:
        idx = path_parts.index('event')
        if idx + 1 < len(path_parts):
            return 'event', path_parts[idx + 1]
    elif 'bout' in path_parts:
        idx = path_parts.index('bout')
        if idx + 1 < len(path_parts):
            return 'bout', path_parts[idx + 1]
    
    return None, None

def upload_html_to_db(html_file_path, url=None):
    """Upload a single HTML file to the appropriate database table"""
    try:
        # Read HTML content
        with open(html_file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Determine entity type and ID
        if url:
            entity_type, entity_id = determine_entity_from_url(url)
        else:
            # Try to parse from filename
            file_info = parse_filename(html_file_path.name)
            if file_info:
                entity_type = file_info['entity_type']
                entity_id = file_info['entity_id']
            else:
                logging.error(f"Cannot determine entity type for {html_file_path}")
                return False
        
        if not entity_type or not entity_id:
            logging.error(f"Cannot determine entity info for {html_file_path}")
            return False
        
        # Reconstruct URL if not provided
        if not url:
            lang = file_info.get('language', 'en') if file_info else 'en'
            if entity_type == 'boxer':
                url = f"https://boxrec.com/{lang}/box-pro/{entity_id}"
            elif entity_type == 'event':
                url = f"https://boxrec.com/{lang}/event/{entity_id}"
            elif entity_type == 'bout':
                url = f"https://boxrec.com/{lang}/bout/{entity_id}"
        
        # Upload to database
        conn = get_db_connection()
        cur = conn.cursor()
        
        if entity_type == 'boxer':
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
            cur.execute("""
                INSERT INTO "data-pipelines-staging".boxrec_bout 
                (boxrec_url, boxrec_bout_id, html_file, scraped_at)
                VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (boxrec_bout_id) DO UPDATE SET
                    html_file = EXCLUDED.html_file,
                    scraped_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
            """, (url, entity_id, html_content))
        
        conn.commit()
        cur.close()
        
        with progress_lock:
            stats['uploaded'] += 1
        
        logging.info(f"[UPLOADED] {entity_type} {entity_id}: {html_file_path.name}")
        return True
        
    except Exception as e:
        with progress_lock:
            stats['failed'] += 1
        logging.error(f"[ERROR] Failed to upload {html_file_path}: {e}")
        return False

def process_directory(html_dir, workers=5):
    """Process all HTML files in a directory"""
    html_files = list(Path(html_dir).glob('*.html'))
    
    with progress_lock:
        stats['total'] = len(html_files)
    
    logging.info(f"Found {len(html_files)} HTML files to upload")
    
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(upload_html_to_db, f) for f in html_files]
        
        for i, future in enumerate(as_completed(futures), 1):
            future.result()
            
            # Print progress every 10 files
            if i % 10 == 0:
                with progress_lock:
                    logging.info(
                        f"Progress: {i}/{stats['total']} "
                        f"(Uploaded: {stats['uploaded']}, Failed: {stats['failed']})"
                    )

def main():
    parser = argparse.ArgumentParser(description='Upload HTML files to staging database')
    parser.add_argument('html_dir', type=Path, help='Directory containing HTML files')
    parser.add_argument('--workers', type=int, default=5, help='Number of parallel workers')
    parser.add_argument('--file', type=Path, help='Upload single file')
    parser.add_argument('--url', help='URL for single file upload')
    
    args = parser.parse_args()
    
    if args.file:
        # Single file mode
        success = upload_html_to_db(args.file, args.url)
        sys.exit(0 if success else 1)
    else:
        # Directory mode
        if not args.html_dir.exists():
            logging.error(f"Directory not found: {args.html_dir}")
            sys.exit(1)
        
        process_directory(args.html_dir, args.workers)
        
        # Final summary
        with progress_lock:
            logging.info(
                f"\nFinal Summary:\n"
                f"Total files: {stats['total']}\n"
                f"Uploaded: {stats['uploaded']}\n"
                f"Failed: {stats['failed']}\n"
                f"Skipped: {stats['skipped']}"
            )

if __name__ == '__main__':
    main()