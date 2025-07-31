#!/usr/bin/env python3
"""Test wiki scraping with a few boxers."""

import json
from pathlib import Path
from scrape_wiki import fetch_wiki_page

# Test with a few known boxers
test_boxers = [
    ("352", "Floyd Mayweather Jr"),
    ("628407", "Naoya Inoue"),
    ("474", "Mike Tyson"),
    ("000180", "Muhammad Ali")
]

output_dir = Path('data/raw/boxrec_wiki_test')
output_dir.mkdir(parents=True, exist_ok=True)

print("Testing wiki scraper with sample boxers:")
print("=" * 50)

for boxrec_id, name in test_boxers:
    print(f"\nTesting {name} (ID: {boxrec_id})...")
    success, boxer_id, result = fetch_wiki_page(boxrec_id, output_dir)
    
    if success:
        print(f"✅ Success: {result}")
    else:
        print(f"❌ Failed: {result}")

print("\n" + "=" * 50)
print(f"Test files saved to: {output_dir}")