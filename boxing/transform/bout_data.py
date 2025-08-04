#!/usr/bin/env python3
"""Transform bout data to ensure consistency."""

from typing import Optional
import re
import dateparser


def normalize_bout_date(date_str: str, base_year: Optional[int] = None) -> Optional[str]:
    """Normalize bout date to YYYY-MM-DD format using dateparser.
    
    Handles various formats including:
    - "Apr 02" (with base_year context)
    - "2024-04-02" 
    - "April 2, 2024"
    - "2/4/24"
    - etc.
    """
    if not date_str:
        return None
    
    date_str = date_str.strip()
    
    # Check if already in YYYY-MM-DD format
    if re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
        return date_str
    
    # Parse with dateparser
    settings = {
        'PREFER_DATES_FROM': 'past',
        'RETURN_AS_TIMEZONE_AWARE': False
    }
    
    # If we have a base year and the date has no year, add it
    if base_year and not re.search(r'\d{4}', date_str):
        # Try adding the year to help dateparser
        date_str_with_year = f"{date_str} {base_year}"
        parsed = dateparser.parse(date_str_with_year, settings=settings)
        if parsed:
            return parsed.strftime('%Y-%m-%d')
    
    # Try parsing as-is
    parsed = dateparser.parse(date_str, settings=settings)
    if parsed:
        return parsed.strftime('%Y-%m-%d')
    
    return None


def normalize_bout_result(result_str: str) -> Optional[str]:
    """Normalize bout result to standard format.
    
    Converts various result formats to standard:
    - "win", "won", "victory" -> "W"
    - "loss", "lost", "defeat" -> "L"
    - "draw", "tie" -> "D"
    - "no contest", "NC" -> "NC"
    - "technical draw", "TD" -> "TD"
    
    Args:
        result_str: The result string to normalize
    
    Returns:
        Normalized result (W/L/D/NC/TD) or None if invalid
    """
    if not result_str:
        return None
    
    result_lower = result_str.strip().lower()
    
    # Win variations
    if result_lower in ['win', 'won', 'victory', 'w']:
        return 'W'
    
    # Loss variations
    if result_lower in ['loss', 'lost', 'defeat', 'l']:
        return 'L'
    
    # Draw variations
    if result_lower in ['draw', 'tie', 'd', 'drawn']:
        return 'D'
    
    # No contest
    if result_lower in ['no contest', 'nc', 'no-contest']:
        return 'NC'
    
    # Technical draw
    if result_lower in ['technical draw', 'td', 'tech draw']:
        return 'TD'
    
    # If already in correct format
    if result_str.upper() in ['W', 'L', 'D', 'NC', 'TD']:
        return result_str.upper()
    
    # Unknown result
    return None