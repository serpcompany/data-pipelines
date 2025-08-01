#!/usr/bin/env python3
"""Extract total bouts from HTML."""

from base_extractor import load_html, test_extraction

def extract_total_bouts(soup):
    """Extract total number of professional bouts from HTML."""
    
    # Method 1: Look for bouts in table rows
    rows = soup.find_all('tr')
    for row in rows:
        cells = row.find_all(['td', 'th'])
        if len(cells) >= 2:
            label = cells[0].get_text().strip().lower()
            # Look for "bouts" but not "about"
            if 'bouts' in label and 'about' not in label and 'count' not in label:
                value = cells[1].get_text().strip()
                if value.isdigit():
                    return value
    
    # Method 2: Calculate from record
    wld_table = soup.find('table', {'class': 'profileWLD'})
    if wld_table:
        first_row = wld_table.find('tr')
        if first_row:
            cells = first_row.find_all(['td', 'th'])
            if len(cells) >= 3:
                try:
                    wins = int(cells[0].get_text().strip() or 0)
                    losses = int(cells[1].get_text().strip() or 0)
                    draws = int(cells[2].get_text().strip() or 0)
                    return str(wins + losses + draws)
                except ValueError:
                    pass
    
    return None

if __name__ == "__main__":
    test_extraction(extract_total_bouts)