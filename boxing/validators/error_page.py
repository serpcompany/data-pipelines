#!/usr/bin/env python3
"""
Error page validator - checks for HTTP error pages (404, 403, etc).
"""

def validate(html_content: str) -> bool:
    """
    Check if HTML content is an error page.
    
    Args:
        html_content: HTML string content
        
    Returns:
        bool: True if validation passes (NOT an error page), False if it's an error page
    """
    error_indicators = [
        '404 Not Found',
        'Page Not Found',
        'Error 404',
        '403 Forbidden',
        'Access Denied',
        '500 Internal Server Error',
        '502 Bad Gateway',
        '503 Service Unavailable'
    ]
    
    for indicator in error_indicators:
        if indicator in html_content:
            return False
    
    return True