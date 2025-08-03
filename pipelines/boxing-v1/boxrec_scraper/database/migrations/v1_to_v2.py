#!/usr/bin/env python3
"""
Migration script from schema v1.0.0 to v2.0.0
Transforms boxer data to match the new schema requirements.
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime, timezone
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def migrate_boxer_data(v1_data):
    """Transform boxer data from v1.0.0 to v2.0.0 schema."""
    
    # Create v2 structure with default values for new fields
    v2_data = {
        # Identifiers
        'boxrec_id': v1_data.get('boxrec_id'),
        'boxrec_url': v1_data.get('boxrec_url'),
        'boxrec_wiki_url': v1_data.get('wiki'),  # Renamed field
        'slug': v1_data.get('slug'),
        
        # Names
        'full_name': v1_data.get('name'),  # Renamed from 'name'
        'birth_name': v1_data.get('birth_name'),
        'nickname': v1_data.get('alias'),  # Renamed from 'alias'
        
        # New fields with defaults
        'image_url': None,
        'date_of_birth': None,
        'weight': None,
        'bio': None,
        'trainer': None,
        'gym': None,
        
        # Existing fields
        'residence': v1_data.get('residence'),
        'birth_place': v1_data.get('birth_place'),
        'gender': v1_data.get('sex'),  # Renamed from 'sex'
        'nationality': v1_data.get('nationality'),
        'height': v1_data.get('height'),
        'reach': v1_data.get('reach'),
        'stance': v1_data.get('stance'),
        'promoter': v1_data.get('promoter'),
        'manager': v1_data.get('manager_agent'),  # Renamed from 'manager_agent'
        
        # Professional record - expanded from nested structure
        'pro_debut_date': v1_data.get('debut'),
        'pro_division': v1_data.get('division'),
        'pro_wins': v1_data.get('record', {}).get('wins'),
        'pro_wins_by_knockout': v1_data.get('record', {}).get('kos'),
        'pro_losses': v1_data.get('record', {}).get('losses'),
        'pro_losses_by_knockout': None,  # New field
        'pro_draws': v1_data.get('record', {}).get('draws'),
        'pro_status': v1_data.get('status'),
        'pro_total_bouts': v1_data.get('bouts_count'),
        'pro_total_rounds': v1_data.get('rounds_count'),
        
        # Amateur record - all new fields
        'amateur_debut_date': None,
        'amateur_division': None,
        'amateur_wins': None,
        'amateur_wins_by_knockout': None,
        'amateur_losses': None,
        'amateur_losses_by_knockout': None,
        'amateur_draws': None,
        'amateur_status': None,
        'amateur_total_bouts': None,
        'amateur_total_rounds': None,
        
        # Other fields
        'rating': v1_data.get('rating'),
        'ranking': v1_data.get('ranking'),
        'titles': v1_data.get('titles', []),
        'ko_percentage': v1_data.get('ko_percentage'),
        
        # Timestamps
        'created_at': datetime.now(timezone.utc).isoformat(),
        'updated_at': datetime.now(timezone.utc).isoformat()
    }
    
    # Migrate bouts
    v2_bouts = []
    for v1_bout in v1_data.get('bouts', []):
        v2_bout = {
            'bout_date': v1_bout.get('date'),  # Renamed from 'date'
            'opponent_name': v1_bout.get('opponent'),  # Renamed from 'opponent'
            'opponent_id': v1_bout.get('opponent_id'),
            'opponent_url': v1_bout.get('opponent_url'),
            'opponent_weight': None,  # New field
            'opponent_record': v1_bout.get('opponent_record'),
            'recent_form': v1_bout.get('recent_form'),
            'venue_name': v1_bout.get('venue'),  # Renamed from 'venue'
            
            # New fields for officials
            'referee_name': None,
            'judge_1_name': None,
            'judge_1_score': None,
            'judge_2_name': None,
            'judge_2_score': None,
            'judge_3_name': None,
            'judge_3_score': None,
            
            # Fight details
            'num_rounds_scheduled': None,
            'result': v1_bout.get('result'),
            'result_method': v1_bout.get('method'),  # Renamed from 'method'
            'result_round': v1_bout.get('rounds'),  # Renamed from 'rounds'
            
            # New link fields
            'event_page_link': None,
            'bout_page_link': None,
            'scorecards_page_link': None,
            'title_fight': None,
            
            'bout_rating': v1_bout.get('bout_rating')
        }
        v2_bouts.append(v2_bout)
    
    v2_data['bouts'] = v2_bouts
    
    # Include source_file if present (from combine script)
    if 'source_file' in v1_data:
        v2_data['source_file'] = v1_data['source_file']
    
    return v2_data

def validate_migration(v1_data, v2_data):
    """Validate that critical data wasn't lost in migration."""
    issues = []
    
    # Check key fields
    if v1_data.get('boxrec_id') != v2_data.get('boxrec_id'):
        issues.append("BoxRec ID mismatch")
    
    if v1_data.get('name') != v2_data.get('full_name'):
        issues.append("Name mismatch")
    
    # Check record
    v1_record = v1_data.get('record', {})
    if v1_record.get('wins') != v2_data.get('pro_wins'):
        issues.append("Wins count mismatch")
    
    # Check bouts count
    if len(v1_data.get('bouts', [])) != len(v2_data.get('bouts', [])):
        issues.append("Bouts count mismatch")
    
    return issues

def main():
    if len(sys.argv) < 3:
        print("Usage: python v1_to_v2.py <input_file_or_dir> <output_dir>")
        print("Example: python v1_to_v2.py data/processed/boxers_combined.json data/processed/v2/")
        sys.exit(1)
    
    input_path = Path(sys.argv[1])
    output_dir = Path(sys.argv[2])
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    files_to_process = []
    
    if input_path.is_file():
        files_to_process = [input_path]
    elif input_path.is_dir():
        files_to_process = list(input_path.glob('*.json'))
    else:
        logging.error(f"Input path not found: {input_path}")
        sys.exit(1)
    
    successful = 0
    failed = 0
    
    for json_file in files_to_process:
        try:
            logging.info(f"Processing {json_file.name}...")
            
            # Load v1 data
            with open(json_file, 'r', encoding='utf-8') as f:
                v1_data = json.load(f)
            
            # Handle both single boxer and combined files
            if isinstance(v1_data, list):
                # Combined file with multiple boxers
                v2_data = []
                for boxer in v1_data:
                    migrated = migrate_boxer_data(boxer)
                    
                    # Validate migration
                    issues = validate_migration(boxer, migrated)
                    if issues:
                        logging.warning(f"  Issues for {boxer.get('name', 'Unknown')}: {', '.join(issues)}")
                    
                    v2_data.append(migrated)
                
                output_file = output_dir / json_file.name
            else:
                # Single boxer file
                v2_data = migrate_boxer_data(v1_data)
                
                # Validate migration
                issues = validate_migration(v1_data, v2_data)
                if issues:
                    logging.warning(f"  Issues: {', '.join(issues)}")
                
                output_file = output_dir / json_file.name
            
            # Save migrated data
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(v2_data, f, indent=2)
            
            successful += 1
            logging.info(f"  ✅ Migrated to {output_file}")
            
        except Exception as e:
            failed += 1
            logging.error(f"  ❌ Failed to migrate {json_file.name}: {e}")
    
    # Summary
    logging.info(f"\nMigration complete:")
    logging.info(f"  Successful: {successful}")
    logging.info(f"  Failed: {failed}")
    
    # Create migration metadata
    metadata = {
        'migration': 'v1.0.0_to_v2.0.0',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'files_processed': successful,
        'files_failed': failed,
        'source_dir': str(input_path),
        'output_dir': str(output_dir)
    }
    
    metadata_file = output_dir / 'migration_metadata.json'
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    logging.info(f"Migration metadata saved to {metadata_file}")

if __name__ == "__main__":
    main()