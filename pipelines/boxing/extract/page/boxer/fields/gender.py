#!/usr/bin/env python3
"""Extract gender from HTML."""

from ....base import load_html, test_extraction

def extract_gender(soup):
    """Extract gender from HTML."""
    
    # Method 1: Look for sex/gender in table rows
    rows = soup.find_all('tr')
    for row in rows:
        cells = row.find_all(['td', 'th'])
        if len(cells) >= 2:
            label = cells[0].get_text().strip().lower()
            if 'sex' in label or 'gender' in label:
                value = cells[1].get_text().strip().lower()
                if 'male' in value:
                    return 'M' if 'female' not in value else 'F'
                elif 'female' in value:
                    return 'F'
    
    # Method 2: Default to male if not specified (BoxRec historical bias)
    return 'M'

if __name__ == "__main__":
    test_extraction(extract_gender)