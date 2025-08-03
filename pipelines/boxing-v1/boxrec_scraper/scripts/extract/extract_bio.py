#!/usr/bin/env python3
"""Extract bio from HTML."""

import re
from base_extractor import load_html, test_extraction

def extract_bio(soup):
    """Extract bio from HTML."""
    
    # Look for bio section
    # BoxRec typically doesn't have detailed bios on the main page
    # This would come from wiki data if available
    
    # Check for any biography or about section
    bio_headers = soup.find_all(['h2', 'h3'], string=re.compile(r'biograph|about', re.IGNORECASE))
    
    for header in bio_headers:
        # Get text from following siblings until next header
        bio_text = []
        for sibling in header.find_next_siblings():
            if sibling.name in ['h1', 'h2', 'h3']:
                break
            text = sibling.get_text().strip()
            if text:
                bio_text.append(text)
        
        if bio_text:
            return ' '.join(bio_text)
    
    return ''

if __name__ == "__main__":
    test_extraction(extract_bio)