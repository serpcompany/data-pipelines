#!/usr/bin/env python3
"""Extract nicknames from HTML."""

import re
from ....base import load_html, test_extraction

def extract(soup):
    """Extract nicknames/aliases from HTML."""
    
    # Method 1: Look for alias/nickname in table rows
    rows = soup.find_all('tr')
    for row in rows:
        cells = row.find_all(['td', 'th'])
        if len(cells) >= 2:
            label = cells[0].get_text().strip().lower()
            if 'alias' in label or 'nickname' in label:
                value = cells[1].get_text().strip()
                # Split by comma and format as quoted strings
                if value:
                    nicknames = [n.strip() for n in value.split(',') if n.strip()]
                    return ','.join(f'{n}' for n in nicknames)
    
    # Method 2: Look in specific divs or spans with class names
    nickname_elements = soup.find_all(['div', 'span'], class_=re.compile(r'nickname|alias', re.I))
    for elem in nickname_elements:
        text = elem.get_text().strip()
        if text:
            nicknames = [n.strip() for n in text.split(',') if n.strip()]
            return ','.join(f'{n}' for n in nicknames)
    
    return None

if __name__ == "__main__":
    test_extraction(extract)