#!/usr/bin/env python3
"""Extract birth place from HTML."""

from base_extractor import load_html, test_extraction

def extract_birth_place(soup):
    """Extract birth place from HTML."""
    
    # Method 1: Look for birth place in table rows
    rows = soup.find_all('tr')
    for row in rows:
        cells = row.find_all(['td', 'th'])
        if len(cells) >= 2:
            label = cells[0].get_text().strip().lower()
            if 'birth place' in label or 'birthplace' in label:
                value = cells[1].get_text().strip()
                # Clean up flag icons and extra spaces
                value = ' '.join(value.split())
                return value
    
    return None

if __name__ == "__main__":
    test_extraction(extract_birth_place)