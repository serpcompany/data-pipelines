#!/usr/bin/env python3
"""Process all boxer HTML files with v2 parser."""

import os
import json
import logging
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

from parse_boxer_v2 import parse_boxer_html

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def process_html_file(html_path):
    """Process a single HTML file."""
    try:
        data = parse_boxer_html(html_path)
        
        # Save to file
        output_file = str(html_path).replace('.html', '.json').replace('boxrec_html', 'boxrec_json_v2')
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        
        return True, html_path.name, data.get('full_name', 'Unknown')
    except Exception as e:
        logging.error(f"Error processing {html_path}: {e}")
        return False, html_path.name, str(e)

def main():
    # Find all boxer HTML files
    html_dir = Path('data/raw/boxrec_html')
    html_files = list(html_dir.glob('*box-pro*.html'))
    
    if not html_files:
        logging.error("No boxer HTML files found")
        return
    
    logging.info(f"Found {len(html_files)} boxer HTML files to process")
    
    # Process files concurrently
    successful = 0
    failed = 0
    
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(process_html_file, html_file): html_file 
                  for html_file in html_files}
        
        for future in as_completed(futures):
            success, filename, result = future.result()
            if success:
                successful += 1
                logging.info(f"✅ Processed {filename}: {result}")
            else:
                failed += 1
                logging.error(f"❌ Failed {filename}: {result}")
    
    # Summary
    logging.info(f"\nProcessing complete:")
    logging.info(f"  Successful: {successful}")
    logging.info(f"  Failed: {failed}")
    logging.info(f"  Total: {len(html_files)}")
    
    # Validate against schema
    logging.info("\nValidating output against v2.0.0 schema...")
    try:
        from jsonschema import validate
        
        with open('schema/v2.0.0.json', 'r') as f:
            schema = json.load(f)
        
        # Sample validation on first file
        json_files = list(Path('data/raw/boxrec_json_v2').glob('*.json'))
        if json_files:
            with open(json_files[0], 'r') as f:
                sample_data = json.load(f)
            
            validate(instance=sample_data, schema=schema)
            logging.info("✅ Schema validation passed!")
    except ImportError:
        logging.warning("jsonschema not available, skipping validation")
    except Exception as e:
        logging.error(f"Schema validation failed: {e}")

if __name__ == "__main__":
    main()