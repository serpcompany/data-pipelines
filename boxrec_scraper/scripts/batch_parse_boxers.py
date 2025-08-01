#!/usr/bin/env python3
import os
import sys
import subprocess
import logging
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
import time

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def parse_single_file(html_file):
    """Parse a single HTML file."""
    try:
        # Run the parser script
        result = subprocess.run(
            ['python', 'boxrec_scraper/scripts/parse_boxer.py', html_file],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            return True, html_file, None
        else:
            return False, html_file, result.stderr
            
    except subprocess.TimeoutExpired:
        return False, html_file, "Timeout"
    except Exception as e:
        return False, html_file, str(e)

def main():
    # Find all HTML files
    html_dir = Path("boxrec_scraper/data/raw/boxrec_html")
    html_files = list(html_dir.glob("en_box-pro_*.html"))
    
    # Limit to 5000 files
    html_files = html_files[:1000]
    
    logging.info(f"Found {len(html_files)} HTML files to process")
    
    # Track progress
    successful = 0
    failed = 0
    start_time = time.time()
    
    # Process files in parallel
    with ProcessPoolExecutor(max_workers=8) as executor:
        # Submit all tasks
        future_to_file = {executor.submit(parse_single_file, str(f)): f for f in html_files}
        
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