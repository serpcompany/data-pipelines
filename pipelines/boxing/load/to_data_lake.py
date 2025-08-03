#!/usr/bin/env python3
"""Load validated HTML files to Postgres data lake."""

import os
import psycopg2
from pathlib import Path
from datetime import datetime
from typing import Optional
import logging
from ..utils.config import VALIDATED_HTML_DIR, LOG_DIR

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / 'data_lake_loader.log'),
        logging.StreamHandler()
    ]
)

# Load database credentials from environment
DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST'),
    'port': os.getenv('POSTGRES_PORT'),
    'user': os.getenv('POSTGRES_USER'),
    'password': os.getenv('POSTGRES_PASSWORD'),
    'database': os.getenv('POSTGRES_DEFAULT_DB')
}


def extract_boxer_id_from_filename(filename: str) -> Optional[str]:
    """Extract boxer ID from filename like 'en_box-pro_123456.html' or 'en_box-am_123456.html'."""
    parts = filename.replace('.html', '').split('_')
    if len(parts) >= 3 and ('box-pro' in parts[1] or 'box-am' in parts[1]):
        return parts[-1]
    return None


def construct_boxrec_url(filename: str) -> Optional[str]:
    """Construct BoxRec URL from filename."""
    parts = filename.replace('.html', '').split('_')
    if len(parts) >= 3:
        lang = parts[0]
        page_type = parts[1]  # box-pro or box-am
        boxer_id = parts[-1]
        if page_type in ['box-pro', 'box-am']:
            return f"https://boxrec.com/{lang}/{page_type}/{boxer_id}"
    return None


def get_competition_level(filename: str) -> str:
    """Determine competition level from filename."""
    if 'box-am' in filename:
        return 'amateur'
    return 'professional'


def load_html_to_data_lake(html_file: Path) -> bool:
    """Load a single HTML file to the data lake."""
    try:
        # Read HTML content
        with open(html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Extract metadata from filename
        filename = html_file.name
        boxer_id = extract_boxer_id_from_filename(filename)
        boxrec_url = construct_boxrec_url(filename)
        competition_level = get_competition_level(filename)
        
        if not boxer_id or not boxrec_url:
            logging.warning(f"Could not extract metadata from {filename}")
            return False
        
        # Connect to database
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # Check if record exists for this competition level
        cur.execute("""
            SELECT id, html_file 
            FROM "data-lake".boxrec_boxer_raw_html 
            WHERE boxrec_id = %s AND competition_level = %s
        """, (boxer_id, competition_level))
        
        existing = cur.fetchone()
        
        if existing:
            # Update existing record
            record_id, old_html = existing
            
            # Only update if content changed
            if old_html != html_content:
                cur.execute("""
                    UPDATE "data-lake".boxrec_boxer_raw_html 
                    SET html_file = %s, 
                        scraped_at = %s,
                        updated_at = %s
                    WHERE id = %s
                """, (html_content, datetime.now(), datetime.now(), record_id))
                
                logging.info(f"Updated {competition_level} boxer {boxer_id} - content changed")
            else:
                logging.info(f"Skipped {competition_level} boxer {boxer_id} - no changes")
        else:
            # Insert new record
            cur.execute("""
                INSERT INTO "data-lake".boxrec_boxer_raw_html 
                (boxrec_url, boxrec_id, html_file, competition_level, scraped_at, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (boxrec_url, boxer_id, html_content, competition_level, datetime.now(), datetime.now(), datetime.now()))
            
            logging.info(f"Inserted new {competition_level} boxer {boxer_id}")
        
        conn.commit()
        cur.close()
        conn.close()
        
        return True
        
    except Exception as e:
        logging.error(f"Error loading {html_file.name}: {e}")
        return False


def load_all_validated_files():
    """Load all validated HTML files to the data lake."""
    html_files = list(VALIDATED_HTML_DIR.glob('*.html'))
    
    if not html_files:
        logging.info("No validated HTML files found")
        return
    
    logging.info(f"Found {len(html_files)} validated HTML files")
    
    success_count = 0
    for html_file in html_files:
        if load_html_to_data_lake(html_file):
            success_count += 1
    
    logging.info(f"Successfully loaded {success_count}/{len(html_files)} files to data lake")


if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent.parent / '.env'
    load_dotenv(env_path)
    
    # Run the loader
    load_all_validated_files()