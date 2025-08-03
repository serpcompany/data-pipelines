#!/usr/bin/env python3
"""
Update the primary URL list for scraping and clean up old files.
Makes boxrec-urls-to-scrape-with-slugs.csv the primary source.
"""

import csv
import json
import shutil
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)

def remove_duplicates_from_csv():
    """Remove duplicate BoxRec IDs from the main CSV file."""
    input_file = Path('data/boxrec-urls-to-scrape-with-slugs.csv')
    output_file = Path('data/urls.csv')  # Standard name for scraping
    
    if not input_file.exists():
        logging.error(f"Input file not found: {input_file}")
        return
    
    seen_ids = set()
    unique_boxers = []
    duplicates_removed = 0
    
    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            boxrec_id = row.get('boxrec_id')
            
            if boxrec_id and boxrec_id not in seen_ids:
                seen_ids.add(boxrec_id)
                unique_boxers.append(row)
            else:
                duplicates_removed += 1
    
    # Save cleaned CSV with standard format for scraping
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        if unique_boxers:
            writer = csv.DictWriter(f, fieldnames=unique_boxers[0].keys())
            writer.writeheader()
            writer.writerows(unique_boxers)
    
    logging.info(f"✅ Created primary URL file: {output_file}")
    logging.info(f"   Unique boxers: {len(unique_boxers):,}")
    logging.info(f"   Duplicates removed: {duplicates_removed:,}")
    
    return len(unique_boxers), duplicates_removed

def cleanup_old_files():
    """Remove old/duplicate files identified in audit."""
    files_to_remove = [
        'data/raw/urls.csv',
        'data/existing_boxers_urls.csv',
        'data/existing_boxers.csv', 
        'data/existing_boxers.json',
        'data/unmatched_boxers.json',
        'data/scraping_time_estimate.json',
        'data/update_plan.json'
    ]
    
    dirs_to_remove = [
        'data/raw/boxrec_json',
        'data/raw/boxrec_json_v2'
    ]
    
    removed_files = 0
    removed_dirs = 0
    
    # Remove files
    for file_path in files_to_remove:
        path = Path(file_path)
        if path.exists():
            path.unlink()
            removed_files += 1
            logging.info(f"🗑️  Removed: {file_path}")
    
    # Remove directories
    for dir_path in dirs_to_remove:
        path = Path(dir_path)
        if path.exists():
            shutil.rmtree(path)
            removed_dirs += 1
            logging.info(f"🗑️  Removed directory: {dir_path}")
    
    logging.info(f"✅ Cleanup complete: {removed_files} files, {removed_dirs} directories removed")
    
    return removed_files, removed_dirs

def create_url_summary():
    """Create summary of the new primary URL file."""
    url_file = Path('data/urls.csv')
    
    if not url_file.exists():
        logging.error("Primary URL file not found")
        return
    
    stats = {
        'total_boxers': 0,
        'with_existing_slugs': 0,
        'new_boxers': 0,
        'sample_boxers': []
    }
    
    with open(url_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for i, row in enumerate(reader):
            stats['total_boxers'] += 1
            
            if row.get('slug'):
                stats['with_existing_slugs'] += 1
            else:
                stats['new_boxers'] += 1
            
            # Sample first 5 boxers
            if i < 5:
                stats['sample_boxers'].append({
                    'name': row.get('name'),
                    'boxrec_id': row.get('boxrec_id'),
                    'slug': row.get('slug', 'NEW'),
                    'has_slug': bool(row.get('slug'))
                })
    
    # Save summary
    summary_file = Path('data/url_summary.json')
    with open(summary_file, 'w') as f:
        json.dump(stats, f, indent=2)
    
    logging.info(f"\n📊 URL Summary:")
    logging.info(f"   Total boxers: {stats['total_boxers']:,}")
    logging.info(f"   With existing slugs: {stats['with_existing_slugs']:,}")
    logging.info(f"   New boxers: {stats['new_boxers']:,}")
    logging.info(f"   Summary saved: {summary_file}")
    
    return stats

def update_scraping_scripts():
    """Update scraping scripts to use the new primary URL file."""
    # Check which scripts need updating
    scripts_to_check = [
        'scripts/scrape.py',
        'scripts/scrape_concurrent.py'
    ]
    
    updates_needed = []
    
    for script_path in scripts_to_check:
        script = Path(script_path)
        if script.exists():
            content = script.read_text()
            if 'urls.csv' not in content and 'boxrec-urls-to-scrape' in content:
                updates_needed.append(script_path)
    
    if updates_needed:
        logging.info(f"\n⚠️  Scripts may need URL file updates:")
        for script in updates_needed:
            logging.info(f"   - {script}")
        logging.info(f"   Update to use: data/urls.csv")
    else:
        logging.info(f"\n✅ Scraping scripts appear compatible with data/urls.csv")

def main():
    """Main function to update URLs and clean up."""
    logging.info("🔄 Updating primary URL list and cleaning up repository...")
    
    # Remove duplicates and create primary URL file
    logging.info("\n1️⃣ Creating deduplicated primary URL file...")
    unique_count, duplicates = remove_duplicates_from_csv()
    
    # Clean up old files
    logging.info("\n2️⃣ Cleaning up old/duplicate files...")
    removed_files, removed_dirs = cleanup_old_files()
    
    # Create summary
    logging.info("\n3️⃣ Creating URL summary...")
    stats = create_url_summary()
    
    # Check script compatibility
    logging.info("\n4️⃣ Checking script compatibility...")
    update_scraping_scripts()
    
    # Final summary
    logging.info(f"\n🎉 Repository Update Complete!")
    logging.info(f"   Primary URL file: data/urls.csv")
    logging.info(f"   Unique boxers: {unique_count:,}")
    logging.info(f"   Duplicates removed: {duplicates:,}")
    logging.info(f"   Files cleaned up: {removed_files}")
    logging.info(f"   Directories cleaned up: {removed_dirs}")
    logging.info(f"   With existing slugs: {stats['with_existing_slugs']:,}")
    logging.info(f"   New boxers: {stats['new_boxers']:,}")
    
    logging.info(f"\n🚀 Ready for scraping with data/urls.csv!")

if __name__ == "__main__":
    main()