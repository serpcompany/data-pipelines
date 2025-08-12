"""Extract commission from HTML."""

from bs4 import BeautifulSoup
from typing import Optional


def extract(soup: BeautifulSoup) -> Optional[str]:
    """
    Extract commission from event page HTML.

    Args:
        soup: BeautifulSoup object of the event page

    Returns:
        str: Commission name or None if not found
    """
    label = soup.find("b", string=lambda s: s and s.strip().lower() == "commission")
    if not label:
        return None

    td_label = label.find_parent("td")
    td_value = td_label.find_next_sibling("td")
    return td_value.get_text(" ", strip=True)
