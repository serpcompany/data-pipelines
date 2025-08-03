#!/usr/bin/env python3
"""Extract amateur wins by knockout from HTML."""

import re
from ....base import load_html, test_extraction

def extract_amateur_wins_by_knockout(soup):
    """Extract amateur wins by knockout from HTML."""
    
    # Look for amateur section with KO information
    amateur_headers = soup.find_all(string=re.compile(r'amateur', re.IGNORECASE))
    
    for header in amateur_headers:
        parent = header.parent
        while parent and parent.name != 'body':
            text = parent.get_text()
            
            # Look for KO pattern after record
            if re.search(r'\d+\s*[-–]\s*\d+\s*[-–]\s*\d+', text):
                # Found record, now look for KOs
                ko_match = re.search(r'(\d+)\s*KOs?', text)
                if ko_match:
                    return int(ko_match.group(1))
            
            # Check siblings
            for sibling in parent.find_next_siblings():
                sibling_text = sibling.get_text()
                if re.search(r'\d+\s*[-–]\s*\d+\s*[-–]\s*\d+', sibling_text):
                    ko_match = re.search(r'(\d+)\s*KOs?', sibling_text)
                    if ko_match:
                        return int(ko_match.group(1))
                if sibling.name in ['h1', 'h2', 'h3']:
                    break
            
            parent = parent.parent if parent else None
    
    # Look in profileTable
    profile_table = soup.find('table', {'class': 'profileTable'})
    if profile_table:
        rows = profile_table.find_all('tr')
        for row in rows:
            cells = row.find_all(['td', 'th'])
            if len(cells) >= 2:
                label = cells[0].get_text().strip().lower()
                value = cells[1].get_text().strip()
                
                if 'amateur' in label and 'record' in label:
                    # Look for KO information
                    ko_match = re.search(r'(\d+)\s*KOs?', value)
                    if ko_match:
                        return int(ko_match.group(1))
    
    return None

if __name__ == "__main__":
    test_extraction(extract_amateur_wins_by_knockout)