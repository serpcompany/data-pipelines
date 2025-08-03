#!/usr/bin/env python3
"""Extract BoxRec URL from HTML."""

import re
from base_extractor import load_html, test_extraction

def extract_boxrec_url(soup):
    """Extract BoxRec URL from canonical link."""
    
    canonical = soup.find('link', {'rel': 'canonical'})
    if canonical and canonical.get('href'):
        return canonical['href']
    
    return ''

if __name__ == "__main__":
    test_extraction(extract_boxrec_url)