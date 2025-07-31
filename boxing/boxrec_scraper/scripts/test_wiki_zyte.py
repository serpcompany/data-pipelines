#!/usr/bin/env python3
"""Test wiki scraping with Zyte API for a single boxer."""

import os
import requests
from pathlib import Path
from base64 import b64decode
from dotenv import load_dotenv

# Load environment variables
env_path = Path('..') / '.env'
load_dotenv(dotenv_path=env_path)

# Configuration
ZYTE_API_KEY = os.getenv("ZYTE_API_KEY")
if not ZYTE_API_KEY:
    print("Error: ZYTE_API_KEY not found in environment")
    exit(1)

# Test with Floyd Mayweather
boxrec_id = "352"
wiki_url = f"https://boxrec.com/wiki/index.php?title=Human:{boxrec_id}"

print(f"Testing wiki URL with Zyte API")
print(f"BoxRec ID: {boxrec_id}")
print(f"Wiki URL: {wiki_url}")
print("-" * 50)

try:
    # Make request to Zyte API
    response = requests.post(
        "https://api.zyte.com/v1/extract",
        json={
            "url": wiki_url,
            "httpResponseBody": True,
            "httpResponseHeaders": True
        },
        auth=(ZYTE_API_KEY, ""),
        timeout=30
    )
    response.raise_for_status()
    
    # Parse response
    data = response.json()
    
    print(f"Status Code: {response.status_code}")
    print(f"Final URL: {data.get('url', 'N/A')}")
    print(f"Redirected: {data.get('url') != wiki_url}")
    
    # Check if it's a wiki page
    final_url = data.get('url', '')
    if '/wiki/index.php' in final_url:
        print("✅ Successfully found wiki page!")
        
        # Decode and check HTML
        html = b64decode(data["httpResponseBody"]).decode('utf-8')
        
        # Extract title
        import re
        title_match = re.search(r'<title>(.*?)</title>', html)
        if title_match:
            print(f"Page title: {title_match.group(1)}")
        
        # Check for some expected content
        if "Mayweather" in html:
            print("✅ Found Mayweather content in HTML")
        
        # Save test file
        test_dir = Path('data/raw/boxrec_wiki_test')
        test_dir.mkdir(parents=True, exist_ok=True)
        test_file = test_dir / f"wiki_test_{boxrec_id}.html"
        
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"\nTest file saved to: {test_file}")
        print(f"File size: {len(html):,} bytes")
        
    else:
        print(f"❌ Not a wiki page URL: {final_url}")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()