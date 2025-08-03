#!/usr/bin/env python3
"""
Validator to detect blank or minimal content pages.
These are often error pages, maintenance pages, or failed loads.
"""

from bs4 import BeautifulSoup
from typing import Tuple


def validate(html_content: str, url: str = None) -> Tuple[bool, str]:
    """
    Check if HTML represents a blank or minimal content page.
    
    Args:
        html_content: HTML content to validate
        url: URL being validated (optional)
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not html_content or not html_content.strip():
        return False, "Empty HTML content"
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Get text content without scripts and styles
    for script in soup(["script", "style"]):
        script.decompose()
    
    text_content = soup.get_text(strip=True)
    
    # Check if page is too short
    if len(text_content) < 50:
        return False, f"Page has minimal content ({len(text_content)} chars)"
    
    # Check for common error/blank page patterns
    if not soup.find('body'):
        return False, "No body tag found"
    
    # Check if body has no substantial content
    body = soup.find('body')
    body_text = body.get_text(strip=True) if body else ""
    
    if len(body_text) < 20:
        return False, f"Body has minimal content ({len(body_text)} chars)"
    
    # Check for maintenance/error messages
    common_error_patterns = [
        'under maintenance',
        'coming soon',
        'be right back',
        'temporarily unavailable',
        'service unavailable',
        'please try again later'
    ]
    
    text_lower = text_content.lower()
    for pattern in common_error_patterns:
        if pattern in text_lower:
            return False, f"Error/maintenance pattern detected: {pattern}"
    
    # Check if page only has navigation/header but no main content
    # (This is common in failed loads where only the template renders)
    main_content_tags = ['main', 'article', 'section']
    has_main_content = any(soup.find(tag) for tag in main_content_tags)
    
    # If no main content tags, check for divs with substantial text
    if not has_main_content:
        divs_with_content = [
            div for div in soup.find_all('div') 
            if len(div.get_text(strip=True)) > 100
        ]
        if not divs_with_content:
            return False, "No substantial content sections found"
    
    return True, "Page has sufficient content"


if __name__ == "__main__":
    # Test with sample blank page
    test_html = """
    <html>
    <head><title>BoxRec</title></head>
    <body>
        <div class="header">BoxRec</div>
        <div class="content"></div>
    </body>
    </html>
    """
    
    is_valid, message = validate(test_html)
    print(f"Valid: {is_valid}")
    print(f"Message: {message}")