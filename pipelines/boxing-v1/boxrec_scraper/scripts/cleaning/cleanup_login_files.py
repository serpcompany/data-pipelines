#!/usr/bin/env python3
"""
Identify and clean up HTML files that contain login pages instead of boxer data.
Generates a list of URLs that need to be re-scraped.
"""
import os
import sys
import csv
import logging
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))
from utils.login_detector import find_login_pages, extract_original_url

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


def main():
    """Main function to identify and clean up login files."""
    # Paths
    html_dir = Path("boxrec_scraper/data/raw/boxrec_html")
    output_dir = Path("boxrec_scraper/data")
    failed_urls_file = output_dir / "login_blocked_urls.csv"
    
    if not html_dir.exists():
        logging.error(f"HTML directory not found: {html_dir}")
        return 1
    
    logging.info(f"Scanning for login pages in: {html_dir}")
    
    # Find all login pages
    login_files = find_login_pages(html_dir)
    logging.info(f"Found {len(login_files)} login page files")
    
    # Extract URLs and prepare for re-scraping
    failed_urls = []
    for file_path in login_files:
        url = extract_original_url(file_path)
        if url:
            failed_urls.append({
                'url': url,
                'filename': file_path.name,
                'file_path': str(file_path)
            })
            logging.info(f"Login page: {file_path.name} -> {url}")
        else:
            logging.warning(f"Could not extract URL from: {file_path.name}")
    
    # Save list of URLs to re-scrape
    if failed_urls:
        with open(failed_urls_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['url', 'filename', 'file_path'])
            writer.writeheader()
            writer.writerows(failed_urls)
        logging.info(f"Saved {len(failed_urls)} URLs to re-scrape: {failed_urls_file}")
    
    # Option to delete login files
    if failed_urls and '--delete' in sys.argv:
        logging.info("Deleting login page files...")
        deleted_count = 0
        for item in failed_urls:
            try:
                os.remove(item['file_path'])
                deleted_count += 1
            except Exception as e:
                logging.error(f"Failed to delete {item['file_path']}: {e}")
        logging.info(f"Deleted {deleted_count} login page files")
    else:
        logging.info("Run with --delete flag to remove login page files")
    
    # Summary
    logging.info("\n=== Summary ===")
    logging.info(f"Total HTML files scanned: {len(list(html_dir.glob('*.html')))}")
    logging.info(f"Login pages found: {len(login_files)}")
    logging.info(f"URLs to re-scrape: {len(failed_urls)}")
    
    if failed_urls:
        logging.info(f"\nTo re-scrape these URLs, run:")
        logging.info(f"python boxrec_scraper/scripts/scrape/scrape_boxers_html.py {failed_urls_file}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())