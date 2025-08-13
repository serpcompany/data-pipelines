"""Extract boxer_b_side_age from HTML."""

import re
from bs4 import BeautifulSoup
from typing import Optional


def extract(soup: BeautifulSoup) -> Optional[str]:
    """
    Extract boxer_b_side_age from bout page HTML.

    Args:
        soup: BeautifulSoup object of the bout page

    Returns:
        str: boxer_b_side_age data or None if not found
    """
    age_td = soup.find("td", string=lambda s: s and s.strip().lower() == "age")
    if not age_td:
        return None
    row = age_td.find_parent("tr")
    tds = row.find_all("td")
    if len(tds) < 3:
        return None
    left_text = tds[2].get_text(strip=True)
    m = re.search(r"\d+", left_text)
    return int(m.group()) if m else None
