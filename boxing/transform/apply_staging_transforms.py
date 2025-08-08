#!/usr/bin/env python3
"""Apply data transformations to the staging database."""

import logging
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from boxing.database.staging_mirror import get_connection as get_staging_connection
from boxing.transform.bout_data import normalize_bout_date, normalize_bout_result

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def apply_date_normalization():
    """Apply date normalization to all bouts in staging."""
    conn = get_staging_connection()
    cursor = conn.cursor()
    
    logger.info("Starting date normalization...")
    
    # Get all boxers with bouts
    query = """
    SELECT id, bouts 
    FROM boxers 
    WHERE bouts IS NOT NULL
    """
    
    cursor.execute(query)
    boxers = cursor.fetchall()
    logger.info(f"Found {len(boxers)} boxers with bouts")
    
    updated_count = 0
    failed_count = 0
    total_bouts = 0
    
    import json
    
    for boxer in boxers:
        boxer_id, bouts_json = boxer
        if not bouts_json:
            continue
            
        bouts = json.loads(bouts_json)
        modified = False
        
        for bout in bouts:
            total_bouts += 1
            original_date = bout.get('boutDate')
            
            if original_date:
                # Try to get boxer's career year for context (approximate)
                # For now, we'll use 2023 as default for recent data
                base_year = 2023
                
                normalized_date = normalize_bout_date(original_date, base_year)
                
                if normalized_date and normalized_date != original_date:
                    bout['boutDate'] = normalized_date
                    modified = True
                    updated_count += 1
                    if updated_count % 100 == 0:
                        logger.info(f"Progress: {updated_count} dates normalized")
                elif not normalized_date:
                    failed_count += 1
                    if failed_count <= 10:  # Log first 10 failures
                        logger.warning(f"Could not normalize date '{original_date}' for boxer {boxer_id}")
        
        if modified:
            # Update boxer with modified bouts
            update_query = "UPDATE boxers SET bouts = ? WHERE id = ?"
            try:
                cursor.execute(update_query, (json.dumps(bouts), boxer_id))
            except Exception as e:
                logger.error(f"Failed to update boxer {boxer_id}: {e}")
    
    conn.commit()
    conn.close()
    
    logger.info(f"Date normalization complete: {updated_count}/{total_bouts} dates updated, {failed_count} failed")
    return updated_count, failed_count


def apply_result_normalization():
    """Apply result normalization to all bouts in staging."""
    conn = get_staging_connection()
    cursor = conn.cursor()
    
    logger.info("Starting result normalization...")
    
    # Get all boxers with bouts
    query = """
    SELECT id, bouts 
    FROM boxers 
    WHERE bouts IS NOT NULL
    """
    
    cursor.execute(query)
    boxers = cursor.fetchall()
    logger.info(f"Found {len(boxers)} boxers with bouts")
    
    updated_count = 0
    failed_count = 0
    total_bouts = 0
    
    import json
    
    for boxer in boxers:
        boxer_id, bouts_json = boxer
        if not bouts_json:
            continue
            
        bouts = json.loads(bouts_json)
        modified = False
        
        for bout in bouts:
            total_bouts += 1
            original_result = bout.get('result')
            
            if original_result:
                normalized_result = normalize_bout_result(original_result)
                
                if normalized_result and normalized_result != original_result:
                    bout['result'] = normalized_result
                    modified = True
                    updated_count += 1
                    if updated_count % 100 == 0:
                        logger.info(f"Progress: {updated_count} results normalized")
                elif not normalized_result:
                    failed_count += 1
                    if failed_count <= 10:  # Log first 10 failures
                        logger.warning(f"Could not normalize result '{original_result}' for boxer {boxer_id}")
        
        if modified:
            # Update boxer with modified bouts
            update_query = "UPDATE boxers SET bouts = ? WHERE id = ?"
            try:
                cursor.execute(update_query, (json.dumps(bouts), boxer_id))
            except Exception as e:
                logger.error(f"Failed to update boxer {boxer_id}: {e}")
    
    conn.commit()
    conn.close()
    
    logger.info(f"Result normalization complete: {updated_count}/{total_bouts} results updated, {failed_count} failed")
    return updated_count, failed_count


def main():
    """Run all transformations."""
    logger.info("Starting staging database transformations...")
    
    # Apply date normalization
    date_updated, date_failed = apply_date_normalization()
    
    # Apply result normalization
    result_updated, result_failed = apply_result_normalization()
    
    logger.info("Transformation summary:")
    logger.info(f"  Dates: {date_updated} normalized, {date_failed} failed")
    logger.info(f"  Results: {result_updated} normalized, {result_failed} failed")
    
    total_failed = date_failed + result_failed
    return 0 if total_failed == 0 else 1


if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent.parent / '.env'
    load_dotenv(env_path)
    
    sys.exit(main())