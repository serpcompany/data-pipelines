#!/usr/bin/env python3
"""Extract ID (this will be set by database, return empty)."""

from base_extractor import load_html, test_extraction

def extract_id(soup):
    """Extract ID - this is set by database, return empty string."""
    return ''

if __name__ == "__main__":
    test_extraction(extract_id)