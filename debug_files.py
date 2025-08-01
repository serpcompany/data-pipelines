#!/usr/bin/env python3
"""
Debug the file existence checking issue
"""

import csv
from pathlib import Path
from urllib.parse import urlparse

def create_filename_from_url(url: str) -> str:
    """Create a safe filename from a BoxRec URL - copied from scraper"""
    parsed = urlparse(url)
    path_parts = parsed.path.strip('/').split('/')
    
    # Handle different URL formats
    if 'box-pro' in url:
        # Extract language and ID: /en/box-pro/123456
        if len(path_parts) >= 3:
            lang = path_parts[0] if path_parts[0] in ['en', 'es', 'fr', 'de', 'ru'] else 'en'
            boxer_id = path_parts[-1]
            return f"{lang}_box-pro_{boxer_id}.html"
    
    # Fallback
    return "unknown.html"

def debug_file_check():
    """Debug why the scraper thinks files exist when they don't"""
    
    csv_file = Path('missing_urls.csv')
    html_dir = Path('boxrec_scraper/data/raw/boxrec_html')
    
    print(f"🔍 Debugging file existence checks...")
    print(f"CSV file: {csv_file}")
    print(f"HTML dir: {html_dir}")
    
    # Load first 10 URLs from missing_urls.csv
    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)
        urls = [row['URL'] for i, row in enumerate(reader) if i < 10]
    
    print(f"\n📋 Checking first 10 URLs:")
    
    for url in urls:
        filename = create_filename_from_url(url)
        file_path = html_dir / filename
        exists = file_path.exists()
        
        print(f"URL: {url}")
        print(f"  Expected filename: {filename}")
        print(f"  Full path: {file_path}")
        print(f"  File exists: {exists}")
        if exists:
            size = file_path.stat().st_size
            print(f"  File size: {size} bytes")
        print()

if __name__ == "__main__":
    debug_file_check()
