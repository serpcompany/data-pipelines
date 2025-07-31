#!/usr/bin/env python3
"""
Combine individual boxer JSON files (v2 schema) into a single dataset.
Supports filtering by various criteria.
"""

import json
import os
import sys
from pathlib import Path
import logging
from datetime import datetime, timezone

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def load_boxer_data(json_path):
    """Load boxer data from JSON file."""
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def filter_boxer(boxer, filters):
    """Apply filters to determine if boxer should be included."""
    # Active only filter
    if filters.get('active_only'):
        if boxer.get('pro_status') != 'active':
            return False
    
    # Minimum wins filter
    min_wins = filters.get('min_wins')
    if min_wins is not None:
        wins = boxer.get('pro_wins', 0) or 0
        if wins < min_wins:
            return False
    
    # Winning record filter
    if filters.get('winning_record'):
        wins = boxer.get('pro_wins', 0) or 0
        losses = boxer.get('pro_losses', 0) or 0
        if wins <= losses:
            return False
    
    # Division filter
    divisions = filters.get('divisions')
    if divisions and boxer.get('pro_division'):
        if boxer['pro_division'].lower() not in [d.lower() for d in divisions]:
            return False
    
    # Nationality filter
    nationalities = filters.get('nationalities')
    if nationalities and boxer.get('nationality'):
        if boxer['nationality'] not in nationalities:
            return False
    
    # Title holder filter
    if filters.get('title_holders_only'):
        if not boxer.get('titles'):
            return False
    
    # KO percentage filter
    min_ko_pct = filters.get('min_ko_percentage')
    if min_ko_pct is not None:
        ko_pct_str = boxer.get('ko_percentage', '0%')
        try:
            ko_pct = float(ko_pct_str.rstrip('%'))
            if ko_pct < min_ko_pct:
                return False
        except ValueError:
            return False
    
    return True

def combine_boxers(input_dir, output_file, filters=None):
    """Combine individual boxer JSON files into one dataset."""
    if filters is None:
        filters = {}
    
    input_path = Path(input_dir)
    boxer_files = list(input_path.glob('*box-pro*.json'))
    
    if not boxer_files:
        logging.error(f"No boxer JSON files found in {input_dir}")
        return
    
    logging.info(f"Found {len(boxer_files)} boxer files to process")
    
    combined_data = []
    included = 0
    excluded = 0
    
    for json_file in boxer_files:
        try:
            boxer_data = load_boxer_data(json_file)
            
            # Add source file info
            boxer_data['source_file'] = json_file.name
            
            # Apply filters
            if filter_boxer(boxer_data, filters):
                combined_data.append(boxer_data)
                included += 1
                logging.debug(f"✅ Included: {boxer_data.get('full_name', 'Unknown')} ({json_file.name})")
            else:
                excluded += 1
                logging.debug(f"❌ Excluded: {boxer_data.get('full_name', 'Unknown')} ({json_file.name})")
                
        except Exception as e:
            logging.error(f"Error processing {json_file}: {e}")
    
    # Sort by name
    combined_data.sort(key=lambda x: x.get('full_name', '').lower())
    
    # Add metadata
    metadata = {
        '_metadata': {
            'schema_version': '2.0.0',
            'created_at': datetime.now(timezone.utc).isoformat(),
            'total_boxers': len(combined_data),
            'filters_applied': filters,
            'source_directory': str(input_dir),
            'files_processed': len(boxer_files),
            'boxers_included': included,
            'boxers_excluded': excluded
        }
    }
    
    # Save combined data
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        # Write metadata as first object
        json.dump(metadata, f, indent=2)
        f.write(',\n')
        # Write boxer array
        json.dump(combined_data, f, indent=2)
    
    logging.info(f"\nCombination complete:")
    logging.info(f"  Total files: {len(boxer_files)}")
    logging.info(f"  Boxers included: {included}")
    logging.info(f"  Boxers excluded: {excluded}")
    logging.info(f"  Output saved to: {output_file}")
    
    # Create summary report
    create_summary_report(combined_data, output_path.parent / 'summary_v2.json')

def create_summary_report(boxers, output_file):
    """Create a summary report of the combined data."""
    summary = {
        'total_boxers': len(boxers),
        'by_status': {},
        'by_division': {},
        'by_nationality': {},
        'by_stance': {},
        'title_holders': 0,
        'average_stats': {
            'wins': 0,
            'losses': 0,
            'draws': 0,
            'ko_percentage': 0,
            'bouts': 0,
            'rounds': 0
        },
        'top_boxers': {
            'by_wins': [],
            'by_ko_percentage': [],
            'by_total_bouts': []
        }
    }
    
    # Calculate statistics
    total_wins = 0
    total_losses = 0
    total_draws = 0
    total_ko_pct = 0
    total_bouts = 0
    total_rounds = 0
    valid_ko_pct_count = 0
    
    for boxer in boxers:
        # Status
        status = boxer.get('pro_status', 'unknown')
        summary['by_status'][status] = summary['by_status'].get(status, 0) + 1
        
        # Division
        division = boxer.get('pro_division', 'unknown')
        summary['by_division'][division] = summary['by_division'].get(division, 0) + 1
        
        # Nationality
        nationality = boxer.get('nationality', 'unknown')
        summary['by_nationality'][nationality] = summary['by_nationality'].get(nationality, 0) + 1
        
        # Stance
        stance = boxer.get('stance', 'unknown')
        summary['by_stance'][stance] = summary['by_stance'].get(stance, 0) + 1
        
        # Title holders
        if boxer.get('titles'):
            summary['title_holders'] += 1
        
        # Stats
        wins = boxer.get('pro_wins', 0) or 0
        losses = boxer.get('pro_losses', 0) or 0
        draws = boxer.get('pro_draws', 0) or 0
        bouts = boxer.get('pro_total_bouts', 0) or 0
        rounds = boxer.get('pro_total_rounds', 0) or 0
        
        total_wins += wins
        total_losses += losses
        total_draws += draws
        total_bouts += bouts
        total_rounds += rounds
        
        # KO percentage
        ko_pct_str = boxer.get('ko_percentage', '0%')
        try:
            ko_pct = float(ko_pct_str.rstrip('%'))
            total_ko_pct += ko_pct
            valid_ko_pct_count += 1
        except ValueError:
            pass
    
    # Calculate averages
    if len(boxers) > 0:
        summary['average_stats']['wins'] = round(total_wins / len(boxers), 1)
        summary['average_stats']['losses'] = round(total_losses / len(boxers), 1)
        summary['average_stats']['draws'] = round(total_draws / len(boxers), 1)
        summary['average_stats']['bouts'] = round(total_bouts / len(boxers), 1)
        summary['average_stats']['rounds'] = round(total_rounds / len(boxers), 1)
    
    if valid_ko_pct_count > 0:
        summary['average_stats']['ko_percentage'] = round(total_ko_pct / valid_ko_pct_count, 1)
    
    # Top boxers
    boxers_with_wins = [(b.get('full_name'), b.get('pro_wins', 0)) for b in boxers if b.get('pro_wins')]
    summary['top_boxers']['by_wins'] = sorted(boxers_with_wins, key=lambda x: x[1], reverse=True)[:10]
    
    boxers_with_ko = []
    for b in boxers:
        ko_pct_str = b.get('ko_percentage', '0%')
        try:
            ko_pct = float(ko_pct_str.rstrip('%'))
            if b.get('pro_wins', 0) >= 10:  # Only include boxers with 10+ wins
                boxers_with_ko.append((b.get('full_name'), ko_pct))
        except ValueError:
            pass
    summary['top_boxers']['by_ko_percentage'] = sorted(boxers_with_ko, key=lambda x: x[1], reverse=True)[:10]
    
    boxers_with_bouts = [(b.get('full_name'), b.get('pro_total_bouts', 0)) for b in boxers if b.get('pro_total_bouts')]
    summary['top_boxers']['by_total_bouts'] = sorted(boxers_with_bouts, key=lambda x: x[1], reverse=True)[:10]
    
    # Save summary
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2)
    
    logging.info(f"Summary report saved to: {output_file}")

def main():
    # Example usage with different filter combinations
    
    # Default: combine all boxers
    if len(sys.argv) < 3:
        print("Usage: python combine_boxer_json_v2.py <input_dir> <output_file> [filters]")
        print("\nExample filters:")
        print("  --active-only         Only include active boxers")
        print("  --min-wins N          Minimum number of wins")
        print("  --winning-record      Only boxers with more wins than losses")
        print("  --divisions D1,D2     Only specific divisions")
        print("  --nationalities N1,N2 Only specific nationalities")
        print("  --title-holders       Only current title holders")
        print("  --min-ko-pct N        Minimum KO percentage")
        sys.exit(1)
    
    input_dir = sys.argv[1]
    output_file = sys.argv[2]
    
    # Parse filters from command line
    filters = {}
    i = 3
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == '--active-only':
            filters['active_only'] = True
        elif arg == '--min-wins' and i + 1 < len(sys.argv):
            filters['min_wins'] = int(sys.argv[i + 1])
            i += 1
        elif arg == '--winning-record':
            filters['winning_record'] = True
        elif arg == '--divisions' and i + 1 < len(sys.argv):
            filters['divisions'] = sys.argv[i + 1].split(',')
            i += 1
        elif arg == '--nationalities' and i + 1 < len(sys.argv):
            filters['nationalities'] = sys.argv[i + 1].split(',')
            i += 1
        elif arg == '--title-holders':
            filters['title_holders_only'] = True
        elif arg == '--min-ko-pct' and i + 1 < len(sys.argv):
            filters['min_ko_percentage'] = float(sys.argv[i + 1])
            i += 1
        i += 1
    
    combine_boxers(input_dir, output_file, filters)

if __name__ == "__main__":
    main()