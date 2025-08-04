#!/usr/bin/env python3
"""
Login page validator - checks if HTML is a BoxRec login page.
"""

def validate(html_content: str) -> bool:
    """
    Check if HTML content is a BoxRec login page.
    
    Args:
        html_content: HTML string content
        
    Returns:
        bool: True if validation passes (NOT a login page), False if it's a login page
    """
    login_indicators = [
        'Boxrec: Login',
        'BoxRec: Login',
        '<title>Boxrec: Login</title>',
        '<title>BoxRec: Login</title>',
        'Please login to BoxRec',
        '/en/login?error=limit',
        'Login - BoxRec'
    ]
    
    for indicator in login_indicators:
        if indicator in html_content:
            return False
    
    return True