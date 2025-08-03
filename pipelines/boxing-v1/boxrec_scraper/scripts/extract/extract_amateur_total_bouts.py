#!/usr/bin/env python3
"""Extract amateur total bouts from HTML."""

import re
from base_extractor import load_html, test_extraction

def extract_amateur_total_bouts(soup):
    """Extract amateur total bouts from HTML."""
    
    # Method 1: Calculate from W-L-D if available
    wins = losses = draws = 0
    found_record = False
    
    # Look for amateur record
    amateur_headers = soup.find_all(string=re.compile(r'amateur', re.IGNORECASE))
    
    for header in amateur_headers:
        parent = header.parent
        while parent and parent.name != 'body':
            text = parent.get_text()
            
            # Pattern: number-number-number (e.g., "10-2-1")
            record_match = re.search(r'(\d+)\s*[-–]\s*(\d+)\s*[-–]\s*(\d+)', text)
            if record_match:
                wins = int(record_match.group(1))
                losses = int(record_match.group(2))
                draws = int(record_match.group(3))
                found_record = True
                break
            
            parent = parent.parent if parent else None
        
        if found_record:
            break
    
    # Method 2: Look in profileTable
    if not found_record:
        profile_table = soup.find('table', {'class': 'profileTable'})
        if profile_table:
            rows = profile_table.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    label = cells[0].get_text().strip().lower()
                    value = cells[1].get_text().strip()
                    
                    if 'amateur' in label and 'record' in label:
                        record_match = re.search(r'(\d+)\s*[-–]\s*(\d+)\s*[-–]\s*(\d+)', value)
                        if record_match:
                            wins = int(record_match.group(1))
                            losses = int(record_match.group(2))
                            draws = int(record_match.group(3))
                            found_record = True
                            break
    
    if found_record:
        total = wins + losses + draws
        if total > 0:
            return total
    
    # Method 3: Look for explicit amateur bouts field
    profile_table = soup.find('table', {'class': 'profileTable'})
    if profile_table:
        rows = profile_table.find_all('tr')
        for row in rows:
            cells = row.find_all(['td', 'th'])
            if len(cells) >= 2:
                label = cells[0].get_text().strip().lower()
                value = cells[1].get_text().strip()
                
                if 'amateur' in label and 'bouts' in label:
                    if value.isdigit():
                        return int(value)
    
    return None

if __name__ == "__main__":
    test_extraction(extract_amateur_total_bouts)