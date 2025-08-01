#!/usr/bin/env python3
"""
Find URLs from 5000boxers.csv that don't have corresponding HTML files
"""

import csv
import os
from pathlib import Path
from urllib.parse import urlparse

def extract_boxer_id_from_url(url):
    """Extract boxer ID from BoxRec URL"""
    # URL format: https://boxrec.com/en/box-pro/123456
    parts = url.strip().split('/')
    if len(parts) >= 3 and 'box-pro' in parts:
        return parts[-1]
    return None

def get_expected_filename(url):
    """Get expected HTML filename for a URL"""
    boxer_id = extract_boxer_id_from_url(url)
    if boxer_id:
        return f"en_box-pro_{boxer_id}.html"
    return None

def find_missing_html_files():
    """Find URLs that don't have corresponding HTML files"""
    
    # Paths
    csv_file = Path('boxrec_scraper/scripts/5000boxers.csv')
    html_dir = Path('boxrec_scraper/data/raw/boxrec_html')
    output_file = Path('missing_urls.csv')
    
    print(f"📄 Reading URLs from: {csv_file}")
    print(f"📁 Checking HTML files in: {html_dir}")
    
    # Get existing HTML files
    existing_files = set()
    if html_dir.exists():
        for html_file in html_dir.glob('*.html'):
            existing_files.add(html_file.name)
    
    print(f"📊 Found {len(existing_files)} existing HTML files")
    
    # Check which URLs are missing HTML files
    missing_urls = []
    total_urls = 0
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            total_urls += 1
            url = row['URL']
            expected_filename = get_expected_filename(url)
            
            if expected_filename and expected_filename not in existing_files:
                missing_urls.append({
                    'URL': url,
                    'expected_filename': expected_filename,
                    'boxer_id': extract_boxer_id_from_url(url)
                })
    
    print(f"📊 Total URLs: {total_urls}")
    print(f"❌ Missing HTML files: {len(missing_urls)}")
    
    # Save missing URLs to CSV
    if missing_urls:
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['URL']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for item in missing_urls:
                writer.writerow({'URL': item['URL']})
        
        print(f"💾 Saved {len(missing_urls)} missing URLs to: {output_file}")
        
        # Show first few
        print(f"\n🔍 Sample missing URLs:")
        for item in missing_urls[:5]:
            print(f"   {item['URL']} -> {item['expected_filename']}")
        if len(missing_urls) > 5:
            print(f"   ... and {len(missing_urls) - 5} more")
            
        return str(output_file)
    else:
        print("✅ All URLs have corresponding HTML files!")
        return None

if __name__ == "__main__":
    missing_csv = find_missing_html_files()
    if missing_csv:
        print(f"\n🚀 To re-scrape the missing URLs, run:")
        print(f"   python boxrec_scraper/scripts/scrape_raw_html/scrape_boxers_html.py {missing_csv} --workers 10")
