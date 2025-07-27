#!/usr/bin/env python3
"""Batch process all boxer HTML files to JSON."""

import os
import sys
import json
import logging
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from parse_boxer_final import parse_boxer_html

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('batch_parse.log'),
        logging.StreamHandler()
    ]
)

def process_file(html_file):
    """Process a single HTML file."""
    try:
        # Parse HTML
        data = parse_boxer_html(html_file)
        
        # Create output path
        output_file = str(html_file).replace('boxrec_html', 'boxrec_json').replace('.html', '.json')
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        # Save JSON
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        
        return {
            'file': str(html_file),
            'status': 'success',
            'name': data.get('name'),
            'id': data.get('boxrec_id')
        }
    except Exception as e:
        logging.error(f"Error processing {html_file}: {e}")
        return {
            'file': str(html_file),
            'status': 'error',
            'error': str(e)
        }

def main():
    # Find all boxer HTML files
    html_dir = Path('boxrec_html')
    html_files = list(html_dir.glob('*box-pro*.html'))
    
    if not html_files:
        print("No boxer HTML files found in boxrec_html/")
        return
    
    print(f"Found {len(html_files)} boxer HTML files to process")
    
    # Process files
    results = []
    successful = 0
    failed = 0
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        # Submit all tasks
        futures = {executor.submit(process_file, f): f for f in html_files}
        
        # Process results with progress bar
        with tqdm(total=len(html_files), desc="Processing boxers") as pbar:
            for future in as_completed(futures):
                result = future.result()
                results.append(result)
                
                if result['status'] == 'success':
                    successful += 1
                    pbar.set_postfix_str(f"Success: {result['name']}")
                else:
                    failed += 1
                    pbar.set_postfix_str(f"Failed: {result['file']}")
                
                pbar.update(1)
    
    # Save summary
    summary = {
        'total_files': len(html_files),
        'successful': successful,
        'failed': failed,
        'results': results
    }
    
    with open('boxrec_json/parse_summary.json', 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\nProcessing complete!")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Summary saved to: boxrec_json/parse_summary.json")

if __name__ == "__main__":
    main()