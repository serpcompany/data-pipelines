#!/usr/bin/env python3
"""
Simple scraper runner using config.py for proper imports.
"""
import sys
import os
from pathlib import Path

# Use config.py approach - add parent directories to path
current_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(current_dir.parent.parent))  # Add data-pipelines to path

# Now use the config to handle the rest
try:
    from pipelines.boxing.utils.config import INPUT_DIR, PENDING_HTML_DIR
    from pipelines.boxing.scrapers.boxrec.boxer import load_urls_from_csv, scrape_urls
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you're running from the correct directory")
    sys.exit(1)

def main():
    csv_file = INPUT_DIR / 'boxers_test.csv'
    
    print(f"Loading URLs from: {csv_file}")
    urls = load_urls_from_csv(csv_file)
    
    if not urls:
        print("No URLs found in CSV file")
        return False
    
    print(f"Found {len(urls)} URLs:")
    for i, url in enumerate(urls, 1):
        print(f"  {i}. {url}")
    
    print(f"\nScraping HTML files...")
    print(f"Output directory: {PENDING_HTML_DIR}")
    
    results = scrape_urls(urls, max_workers=1, rate_limit=0.5, max_age_days=None)
    
    print(f"\nScraping completed!")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)