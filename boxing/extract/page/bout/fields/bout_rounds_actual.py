"""Extract bout_rounds_actual from HTML."""

import re
from bs4 import BeautifulSoup
from typing import Optional


def extract(soup: BeautifulSoup) -> Optional[int]:
    """
    Extract bout_rounds_actual from bout page HTML.

    Args:
        soup: BeautifulSoup object of the bout page

    Returns:
        str: bout_rounds_actual data or None if not found
    """
    # Try to read the explicit "round N" text in the result cell
    explicit = None
    for td in soup.find_all("td"):
        if td.find("div", class_="boutResult"):
            text = " ".join(td.stripped_strings)
            m = re.search(r"\bround\s+(\d+)\b", text, flags=re.I)
            if m:
                explicit = int(m.group(1))
                break
    return explicit
