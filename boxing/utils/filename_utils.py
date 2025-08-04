#!/usr/bin/env python3
"""
Filename utility functions for the boxing pipeline.
"""

import re
from urllib.parse import urlparse


def create_filename_from_url(url: str) -> str:
    """Create a safe filename from a BoxRec URL."""
    parsed = urlparse(url)
    path_parts = parsed.path.strip('/').split('/')
    
    # Handle different URL formats
    if 'box-pro' in url:
        # Extract language and ID: /en/box-pro/123456
        if len(path_parts) >= 3:
            lang = path_parts[0] if path_parts[0] in ['en', 'es', 'fr', 'de', 'ru'] else 'en'
            boxer_id = path_parts[-1]
            return f"{lang}_box-pro_{boxer_id}.html"
    elif 'box-am' in url:
        # Extract language and ID: /en/box-am/123456
        if len(path_parts) >= 3:
            lang = path_parts[0] if path_parts[0] in ['en', 'es', 'fr', 'de', 'ru'] else 'en'
            boxer_id = path_parts[-1]
            return f"{lang}_box-am_{boxer_id}.html"
    elif 'wiki' in url:
        # Extract ID from wiki URL
        id_match = re.search(r'Human:(\d+)', url)
        if id_match:
            return f"wiki_box-pro_{id_match.group(1)}.html"
    
    # Fallback: clean up the path
    filename_parts = []
    for part in path_parts:
        clean_part = part.replace('/', '_').replace('\\', '_').replace(':', '_')
        if clean_part:
            filename_parts.append(clean_part)
    
    filename = '_'.join(filename_parts) if filename_parts else 'index'
    return f"{filename[:100]}.html"  # Limit length