#!/usr/bin/env python3
"""Extract promoter(s) from HTML."""

from base_extractor import load_html, test_extraction

def extract_promoter(soup):
    """Extract promoter(s) from HTML."""
    
    # Method 1: Look for promoter in table rows
    rows = soup.find_all('tr')
    for row in rows:
        cells = row.find_all(['td', 'th'])
        if len(cells) >= 2:
            label = cells[0].get_text().strip().lower()
            if 'promoter' in label:
                value = cells[1].get_text().strip()
                # Handle multiple promoters separated by comma
                if value:
                    promoters = [p.strip() for p in value.split(',') if p.strip()]
                    return ', '.join(promoters)
    
    return None

if __name__ == "__main__":
    test_extraction(extract_promoter)