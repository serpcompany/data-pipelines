#!/usr/bin/env python3
"""Extract amateur debut date from HTML."""

import re
from datetime import datetime
from ....base import load_html, test_extraction

def format_date_iso(date_str):
    """Convert date string to ISO format."""
    if not date_str:
        return ''
    
    # Try common date formats
    formats = [
        '%Y-%m-%d',
        '%d/%m/%Y',
        '%m/%d/%Y',
        '%d-%m-%Y',
        '%m-%d-%Y',
        '%B %d, %Y',
        '%d %B %Y',
        '%b %d, %Y',
        '%d %b %Y'
    ]
    
    for fmt in formats:
        try:
            dt = datetime.strptime(date_str.strip(), fmt)
            return dt.strftime('%Y-%m-%d')
        except ValueError:
            continue
    
    return date_str  # Return original if can't parse

def extract(soup):
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
    test_extraction(extract)