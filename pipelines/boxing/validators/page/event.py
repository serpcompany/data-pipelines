#!/usr/bin/env python3
"""
Event page validator - validates event pages have expected content.
"""

def validate(html_content: str) -> bool:
    """
    Check if HTML content has expected event page elements.
    
    Args:
        html_content: HTML string content
        
    Returns:
        bool: True if page has event content, False otherwise
    """
    # Must have at least one of these key elements
    required_elements = [
        'class="eventTable"',
        'class=\'eventTable\'',
        'class="eventDetails"',
        'class=\'eventDetails\'',
        'class="fightCard"',
        'class=\'fightCard\'',
        '/event/'
    ]
    
    for element in required_elements:
        if element in html_content:
            return True
    
    return False