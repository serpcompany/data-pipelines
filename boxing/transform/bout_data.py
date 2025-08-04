#!/usr/bin/env python3
"""Transform bout data to ensure consistency."""

from datetime import datetime
from typing import Optional
import re
from dateutil import parser
from dateutil.relativedelta import relativedelta


def normalize_bout_date(date_str: str, base_year: Optional[int] = None) -> Optional[str]:
    """Normalize bout date from various formats to YYYY-MM-DD.
    
    Handles formats like:
    - "Apr 02" -> needs year context
    - "2024-04-02" -> already correct
    - "April 2, 2024" -> needs conversion
    - "2024.04.02" -> needs conversion
    
    Args:
        date_str: The date string to normalize
        base_year: The year to use for dates without year (e.g., boxer's career year)
    
    Returns:
        Normalized date in YYYY-MM-DD format or None if invalid
    """
    if not date_str or date_str.strip() == '':
        return None
    
    date_str = date_str.strip()
    
    # Already in correct format
    if re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
        return date_str
    
    # Try various date formats
    formats_with_year = [
        '%Y-%m-%d',      # 2024-04-02
        '%Y.%m.%d',      # 2024.04.02
        '%Y/%m/%d',      # 2024/04/02
        '%d/%m/%Y',      # 02/04/2024
        '%m/%d/%Y',      # 04/02/2024
        '%B %d, %Y',     # April 2, 2024
        '%b %d, %Y',     # Apr 2, 2024
        '%d %B %Y',      # 2 April 2024
        '%d %b %Y',      # 2 Apr 2024
    ]
    
    # Try formats with year first
    for fmt in formats_with_year:
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime('%Y-%m-%d')
        except ValueError:
            continue
    
    # Try formats without year (need base_year)
    if base_year:
        formats_without_year = [
            '%b %d',     # Apr 02
            '%B %d',     # April 02
            '%m/%d',     # 04/02
            '%d/%m',     # 02/04
        ]
        
        for fmt in formats_without_year:
            try:
                # Parse without year
                dt = datetime.strptime(date_str, fmt)
                # Add the base year
                dt = dt.replace(year=base_year)
                return dt.strftime('%Y-%m-%d')
            except ValueError:
                continue
    
    # If all parsing fails, return None
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