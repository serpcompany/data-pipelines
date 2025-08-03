#!/usr/bin/env python3
"""Extract birth name from HTML."""

from ....base import load_html, test_extraction

def extract_birth_name(soup):
    """Extract birth name from HTML."""
    
    # Method 1: Look for birth name in table rows
    rows = soup.find_all('tr')
    for row in rows:
        cells = row.find_all(['td', 'th'])
        if len(cells) >= 2:
            label = cells[0].get_text().strip().lower()
            if 'birth name' in label:
                value = cells[1].get_text().strip()
                return value if value else None
    
    return None

if __name__ == "__main__":
    test_extraction(extract_birth_name)