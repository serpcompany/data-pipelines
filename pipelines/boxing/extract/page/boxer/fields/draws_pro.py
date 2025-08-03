#!/usr/bin/env python3
"""Extract professional draws from HTML."""

import re
from ....base import load_html, test_extraction

def extract(soup):
    """Extract professional draws from HTML."""
    
    # Method 1: Look for profileWLD table
    wld_table = soup.find('table', {'class': 'profileWLD'})
    if wld_table:
        # First row has W-L-D
        first_row = wld_table.find('tr')
        if first_row:
            # Look for draws (usually has bgD class)
            draw_cell = first_row.find(class_='bgD')
            if draw_cell:
                draws_text = draw_cell.get_text().strip()
                if draws_text.isdigit():
                    return int(draws_text)
    
    # Method 2: Look for draws in third cell of first row
    if wld_table:
        first_row = wld_table.find('tr')
        if first_row:
            cells = first_row.find_all(['td', 'th'])
            if cells and len(cells) > 2:
                draws_text = cells[2].get_text().strip()
                if draws_text.isdigit():
                    return int(draws_text)
    
    return 0

if __name__ == "__main__":
    test_extraction(extract)