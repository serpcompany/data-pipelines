#!/usr/bin/env python3
"""
Extract opponent boxer URLs from BoxRec HTML fight tables and add new ones to urls.csv
"""

import os
import re
import csv
from pathlib import Path
from bs4 import BeautifulSoup
import argparse
from collections import defaultdict

def extract_opponent_urls_from_html(html_content):
    """Extract all opponent boxer URLs from HTML fight tables"""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Find all fight tables
    fight_tables = soup.find_all('table', class_='dataTable')
    
    opponent_urls = set()
    
    for table in fight_tables:
        # Find all opponent links in the table
        opponent_links = table.find_all('a', class_='personLink', href=True)
        
        for link in opponent_links:
            href = link.get('href')
            # Extract URLs that match the boxer pattern
            if href and re.match(r'/en/box-pro/\d+', href):
                # Convert to full URL
                full_url = f"https://boxrec.com{href}"
                opponent_urls.add(full_url)
    
    return opponent_urls

def extract_boxrec_id_from_url(url):
    """Extract boxrec_id from URL"""
    match = re.search(r'/(?:box-pro|proboxer)/(\d+)', url)
    return match.group(1) if match else None

def load_existing_urls(csv_file):
    """Load existing URLs and their boxrec_ids from CSV"""
    existing_urls = set()
    existing_ids = set()
    
    if os.path.exists(csv_file):
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                url = row.get('url', '')
                boxrec_id = row.get('boxrec_id', '')
                
                existing_urls.add(url)
                if boxrec_id:
                    existing_ids.add(boxrec_id)
    
    return existing_urls, existing_ids

def process_html_files(html_dir, csv_file):
    """Process all HTML files and extract opponent URLs"""
    
    print(f"🔍 Processing HTML files in {html_dir}")
    print(f"📋 Checking against existing URLs in {csv_file}")
    
    # Load existing URLs
    existing_urls, existing_ids = load_existing_urls(csv_file)
    print(f"📊 Found {len(existing_urls)} existing URLs")
    
    # Track statistics
    stats = {
        'files_processed': 0,
        'total_opponents_found': 0,
        'unique_opponents': set(),
        'new_opponents': []
    }
    
    # Process all HTML files
    html_path = Path(html_dir)
    for html_file in html_path.glob('*.html'):
        if html_file.is_file():
            stats['files_processed'] += 1
            
            # Read and parse HTML
            with open(html_file, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # Extract opponent URLs
            opponent_urls = extract_opponent_urls_from_html(html_content)
            stats['total_opponents_found'] += len(opponent_urls)
            stats['unique_opponents'].update(opponent_urls)
            
            if stats['files_processed'] % 1000 == 0:
                print(f"   Processed {stats['files_processed']} files...")
    
    print(f"✅ Processed {stats['files_processed']} HTML files")
    print(f"🥊 Found {stats['total_opponents_found']} total opponent references")
    print(f"🔢 Found {len(stats['unique_opponents'])} unique opponent URLs")
    
    # Check which URLs are new
    for url in stats['unique_opponents']:
        boxrec_id = extract_boxrec_id_from_url(url)
        
        if boxrec_id and boxrec_id not in existing_ids and url not in existing_urls:
            # Try to extract name from the last scraped HTML file that contained this opponent
            opponent_name = f"Boxer {boxrec_id}"  # Default name
            
            stats['new_opponents'].append({
                'name': opponent_name,
                'url': url,
                'boxrec_id': boxrec_id,
                'slug': '',  # Will be empty for new boxers
                'db_matched': 'no'
            })
    
    print(f"🆕 Found {len(stats['new_opponents'])} new opponent URLs to add")
    
    return stats['new_opponents']

def append_new_urls_to_csv(csv_file, new_opponents):
    """Append new opponent URLs to the CSV file"""
    
    if not new_opponents:
        print("ℹ️  No new URLs to add")
        return
    
    # Check if file exists and has headers
    file_exists = os.path.exists(csv_file)
    
    with open(csv_file, 'a', newline='', encoding='utf-8') as f:
        fieldnames = ['name', 'url', 'boxrec_id', 'slug', 'db_matched']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        
        # Write header if file is new
        if not file_exists:
            writer.writeheader()
        
        # Write new opponents
        for opponent in new_opponents:
            writer.writerow(opponent)
    
    print(f"✅ Added {len(new_opponents)} new opponent URLs to {csv_file}")

def main():
    parser = argparse.ArgumentParser(description='Extract opponent URLs from BoxRec HTML files')
    parser.add_argument('--html-dir', default='data/raw/boxrec_html', 
                       help='Directory containing HTML files')
    parser.add_argument('--csv-file', default='data/urls.csv',
                       help='CSV file to check and update with new URLs')
    parser.add_argument('--dry-run', action='store_true',
                       help='Only show what would be added, do not modify CSV')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.html_dir):
        print(f"❌ HTML directory not found: {args.html_dir}")
        return
    
    # Extract new opponent URLs
    new_opponents = process_html_files(args.html_dir, args.csv_file)
    
    if args.dry_run:
        print("\n🔍 DRY RUN - Would add these URLs:")
        # Save to a file for easy viewing
        dry_run_file = 'data/new_opponent_urls_dry_run.txt'
        with open(dry_run_file, 'w', encoding='utf-8') as f:
            for opponent in new_opponents:
                f.write(f"{opponent['url']} (ID: {opponent['boxrec_id']})\n")
        print(f"📄 Full list saved to: {dry_run_file}")
        
        # Show first 20 as sample
        for opponent in new_opponents[:20]:
            print(f"   {opponent['url']} (ID: {opponent['boxrec_id']})")
        if len(new_opponents) > 20:
            print(f"   ... and {len(new_opponents) - 20} more (see {dry_run_file} for full list)")
    else:
        # Add new URLs to CSV
        append_new_urls_to_csv(args.csv_file, new_opponents)
        
        # Show final statistics
        total_urls = len(load_existing_urls(args.csv_file)[0])
        print(f"📊 Total URLs in {args.csv_file}: {total_urls}")

if __name__ == "__main__":
    main()