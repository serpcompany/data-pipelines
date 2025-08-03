#!/usr/bin/env python3
"""Extract BoxRec wiki URL from HTML."""

import re
from base_extractor import load_html, test_extraction

def extract_wiki_url(soup):
    """Extract BoxRec wiki URL from HTML."""
    
    # Method 1: Look for wiki link
    wiki_link = soup.find('a', href=re.compile(r'/wiki/index\.php\?title=Human:'))
    if wiki_link and wiki_link.get('href'):
        href = wiki_link['href']
        if href.startswith('/'):
            return f"https://boxrec.com{href}"
        elif href.startswith('http'):
            return href
    
    # Method 2: Look for wiki button/icon
    wiki_links = soup.find_all('a', href=True)
    for link in wiki_links:
        href = link['href']
        if 'wiki' in href and 'Human:' in href:
            if href.startswith('/'):
                return f"https://boxrec.com{href}"
            elif href.startswith('http'):
                return href
    
    return None

if __name__ == "__main__":
    test_extraction(extract_wiki_url)