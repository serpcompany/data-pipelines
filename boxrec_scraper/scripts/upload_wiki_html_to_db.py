#!/usr/bin/env python3
"""
Upload wiki HTML files to the wiki_html column in boxrec_boxer table.
"""

import os
import sys
import logging
import argparse
import re
from pathlib import Path
from datetime import datetime, timezone
from dotenv import load_dotenv
import psycopg2
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

# Load environment variables  
load_dotenv('/Users/devin/repos/projects/data-pipelines/.env')

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
    'updated': 0,
    'failed': 0,
    'not_found': 0,
    'empty_wiki': 0
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

def process_wiki_file(wiki_file):
    """Read wiki HTML file and update corresponding boxer record."""
    try:
        # Extract BoxRec ID from filename
        match = re.search(r'wiki_box-pro_(\d+)\.html', wiki_file.name)
        if not match:
            logging.warning(f"Cannot extract BoxRec ID from filename: {wiki_file.name}")
            with progress_lock:
                stats['failed'] += 1
            return False
        
        boxrec_id = match.group(1)
        
        # Read wiki HTML content
        with open(wiki_file, 'r', encoding='utf-8') as f:
            wiki_html = f.read()
        
        # Check if it's an empty wiki page
        if 'There is currently no text in this page' in wiki_html:
            with progress_lock:
                stats['empty_wiki'] += 1
            logging.debug(f"[SKIP] Empty wiki page for boxer {boxrec_id}")
            return False
        
        # Update database
        conn = get_db_connection()
        cur = conn.cursor()
        
        try:
            # Construct wiki URL
            wiki_url = f"https://boxrec.com/wiki/index.php?title=Human:{boxrec_id}"
            
            # Update wiki_html and wiki_url columns
            cur.execute("""
                UPDATE "data-pipelines-staging".boxrec_boxer 
                SET wiki_html = %s, wiki_url = %s, updated_at = %s
                WHERE boxrec_id = %s;
            """, (wiki_html, wiki_url, datetime.now(timezone.utc), boxrec_id))
            
            if cur.rowcount > 0:
                conn.commit()
                with progress_lock:
                    stats['updated'] += 1
                logging.info(f"[UPDATED] Boxer {boxrec_id} with wiki HTML ({len(wiki_html)} chars)")
                return True
            else:
                with progress_lock:
                    stats['not_found'] += 1
                logging.warning(f"[NOT FOUND] Boxer {boxrec_id} not in database")
                return False
                
        except Exception as e:
            conn.rollback()
            with progress_lock:
                stats['failed'] += 1
            logging.error(f"[ERROR] Failed to update boxer {boxrec_id}: {e}")
            return False
        finally:
            cur.close()
            
    except Exception as e:
        with progress_lock:
            stats['failed'] += 1
        logging.error(f"[ERROR] Failed to process {wiki_file}: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Upload wiki HTML files to boxrec_boxer table')
    parser.add_argument('wiki_dir', type=Path, help='Directory containing wiki HTML files')
    parser.add_argument('--limit', type=int, help='Limit number of files to process')
    parser.add_argument('--workers', type=int, default=5, help='Number of parallel workers')
    
    args = parser.parse_args()
    
    if not args.wiki_dir.exists():
        logging.error(f"Wiki directory not found: {args.wiki_dir}")
        sys.exit(1)
    
    # Find all wiki HTML files
    wiki_files = list(args.wiki_dir.glob('wiki_box-pro_*.html'))
    
    if args.limit:
        wiki_files = wiki_files[:args.limit]
    
    with progress_lock:
        stats['total'] = len(wiki_files)
    
    logging.info(f"Found {len(wiki_files)} wiki HTML files to upload")
    
    # Process files in parallel
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = [executor.submit(process_wiki_file, f) for f in wiki_files]
        
        for i, future in enumerate(as_completed(futures), 1):
            future.result()
            
            # Print progress every 20 files
            if i % 20 == 0:
                with progress_lock:
                    logging.info(
                        f"Progress: {i}/{stats['total']} | "
                        f"Updated: {stats['updated']} | Not found: {stats['not_found']} | "
                        f"Empty wiki: {stats['empty_wiki']} | Failed: {stats['failed']}"
                    )
    
    # Final summary
    with progress_lock:
        logging.info(
            f"\nFinal Summary:\n"
            f"Total files processed: {stats['total']}\n"
            f"Successfully updated: {stats['updated']}\n"
            f"Boxers not found in DB: {stats['not_found']}\n"
            f"Empty wiki pages: {stats['empty_wiki']}\n"
            f"Failed: {stats['failed']}"
        )
    
    # Close database connection
    if db_conn:
        db_conn.close()

if __name__ == '__main__':
    main()