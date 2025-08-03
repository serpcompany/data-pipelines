#!/usr/bin/env python3
"""
Load extracted data from HTML to staging mirror database.
This is the main ETL script that processes HTML files and populates the staging mirror DB.
"""

import json
import logging
import re
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import psycopg2

from ..utils.config import get_postgres_connection, OUTPUT_DIR
from ..database.staging_mirror import get_connection as get_staging_connection
from ..extract.orchestrator import ExtractionOrchestrator

logger = logging.getLogger(__name__)

class StagingLoader:
    """Load extracted boxer data into staging mirror database."""
    
    def __init__(self):
        self.staging_conn = None
        self.extractor = ExtractionOrchestrator()
    
    def __enter__(self):
        self.staging_conn = get_staging_connection()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.staging_conn:
            self.staging_conn.close()
    
    def load_boxer(self, boxer_data: Dict[str, Any]) -> bool:
        """Load a single boxer's data into staging mirror database."""
        cursor = self.staging_conn.cursor()
        
        try:
            # Start transaction
            cursor.execute("BEGIN")
            
            # Prepare boxer data
            boxer_id = boxer_data.get('boxrec_id', '').replace('/', '-')
            
            # Insert or update boxer
            cursor.execute("""
                INSERT OR REPLACE INTO boxers (
                    id, boxrecId, boxrecUrl, boxrecWikiUrl, slug, name,
                    birthName, nicknames, avatarImage, residence, birthPlace,
                    dateOfBirth, gender, nationality, height, reach, stance,
                    bio, promoters, trainers, managers, gym,
                    proDebutDate, proDivision, proWins, proWinsByKnockout,
                    proLosses, proLossesByKnockout, proDraws, proStatus,
                    proTotalBouts, proTotalRounds,
                    amateurDebutDate, amateurDivision, amateurWins, amateurWinsByKnockout,
                    amateurLosses, amateurLossesByKnockout, amateurDraws, amateurStatus,
                    amateurTotalBouts, amateurTotalRounds, hasAmateurRecord,
                    createdAt, updatedAt
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                boxer_id,
                boxer_data.get('boxrec_id'),
                boxer_data.get('url'),
                boxer_data.get('wiki_url'),
                boxer_data.get('slug', boxer_id),
                boxer_data.get('name'),
                boxer_data.get('birth_name'),
                json.dumps(boxer_data.get('nicknames', [])) if boxer_data.get('nicknames') else None,
                boxer_data.get('avatar_image'),
                boxer_data.get('residence'),
                boxer_data.get('birth_place'),
                boxer_data.get('date_of_birth'),
                boxer_data.get('gender'),
                boxer_data.get('nationality'),
                boxer_data.get('height'),
                boxer_data.get('reach'),
                boxer_data.get('stance'),
                boxer_data.get('bio'),
                json.dumps(boxer_data.get('promoters', [])) if boxer_data.get('promoters') else None,
                json.dumps(boxer_data.get('trainers', [])) if boxer_data.get('trainers') else None,
                json.dumps(boxer_data.get('managers', [])) if boxer_data.get('managers') else None,
                boxer_data.get('gym'),
                boxer_data.get('pro_debut_date'),
                boxer_data.get('division'),
                boxer_data.get('wins', 0),
                boxer_data.get('ko_wins', 0),
                boxer_data.get('losses', 0),
                boxer_data.get('ko_losses', 0),
                boxer_data.get('draws', 0),
                boxer_data.get('status'),
                boxer_data.get('total_bouts'),
                boxer_data.get('rounds'),
                boxer_data.get('amateur_debut_date'),
                boxer_data.get('division_amateur'),
                boxer_data.get('wins_amateur'),
                boxer_data.get('ko_wins_amateur'),
                boxer_data.get('losses_amateur'),
                boxer_data.get('ko_losses_amateur'),
                boxer_data.get('draws_amateur'),
                boxer_data.get('status_amateur'),
                boxer_data.get('total_amateur_bouts'),
                boxer_data.get('rounds_amateur'),
                boxer_data.get('has_amateur_record', False),
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))
            
            # Delete existing bouts for this boxer
            cursor.execute("DELETE FROM boxerBouts WHERE boxerId = ?", (boxer_id,))
            
            # Insert bouts
            bouts = boxer_data.get('bouts', [])
            for i, bout in enumerate(bouts):
                # Use the extracted bout_id if available, otherwise fall back to synthetic ID
                bout_id = bout.get('bout_id')
                if not bout_id:
                    # Try extracting from bout_link as fallback
                    bout_link = bout.get('bout_link', '')
                    if bout_link:
                        match = re.search(r'/event/\d+/(\d+)', bout_link)
                        if match:
                            bout_id = match.group(1)
                        else:
                            bout_id = f"{boxer_id}_bout_{i}"
                    else:
                        bout_id = f"{boxer_id}_bout_{i}"
                
                # Map field names from extractor to database schema
                cursor.execute("""
                    INSERT INTO boxerBouts (
                        id, boxerId, date, opponent, opponentUrl, location,
                        result, resultType, rounds, time, division, titles,
                        firstBoxerWeight, secondBoxerWeight, referee, judges,
                        boutType, boutOrder, createdAt, updatedAt
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    bout_id,
                    boxer_id,
                    bout.get('date'),
                    bout.get('opponent_name'),  # Extractor returns 'opponent_name'
                    bout.get('opponent_url'),
                    bout.get('venue'),  # Extractor returns 'venue'
                    bout.get('result'),
                    bout.get('result_type'),
                    bout.get('rounds'),
                    bout.get('time'),
                    bout.get('division'),
                    json.dumps(bout.get('titles', [])) if bout.get('titles') else None,
                    bout.get('first_boxer_weight'),
                    bout.get('second_boxer_weight'),
                    bout.get('referee'),
                    json.dumps(bout.get('judges', [])) if bout.get('judges') else None,
                    'pro',  # We're only handling pro bouts for now
                    i,
                    datetime.now().isoformat(),
                    datetime.now().isoformat()
                ))
            
            # Commit transaction
            cursor.execute("COMMIT")
            
            logger.info(f"Loaded boxer {boxer_data.get('name')} with {len(bouts)} bouts")
            return True
            
        except Exception as e:
            cursor.execute("ROLLBACK")
            logger.error(f"Error loading boxer {boxer_data.get('boxrec_id')}: {e}")
            return False
    
    def process_boxer_with_both_records(self, boxer_id: str, pro_url: str, 
                                      pro_html: str, amateur_html: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Extract data from both professional and amateur HTML and load to staging."""
        try:
            # Extract professional data (primary record)
            logger.info(f"Extracting professional data for boxer {boxer_id}")
            pro_data = self.extractor.extract_all(pro_html)
            
            if not pro_data:
                logger.warning(f"No professional data extracted for boxer {boxer_id}")
                return None
            
            # Add URL and ID to professional data
            pro_data['url'] = pro_url
            pro_data['boxrec_id'] = boxer_id
            
            # Extract amateur data if available
            if amateur_html:
                logger.info(f"Extracting amateur data for boxer {boxer_id}")
                try:
                    amateur_data = self.extractor.extract_all(amateur_html)
                    
                    if amateur_data:
                        # Copy amateur-specific fields to main data structure
                        # Amateur page shows amateur stats with same field names as pro
                        pro_data['wins_amateur'] = amateur_data.get('wins', 0)
                        pro_data['ko_wins_amateur'] = amateur_data.get('ko_wins', 0)
                        pro_data['losses_amateur'] = amateur_data.get('losses', 0)
                        pro_data['ko_losses_amateur'] = amateur_data.get('ko_losses', 0)
                        pro_data['draws_amateur'] = amateur_data.get('draws', 0)
                        pro_data['total_amateur_bouts'] = amateur_data.get('total_bouts')
                        pro_data['rounds_amateur'] = amateur_data.get('rounds')
                        pro_data['status_amateur'] = amateur_data.get('status')
                        pro_data['division_amateur'] = amateur_data.get('division')
                        pro_data['amateur_debut_date'] = amateur_data.get('debut_date')
                        
                        # Set flag indicating this boxer has amateur record
                        pro_data['has_amateur_record'] = True
                        logger.info(f"Successfully extracted amateur data for boxer {boxer_id}")
                    else:
                        logger.warning(f"No amateur data extracted for boxer {boxer_id}")
                        pro_data['has_amateur_record'] = False
                        
                except Exception as e:
                    logger.error(f"Error extracting amateur data for boxer {boxer_id}: {e}")
                    pro_data['has_amateur_record'] = False
            else:
                # No amateur HTML provided
                pro_data['has_amateur_record'] = False
            
            # Load combined data to staging
            success = self.load_boxer(pro_data)
            
            return pro_data if success else None
            
        except Exception as e:
            logger.error(f"Error processing boxer {boxer_id}: {e}")
            return None
    
    def load_from_data_lake(self, limit: Optional[int] = None) -> Dict:
        """Load unprocessed HTML files from data lake to staging."""
        logger.info("Loading data from data lake to staging database")
        
        # Get Postgres connection
        pg_conn = get_postgres_connection()
        pg_cursor = pg_conn.cursor()
        
        # Find boxer records not yet in staging
        staging_cursor = self.staging_conn.cursor()
        staging_cursor.execute("SELECT boxrecId FROM boxers")
        existing_ids = {row[0] for row in staging_cursor.fetchall()}
        
        # Get unprocessed records from data lake (both pro and amateur)
        query = """
            SELECT boxrec_url, boxrec_id, html_file, competition_level
            FROM "data-lake".boxrec_boxer_raw_html
            ORDER BY boxrec_id, competition_level DESC  -- Pro first, then amateur
        """
        if limit:
            query += f" LIMIT {limit}"
            
        pg_cursor.execute(query)
        all_records = pg_cursor.fetchall()
        
        # Group by boxer ID to get both pro and amateur HTML
        boxer_records = {}
        for url, boxer_id, html, comp_level in all_records:
            if boxer_id not in existing_ids:
                if boxer_id not in boxer_records:
                    boxer_records[boxer_id] = {}
                boxer_records[boxer_id][comp_level] = (url, html)
        
        logger.info(f"Found {len(boxer_records)} unprocessed boxers")
        
        if not boxer_records:
            return {'processed': 0, 'successful': 0, 'failed': 0}
        
        processed = 0
        successful = 0
        failed = 0
        
        for boxer_id, html_data in boxer_records.items():
            try:
                # Get professional HTML (required)
                if 'professional' not in html_data:
                    logger.warning(f"No professional HTML for boxer {boxer_id}, skipping")
                    continue
                
                pro_url, pro_html = html_data['professional']
                
                # Get amateur HTML (optional)
                amateur_html = None
                if 'amateur' in html_data:
                    _, amateur_html = html_data['amateur']
                
                # Process and load with both HTML versions
                extracted_data = self.process_boxer_with_both_records(
                    boxer_id=boxer_id,
                    pro_url=pro_url,
                    pro_html=pro_html,
                    amateur_html=amateur_html
                )
                
                processed += 1
                
                if extracted_data:
                    successful += 1
                else:
                    failed += 1
                
                # Log progress
                if processed % 10 == 0:
                    logger.info(f"Progress: {processed}/{len(boxer_records)} processed")
                
            except Exception as e:
                logger.error(f"Error processing boxer {boxer_id}: {e}")
                failed += 1
        
        pg_conn.close()
        
        summary = {
            'processed': processed,
            'successful': successful,
            'failed': failed,
            'total_unprocessed': len(boxer_records)
        }
        
        logger.info(f"Loading complete: {summary}")
        
        return summary
    
    def get_staging_stats(self) -> Dict:
        """Get statistics about the staging database."""
        cursor = self.staging_conn.cursor()
        
        stats = {}
        
        # Count boxers
        cursor.execute("SELECT COUNT(*) FROM boxers")
        stats['total_boxers'] = cursor.fetchone()[0]
        
        # Count bouts
        cursor.execute("SELECT COUNT(*) FROM boxerBouts")
        stats['total_bouts'] = cursor.fetchone()[0]
        
        # Count by status
        cursor.execute("""
            SELECT proStatus, COUNT(*) 
            FROM boxers 
            WHERE proStatus IS NOT NULL 
            GROUP BY proStatus
        """)
        stats['boxers_by_status'] = dict(cursor.fetchall())
        
        # Count by division
        cursor.execute("""
            SELECT proDivision, COUNT(*) 
            FROM boxers 
            WHERE proDivision IS NOT NULL 
            GROUP BY proDivision
            ORDER BY COUNT(*) DESC
            LIMIT 10
        """)
        stats['top_divisions'] = dict(cursor.fetchall())
        
        return stats

def run_staging_load(limit: Optional[int] = None):
    """Run the staging load process."""
    logger.info("Starting staging load process")
    
    with StagingLoader() as loader:
        # Load from data lake
        summary = loader.load_from_data_lake(limit=limit)
        
        # Get final stats
        stats = loader.get_staging_stats()
        
        logger.info(f"Staging database stats: {stats}")
        
        return {
            'load_summary': summary,
            'staging_stats': stats
        }

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Test loading with a small batch
    result = run_staging_load(limit=5)
    
    print("\nStaging Load Results:")
    print(json.dumps(result, indent=2))