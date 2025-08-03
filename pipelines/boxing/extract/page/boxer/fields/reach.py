#!/usr/bin/env python3
"""Extract reach from HTML."""

import re
from ....base import load_html, test_extraction

def extract_reach(soup):
    """Extract reach in cm from HTML."""
    
    # Method 1: Look for reach in table rows
    rows = soup.find_all('tr')
    for row in rows:
        cells = row.find_all(['td', 'th'])
        if len(cells) >= 2:
            label = cells[0].get_text().strip().lower()
            if 'reach' in label:
                value = cells[1].get_text().strip()
                # Extract cm value
                cm_match = re.search(r'(\d+)\s*cm', value)
                if cm_match:
                    return cm_match.group(1)
                # If no cm, try to extract inches and convert
                in_match = re.search(r'(\d+)[″"]?', value)
                if in_match:
                    inches = int(in_match.group(1))
                    cm = int(inches * 2.54)
                    return str(cm)
    
    return None

if __name__ == "__main__":
    test_extraction(extract_reach)