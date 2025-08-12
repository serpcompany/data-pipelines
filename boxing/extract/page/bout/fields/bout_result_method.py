"""Extract bout_result_method from HTML."""

from bs4 import BeautifulSoup
from typing import Optional


def extract(soup: BeautifulSoup) -> Optional[str]:
    """
    Extract bout_result_method from bout page HTML.

    Args:
        soup: BeautifulSoup object of the bout page

    Returns:
        str: bout_result_method data or None if not found
    """
    # Look for the center TD that contains the main bout result and the "round" text
    for td in soup.select("table.dataTable td"):
        badge = td.select_one("div.boutResult")
        if badge and "round" in td.get_text(strip=True).lower():
            return badge.get_text(strip=True)
    return None
