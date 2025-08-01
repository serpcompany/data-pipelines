#!/usr/bin/env python3
"""Extract amateur division from HTML."""

import re
from base_extractor import load_html, test_extraction

def extract_amateur_division(soup):
    """Extract amateur division from HTML."""
    
    # Look in profileTable
    profile_table = soup.find('table', {'class': 'profileTable'})
    if profile_table:
        row_tables = profile_table.find_all('table', {'class': 'rowTable'})
        
        for row_table in row_tables:
            rows = row_table.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    label = cells[0].get_text().strip().lower()
                    value = cells[1].get_text().strip()
                    
                    if 'amateur' in label and 'division' in label:
                        return value
    
    return ''

if __name__ == "__main__":
    test_extraction(extract_amateur_division)