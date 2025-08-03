#!/usr/bin/env python3
"""Extract nationality from HTML."""

import re
from ....base import load_html, test_extraction

def extract(soup):
    """Extract nationality from HTML."""
    
    # Method 1: Look for nationality in table rows
    rows = soup.find_all('tr')
    for row in rows:
        cells = row.find_all(['td', 'th'])
        if len(cells) >= 2:
            label = cells[0].get_text().strip().lower()
            if 'nationality' in label:
                value = cells[1].get_text().strip()
                # Remove flag icons or extra whitespace
                value = ' '.join(value.split())
                return value
    
    # Method 2: Look for flag icon with country name
    flag_elements = soup.find_all(class_=re.compile(r'flag-icon'))
    for flag in flag_elements:
        # Check if there's text next to the flag
        parent = flag.parent
        if parent:
            text = parent.get_text().strip()
            # Extract country name after flag
            if text:
                return text.split()[-1]  # Usually country is last word
    
    return None

if __name__ == "__main__":
    test_extraction(extract)