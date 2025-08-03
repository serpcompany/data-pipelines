#!/usr/bin/env python3
"""
Metadata tracking for the data lake.
Tracks HTML files, their hashes, and change detection.
"""

import hashlib
import psycopg2
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List
import logging

from ..utils.config import get_postgres_connection
from .staging_mirror import get_connection as get_staging_connection

logger = logging.getLogger(__name__)

class MetadataTracker:
    """Track metadata for HTML files in the data lake."""
    
    def __init__(self):
        self.pg_conn = None
        self.staging_conn = None
    
    def __enter__(self):
        self.pg_conn = get_postgres_connection()
        self.staging_conn = get_staging_connection()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.pg_conn:
            self.pg_conn.close()
        if self.staging_conn:
            self.staging_conn.close()
    
    def calculate_hash(self, content: str) -> str:
        """Calculate SHA-256 hash of HTML content."""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def track_scraped_html(self, boxrec_url: str, boxrec_id: str, 
                          html_content: str, scraped_at: datetime) -> Dict:
        """Track a newly scraped HTML file in metadata."""
        html_hash = self.calculate_hash(html_content)
        
        cursor = self.staging_conn.cursor()
        
        # Check if URL already exists
        cursor.execute("""
            SELECT id, html_hash, last_checked_at 
            FROM data_lake_metadata 
            WHERE boxrec_url = ?
        """, (boxrec_url,))
        
        existing = cursor.fetchone()
        
        if existing:
            metadata_id, old_hash, last_checked = existing
            change_detected = old_hash != html_hash
            
            # Update existing record
            cursor.execute("""
                UPDATE data_lake_metadata 
                SET html_hash = ?, 
                    last_checked_at = ?,
                    change_detected = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (html_hash, scraped_at, change_detected, metadata_id))
            
            self.staging_conn.commit()
            
            logger.info(f"Updated metadata for {boxrec_url}, change detected: {change_detected}")
            
            return {
                'id': metadata_id,
                'change_detected': change_detected,
                'previous_hash': old_hash,
                'new_hash': html_hash,
                'last_checked': last_checked
            }
        else:
            # Insert new record
            cursor.execute("""
                INSERT INTO data_lake_metadata 
                (boxrec_url, boxrec_id, html_hash, scraped_at, last_checked_at)
                VALUES (?, ?, ?, ?, ?)
            """, (boxrec_url, boxrec_id, html_hash, scraped_at, scraped_at))
            
            self.staging_conn.commit()
            metadata_id = cursor.lastrowid
            
            logger.info(f"Created new metadata record for {boxrec_url}")
            
            return {
                'id': metadata_id,
                'change_detected': False,
                'new_hash': html_hash,
                'first_scrape': True
            }
    
    def mark_extracted(self, boxrec_url: str, extracted_at: Optional[datetime] = None):
        """Mark that HTML has been extracted to structured data."""
        if extracted_at is None:
            extracted_at = datetime.now()
        
        cursor = self.staging_conn.cursor()
        cursor.execute("""
            UPDATE data_lake_metadata 
            SET extracted_at = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE boxrec_url = ?
        """, (extracted_at, boxrec_url))
        
        self.staging_conn.commit()
        logger.info(f"Marked {boxrec_url} as extracted")
    
    def get_changed_urls(self) -> List[Dict]:
        """Get all URLs where changes have been detected."""
        cursor = self.staging_conn.cursor()
        cursor.execute("""
            SELECT boxrec_url, boxrec_id, html_hash, 
                   scraped_at, last_checked_at, extracted_at
            FROM data_lake_metadata 
            WHERE change_detected = TRUE
            ORDER BY last_checked_at DESC
        """)
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'boxrec_url': row[0],
                'boxrec_id': row[1],
                'html_hash': row[2],
                'scraped_at': row[3],
                'last_checked_at': row[4],
                'extracted_at': row[5]
            })
        
        return results
    
    def get_unextracted_urls(self) -> List[Dict]:
        """Get all URLs that haven't been extracted yet."""
        cursor = self.staging_conn.cursor()
        cursor.execute("""
            SELECT boxrec_url, boxrec_id, html_hash, scraped_at
            FROM data_lake_metadata 
            WHERE extracted_at IS NULL
            ORDER BY scraped_at DESC
        """)
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'boxrec_url': row[0],
                'boxrec_id': row[1],
                'html_hash': row[2],
                'scraped_at': row[3]
            })
        
        return results
    
    def get_stats(self) -> Dict:
        """Get statistics about the data lake."""
        cursor = self.staging_conn.cursor()
        
        stats = {}
        
        # Total URLs
        cursor.execute("SELECT COUNT(*) FROM data_lake_metadata")
        stats['total_urls'] = cursor.fetchone()[0]
        
        # Extracted URLs
        cursor.execute("SELECT COUNT(*) FROM data_lake_metadata WHERE extracted_at IS NOT NULL")
        stats['extracted_urls'] = cursor.fetchone()[0]
        
        # URLs with changes
        cursor.execute("SELECT COUNT(*) FROM data_lake_metadata WHERE change_detected = TRUE")
        stats['urls_with_changes'] = cursor.fetchone()[0]
        
        # Latest scrape
        cursor.execute("SELECT MAX(scraped_at) FROM data_lake_metadata")
        stats['latest_scrape'] = cursor.fetchone()[0]
        
        # Latest extraction
        cursor.execute("SELECT MAX(extracted_at) FROM data_lake_metadata")
        stats['latest_extraction'] = cursor.fetchone()[0]
        
        return stats

def sync_metadata_from_postgres():
    """Sync metadata from Postgres data lake to local staging."""
    logger.info("Syncing metadata from Postgres data lake...")
    
    with MetadataTracker() as tracker:
        pg_cursor = tracker.pg_conn.cursor()
        
        # Get all records from Postgres
        pg_cursor.execute("""
            SELECT boxrec_url, boxrec_id, scraped_at, created_at
            FROM "data-pipelines-raw".boxrec_boxer_raw_html
            ORDER BY created_at
        """)
        
        count = 0
        for row in pg_cursor.fetchall():
            boxrec_url, boxrec_id, scraped_at, created_at = row
            
            # For initial sync, we don't have the HTML content to hash
            # So we'll use a placeholder and mark for extraction
            tracker.track_scraped_html(
                boxrec_url=boxrec_url,
                boxrec_id=boxrec_id,
                html_content=f"INITIAL_SYNC_{boxrec_id}",  # Placeholder
                scraped_at=scraped_at or created_at
            )
            count += 1
        
        logger.info(f"Synced {count} metadata records from Postgres")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Test metadata tracking
    with MetadataTracker() as tracker:
        stats = tracker.get_stats()
        print("\nData Lake Statistics:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
        
        # Show unextracted URLs
        unextracted = tracker.get_unextracted_urls()
        print(f"\nUnextracted URLs: {len(unextracted)}")
        if unextracted:
            print("  First 5:")
            for url_info in unextracted[:5]:
                print(f"    - {url_info['boxrec_url']}")