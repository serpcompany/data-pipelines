#!/usr/bin/env python3
"""Extract amateur debut date from HTML."""

import re
from ....base import load_html, test_extraction
from extract_debut_date import format_date_iso

def extract_amateur_debut_date(soup):
    """Extract amateur debut date from HTML."""
    
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
                    
                    if 'amateur' in label and 'debut' in label:
                        return format_date_iso(value)
    
    return ''

if __name__ == "__main__":
    test_extraction(extract_amateur_debut_date)