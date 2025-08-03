#!/usr/bin/env python3
"""Extract gym from HTML."""

from base_extractor import load_html, test_extraction

def extract_gym(soup):
    """Extract training gym from HTML."""
    
    # Method 1: Look for gym in table rows
    rows = soup.find_all('tr')
    for row in rows:
        cells = row.find_all(['td', 'th'])
        if len(cells) >= 2:
            label = cells[0].get_text().strip().lower()
            if 'gym' in label:
                value = cells[1].get_text().strip()
                return value if value else None
    
    return None

if __name__ == "__main__":
    test_extraction(extract_gym)