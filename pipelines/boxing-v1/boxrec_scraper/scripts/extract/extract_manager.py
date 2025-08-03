#!/usr/bin/env python3
"""Extract manager(s) from HTML."""

from base_extractor import load_html, test_extraction

def extract_manager(soup):
    """Extract manager(s) from HTML."""
    
    # Method 1: Look for manager in table rows
    rows = soup.find_all('tr')
    for row in rows:
        cells = row.find_all(['td', 'th'])
        if len(cells) >= 2:
            label = cells[0].get_text().strip().lower()
            if 'manager' in label:
                value = cells[1].get_text().strip()
                # Handle multiple managers separated by comma
                if value:
                    managers = [m.strip() for m in value.split(',') if m.strip()]
                    return ', '.join(managers)
    
    return None

if __name__ == "__main__":
    test_extraction(extract_manager)