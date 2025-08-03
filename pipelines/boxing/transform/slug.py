#!/usr/bin/env python3
"""Extract slug from boxer name."""

import re
from base_extractor import load_html, test_extraction

def extract_slug(soup):
    """Extract slug from boxer name."""
    
    # Get name from title
    title_tag = soup.find('title')
    if title_tag:
        title_text = title_tag.get_text().strip()
        if 'BoxRec:' in title_text:
            name = title_text.replace('BoxRec:', '').strip()
            if name:
                # Generate slug from name
                slug = re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')
                return slug
    
    return ''

if __name__ == "__main__":
    test_extraction(extract_slug)