#!/usr/bin/env python3
"""Extract professional wins from HTML."""

import re
from ....base import load_html, test_extraction

def extract_pro_wins(soup):
    """Extract professional wins from HTML."""
    
    # Method 1: Look for profileWLD table
    wld_table = soup.find('table', {'class': 'profileWLD'})
    if wld_table:
        # First row has W-L-D
        first_row = wld_table.find('tr')
        if first_row:
            # Look for wins (usually has bgW class)
            win_cell = first_row.find(class_='bgW')
            if win_cell:
                wins_text = win_cell.get_text().strip()
                if wins_text.isdigit():
                    return int(wins_text)
    
    # Method 2: Look for wins in first cell of first row
    if wld_table:
        first_row = wld_table.find('tr')
        if first_row:
            cells = first_row.find_all(['td', 'th'])
            if cells and len(cells) > 0:
                wins_text = cells[0].get_text().strip()
                if wins_text.isdigit():
                    return int(wins_text)
    
    return 0

if __name__ == "__main__":
    test_extraction(extract_pro_wins)