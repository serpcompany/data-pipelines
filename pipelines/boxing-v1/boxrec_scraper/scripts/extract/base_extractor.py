#!/usr/bin/env python3
"""Base extractor with common functions for all field extractors."""

import sys
from bs4 import BeautifulSoup
from pathlib import Path

def load_html(html_path):
    """Load HTML file and return BeautifulSoup object."""
    with open(html_path, 'r', encoding='utf-8') as f:
        return BeautifulSoup(f.read(), 'html.parser')

def get_test_file():
    """Get a test HTML file - Floyd Mayweather as example."""
    return "/Users/devin/repos/projects/data-pipelines/boxrec_scraper/data/raw/boxrec_html/en_box-pro_352.html"

def test_extraction(extract_func, html_path=None):
    """Test an extraction function."""
    if not html_path:
        html_path = get_test_file()
    
    print(f"Testing on: {html_path}")
    soup = load_html(html_path)
    result = extract_func(soup)
    print(f"Result: {result}")
    return result