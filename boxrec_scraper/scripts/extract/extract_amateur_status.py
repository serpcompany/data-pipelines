#!/usr/bin/env python3
"""Extract amateur status from HTML."""

import re
from base_extractor import load_html, test_extraction

def extract_amateur_status(soup):
    """Extract amateur status (active/inactive) from HTML."""
    
    # Look for amateur status in profileTable
    profile_table = soup.find('table', {'class': 'profileTable'})
    if profile_table:
        rows = profile_table.find_all('tr')
        for row in rows:
            cells = row.find_all(['td', 'th'])
            if len(cells) >= 2:
                label = cells[0].get_text().strip().lower()
                value = cells[1].get_text().strip().lower()
                
                if 'amateur' in label and 'status' in label:
                    if any(word in value for word in ['inactive', 'retired', 'not active']):
                        return 'inactive'
                    elif 'active' in value:
                        return 'active'
    
    # If no explicit amateur status, infer from whether they have pro record
    # If they have a pro record, amateur is likely inactive
    wld_table = soup.find('table', {'class': 'profileWLD'})
    if wld_table:
        first_row = wld_table.find('tr')
        if first_row:
            cells = first_row.find_all(['td', 'th'])
            if len(cells) >= 3:
                # Check if they have any pro fights
                has_pro_fights = False
                for cell in cells:
                    text = cell.get_text().strip()
                    if text.isdigit() and int(text) > 0:
                        has_pro_fights = True
                        break
                
                if has_pro_fights:
                    return 'inactive'
    
    return ''

if __name__ == "__main__":
    test_extraction(extract_amateur_status)