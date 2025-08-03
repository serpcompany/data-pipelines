#!/usr/bin/env python3
"""Extract division from HTML."""

from base_extractor import load_html, test_extraction

def extract_division(soup):
    """Extract current boxing division from HTML."""
    
    # Method 1: Look for division in table rows
    rows = soup.find_all('tr')
    for row in rows:
        cells = row.find_all(['td', 'th'])
        if len(cells) >= 2:
            label = cells[0].get_text().strip().lower()
            # Look for division but not "sub-division"
            if 'division' in label and 'sub' not in label and 'weight' not in label:
                value = cells[1].get_text().strip()
                return value
    
    # Method 2: Look for weight class references
    weight_classes = [
        'heavyweight', 'cruiser', 'light heavy', 'super middle', 
        'middle', 'super welter', 'welter', 'super light', 
        'light', 'super feather', 'feather', 'super bantam', 
        'bantam', 'super fly', 'fly', 'light fly', 'minimum'
    ]
    
    text = soup.get_text().lower()
    for weight_class in weight_classes:
        if f"division: {weight_class}" in text:
            return weight_class
    
    return None

if __name__ == "__main__":
    test_extraction(extract_division)