#!/usr/bin/env python3
"""Extract amateur losses by knockout from HTML."""

import re
from ....base import load_html, test_extraction

def extract(soup):
    """Extract amateur losses by knockout from HTML."""
    
    # This information is rarely available for amateur records
    # BoxRec typically only shows total KOs for wins, not losses
    
    # Still check in case it's available
    amateur_headers = soup.find_all(string=re.compile(r'amateur', re.IGNORECASE))
    
    for header in amateur_headers:
        parent = header.parent
        while parent and parent.name != 'body':
            text = parent.get_text()
            
            # Look for specific pattern mentioning losses by KO
            ko_loss_match = re.search(r'(\d+)\s*(?:losses?\s*by\s*)?KOs?\s*(?:losses?|against)', text, re.IGNORECASE)
            if ko_loss_match:
                return int(ko_loss_match.group(1))
            
            parent = parent.parent if parent else None
    
    return None

if __name__ == "__main__":
    test_extraction(extract)