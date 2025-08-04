#!/usr/bin/env python3
"""Fix boxer IDs by normalizing them (removing leading zeros)."""

import logging
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from boxing.database.staging_mirror import get_connection as get_staging_connection
from boxing.transform import normalize_boxer_id

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def fix_boxer_ids_in_staging():
    """Fix boxer IDs in staging database by removing leading zeros."""
    conn = get_staging_connection()
    cursor = conn.cursor()
    
    try:
        # Get all boxers
        cursor.execute("SELECT id FROM boxers")
        boxers = cursor.fetchall()
        logger.info(f"Found {len(boxers)} boxers to check")
        
        updated_count = 0
        
        for (boxer_id,) in boxers:
            normalized_id = normalize_boxer_id(boxer_id)
            
            if normalized_id != boxer_id:
                logger.info(f"Normalizing boxer ID: {boxer_id} -> {normalized_id}")
                
                # Check if normalized ID already exists
                cursor.execute("SELECT COUNT(*) FROM boxers WHERE id = ?", (normalized_id,))
                if cursor.fetchone()[0] > 0:
                    logger.warning(f"Normalized ID {normalized_id} already exists, skipping {boxer_id}")
                    continue
                
                # Update boxer ID and all related records
                cursor.execute("BEGIN")
                
                # Update boxers table
                cursor.execute("UPDATE boxers SET id = ? WHERE id = ?", (normalized_id, boxer_id))
                
                # Update boxerBouts table
                cursor.execute("UPDATE boxerBouts SET boxerId = ? WHERE boxerId = ?", (normalized_id, boxer_id))
                
                cursor.execute("COMMIT")
                updated_count += 1
        
        logger.info(f"Normalized {updated_count} boxer IDs")
        
        # Now fix boxrec_id in data lake references
        cursor.execute("SELECT id, boxrecId FROM boxerBouts WHERE boxrecId IS NOT NULL")
        bouts = cursor.fetchall()
        
        bout_updates = 0
        for bout_id, boxrec_id in bouts:
            normalized = normalize_boxer_id(boxrec_id)
            if normalized != boxrec_id:
                cursor.execute("UPDATE boxerBouts SET boxrecId = ? WHERE id = ?", (normalized, bout_id))
                bout_updates += 1
        
        conn.commit()
        logger.info(f"Normalized {bout_updates} boxrec IDs in bouts")
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Error fixing boxer IDs: {e}")
        raise
    finally:
        conn.close()


def fix_boxer_ids_in_data_lake():
    """Fix boxer IDs in data lake by removing leading zeros."""
    import psycopg2
    import os
    
    DB_CONFIG = {
        'host': os.getenv('POSTGRES_HOST'),
        'port': os.getenv('POSTGRES_PORT'),
        'user': os.getenv('POSTGRES_USER'),
        'password': os.getenv('POSTGRES_PASSWORD'),
        'database': os.getenv('POSTGRES_DEFAULT_DB')
    }
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Get all boxer IDs with leading zeros
        cursor.execute("""
            SELECT DISTINCT boxrec_id 
            FROM "data-lake".boxrec_boxer_raw_html 
            WHERE boxrec_id ~ '^0+[0-9]+$'
        """)
        
        ids_to_fix = cursor.fetchall()
        logger.info(f"Found {len(ids_to_fix)} boxer IDs with leading zeros in data lake")
        
        for (boxer_id,) in ids_to_fix:
            normalized = normalize_boxer_id(boxer_id)
            logger.info(f"Normalizing data lake ID: {boxer_id} -> {normalized}")
            
            cursor.execute("""
                UPDATE "data-lake".boxrec_boxer_raw_html 
                SET boxrec_id = %s 
                WHERE boxrec_id = %s
            """, (normalized, boxer_id))
        
        conn.commit()
        logger.info(f"Normalized {len(ids_to_fix)} boxer IDs in data lake")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        logger.error(f"Error fixing data lake IDs: {e}")
        raise


if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent.parent / '.env'
    load_dotenv(env_path)
    
    logger.info("Fixing boxer IDs...")
    
    # Fix staging first
    fix_boxer_ids_in_staging()
    
    # Then fix data lake
    fix_boxer_ids_in_data_lake()
    
    logger.info("Boxer ID normalization complete")