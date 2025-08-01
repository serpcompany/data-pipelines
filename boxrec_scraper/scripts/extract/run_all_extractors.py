#!/usr/bin/env python3
"""
Run all field extractors on HTML files and combine results.
"""

import os
import sys
import json
import glob
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
import logging
from datetime import datetime

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))
from utils.login_detector import is_login_page_file

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# List all extractors to run
EXTRACTORS = [
    # IDs and URLs
    'extract_id',
    'extract_boxrec_id', 
    'extract_boxrec_url',
    'extract_boxrec_wiki_url',
    'extract_slug',
    
    # Basic info
    'extract_name',
    'extract_birth_name',
    'extract_nicknames',
    'extract_avatar_image',
    
    # Personal details
    'extract_residence',
    'extract_birth_place',
    'extract_birth_date',
    'extract_gender',
    'extract_nationality',
    
    # Physical attributes
    'extract_height',
    'extract_reach',
    'extract_stance',
    
    # Bio and team
    'extract_bio',
    'extract_promoters',
    'extract_trainers',
    'extract_managers',
    'extract_gym',
    
    # Professional record
    'extract_pro_debut_date',
    'extract_pro_division',
    'extract_pro_wins',
    'extract_pro_wins_by_knockout',
    'extract_pro_losses',
    'extract_pro_losses_by_knockout',
    'extract_pro_draws',
    'extract_pro_status',
    'extract_pro_total_bouts',
    'extract_pro_total_rounds',
    
    # Amateur record
    'extract_amateur_debut_date',
    'extract_amateur_division',
    'extract_amateur_wins',
    'extract_amateur_wins_by_knockout',
    'extract_amateur_losses',
    'extract_amateur_losses_by_knockout',
    'extract_amateur_draws',
    'extract_amateur_status',
    'extract_amateur_total_bouts',
    'extract_amateur_total_rounds',
    
    # Bouts
    'extract_bouts'
]

def run_single_extractor(extractor_name, soup):
    """Run a single extractor on a BeautifulSoup object."""
    try:
        # Import the extractor module dynamically
        module = __import__(extractor_name)
        # Get the extraction function (same name as module)
        extract_func = getattr(module, extractor_name)
        # Run the extraction
        return extract_func(soup)
    except Exception as e:
        logging.error(f"Error running {extractor_name}: {e}")
        return None

def extract_all_fields(html_path):
    """Extract all fields from a single HTML file."""
    try:
        # Check if it's a login page first
        if is_login_page_file(html_path):
            logging.warning(f"Skipping login page: {html_path}")
            return None
        
        # Load HTML once
        from base_extractor import load_html
        soup = load_html(html_path)
        
        # Initialize results with filename
        results = {
            'source_file': str(html_path),
            'extracted_at': datetime.utcnow().isoformat()
        }
        
        # Run each extractor
        for extractor_name in EXTRACTORS:
            try:
                # Import and run extractor
                module = __import__(extractor_name)
                extract_func = getattr(module, extractor_name)
                
                # Get field name from extractor name (remove 'extract_' prefix)
                field_name = extractor_name.replace('extract_', '')
                
                # Run extraction
                value = extract_func(soup)
                
                # Store result
                results[field_name] = value
                
            except Exception as e:
                logging.error(f"Error with {extractor_name} on {html_path}: {e}")
                results[field_name] = None
        
        return results
        
    except Exception as e:
        logging.error(f"Error processing {html_path}: {e}")
        return None

def process_html_file(html_path):
    """Process a single HTML file with all extractors."""
    filename = Path(html_path).name
    logging.info(f"Processing: {filename}")
    
    results = extract_all_fields(html_path)
    
    if results:
        # Save individual JSON file
        output_dir = Path("data/processed/extracted_fields")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_file = output_dir / filename.replace('.html', '_extracted.json')
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)
        
        return True, html_path, results
    else:
        return False, html_path, None

def main():
    """Main function to run all extractors on all HTML files."""
    # Get HTML files
    html_dir = Path("data/raw/boxrec_html")
    if not html_dir.exists():
        logging.error(f"HTML directory not found: {html_dir}")
        return
    
    html_files = list(html_dir.glob("*.html"))
    logging.info(f"Found {len(html_files)} HTML files to process")
    
    # Output directory
    output_dir = Path("data/processed/extracted_fields")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Track progress
    successful = 0
    failed = 0
    login_pages = 0
    
    # Process files in parallel
    with ProcessPoolExecutor(max_workers=4) as executor:
        # Submit all tasks
        futures = {executor.submit(process_html_file, str(f)): f for f in html_files[:100]}  # Limit for testing
        
        # Process completed tasks
        for i, future in enumerate(as_completed(futures), 1):
            success, file_path, results = future.result()
            
            if success:
                successful += 1
            else:
                if results is None:
                    login_pages += 1
                else:
                    failed += 1
            
            # Progress update
            if i % 10 == 0:
                logging.info(f"Progress: {i}/{len(futures)} files processed "
                           f"({successful} successful, {failed} failed, {login_pages} login pages)")
    
    # Final summary
    logging.info(f"\nProcessing complete!")
    logging.info(f"Total files: {len(html_files)}")
    logging.info(f"Successful: {successful}")
    logging.info(f"Failed: {failed}")
    logging.info(f"Login pages: {login_pages}")
    
    # Combine all results into one file
    logging.info("\nCombining all results...")
    all_results = []
    
    for json_file in output_dir.glob("*_extracted.json"):
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            all_results.append(data)
    
    # Save combined results
    combined_file = Path("data/processed/all_boxers_extracted.json")
    with open(combined_file, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2)
    
    logging.info(f"Combined results saved to: {combined_file}")
    logging.info(f"Total records: {len(all_results)}")

if __name__ == "__main__":
    main()