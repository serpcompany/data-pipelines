#!/usr/bin/env python3
"""Extract professional losses from HTML."""

import re
from ....base import load_html, test_extraction

def extract_pro_losses(soup):
    """Extract professional losses from HTML."""
    
    # Method 1: Look for profileWLD table
    wld_table = soup.find('table', {'class': 'profileWLD'})
    if wld_table:
        # First row has W-L-D
        first_row = wld_table.find('tr')
        if first_row:
            # Look for losses (usually has bgL class)
            loss_cell = first_row.find(class_='bgL')
            if loss_cell:
                losses_text = loss_cell.get_text().strip()
                if losses_text.isdigit():
                    return int(losses_text)
    
    # Method 2: Look for losses in second cell of first row
    if wld_table:
        first_row = wld_table.find('tr')
        if first_row:
            cells = first_row.find_all(['td', 'th'])
            if cells and len(cells) > 1:
                losses_text = cells[1].get_text().strip()
                if losses_text.isdigit():
                    return int(losses_text)
    
    return 0

if __name__ == "__main__":
    test_extraction(extract_pro_losses)