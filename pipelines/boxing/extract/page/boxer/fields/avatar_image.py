#!/usr/bin/env python3
"""Extract avatar/profile image from HTML."""

import re
from ....base import load_html, test_extraction

def extract_avatar_image(soup):
    """Extract profile image URL from HTML."""
    
    # Method 1: Look for profile picture class
    img_selectors = [
        'img.profileBoxerPicture',
        'img.photoBorder',
        'img[alt*="profile"]',
        'div.profileImage img',
        'td.profileBoxerPicture img',
        'div.profileTablePhoto img'
    ]
    
    for selector in img_selectors:
        img = soup.select_one(selector)
        if img and img.get('src'):
            src = img['src']
            # Skip placeholder/blank images
            if 'blank' in src.lower() or 'default' in src.lower():
                continue
            # Convert relative to absolute URL
            if src.startswith('/'):
                return f"https://boxrec.com{src}"
            elif src.startswith('http'):
                return src
    
    # Method 2: Look for wiki image link
    wiki_link = soup.find('a', href=re.compile(r'/wiki/index\.php\?title=Human:'))
    if wiki_link:
        img = wiki_link.find('img')
        if img and img.get('src'):
            src = img['src']
            if src.startswith('/'):
                return f"https://boxrec.com{src}"
            elif src.startswith('http'):
                return src
    
    return None

if __name__ == "__main__":
    test_extraction(extract_avatar_image)