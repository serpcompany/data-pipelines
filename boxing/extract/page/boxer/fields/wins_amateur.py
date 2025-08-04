#!/usr/bin/env python3
"""Extract amateur wins from HTML."""

import re
from ....base import load_html, test_extraction

def extract(soup):
    """Extract amateur wins from HTML."""
    
    # Method 1: Look for amateur section with record
    amateur_headers = soup.find_all(string=re.compile(r'amateur', re.IGNORECASE))
    
    for header in amateur_headers:
        parent = header.parent
        while parent and parent.name != 'body':
            # Look for record pattern near amateur header
            text = parent.get_text()
            
            # Pattern: number-number-number (e.g., "10-2-1")
            record_match = re.search(r'(\d+)\s*[-–]\s*(\d+)\s*[-–]\s*(\d+)', text)
            if record_match:
                return int(record_match.group(1))
            
            # Check siblings
            for sibling in parent.find_next_siblings():
                sibling_text = sibling.get_text()
                record_match = re.search(r'(\d+)\s*[-–]\s*(\d+)\s*[-–]\s*(\d+)', sibling_text)
                if record_match:
                    return int(record_match.group(1))
                # Don't go too far
                if sibling.name in ['h1', 'h2', 'h3']:
                    break
            
            parent = parent.parent if parent else None
    
    # Method 2: Look in profileTable for amateur record
    profile_table = soup.find('table', {'class': 'profileTable'})
    if profile_table:
        rows = profile_table.find_all('tr')
        for row in rows:
            cells = row.find_all(['td', 'th'])
            if len(cells) >= 2:
                label = cells[0].get_text().strip().lower()
                value = cells[1].get_text().strip()
                
                if 'amateur' in label and 'record' in label:
                    # Parse amateur record like "10-2-1"
                    record_match = re.search(r'(\d+)\s*[-–]\s*(\d+)\s*[-–]\s*(\d+)', value)
                    if record_match:
                        return int(record_match.group(1))
    
    return None

if __name__ == "__main__":
    test_extraction(extract)