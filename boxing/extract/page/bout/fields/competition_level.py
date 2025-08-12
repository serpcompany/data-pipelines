"""Extract competition_level from HTML."""

from bs4 import BeautifulSoup
from typing import Optional


def extract(soup: BeautifulSoup) -> Optional[str]:
    """
    Extract competition_level from bout page HTML.

    Args:
        soup: BeautifulSoup object of the bout page

    Returns:
        str: competition_level data or None if not found
    """
    node = soup.select_one("div.sportDiv")
    if node:
        classes = set(node.get("class", []))
        if "box-pro" in classes or "box_pro" in classes:
            return "pro"
        if "box-am" in classes or "box_am" in classes:
            return "am"

        # Sometimes the text itself will read "Box-pro" / "Box-am"
        txt = node.get_text(" ", strip=True).lower()
        if "box-pro" in txt or "box pro" in txt:
            return "pro"
        if "box-am" in txt or "box am" in txt or "amateur" in txt:
            return "am"

    return None
