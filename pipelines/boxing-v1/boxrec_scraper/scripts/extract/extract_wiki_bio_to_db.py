#!/usr/bin/env python3
"""
Extract biographical content from wiki_html column and update boxer records with cleaned bio text.
"""

import os
import sys
import logging
import argparse
import re
from datetime import datetime, timezone
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import execute_batch
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from bs4 import BeautifulSoup

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
    'no_wiki': 0,
    'empty_bio': 0
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

def clean_text(text):
    """Clean and normalize text."""
    if not text:
        return None
    # Remove excessive whitespace and newlines
    text = ' '.join(text.split())
    # Remove wiki reference markers like [1], [2], etc.
    text = re.sub(r'\[\d+\]', '', text)
    # Remove edit links
    text = re.sub(r'\[edit\]', '', text)
    return text.strip()

def extract_bio_from_wiki_html(wiki_html):
    """Extract biographical content from wiki HTML."""
    if not wiki_html or len(wiki_html) < 100:
        return None
    
    # Check if page has actual content (not empty wiki page)
    if 'There is currently no text in this page' in wiki_html:
        return None
        
    soup = BeautifulSoup(wiki_html, 'html.parser')
    
    # Remove script and style elements
    for script in soup(["script", "style"]):
        script.decompose()
    
    bio_parts = []
    
    # 1. Extract basic info from the top (name, alias, hometown, etc.)
    basic_info = []
    for p in soup.find_all('p'):
        text = p.get_text()
        if any(keyword in text for keyword in ['Name:', 'Alias:', 'Hometown:', 'Birthplace:', 'Born:']):
            lines = text.split('\n')
            for line in lines:
                line = clean_text(line)
                if line and ':' in line:
                    basic_info.append(line)
    
    if basic_info:
        bio_parts.append('\n'.join(basic_info[:5]))  # Limit to first 5 info lines
    
    # 2. Extract career overview/biography sections
    section_headers = ['Career Overview', 'Biography', 'Early life', 'Career', 'Professional career', 'Amateur career']
    
    for header in section_headers:
        # Find h2 or h3 with this header
        header_elem = None
        for h in soup.find_all(['h2', 'h3']):
            if header.lower() in h.get_text().lower():
                header_elem = h
                break
        
        if header_elem:
            section_content = []
            
            # Add the section header
            section_content.append(f"\n{header}:")
            
            # Get content following this header until next header
            current = header_elem.find_next_sibling()
            items_added = 0
            
            while current and current.name not in ['h2', 'h3'] and items_added < 10:
                if current.name == 'p':
                    text = clean_text(current.get_text())
                    if text and len(text) > 30:  # Skip very short paragraphs
                        section_content.append(text)
                        items_added += 1
                        
                elif current.name == 'ul':
                    # Include career highlights from lists
                    for li in current.find_all('li'):
                        text = clean_text(li.get_text())
                        if text and len(text) > 20:
                            # Format as bullet point
                            section_content.append(f"• {text}")
                            items_added += 1
                            if items_added >= 10:
                                break
                                
                current = current.find_next_sibling()
            
            if len(section_content) > 1:  # More than just the header
                bio_parts.append('\n'.join(section_content))
    
    # 3. If no structured sections found, try to get any substantial paragraphs
    if not bio_parts:
        paragraphs = []
        for p in soup.find_all('p'):
            text = clean_text(p.get_text())
            if text and len(text) > 100:  # Only substantial paragraphs
                paragraphs.append(text)
        
        if paragraphs:
            bio_parts.extend(paragraphs[:3])  # First 3 paragraphs
    
    # Combine all parts with proper spacing
    if bio_parts:
        full_bio = '\n\n'.join(bio_parts)
        
        # Truncate if too long (e.g., for database field limits)
        max_length = 5000  # Adjust based on your database field
        if len(full_bio) > max_length:
            full_bio = full_bio[:max_length-3] + '...'
        
        return full_bio
    
    return None

def check_bio_column_exists(cur):
    """Check if bio column exists in the boxrec_boxer table."""
    cur.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_schema = 'data-pipelines-staging' 
        AND table_name = 'boxrec_boxer'
        AND column_name = 'bio';
    """)
    return cur.fetchone() is not None

def add_bio_column_if_needed(conn):
    """Add bio column to boxrec_boxer table if it doesn't exist."""
    cur = conn.cursor()
    
    if not check_bio_column_exists(cur):
        logging.info("Bio column not found. Adding it to the table...")
        cur.execute("""
            ALTER TABLE "data-pipelines-staging".boxrec_boxer 
            ADD COLUMN bio TEXT;
        """)
        conn.commit()
        logging.info("Bio column added successfully.")
    else:
        logging.info("Bio column already exists.")
    
    cur.close()

def process_boxer_record(record_id, boxrec_id, wiki_html):
    """Extract bio from wiki_html and update the record."""
    bio = extract_bio_from_wiki_html(wiki_html)
    
    if not bio:
        with progress_lock:
            stats['empty_bio'] += 1
        return False
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Update the bio field
        cur.execute("""
            UPDATE "data-pipelines-staging".boxrec_boxer 
            SET bio = %s, updated_at = %s
            WHERE id = %s;
        """, (bio, datetime.now(timezone.utc), record_id))
        
        if cur.rowcount > 0:
            conn.commit()
            with progress_lock:
                stats['updated'] += 1
            logging.info(f"[UPDATED] Boxer {boxrec_id} with bio ({len(bio)} chars)")
            return True
        else:
            with progress_lock:
                stats['failed'] += 1
            return False
            
    except Exception as e:
        conn.rollback()
        with progress_lock:
            stats['failed'] += 1
        logging.error(f"[ERROR] Failed to update boxer {boxrec_id}: {e}")
        return False
    finally:
        cur.close()

def main():
    parser = argparse.ArgumentParser(description='Extract bio from wiki_html and update boxer records')
    parser.add_argument('--limit', type=int, help='Limit number of records to process')
    parser.add_argument('--workers', type=int, default=5, help='Number of parallel workers')
    parser.add_argument('--boxrec-id', help='Process specific boxer by BoxRec ID')
    
    args = parser.parse_args()
    
    conn = get_db_connection()
    
    # Add bio column if it doesn't exist
    add_bio_column_if_needed(conn)
    
    cur = conn.cursor()
    
    try:
        # Build query to get boxers with wiki content
        query = """
            SELECT id, boxrec_id, wiki_html
            FROM "data-pipelines-staging".boxrec_boxer
            WHERE wiki_html IS NOT NULL 
            AND LENGTH(wiki_html) > 100
        """
        
        if args.boxrec_id:
            query += f" AND boxrec_id = '{args.boxrec_id}'"
        
        if args.limit:
            query += f" LIMIT {args.limit}"
        
        cur.execute(query)
        records = cur.fetchall()
        
        with progress_lock:
            stats['total'] = len(records)
        
        if not records:
            logging.info("No boxers found with wiki content.")
            return
        
        logging.info(f"Processing {len(records)} boxers with wiki content using {args.workers} workers")
        
        # Process records in parallel
        with ThreadPoolExecutor(max_workers=args.workers) as executor:
            futures = []
            for record_id, boxrec_id, wiki_html in records:
                future = executor.submit(process_boxer_record, record_id, boxrec_id, wiki_html)
                futures.append(future)
            
            for i, future in enumerate(as_completed(futures), 1):
                future.result()
                
                # Print progress every 20 records
                if i % 20 == 0:
                    with progress_lock:
                        logging.info(
                            f"Progress: {i}/{stats['total']} | "
                            f"Updated: {stats['updated']} | Empty bio: {stats['empty_bio']} | Failed: {stats['failed']}"
                        )
        
        # Final summary
        with progress_lock:
            logging.info(
                f"\nFinal Summary:\n"
                f"Total processed: {stats['total']}\n"
                f"Successfully updated: {stats['updated']}\n"
                f"Empty/no bio extracted: {stats['empty_bio']}\n"
                f"Failed: {stats['failed']}"
            )
    
    finally:
        cur.close()
        if db_conn:
            db_conn.close()

if __name__ == '__main__':
    main()