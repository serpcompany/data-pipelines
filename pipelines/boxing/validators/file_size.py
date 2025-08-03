#!/usr/bin/env python3
"""
File size validator - checks if HTML file is too small to be valid content.
"""

def validate(html_content: str, min_size: int = 1000) -> bool:
    """
    Check if HTML content meets minimum size requirements.
    
    Args:
        html_content: HTML string content
        min_size: Minimum acceptable size in bytes (default: 1000)
        
    Returns:
        bool: True if file size is acceptable, False if too small
    """
    return len(html_content) >= min_size