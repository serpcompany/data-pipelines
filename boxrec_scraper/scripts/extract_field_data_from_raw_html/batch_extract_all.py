#!/usr/bin/env python3
"""Batch extract all boxer HTML files to JSON using individual extractors."""

import os
import sys
import json
import logging
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
import time
from extract_all_to_json import extract_all_fields

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def process_single_file(html_file):
    """Process a single HTML file."""
    try:
        # Extract all fields
        data = extract_all_fields(html_file)
        
        # Create output filename
        output_file = str(html_file).replace('.html', '.json').replace('boxrec_html', 'boxrec_json')
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        # Save to JSON
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        return True, str(html_file), None
        
    except Exception as e:
        return False, str(html_file), str(e)

def main():
    # Find all HTML files
    html_dir = Path("boxrec_scraper/data/raw/boxrec_html")
    html_files = list(html_dir.glob("en_box-pro_*.html"))
    
    # Limit for testing
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else None
    if limit:
        html_files = html_files[:limit]
    
    logging.info(f"Found {len(html_files)} HTML files to process")
    
    # Track progress
    successful = 0
    failed = 0
    start_time = time.time()
    
    # Process files in parallel
    with ProcessPoolExecutor(max_workers=8) as executor:
        # Submit all tasks
        future_to_file = {executor.submit(process_single_file, f): f for f in html_files}
        
        # Process completed tasks
        for i, future in enumerate(as_completed(future_to_file), 1):
            success, file_path, error = future.result()
            
            if success:
                successful += 1
            else:
                failed += 1
                logging.error(f"Failed to parse {file_path}: {error}")
            
            # Log progress every 100 files
            if i % 100 == 0:
                elapsed = time.time() - start_time
                rate = i / elapsed
                eta = (len(html_files) - i) / rate if rate > 0 else 0
                
                logging.info(f"Progress: {i}/{len(html_files)} files processed "
                           f"({successful} successful, {failed} failed) "
                           f"Rate: {rate:.1f} files/sec, ETA: {eta/60:.1f} minutes")
    
    # Final summary
    total_time = time.time() - start_time
    logging.info(f"\nProcessing complete!")
    logging.info(f"Total files: {len(html_files)}")
    logging.info(f"Successful: {successful}")
    logging.info(f"Failed: {failed}")
    logging.info(f"Total time: {total_time/60:.1f} minutes")
    logging.info(f"Average rate: {len(html_files)/total_time:.1f} files/sec")

if __name__ == "__main__":
    main()