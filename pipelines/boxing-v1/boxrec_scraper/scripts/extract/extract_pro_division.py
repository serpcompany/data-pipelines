#!/usr/bin/env python3
"""Extract professional division from HTML."""

import re
from base_extractor import load_html, test_extraction

def extract_pro_division(soup):
    """Extract professional division from HTML."""
    
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
                    
                    # Look for division but not weight division
                    if 'division' in label and 'weight' not in label and 'amateur' not in label:
                        return value
    
    return ''

if __name__ == "__main__":
    test_extraction(extract_pro_division)