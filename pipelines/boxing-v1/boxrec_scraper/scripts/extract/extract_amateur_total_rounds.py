#!/usr/bin/env python3
"""Extract amateur total rounds from HTML."""

import re
from base_extractor import load_html, test_extraction

def extract_amateur_total_rounds(soup):
    """Extract amateur total rounds from HTML."""
    
    # Look in profileTable for amateur rounds
    profile_table = soup.find('table', {'class': 'profileTable'})
    if profile_table:
        rows = profile_table.find_all('tr')
        for row in rows:
            cells = row.find_all(['td', 'th'])
            if len(cells) >= 2:
                label = cells[0].get_text().strip().lower()
                value = cells[1].get_text().strip()
                
                if 'amateur' in label and 'rounds' in label:
                    if value.isdigit():
                        return int(value)
    
    return None

if __name__ == "__main__":
    test_extraction(extract_amateur_total_rounds)