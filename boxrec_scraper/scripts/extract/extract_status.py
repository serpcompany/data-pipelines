#!/usr/bin/env python3
"""Extract boxer status (active/inactive) from HTML."""

from base_extractor import load_html, test_extraction

def extract_status(soup):
    """Extract boxer status from HTML."""
    
    # Method 1: Look for status in table rows
    rows = soup.find_all('tr')
    for row in rows:
        cells = row.find_all(['td', 'th'])
        if len(cells) >= 2:
            label = cells[0].get_text().strip().lower()
            if 'status' in label:
                value = cells[1].get_text().strip().lower()
                # Check for inactive indicators
                if any(word in value for word in ['inactive', 'retired', 'not active']):
                    return 'inactive'
                elif 'active' in value:
                    return 'active'
    
    # Method 2: Look for retirement indicators in text
    text = soup.get_text().lower()
    if any(phrase in text for phrase in ['retired boxer', 'former boxer', 'status: retired']):
        return 'inactive'
    
    return None

if __name__ == "__main__":
    test_extraction(extract_status)