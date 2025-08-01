#!/usr/bin/env python3
import os
import json
from pathlib import Path

# Delete JSON files with login error
json_dir = Path("boxrec_scraper/data/raw/boxrec_json")
json_deleted = 0

print("Deleting JSON files with login error...")
for json_file in json_dir.glob("en_box-pro_*.json"):
    try:
        with open(json_file, 'r') as f:
            data = json.load(f)
            if data.get('name') == 'Login' or 'login?error=limit' in data.get('boxrecUrl', ''):
                os.remove(json_file)
                json_deleted += 1
                
                # Also delete corresponding HTML file
                html_file = str(json_file).replace('boxrec_json', 'boxrec_html').replace('.json', '.html')
                if os.path.exists(html_file):
                    os.remove(html_file)
                    
    except Exception as e:
        print(f"Error processing {json_file}: {e}")

print(f"Deleted {json_deleted} JSON files and their corresponding HTML files")