#!/usr/bin/env python3
"""
Merge database slug data into the new CSV with 36k+ boxers.
Adds a 'slug' column with existing slug mappings where available.
"""

import csv
import json
import logging
import re
from pathlib import Path

logging.basicConfig(level=logging.INFO)

def load_slug_mappings():
    """Load the slug mappings from database extraction."""
    mapping_file = Path('data/boxrec_url_slug_mapping.json')
    
    if not mapping_file.exists():
        logging.error(f"Slug mapping file not found: {mapping_file}")
        return {}
    
    with open(mapping_file, 'r') as f:
        mappings = json.load(f)
    
    logging.info(f"Loaded {len(mappings)} slug mappings from database")
    return mappings

def convert_url_format(url):
    """Convert between /box-pro/ and /proboxer/ URL formats."""
    # Convert box-pro to proboxer format for matching
    if '/box-pro/' in url:
        return url.replace('/box-pro/', '/proboxer/')
    # Convert proboxer to box-pro format  
    elif '/proboxer/' in url:
        return url.replace('/proboxer/', '/box-pro/')
    return url

def extract_boxrec_id_from_url(url):
    """Extract BoxRec ID from URL."""
    match = re.search(r'(?:box-pro|proboxer)[/_](\d+)', url)
    return match.group(1) if match else None

def merge_slug_data():
    """Merge slug data into the new CSV file."""
    # Load existing slug mappings
    slug_mappings = load_slug_mappings()
    
    # Input and output files
    input_file = Path('data/boxrec-urls-to-scrape.csv')
    output_file = Path('data/boxrec-urls-to-scrape-with-slugs.csv')
    
    if not input_file.exists():
        logging.error(f"Input file not found: {input_file}")
        return
    
    # Track statistics
    stats = {
        'total_boxers': 0,
        'matched_slugs': 0,
        'no_slug_found': 0,
        'duplicate_ids': 0
    }
    
    seen_ids = set()
    
    # Process the CSV
    with open(input_file, 'r', encoding='utf-8') as infile, \
         open(output_file, 'w', newline='', encoding='utf-8') as outfile:
        
        reader = csv.DictReader(infile)
        
        # Add 'slug' and 'boxrec_id' columns to output
        fieldnames = list(reader.fieldnames) + ['boxrec_id', 'slug', 'db_matched']
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for row in reader:
            stats['total_boxers'] += 1
            
            url = row.get('url', '')
            name = row.get('name', '')
            
            # Extract BoxRec ID
            boxrec_id = extract_boxrec_id_from_url(url)
            row['boxrec_id'] = boxrec_id
            
            # Check for duplicates
            if boxrec_id in seen_ids:
                stats['duplicate_ids'] += 1
                logging.warning(f"Duplicate BoxRec ID found: {boxrec_id} ({name})")
            else:
                seen_ids.add(boxrec_id)
            
            # Try to find slug in mappings
            slug = None
            db_matched = False
            
            # First try exact URL match
            if url in slug_mappings:
                slug = slug_mappings[url]['slug']
                db_matched = True
                stats['matched_slugs'] += 1
            else:
                # Try converted URL format
                converted_url = convert_url_format(url)
                if converted_url in slug_mappings:
                    slug = slug_mappings[converted_url]['slug']
                    db_matched = True
                    stats['matched_slugs'] += 1
                else:
                    # Try matching by BoxRec ID
                    for mapped_url, data in slug_mappings.items():
                        if data.get('boxrec_id') == boxrec_id:
                            slug = data['slug']
                            db_matched = True
                            stats['matched_slugs'] += 1
                            break
            
            if not slug:
                stats['no_slug_found'] += 1
            
            # Add new columns
            row['slug'] = slug or ''
            row['db_matched'] = 'yes' if db_matched else 'no'
            
            writer.writerow(row)
    
    # Log statistics
    logging.info(f"\n📊 Merge Results:")
    logging.info(f"  Total boxers processed: {stats['total_boxers']:,}")
    logging.info(f"  Matched with database slugs: {stats['matched_slugs']:,}")
    logging.info(f"  No slug found: {stats['no_slug_found']:,}")
    logging.info(f"  Duplicate BoxRec IDs: {stats['duplicate_ids']}")
    logging.info(f"  Match rate: {stats['matched_slugs']/stats['total_boxers']*100:.1f}%")
    
    logging.info(f"\n💾 Output saved to: {output_file}")
    
    # Create summary report
    summary = {
        'input_file': str(input_file),
        'output_file': str(output_file),
        'statistics': stats,
        'match_rate_percent': round(stats['matched_slugs']/stats['total_boxers']*100, 1)
    }
    
    summary_file = Path('data/slug_merge_summary.json')
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    logging.info(f"📋 Summary saved to: {summary_file}")
    
    return stats

def analyze_unmatched_boxers():
    """Analyze boxers that didn't get slug matches."""
    output_file = Path('data/boxrec-urls-to-scrape-with-slugs.csv')
    
    if not output_file.exists():
        logging.error("Run merge_slug_data() first")
        return
    
    unmatched = []
    total = 0
    
    with open(output_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            total += 1
            if not row.get('slug'):
                unmatched.append({
                    'name': row.get('name'),
                    'url': row.get('url'),
                    'boxrec_id': row.get('boxrec_id')
                })
    
    logging.info(f"\n🔍 Unmatched Boxers Analysis:")
    logging.info(f"  Total unmatched: {len(unmatched):,}")
    logging.info(f"  Sample unmatched boxers:")
    
    for i, boxer in enumerate(unmatched[:10]):
        logging.info(f"    {i+1}. {boxer['name']} (ID: {boxer['boxrec_id']})")
    
    if len(unmatched) > 10:
        logging.info(f"    ... and {len(unmatched) - 10:,} more")
    
    # Save unmatched to file for analysis
    unmatched_file = Path('data/unmatched_boxers.json')
    with open(unmatched_file, 'w') as f:
        json.dump(unmatched, f, indent=2)
    
    logging.info(f"\n💾 Full unmatched list saved to: {unmatched_file}")

def main():
    """Main function to merge slug data."""
    logging.info("🔗 Merging database slug data into new boxer CSV...")
    
    stats = merge_slug_data()
    
    if stats:
        logging.info("\n🔍 Analyzing unmatched boxers...")
        analyze_unmatched_boxers()
        
        logging.info(f"\n✅ Merge complete!")
        logging.info(f"  New file: data/boxrec-urls-to-scrape-with-slugs.csv")
        logging.info(f"  {stats['matched_slugs']:,}/{stats['total_boxers']:,} boxers matched with existing slugs")
        logging.info(f"  {stats['no_slug_found']:,} new boxers without existing slugs")

if __name__ == "__main__":
    main()