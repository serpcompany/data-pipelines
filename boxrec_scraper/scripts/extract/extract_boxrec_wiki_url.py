#!/usr/bin/env python3
"""Extract BoxRec Wiki URL from HTML."""

import re
from base_extractor import load_html, test_extraction

def extract_boxrec_wiki_url(soup):
    """Extract BoxRec Wiki URL from HTML."""
    
    # Look for wiki link
    wiki_link = soup.find('a', href=re.compile(r'/wiki/index\.php\?title=Human:'))
    if wiki_link:
        return 'https://boxrec.com' + wiki_link['href']
    
    return ''

if __name__ == "__main__":
    test_extraction(extract_boxrec_wiki_url)