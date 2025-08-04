#!/usr/bin/env python3
"""Transform bout data to ensure consistency."""

from typing import Optional
import re


def normalize_bout_date(date_str: str) -> Optional[str]:
    """Normalize bout date to YYYY-MM-DD format.
    
    For now, just return dates that are already in the correct format.
    TODO: Use dateparser library for complex date parsing.
    """
    if not date_str:
        return None
    
    # Check if already in YYYY-MM-DD format
    if re.match(r'^\d{4}-\d{2}-\d{2}$', date_str.strip()):
        return date_str.strip()
    
    # For now, return None for dates that need parsing
    # This will be fixed when we add dateparser
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