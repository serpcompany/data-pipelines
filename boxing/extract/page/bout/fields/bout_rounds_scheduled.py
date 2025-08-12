"""Extract bout_rounds_scheduled from HTML."""

import re
from bs4 import BeautifulSoup
from typing import Optional


def extract(soup: BeautifulSoup) -> Optional[str]:
    """
    Extract bout_rounds_scheduled from bout page HTML.

    Args:
        soup: BeautifulSoup object of the bout page

    Returns:
        str: bout_rounds_scheduled data or None if not found
    """
    # Scheduled rounds (e.g., "Heavy 12 Rounds")
    scheduled = None
    for s in soup.stripped_strings:
        m = re.search(r"\b(\d+)\s*Rounds\b", s, flags=re.I)
        if m:
            scheduled = int(m.group(1))
            break

    return scheduled
