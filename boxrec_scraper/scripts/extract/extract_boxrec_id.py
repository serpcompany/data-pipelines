#!/usr/bin/env python3
"""Extract BoxRec ID from HTML."""

import re
from base_extractor import load_html, test_extraction

def extract_boxrec_id(soup):
    """Extract BoxRec ID from various possible locations."""
    
    # Method 1: From canonical link
    canonical = soup.find('link', {'rel': 'canonical'})
    if canonical and canonical.get('href'):
        match = re.search(r'/box-pro/(\d+)', canonical['href'])
        if match:
            return match.group(1)
    
    # Method 2: From profile table (ID# row)
    rows = soup.find_all('tr')
    for row in rows:
        cells = row.find_all(['td', 'th'])
        if len(cells) >= 2:
            label = cells[0].get_text().strip().lower()
            if 'id#' in label:
                return cells[1].get_text().strip().lstrip('0')
    
    # Method 3: From URL in meta tags
    meta_url = soup.find('meta', {'property': 'og:url'})
    if meta_url and meta_url.get('content'):
        match = re.search(r'/box-pro/(\d+)', meta_url['content'])
        if match:
            return match.group(1)
    
    return None

if __name__ == "__main__":
    test_extraction(extract_boxrec_id)