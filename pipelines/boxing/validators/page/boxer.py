#!/usr/bin/env python3
"""
Boxer page validator - validates boxer profile pages have expected content.
"""

def validate(html_content: str) -> bool:
    """
    Check if HTML content has expected boxer page elements.
    
    Args:
        html_content: HTML string content
        
    Returns:
        bool: True if page has boxer content, False otherwise
    """
    # Must have at least one of these key elements
    required_elements = [
        'class="profileTable"',
        'class=\'profileTable\'',
        'class="dataTable"',
        'class=\'dataTable\'',
        'class="boutList"',
        'class=\'boutList\'',
        'class="profileWLD"',  # Win/Loss/Draw stats
        'class=\'profileWLD\''
    ]
    
    for element in required_elements:
        if element in html_content:
            return True
    
    return False