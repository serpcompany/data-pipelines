#!/usr/bin/env python3
"""Extract residence from HTML."""

from ....base import load_html, test_extraction

def extract_residence(soup):
    """Extract current residence from HTML."""
    
    # Method 1: Look for residence in table rows
    rows = soup.find_all('tr')
    for row in rows:
        cells = row.find_all(['td', 'th'])
        if len(cells) >= 2:
            label = cells[0].get_text().strip().lower()
            if 'residence' in label:
                value = cells[1].get_text().strip()
                # Clean up flag icons and extra spaces
                value = ' '.join(value.split())
                return value
    
    return None

if __name__ == "__main__":
    test_extraction(extract_residence)