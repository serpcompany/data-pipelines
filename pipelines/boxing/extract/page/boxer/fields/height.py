#!/usr/bin/env python3
"""Extract height from HTML."""

import re
from ....base import load_html, test_extraction

def extract_height(soup):
    """Extract height in cm from HTML."""
    
    # Method 1: Look for height in table rows
    rows = soup.find_all('tr')
    for row in rows:
        cells = row.find_all(['td', 'th'])
        if len(cells) >= 2:
            label = cells[0].get_text().strip().lower()
            if label == 'height':
                value = cells[1].get_text().strip()
                # Extract cm value
                cm_match = re.search(r'(\d+)\s*cm', value)
                if cm_match:
                    return cm_match.group(1)
                # If no cm, try to extract feet/inches and convert
                ft_in_match = re.search(r'(\d+)[′\']?\s*(\d+)[″"]?', value)
                if ft_in_match:
                    feet = int(ft_in_match.group(1))
                    inches = int(ft_in_match.group(2))
                    cm = int((feet * 12 + inches) * 2.54)
                    return str(cm)
    
    return None

if __name__ == "__main__":
    test_extraction(extract_height)