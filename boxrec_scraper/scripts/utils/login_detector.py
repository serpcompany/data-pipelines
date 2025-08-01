#!/usr/bin/env python3
"""
Utility functions for detecting BoxRec login pages.
"""
import re
from pathlib import Path
from bs4 import BeautifulSoup


def is_login_page(html_content):
    """
    Check if HTML content is a BoxRec login page.
    
    Args:
        html_content: HTML string content
        
    Returns:
        bool: True if this is a login page, False otherwise
    """
    # Quick check for common login page indicators
    if 'Boxrec: Login' in html_content:
        return True
    
    if 'Please login to BoxRec' in html_content:
        return True
    
    if '/en/login?error=limit' in html_content:
        return True
    
    # Parse HTML for more thorough check
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Check title
        title_tag = soup.find('title')
        if title_tag and 'Boxrec: Login' in title_tag.get_text():
            return True
        
        # Check meta description
        desc_meta = soup.find('meta', {'name': 'description'})
        if desc_meta and desc_meta.get('content', '').strip() == 'Please login to BoxRec':
            return True
        
        # Check canonical URL
        canonical = soup.find('link', {'rel': 'canonical'})
        if canonical and canonical.get('href', ''):
            href = canonical['href']
            if '/login' in href or 'error=limit' in href:
                return True
    
    except Exception:
        # If parsing fails, fall back to string matching
        pass
    
    return False


def is_login_page_file(file_path):
    """
    Check if a file contains a BoxRec login page.
    
    Args:
        file_path: Path to HTML file
        
    Returns:
        bool: True if this is a login page, False otherwise
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return is_login_page(content)
    except Exception:
        return False


def find_login_pages(directory):
    """
    Find all login page files in a directory.
    
    Args:
        directory: Path to directory containing HTML files
        
    Returns:
        list: List of Path objects for files containing login pages
    """
    directory = Path(directory)
    login_files = []
    
    for html_file in directory.glob('*.html'):
        if is_login_page_file(html_file):
            login_files.append(html_file)
    
    return login_files


def extract_original_url(file_path):
    """
    Extract the original BoxRec URL from the filename.
    
    Args:
        file_path: Path to HTML file
        
    Returns:
        str: Original BoxRec URL or None
    """
    filename = Path(file_path).name
    
    # Pattern: en_box-pro_123456.html
    match = re.match(r'([a-z]+)_box-pro_(\d+)\.html', filename)
    if match:
        lang = match.group(1)
        boxer_id = match.group(2)
        return f"https://boxrec.com/{lang}/box-pro/{boxer_id}"
    
    return None