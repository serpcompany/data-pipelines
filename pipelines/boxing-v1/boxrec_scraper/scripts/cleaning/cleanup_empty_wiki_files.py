#!/usr/bin/env python3
"""
Clean up empty BoxRec wiki files and create a blacklist to avoid re-scraping them.

This script:
1. Scans all wiki HTML files for the "no text" message
2. Deletes empty wiki files
3. Creates/updates a blacklist file to prevent re-scraping these IDs
4. Provides summary statistics
"""

import json
import os
import sys
import logging
from pathlib import Path
from datetime import datetime, timezone

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def is_empty_wiki_file(file_path):
    """Check if a wiki file contains the 'no text' message."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            return "There is currently no text in this page" in content
    except Exception as e:
        logging.error(f"Error reading {file_path}: {e}")
        return False

def extract_boxrec_id_from_filename(filename):
    """Extract BoxRec ID from wiki filename."""
    # Pattern: wiki_box-pro_XXXXXX.html
    if filename.startswith('wiki_box-pro_') and filename.endswith('.html'):
        return filename.replace('wiki_box-pro_', '').replace('.html', '')
    return None

def load_existing_blacklist(blacklist_path):
    """Load existing blacklist or create empty one."""
    if blacklist_path.exists():
        try:
            with open(blacklist_path, 'r') as f:
                data = json.load(f)
                return set(data.get('empty_wiki_ids', []))
        except Exception as e:
            logging.warning(f"Error loading blacklist: {e}")
    return set()

def save_blacklist(blacklist_path, empty_ids, stats):
    """Save blacklist with metadata."""
    blacklist_data = {
        'empty_wiki_ids': sorted(list(empty_ids)),
        'metadata': {
            'created_at': datetime.now(timezone.utc).isoformat(),
            'total_empty_ids': len(empty_ids),
            'description': 'BoxRec IDs with empty wiki pages - avoid re-scraping',
            'stats': stats
        }
    }
    
    with open(blacklist_path, 'w') as f:
        json.dump(blacklist_data, f, indent=2)

def main():
    if len(sys.argv) < 2:
        print("Usage: python cleanup_empty_wiki_files.py <wiki_directory> [--dry-run]")
        print("\nExamples:")
        print("  Dry run: python cleanup_empty_wiki_files.py data/raw/boxrec_wiki/ --dry-run")
        print("  Delete:  python cleanup_empty_wiki_files.py data/raw/boxrec_wiki/")
        sys.exit(1)

    wiki_dir = Path(sys.argv[1])
    dry_run = '--dry-run' in sys.argv

    if not wiki_dir.exists():
        logging.error(f"Wiki directory not found: {wiki_dir}")
        sys.exit(1)

    # Paths
    blacklist_path = wiki_dir.parent / 'empty_wiki_blacklist.json'
    
    # Load existing blacklist
    existing_blacklist = load_existing_blacklist(blacklist_path)
    logging.info(f"Existing blacklist has {len(existing_blacklist)} IDs")

    # Find all wiki files
    wiki_files = list(wiki_dir.glob('wiki_box-pro_*.html'))
    logging.info(f"Found {len(wiki_files)} wiki files to check")

    # Statistics
    stats = {
        'total_files_checked': len(wiki_files),
        'empty_files_found': 0,
        'files_deleted': 0,
        'new_blacklist_entries': 0,
        'existing_blacklist_entries': len(existing_blacklist),
        'dry_run': dry_run
    }

    empty_ids = existing_blacklist.copy()
    files_to_delete = []

    # Check each file
    for wiki_file in wiki_files:
        boxrec_id = extract_boxrec_id_from_filename(wiki_file.name)
        
        if not boxrec_id:
            logging.warning(f"Could not extract BoxRec ID from: {wiki_file.name}")
            continue

        if is_empty_wiki_file(wiki_file):
            stats['empty_files_found'] += 1
            files_to_delete.append(wiki_file)
            
            if boxrec_id not in empty_ids:
                empty_ids.add(boxrec_id)
                stats['new_blacklist_entries'] += 1
                logging.info(f"📝 New empty wiki found: {boxrec_id}")
            else:
                logging.info(f"🔁 Already blacklisted: {boxrec_id}")

    # Delete files if not dry run
    if not dry_run and files_to_delete:
        logging.info(f"\n🗑️  Deleting {len(files_to_delete)} empty wiki files...")
        for file_path in files_to_delete:
            try:
                file_path.unlink()
                stats['files_deleted'] += 1
                logging.info(f"✅ Deleted: {file_path.name}")
            except Exception as e:
                logging.error(f"❌ Error deleting {file_path.name}: {e}")
    
    # Save updated blacklist
    save_blacklist(blacklist_path, empty_ids, stats)
    
    # Summary
    logging.info(f"\n📊 SUMMARY:")
    logging.info(f"  Files checked: {stats['total_files_checked']}")
    logging.info(f"  Empty files found: {stats['empty_files_found']}")
    logging.info(f"  Files deleted: {stats['files_deleted']}")
    logging.info(f"  New blacklist entries: {stats['new_blacklist_entries']}")
    logging.info(f"  Total blacklisted IDs: {len(empty_ids)}")
    logging.info(f"  Blacklist saved to: {blacklist_path}")
    
    if dry_run:
        logging.info(f"\n🧪 DRY RUN - No files were actually deleted")
        logging.info(f"   Run without --dry-run to delete files")
    
    # Show some examples of empty IDs
    if empty_ids:
        example_ids = sorted(list(empty_ids))[:10]
        logging.info(f"\n📝 Example empty wiki IDs: {', '.join(example_ids)}")

if __name__ == "__main__":
    main()