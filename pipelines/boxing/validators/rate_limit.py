#!/usr/bin/env python3
"""
Rate limit validator - checks if page indicates rate limiting.
"""

def validate(html_content: str) -> bool:
    """
    Check if HTML content indicates rate limiting.
    
    Args:
        html_content: HTML string content
        
    Returns:
        bool: True if validation passes (NOT rate limited), False if rate limited
    """
    rate_limit_indicators = [
        'rate limit',
        'too many requests',
        'temporarily blocked',
        'please try again later',
        'exceeded the rate limit',
        'slow down'
    ]
    
    content_lower = html_content.lower()
    for indicator in rate_limit_indicators:
        if indicator in content_lower:
            return False
    
    return True