#!/usr/bin/env python3
"""
BoxRec URL validator - validates and normalizes BoxRec URLs.
"""

from urllib.parse import urlparse, parse_qs, urlencode, urlunparse


def validate(url: str) -> bool:
    """
    Check if URL is a valid BoxRec URL.
    
    Args:
        url: URL to validate
        
    Returns:
        bool: True if valid BoxRec URL, False otherwise
    """
    try:
        parsed = urlparse(url)
        
        # Must be boxrec.com
        if parsed.netloc not in ['boxrec.com', 'www.boxrec.com']:
            return False
        
        # Must have a path
        if not parsed.path or parsed.path == '/':
            return False
        
        return True
    except:
        return False


def normalize_boxer_url(url: str, include_all_sports: bool = True) -> str:
    """
    Normalize a BoxRec boxer URL to ensure it includes allSports parameter.
    
    Args:
        url: BoxRec URL
        include_all_sports: Whether to add ?allSports=y parameter
        
    Returns:
        Normalized URL with allSports=y if it's a boxer page
    """
    parsed = urlparse(url)
    
    # Only modify box-pro URLs
    if '/box-pro/' not in parsed.path:
        return url
    
    if not include_all_sports:
        return url
    
    # Parse existing query parameters
    query_params = parse_qs(parsed.query)
    
    # Add allSports=y if not present
    if 'allSports' not in query_params:
        query_params['allSports'] = ['y']
    
    # Rebuild URL with updated query
    new_query = urlencode(query_params, doseq=True)
    normalized = urlunparse((
        parsed.scheme,
        parsed.netloc,
        parsed.path,
        parsed.params,
        new_query,
        parsed.fragment
    ))
    
    return normalized


def validate_csv_urls(csv_path: str) -> tuple[list[str], list[str]]:
    """
    Validate all URLs in a CSV file.
    
    Args:
        csv_path: Path to CSV file
        
    Returns:
        Tuple of (valid_urls, invalid_urls)
    """
    import csv
    from pathlib import Path
    
    valid_urls = []
    invalid_urls = []
    
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            url = row.get('URL') or row.get('url')
            if url:
                if validate(url):
                    valid_urls.append(url)
                else:
                    invalid_urls.append(url)
    
    return valid_urls, invalid_urls


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        url = sys.argv[1]
        
        print(f"Original URL: {url}")
        print(f"Valid: {validate(url)}")
        
        if validate(url):
            normalized = normalize_boxer_url(url)
            print(f"Normalized: {normalized}")
    else:
        print("Usage: python boxrec_url.py <url>")