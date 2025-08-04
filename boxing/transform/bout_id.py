#!/usr/bin/env python3
"""Transform bout IDs to ensure global uniqueness."""


def generate_unique_bout_id(boxer_id: str, bout_index: int) -> str:
    """Generate a globally unique bout ID.
    
    Simple and deterministic - just combine boxer ID with bout index.
    """
    # Remove leading zeros from boxer_id
    boxer_id = str(int(boxer_id)) if boxer_id.isdigit() else boxer_id
    return f"{boxer_id}_bout_{bout_index}"