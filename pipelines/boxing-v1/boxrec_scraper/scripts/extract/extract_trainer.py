#!/usr/bin/env python3
"""Extract trainer(s) from HTML."""

from base_extractor import load_html, test_extraction

def extract_trainer(soup):
    """Extract trainer(s) from HTML."""
    
    # Method 1: Look for trainer in table rows
    rows = soup.find_all('tr')
    for row in rows:
        cells = row.find_all(['td', 'th'])
        if len(cells) >= 2:
            label = cells[0].get_text().strip().lower()
            if 'trainer' in label:
                value = cells[1].get_text().strip()
                # Handle multiple trainers separated by comma
                if value:
                    trainers = [t.strip() for t in value.split(',') if t.strip()]
                    return ', '.join(trainers)
    
    return None

if __name__ == "__main__":
    test_extraction(extract_trainer)