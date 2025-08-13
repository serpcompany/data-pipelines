"""Extract boxer_b_side_rating from HTML."""

import re
from bs4 import BeautifulSoup
from typing import Optional


def extract(soup: BeautifulSoup) -> Optional[str]:
    """
    Extract boxer_b_side_rating from bout page HTML.

    Args:
        soup: BeautifulSoup object of the bout page

    Returns:
        str: boxer_b_side_rating data or None if not found
    """
    td = soup.find("td", string=lambda s: s and s.strip().lower() == "rating")
    if not td:
        return None
    row = td.find_parent("tr")
    tds = row.find_all("td")
    if len(tds) < 3:
        return None
    left_text = tds[2].get_text(strip=True)
    m = re.search(r"\d+", left_text)
    return int(m.group()) if m else None
