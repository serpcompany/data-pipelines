#!/usr/bin/env python3
"""
Extract biographical data from wiki HTML files and upload to PostgreSQL database.
Updates boxer records with trainer, manager, bio, and other wiki-derived information.
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

def clean_text(text):
    """Clean and normalize text."""
    if not text:
        return None
    # Remove excessive whitespace and newlines
    text = ' '.join(text.split())
    # Remove wiki reference markers like [1], [2], etc.
    text = re.sub(r'\[\d+\]', '', text)
    return text.strip()

def extract_trainers(soup):
    """Extract trainer information from wiki page."""
    trainers = []
    
    # Look for trainer info in lists
    for li in soup.find_all('li'):
        text = li.get_text()
        if 'Trainer' in text and ':' in text:
            trainer_text = text.split(':', 1)[1]
            trainer_text = clean_text(trainer_text)
            if trainer_text:
                # Handle multiple trainers separated by commas or parentheses
                trainer_parts = re.split(r'[,()]', trainer_text)
                for part in trainer_parts:
                    part = part.strip()
                    # Skip date ranges
                    if part and not re.match(r'^\d{4}-\d{4}$', part):
                        trainers.append(part)
    
    return list(set(trainers))  # Remove duplicates

def extract_managers(soup):
    """Extract manager information from wiki page."""
    managers = []
    
    for li in soup.find_all('li'):
        text = li.get_text()
        if 'Manager' in text and ':' in text:
            manager_text = text.split(':', 1)[1]
            manager_text = clean_text(manager_text)
            if manager_text:
                manager_parts = re.split(r'[,()]', manager_text)
                for part in manager_parts:
                    part = part.strip()
                    if part and not re.match(r'^\d{4}-\d{4}$', part):
                        managers.append(part)
    
    return list(set(managers))

def extract_bio_section(soup):
    """Extract biography or career summary text."""
    bio_text = []
    
    # Look for specific sections
    section_headers = ['Biography', 'Early life', 'Career', 'Professional career', 'Amateur career', 'Career Overview']
    
    for header in section_headers:
        # Find h2 or h3 with this header
        header_elem = None
        for h in soup.find_all(['h2', 'h3']):
            if header.lower() in h.get_text().lower():
                header_elem = h
                break
        
        if header_elem:
            # Get paragraphs following this header until next header
            current = header_elem.find_next_sibling()
            while current and current.name not in ['h2', 'h3']:
                if current.name == 'p':
                    text = clean_text(current.get_text())
                    if text and len(text) > 50:  # Skip very short paragraphs
                        bio_text.append(text)
                elif current.name == 'ul':
                    # Include career highlights from lists
                    for li in current.find_all('li'):
                        text = clean_text(li.get_text())
                        if text and len(text) > 30:
                            bio_text.append(f"• {text}")
                current = current.find_next_sibling()
    
    # Join paragraphs with proper spacing
    return '\n\n'.join(bio_text[:5]) if bio_text else None  # Limit to first 5 paragraphs/points

def extract_additional_info(soup):
    """Extract other useful information from wiki page."""
    info = {}
    
    # Look for structured data in the wiki content
    all_text = soup.get_text()
    
    # Birth date pattern
    birth_match = re.search(r'Born:\s*(\d{4}-\d{2}-\d{2})', all_text)
    if birth_match:
        info['date_of_birth'] = birth_match.group(1)
    
    # Gym pattern
    gym_match = re.search(r'Gym:\s*([^\n]+)', all_text)
    if gym_match:
        info['gym'] = clean_text(gym_match.group(1))
    
    # Hometown pattern
    hometown_match = re.search(r'Hometown:\s*([^\n]+)', all_text)
    if hometown_match:
        info['hometown'] = clean_text(hometown_match.group(1))
    
    # Birthplace pattern  
    birthplace_match = re.search(r'Birthplace:\s*([^\n]+)', all_text)
    if birthplace_match:
        info['birthplace'] = clean_text(birthplace_match.group(1))
    
    return info

def parse_wiki_file(wiki_path):
    """Parse a single wiki HTML file and extract biographical data."""
    try:
        with open(wiki_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if page has actual content (not empty wiki page)
        if 'There is currently no text in this page' in content:
            return None
            
        soup = BeautifulSoup(content, 'html.parser')
        
        # Extract BoxRec ID from filename
        boxrec_id = re.search(r'wiki_box-pro_(\d+)\.html', str(wiki_path))
        if not boxrec_id:
            return None
        
        boxrec_id = boxrec_id.group(1)
        
        # Extract biographical data
        trainers = extract_trainers(soup)
        managers = extract_managers(soup)
        bio = extract_bio_section(soup)
        additional_info = extract_additional_info(soup)
        
        # Only return if we found meaningful data
        if not trainers and not managers and not bio and not additional_info:
            return None
        
        return {
            'boxrec_id': boxrec_id,
            'trainers': trainers if trainers else None,
            'managers': managers if managers else None,
            'bio': bio,
            'additional_info': additional_info
        }
        
    except Exception as e:
        logging.error(f"Error parsing {wiki_path}: {e}")
        return None

def update_boxer_in_db(wiki_data):
    """Update boxer record in database with wiki biographical data."""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        boxrec_id = wiki_data['boxrec_id']
        
        # Build update query dynamically based on available data
        updates = []
        values = []
        
        # Primary trainer (first trainer if multiple)
        if wiki_data.get('trainers'):
            updates.append("trainer = %s")
            values.append(wiki_data['trainers'][0])
        
        # Primary manager (first manager if multiple)
        if wiki_data.get('managers'):
            updates.append("manager = %s") 
            values.append(wiki_data['managers'][0])
        
        # Biography text
        if wiki_data.get('bio'):
            updates.append("bio = %s")
            values.append(wiki_data['bio'])
        
        # Additional info fields
        additional = wiki_data.get('additional_info', {})
        if additional.get('date_of_birth'):
            updates.append("date_of_birth = %s")
            values.append(additional['date_of_birth'])
        
        if additional.get('gym'):
            updates.append("gym = %s")
            values.append(additional['gym'])
            
        if additional.get('hometown'):
            updates.append("residence = %s")  # Map hometown to residence field
            values.append(additional['hometown'])
            
        if additional.get('birthplace'):
            updates.append("birth_place = %s")
            values.append(additional['birthplace'])
        
        # Mark as wiki updated
        updates.append("wiki_scraped = %s")
        updates.append("updated_at = %s")
        values.extend([True, datetime.now(timezone.utc)])
        
        if not updates:
            return False
        
        # Add boxrec_id for WHERE clause
        values.append(boxrec_id)
        
        # Execute update (assuming table name is 'boxers' - adjust as needed)
        query = f"""
            UPDATE boxers 
            SET {', '.join(updates)}
            WHERE boxrec_id = %s
        """
        
        cur.execute(query, values)
        
        if cur.rowcount > 0:
            conn.commit()
            with progress_lock:
                stats['updated'] += 1
            logging.info(f"[UPDATED] Boxer {boxrec_id} with wiki data")
            return True
        else:
            with progress_lock:
                stats['skipped'] += 1
            logging.warning(f"[SKIP] Boxer {boxrec_id} not found in database")
            return False
            
    except Exception as e:
        conn.rollback()
        with progress_lock:
            stats['failed'] += 1
        logging.error(f"[ERROR] Failed to update boxer {boxrec_id}: {e}")
        return False
    finally:
        cur.close()

def process_wiki_file(wiki_file):
    """Process a single wiki file and update database."""
    wiki_data = parse_wiki_file(wiki_file)
    if wiki_data:
        return update_boxer_in_db(wiki_data)
    else:
        with progress_lock:
            stats['skipped'] += 1
        return False

def main():
    parser = argparse.ArgumentParser(description='Upload wiki biographical data to PostgreSQL database')
    parser.add_argument('wiki_dir', type=Path, help='Directory containing wiki HTML files')
    parser.add_argument('--workers', type=int, default=5, help='Number of parallel workers')
    parser.add_argument('--limit', type=int, help='Limit number of files to process')
    
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
    
    logging.info(f"Processing {len(wiki_files)} wiki files with {args.workers} workers")
    
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
                        f"Updated: {stats['updated']} | Failed: {stats['failed']} | Skipped: {stats['skipped']}"
                    )
    
    # Final summary
    with progress_lock:
        logging.info(
            f"\nFinal Summary:\n"
            f"Total files processed: {stats['total']}\n"
            f"Database records updated: {stats['updated']}\n"
            f"Failed: {stats['failed']}\n"
            f"Skipped (no data/not found): {stats['skipped']}"
        )
    
    # Close database connection
    if db_conn:
        db_conn.close()

if __name__ == '__main__':
    main()