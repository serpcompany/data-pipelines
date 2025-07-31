#!/usr/bin/env python3
"""
Simple raw SQL extraction using subprocess to run mysql command directly.
"""

import subprocess
import csv
import json
import logging
from pathlib import Path
from datetime import datetime
import re

logging.basicConfig(level=logging.INFO)

def run_mysql_query():
    """Run the MySQL query using command line mysql client."""
    
    # Database connection details
    host = "38.99.106.18"
    port = "3306"
    username = "root" 
    password = "shSS46hx325EF"
    database = "serp_app_db"
    
    # SQL query (simplified - only essential columns)
    query = """
    SELECT 
        boxer_name,
        boxrec_url,
        boxer_slug,
        id
    FROM boxing_boxers 
    WHERE boxrec_url IS NOT NULL 
    ORDER BY boxer_name;
    """
    
    # Build mysql command
    cmd = [
        'mysql',
        f'-h{host}',
        f'-P{port}',
        f'-u{username}',
        f'-p{password}',
        f'-D{database}',
        '-e', query,
        '--batch',
        '--raw'
    ]
    
    logging.info("Running MySQL query...")
    
    try:
        # Run the command
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        # Parse the tab-separated output
        lines = result.stdout.strip().split('\n')
        if not lines:
            logging.error("No output from MySQL query")
            return []
        
        # First line is headers
        headers = lines[0].split('\t')
        logging.info(f"Headers: {headers}")
        
        # Parse data rows
        boxers = []
        for line in lines[1:]:
            if line.strip():
                values = line.split('\t')
                boxer = dict(zip(headers, values))
                boxers.append(boxer)
        
        logging.info(f"Extracted {len(boxers)} boxers")
        return boxers
        
    except subprocess.CalledProcessError as e:
        logging.error(f"MySQL command failed: {e}")
        logging.error(f"Error output: {e.stderr}")
        return []
    except Exception as e:
        logging.error(f"Error running query: {e}")
        return []

def extract_boxrec_ids(boxers):
    """Extract BoxRec IDs from URLs."""
    failed_extractions = 0
    for boxer in boxers:
        url = boxer.get('boxrec_url', '')
        if url:
            # Extract ID from various BoxRec URL formats
            match = re.search(r'(?:box-pro|proboxer)[/_](\d+)', url)
            if match:
                boxer['boxrec_id'] = match.group(1)
            else:
                boxer['boxrec_id'] = None
                failed_extractions += 1
                if failed_extractions <= 5:  # Only show first 5 failures
                    logging.warning(f"Could not extract BoxRec ID from: {url}")
        else:
            boxer['boxrec_id'] = None
    
    if failed_extractions > 5:
        logging.warning(f"...and {failed_extractions - 5} more URL extraction failures")
    
    return boxers

def save_to_files(boxers):
    """Save data to CSV and JSON files."""
    data_dir = Path('data')
    data_dir.mkdir(exist_ok=True)
    
    # Save to CSV
    csv_file = data_dir / 'existing_boxers.csv'
    if boxers:
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=boxers[0].keys())
            writer.writeheader()
            writer.writerows(boxers)
        logging.info(f"Saved to CSV: {csv_file}")
    
    # Save to JSON
    json_file = data_dir / 'existing_boxers.json'
    data = {
        'extracted_at': datetime.now().isoformat(),
        'total_boxers': len(boxers),
        'boxers': boxers
    }
    
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, default=str)
    logging.info(f"Saved to JSON: {json_file}")
    
    # Create URL mapping
    mapping = {}
    urls_for_scraping = []
    
    for boxer in boxers:
        url = boxer.get('boxrec_url')
        slug = boxer.get('boxer_slug')
        boxrec_id = boxer.get('boxrec_id')
        
        if url and slug:
            mapping[url] = {
                'slug': slug,
                'boxer_name': boxer.get('boxer_name'),
                'boxrec_id': boxrec_id,
                'db_id': boxer.get('id')
            }
            
            # Add to scraping list if we have a valid BoxRec ID
            if boxrec_id:
                urls_for_scraping.append(url)
    
    # Save mapping
    mapping_file = data_dir / 'boxrec_url_slug_mapping.json'
    with open(mapping_file, 'w') as f:
        json.dump(mapping, f, indent=2)
    
    # Save URLs for scraping
    urls_file = data_dir / 'existing_boxers_urls.csv'
    with open(urls_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['url'])
        for url in urls_for_scraping:
            writer.writerow([url])
    
    logging.info(f"URL mapping saved: {mapping_file}")
    logging.info(f"URLs for scraping saved: {urls_file}")
    logging.info(f"Ready to scrape: {len(urls_for_scraping)} URLs")
    
    return len(urls_for_scraping)

def main():
    """Extract boxer data using raw SQL."""
    logging.info("🔍 Extracting boxer data from database...")
    
    # Run query
    boxers = run_mysql_query()
    
    if not boxers:
        logging.error("No data extracted")
        return
    
    # Extract BoxRec IDs
    logging.info("🔗 Extracting BoxRec IDs from URLs...")
    boxers = extract_boxrec_ids(boxers)
    
    # Analyze data
    total = len(boxers)
    with_boxrec_id = sum(1 for b in boxers if b.get('boxrec_id'))
    unique_boxrec_ids = len(set(b['boxrec_id'] for b in boxers if b.get('boxrec_id')))
    
    logging.info(f"\n📊 Data Analysis:")
    logging.info(f"  Total boxers: {total}")
    logging.info(f"  With BoxRec URLs: {total}")
    logging.info(f"  With extractable BoxRec IDs: {with_boxrec_id}")
    logging.info(f"  Unique BoxRec IDs: {unique_boxrec_ids}")
    
    # Save files
    logging.info("\n💾 Saving data...")
    scrape_count = save_to_files(boxers)
    
    # Show sample
    logging.info(f"\n📝 Sample entries:")
    for i, boxer in enumerate(boxers[:5]):
        logging.info(f"  {i+1}. {boxer['boxer_name']}")
        logging.info(f"     Slug: {boxer['boxer_slug']}")
        logging.info(f"     BoxRec: {boxer['boxrec_url']}")
        logging.info(f"     ID: {boxer['boxrec_id']}")
    
    logging.info(f"\n✅ Extraction Complete!")
    logging.info(f"  Ready to scrape: {scrape_count} URLs")

if __name__ == "__main__":
    main()