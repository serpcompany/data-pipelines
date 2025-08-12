"""Extract titles from HTML."""

from bs4 import BeautifulSoup
from typing import Optional


def extract(soup: BeautifulSoup) -> Optional[str]:
    """
    Extract titles from bout page HTML.

    Args:
        soup: BeautifulSoup object of the bout page

    Returns:
        str: titles data or None if not found
    """
    return [
        a.get_text(" ", strip=True) for a in soup.select("div.titleColor a.titleLink")
    ]
