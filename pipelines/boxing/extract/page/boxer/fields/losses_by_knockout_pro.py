#!/usr/bin/env python3
"""Extract professional losses by knockout from HTML."""

import re
from ....base import load_html, test_extraction

def extract_pro_losses_by_knockout(soup):
    """Extract professional losses by knockout from HTML."""
    
    # Look for profileWLD table
    wld_table = soup.find('table', {'class': 'profileWLD'})
    if wld_table:
        # Second row has KOs
        rows = wld_table.find_all('tr')
        if len(rows) > 1:
            second_row = rows[1]
            ko_cells = second_row.find_all(['td', 'th'])
            
            # Second cell should have loss KOs
            if ko_cells and len(ko_cells) > 1:
                ko_text = ko_cells[1].get_text()
                ko_match = re.search(r'(\d+)\s*KOs?', ko_text)
                if ko_match:
                    return int(ko_match.group(1))
    
    return 0

if __name__ == "__main__":
    test_extraction(extract_pro_losses_by_knockout)