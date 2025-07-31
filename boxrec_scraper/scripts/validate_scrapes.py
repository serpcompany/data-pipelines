#!/usr/bin/env python3
"""
Validate scraped HTML files to identify bad scrapes that need to be re-scraped
"""

import os
import csv
from pathlib import Path
import argparse
from collections import defaultdict

def check_html_file(html_file):
    """Check if an HTML file is a valid scrape or a bad scrape"""
    
    with open(html_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    issues = []
    
    # Test 1: Check for login page
    if 'BoxRec: Login' in content or '<title>BoxRec: Login</title>' in content:
        issues.append('LOGIN_PAGE')
    
    # Test 2: Check if file is too small (likely an error page)
    if len(content) < 1000:
        issues.append(f'TOO_SMALL_{len(content)}_bytes')
    
    # Test 3: Check for 404 or error pages
    if '404 Not Found' in content or 'Page Not Found' in content:
        issues.append('404_ERROR')
    
    # Test 4: Check for rate limit errors
    if 'rate limit' in content.lower() or 'too many requests' in content.lower():
        issues.append('RATE_LIMIT')
    
    # Test 5: Check for actual boxer content (should have fight table)
    if 'class="dataTable"' not in content and len(issues) == 0:
        issues.append('NO_FIGHT_TABLE')
    
    return issues

def validate_all_scrapes(html_dir, output_file='data/bad_scrapes.csv'):
    """Validate all HTML files and identify which need re-scraping"""
    
    print(f"🔍 Validating scraped HTML files in {html_dir}")
    
    html_path = Path(html_dir)
    bad_scrapes = []
    issue_counts = defaultdict(int)
    total_files = 0
    
    # Process all HTML files
    for html_file in html_path.glob('*.html'):
        if html_file.is_file():
            total_files += 1
            
            # Extract boxer ID from filename
            filename = html_file.name
            # Pattern: en_box-pro_123456.html
            parts = filename.replace('.html', '').split('_')
            if len(parts) >= 3:
                language = parts[0]
                boxer_id = parts[-1]
                
                # Check for issues
                issues = check_html_file(html_file)
                
                if issues:
                    bad_scrapes.append({
                        'filename': filename,
                        'boxer_id': boxer_id,
                        'language': language,
                        'issues': '|'.join(issues),
                        'url': f"https://boxrec.com/{language}/box-pro/{boxer_id}"
                    })
                    
                    for issue in issues:
                        issue_counts[issue] += 1
            
            if total_files % 1000 == 0:
                print(f"   Validated {total_files} files...")
    
    print(f"\n✅ Validated {total_files} HTML files")
    print(f"❌ Found {len(bad_scrapes)} bad scrapes")
    
    # Show issue breakdown
    if issue_counts:
        print("\n📊 Issue Breakdown:")
        for issue, count in sorted(issue_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"   {issue}: {count} files")
    
    # Save bad scrapes to CSV
    if bad_scrapes:
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['filename', 'boxer_id', 'language', 'issues', 'url']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(bad_scrapes)
        
        print(f"\n📄 Bad scrapes list saved to: {output_file}")
        
        # Show sample
        print("\n🔍 Sample bad scrapes:")
        for scrape in bad_scrapes[:5]:
            print(f"   {scrape['filename']} - Issues: {scrape['issues']}")
        if len(bad_scrapes) > 5:
            print(f"   ... and {len(bad_scrapes) - 5} more")
    
    return bad_scrapes

def create_rescrape_list(bad_scrapes_file, urls_csv, output_file='data/urls_to_rescrape.csv'):
    """Create a CSV of URLs that need to be re-scraped"""
    
    print(f"\n📝 Creating re-scrape list from {bad_scrapes_file}")
    
    # Load bad scrapes
    bad_boxer_ids = set()
    with open(bad_scrapes_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            bad_boxer_ids.add(row['boxer_id'])
    
    # Find matching entries in main URLs file
    rescrape_urls = []
    with open(urls_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get('boxrec_id') in bad_boxer_ids:
                rescrape_urls.append(row)
    
    # Save re-scrape list
    if rescrape_urls:
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['name', 'url', 'boxrec_id', 'slug', 'db_matched']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rescrape_urls)
        
        print(f"✅ Created re-scrape list with {len(rescrape_urls)} URLs")
        print(f"📄 Saved to: {output_file}")
    
    return rescrape_urls

def main():
    parser = argparse.ArgumentParser(description='Validate scraped BoxRec HTML files')
    parser.add_argument('--html-dir', default='data/raw/boxrec_html',
                       help='Directory containing HTML files')
    parser.add_argument('--urls-csv', default='data/urls.csv',
                       help='Main URLs CSV file')
    parser.add_argument('--create-rescrape', action='store_true',
                       help='Create a CSV of URLs that need re-scraping')
    
    args = parser.parse_args()
    
    # Validate all scrapes
    bad_scrapes = validate_all_scrapes(args.html_dir, output_file='data/bad_scrapes.csv')
    
    # Optionally create re-scrape list
    if args.create_rescrape and bad_scrapes:
        create_rescrape_list('data/bad_scrapes.csv', args.urls_csv, 'data/urls_to_rescrape.csv')
        print("\n💡 To re-scrape the bad URLs, run:")
        print("   python scripts/scrape_boxers.py data/urls_to_rescrape.csv --workers 25")

if __name__ == "__main__":
    main()