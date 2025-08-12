"""Extract boxer_a_side_stance from HTML."""

from bs4 import BeautifulSoup
from typing import Optional


def extract(soup: BeautifulSoup) -> Optional[str]:
    """
    Extract boxer_a_side_stance from bout page HTML.

    Args:
        soup: BeautifulSoup object of the bout page

    Returns:
        str: boxer_a_side_stance data or None if not found
    """
    td = soup.find("td", string=lambda s: s and s.strip().lower() == "stance")
    if not td:
        return None
    row = td.find_parent("tr")
    tds = row.find_all("td")
    if len(tds) < 3:
        return None
    left_text = tds[0].get_text(strip=True)
    return left_text if left_text else None
