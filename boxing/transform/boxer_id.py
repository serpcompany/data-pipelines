#!/usr/bin/env python3
"""Transform boxer IDs to ensure consistency."""

from typing import Optional


def normalize_boxer_id(boxer_id: str) -> str:
    """Normalize boxer ID by removing leading zeros.
    
    BoxRec uses numeric IDs but sometimes includes leading zeros.
    We standardize by converting to int and back to string.
    
    Examples:
        '000080' -> '80'
        '001491' -> '1491'
        '272717' -> '272717'
        '000' -> '0'
    """
    if not boxer_id or not boxer_id.isdigit():
        return boxer_id
    
    # Convert to int to remove leading zeros, then back to string
    return str(int(boxer_id))