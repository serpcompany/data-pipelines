"""Extract event name from HTML."""

from bs4 import BeautifulSoup
from typing import Optional


def extract(soup: BeautifulSoup) -> Optional[str]:
    """
    Extract event name from event page HTML.

    Args:
        soup: BeautifulSoup object of the event page

    Returns:
        str: Event name or None if not found
    """
    # Try the canonical URL and find the matching anchor (most reliable)
    canonical = soup.find("link", rel="canonical")
    if canonical and canonical.get("href"):
        a = soup.find("a", href=canonical["href"])
        if a and a.get_text(strip=True):
            return a.get_text(strip=True)

    # Fallback: the header block near the top of the page
    header_a = soup.select_one(
        'div.page > div[style*="text-align:left"] a[href*="/en/event/"]'
    )
    if header_a and header_a.get_text(strip=True):
        return header_a.get_text(strip=True)

    return None
