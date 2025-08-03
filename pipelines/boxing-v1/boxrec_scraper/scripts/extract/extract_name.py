#!/usr/bin/env python3
"""Extract boxer name from HTML."""

from base_extractor import load_html, test_extraction

def extract_name(soup):
    """Extract boxer name from various possible locations."""
    
    # Method 1: From title tag
    title_tag = soup.find('title')
    if title_tag:
        title_text = title_tag.get_text().strip()
        if 'BoxRec:' in title_text:
            return title_text.replace('BoxRec:', '').strip()
    
    # Method 2: From h1 tag
    h1_tag = soup.find('h1')
    if h1_tag:
        return h1_tag.get_text().strip()
    
    # Method 3: From meta tags
    meta_title = soup.find('meta', {'property': 'og:title'})
    if meta_title and meta_title.get('content'):
        content = meta_title['content']
        if 'BoxRec:' in content:
            return content.replace('BoxRec:', '').strip()
    
    return None

if __name__ == "__main__":
    test_extraction(extract_name)