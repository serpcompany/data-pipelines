#!/usr/bin/env python3
"""Extract trainers from HTML."""

import re
from ....base import load_html, test_extraction

def extract(soup):
    """Extract trainers from HTML."""
    
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
                    
                    if 'trainer' in label:
                        # Clean up and split by comma
                        trainers = [v.strip() for v in value.split(',') if v.strip()]
                        return ', '.join(trainers)
    
    return ''

if __name__ == "__main__":
    test_extraction(extract)