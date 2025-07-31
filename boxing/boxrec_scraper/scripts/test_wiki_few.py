#!/usr/bin/env python3
"""Test wiki scraping with a few selected boxers."""

import json
from pathlib import Path
from scrape_wiki_zyte import fetch_wiki_page_zyte

# Test with a few well-known boxers
test_boxers = [
    ("352", "Floyd Mayweather Jr"),
    ("474", "Mike Tyson"),
    ("628407", "Naoya Inoue"),
    ("348759", "Canelo Alvarez"),
    ("000180", "Muhammad Ali")
]

# Create test output directory
output_dir = Path('data/raw/boxrec_wiki_test')
output_dir.mkdir(parents=True, exist_ok=True)

print("Testing wiki scraper with selected boxers")
print("=" * 60)

results = []

for boxrec_id, name in test_boxers:
    print(f"\nTesting {name} (ID: {boxrec_id})...")
    
    try:
        success, boxer_id, result = fetch_wiki_page_zyte(boxrec_id, output_dir)
        
        results.append({
            'boxrec_id': boxrec_id,
            'name': name,
            'success': success,
            'result': result
        })
        
        if success:
            if result == "already_exists":
                print(f"  ✅ Already downloaded")
            else:
                print(f"  ✅ Success! Final URL: {result}")
                # Check if file was created
                file_path = output_dir / f"wiki_box-pro_{boxrec_id}.html"
                if file_path.exists():
                    file_size = file_path.stat().st_size
                    print(f"  📄 File size: {file_size:,} bytes")
        else:
            print(f"  ❌ Failed: {result}")
            
    except Exception as e:
        print(f"  ❌ Error: {e}")
        results.append({
            'boxrec_id': boxrec_id,
            'name': name,
            'success': False,
            'result': str(e)
        })

# Summary
print("\n" + "=" * 60)
print("SUMMARY:")
successful = sum(1 for r in results if r['success'])
failed = len(results) - successful

print(f"  Total tested: {len(results)}")
print(f"  Successful: {successful}")
print(f"  Failed: {failed}")

# Save test results
summary_file = output_dir / 'test_results.json'
with open(summary_file, 'w') as f:
    json.dump({
        'test_count': len(results),
        'successful': successful,
        'failed': failed,
        'results': results
    }, f, indent=2)

print(f"\nResults saved to: {summary_file}")
print(f"HTML files saved to: {output_dir}/")

# Show what's in the directory
print(f"\nFiles in {output_dir}:")
for file in sorted(output_dir.glob('*.html')):
    print(f"  - {file.name} ({file.stat().st_size:,} bytes)")