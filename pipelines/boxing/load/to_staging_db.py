#!/usr/bin/env python3
"""
Load extracted data from HTML to staging mirror database.
This is the main ETL script that processes HTML files and populates the staging mirror DB.
"""

import json
import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import psycopg2

from ..utils.config import get_postgres_connection, OUTPUT_DIR
from ..database.staging import get_connection as get_staging_connection
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
                    amateurTotalBouts, amateurTotalRounds,
                    createdAt, updatedAt
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                boxer_data.get('wins_pro', 0),
                boxer_data.get('ko_wins_pro', 0),
                boxer_data.get('losses_pro', 0),
                boxer_data.get('ko_losses_pro', 0),
                boxer_data.get('draws_pro', 0),
                boxer_data.get('status_pro'),
                boxer_data.get('total_pro_bouts'),
                boxer_data.get('rounds_pro'),
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
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))
            
            # Delete existing bouts for this boxer
            cursor.execute("DELETE FROM boxerBouts WHERE boxerId = ?", (boxer_id,))
            
            # Insert bouts
            bouts = boxer_data.get('bouts', [])
            for i, bout in enumerate(bouts):
                bout_id = f"{boxer_id}_bout_{i}"
                
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
                    bout.get('opponent'),
                    bout.get('opponent_url'),
                    bout.get('location'),
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
    
    def process_html_file(self, boxrec_url: str, html_content: str) -> Optional[Dict]:
        """Extract data from HTML and load to staging."""
        try:
            # Extract data using orchestrator
            extracted_data = self.extractor.extract_all(html_content)
            
            if not extracted_data:
                logger.warning(f"No data extracted from {boxrec_url}")
                return None
            
            # Add URL to extracted data
            extracted_data['url'] = boxrec_url
            extracted_data['boxrec_id'] = boxrec_url.split('/')[-1]
            
            # Load to staging
            success = self.load_boxer(extracted_data)
            
            return extracted_data if success else None
            
        except Exception as e:
            logger.error(f"Error processing {boxrec_url}: {e}")
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
        
        # Get unprocessed records from data lake
        query = """
            SELECT boxrec_url, boxrec_id, html_file
            FROM "data-lake".boxrec_boxer_raw_html
            WHERE competition_level = 'professional'
        """
        if limit:
            query += f" LIMIT {limit}"
            
        pg_cursor.execute(query)
        all_records = pg_cursor.fetchall()
        
        # Filter out already processed records
        unprocessed = [(url, id, html) for url, id, html in all_records if id not in existing_ids]
        
        logger.info(f"Found {len(unprocessed)} unprocessed records")
        
        if not unprocessed:
            return {'processed': 0, 'successful': 0, 'failed': 0}
        
        processed = 0
        successful = 0
        failed = 0
        
        for boxrec_url, boxrec_id, html_content in unprocessed:
            try:
                
                # Process and load
                extracted_data = self.process_html_file(
                    boxrec_url=boxrec_url,
                    html_content=html_content
                )
                
                processed += 1
                
                if extracted_data:
                    successful += 1
                else:
                    failed += 1
                
                # Log progress
                if processed % 10 == 0:
                    logger.info(f"Progress: {processed}/{len(unprocessed)} processed")
                
            except Exception as e:
                logger.error(f"Error processing {boxrec_url}: {e}")
                failed += 1
        
        pg_conn.close()
        
        summary = {
            'processed': processed,
            'successful': successful,
            'failed': failed,
            'total_unprocessed': len(unprocessed)
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