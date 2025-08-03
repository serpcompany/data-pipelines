#!/usr/bin/env python3
"""
Generate amateur boxer URLs from professional boxer URLs.
Converts /box-pro/ URLs to /box-am/ URLs for scraping amateur data.
"""

import csv
import sys
from pathlib import Path

def convert_to_amateur_url(pro_url: str) -> str:
    """Convert a professional BoxRec URL to amateur URL."""
    return pro_url.replace('/box-pro/', '/box-am/')

def main():
    """Generate amateur URLs from a CSV of professional URLs."""
    if len(sys.argv) < 2:
        print("Usage: python generate_amateur_urls.py <input_csv> [output_csv]")
        print("Example: python generate_amateur_urls.py test_boxers.csv test_boxers_amateur.csv")
        sys.exit(1)
    
    input_file = Path(sys.argv[1])
    output_file = Path(sys.argv[2]) if len(sys.argv) > 2 else input_file.with_stem(f"{input_file.stem}_amateur")
    
    if not input_file.exists():
        print(f"Error: Input file {input_file} not found")
        sys.exit(1)
    
    # Read professional URLs
    pro_urls = []
    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            url = row.get('url') or row.get('URL')
            if url and 'box-pro' in url:
                pro_urls.append(url)
    
    print(f"Found {len(pro_urls)} professional boxer URLs")
    
    # Generate amateur URLs
    amateur_urls = []
    for pro_url in pro_urls:
        amateur_url = convert_to_amateur_url(pro_url)
        amateur_urls.append({'url': amateur_url})
    
    # Write amateur URLs
    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['url'])
        writer.writeheader()
        writer.writerows(amateur_urls)
    
    print(f"Generated {len(amateur_urls)} amateur URLs")
    print(f"Output saved to: {output_file}")

if __name__ == "__main__":
    main()