#!/usr/bin/env python3
"""
Extract bout/event URLs from BoxRec boxer HTML files
"""

import os
import re
import csv
from pathlib import Path
from bs4 import BeautifulSoup
import argparse
from collections import defaultdict

def extract_bout_urls_from_html(html_content):
    """Extract all bout/event URLs from boxer HTML"""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    bout_urls = set()
    
    # Find all links to events/bouts
    # Events are typically linked in the fight history table
    event_links = soup.find_all('a', href=re.compile(r'/[a-z]{2}/event/\d+'))
    
    for link in event_links:
        href = link.get('href')
        if href:
            # Convert to full URL
            full_url = f"https://boxrec.com{href}"
            bout_urls.add(full_url)
    
    return bout_urls

def extract_event_id_from_url(url):
    """Extract event_id from URL"""
    match = re.search(r'/event/(\d+)', url)
    return match.group(1) if match else None

def load_existing_urls(csv_file):
    """Load existing bout URLs and their IDs from CSV"""
    existing_urls = set()
    existing_ids = set()
    
    if os.path.exists(csv_file):
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                url = row.get('url', '')
                event_id = row.get('event_id', '')
                
                existing_urls.add(url)
                if event_id:
                    existing_ids.add(event_id)
    
    return existing_urls, existing_ids

def process_html_files(html_dir, bout_csv_file):
    """Process all HTML files and extract bout URLs"""
    
    print(f"🔍 Processing HTML files in {html_dir}")
    print(f"📋 Will save bout URLs to {bout_csv_file}")
    
    # Load existing URLs if file exists
    existing_urls, existing_ids = load_existing_urls(bout_csv_file)
    print(f"📊 Found {len(existing_urls)} existing bout URLs")
    
    # Track statistics
    stats = {
        'files_processed': 0,
        'total_bouts_found': 0,
        'unique_bouts': set(),
        'new_bouts': [],
        'boxers_with_bouts': 0,
        'language_stats': defaultdict(int)
    }
    
    # Process all HTML files
    html_path = Path(html_dir)
    for html_file in html_path.glob('*.html'):
        if html_file.is_file():
            stats['files_processed'] += 1
            
            # Read and parse HTML
            with open(html_file, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # Extract bout URLs
            bout_urls = extract_bout_urls_from_html(html_content)
            
            if bout_urls:
                stats['boxers_with_bouts'] += 1
                stats['total_bouts_found'] += len(bout_urls)
                stats['unique_bouts'].update(bout_urls)
                
                # Track language from URL
                for url in bout_urls:
                    lang_match = re.search(r'/([a-z]{2})/event/', url)
                    if lang_match:
                        stats['language_stats'][lang_match.group(1)] += 1
            
            if stats['files_processed'] % 1000 == 0:
                print(f"   Processed {stats['files_processed']} files...")
    
    print(f"✅ Processed {stats['files_processed']} HTML files")
    print(f"🥊 Found {stats['total_bouts_found']} total bout references")
    print(f"🔢 Found {len(stats['unique_bouts'])} unique bout URLs")
    print(f"👥 {stats['boxers_with_bouts']} boxers have bout history")
    
    # Show language breakdown
    print("\n📊 Language breakdown of bouts:")
    for lang, count in sorted(stats['language_stats'].items(), key=lambda x: x[1], reverse=True):
        print(f"   {lang}: {count:,} bouts")
    
    # Check which URLs are new
    for url in stats['unique_bouts']:
        event_id = extract_event_id_from_url(url)
        
        if event_id and event_id not in existing_ids and url not in existing_urls:
            # Extract language from URL
            lang_match = re.search(r'/([a-z]{2})/event/', url)
            language = lang_match.group(1) if lang_match else 'en'
            
            stats['new_bouts'].append({
                'event_id': event_id,
                'url': url,
                'language': language,
                'type': 'bout'
            })
    
    print(f"\n🆕 Found {len(stats['new_bouts'])} new bout URLs to add")
    
    return stats['new_bouts'], stats

def save_bout_urls_to_csv(csv_file, new_bouts):
    """Save new bout URLs to CSV file"""
    
    if not new_bouts:
        print("ℹ️  No new bout URLs to save")
        return
    
    # Check if file exists
    file_exists = os.path.exists(csv_file)
    
    # Sort bouts by event_id
    new_bouts.sort(key=lambda x: int(x['event_id']))
    
    with open(csv_file, 'w' if not file_exists else 'a', newline='', encoding='utf-8') as f:
        fieldnames = ['event_id', 'url', 'language', 'type']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        
        # Write header if file is new
        if not file_exists:
            writer.writeheader()
        
        # Write new bouts
        for bout in new_bouts:
            writer.writerow(bout)
    
    print(f"✅ Saved {len(new_bouts)} bout URLs to {csv_file}")

def main():
    parser = argparse.ArgumentParser(description='Extract bout URLs from BoxRec boxer HTML files')
    parser.add_argument('--html-dir', default='data/raw/boxrec_html', 
                       help='Directory containing boxer HTML files')
    parser.add_argument('--output', default='data/bout_urls.csv',
                       help='Output CSV file for bout URLs')
    parser.add_argument('--dry-run', action='store_true',
                       help='Only show statistics, do not save URLs')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.html_dir):
        print(f"❌ HTML directory not found: {args.html_dir}")
        return
    
    # Extract bout URLs
    new_bouts, stats = process_html_files(args.html_dir, args.output)
    
    if args.dry_run:
        print("\n🔍 DRY RUN - Would save these bout URLs:")
        print(f"   Total unique bouts found: {len(stats['unique_bouts']):,}")
        print(f"   New bouts to add: {len(new_bouts):,}")
        
        # Show sample
        print("\n   Sample bout URLs:")
        for bout in new_bouts[:10]:
            print(f"   {bout['url']} (ID: {bout['event_id']}, Lang: {bout['language']})")
        if len(new_bouts) > 10:
            print(f"   ... and {len(new_bouts) - 10:,} more")
    else:
        # Save bout URLs to CSV
        save_bout_urls_to_csv(args.output, new_bouts)
        
        # Show final statistics
        if os.path.exists(args.output):
            with open(args.output, 'r') as f:
                total_bouts = sum(1 for _ in csv.DictReader(f))
            print(f"\n📊 Total bout URLs in {args.output}: {total_bouts:,}")

if __name__ == "__main__":
    main()