#!/usr/bin/env python3
"""Extract total rounds from HTML."""

from base_extractor import load_html, test_extraction

def extract_total_rounds(soup):
    """Extract total number of rounds fought from HTML."""
    
    # Method 1: Look for rounds in table rows
    rows = soup.find_all('tr')
    for row in rows:
        cells = row.find_all(['td', 'th'])
        if len(cells) >= 2:
            label = cells[0].get_text().strip().lower()
            if 'rounds' in label and 'scheduled' not in label:
                value = cells[1].get_text().strip()
                if value.isdigit():
                    return value
    
    return None

if __name__ == "__main__":
    test_extraction(extract_total_rounds)