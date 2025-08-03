#!/usr/bin/env python3
"""Extract stance from HTML."""

from ....base import load_html, test_extraction

def extract_stance(soup):
    """Extract boxing stance from HTML."""
    
    # Method 1: Look for stance in table rows
    rows = soup.find_all('tr')
    for row in rows:
        cells = row.find_all(['td', 'th'])
        if len(cells) >= 2:
            label = cells[0].get_text().strip().lower()
            if 'stance' in label:
                value = cells[1].get_text().strip().lower()
                # Normalize common stance values
                if 'orthodox' in value:
                    return 'orthodox'
                elif 'southpaw' in value:
                    return 'southpaw'
                else:
                    return value
    
    return None

if __name__ == "__main__":
    test_extraction(extract_stance)