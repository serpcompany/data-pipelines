"""Extract inspector from HTML."""

from bs4 import BeautifulSoup
from typing import Optional, List


def extract(soup: BeautifulSoup) -> Optional[str]:
    """
    Extract inspector from event page HTML.

    Args:
        soup: BeautifulSoup object of the event page

    Returns:
        str/List: inspector data or None if not found
    """
    label = soup.find("b", string=lambda s: s and s.strip().lower() == "inspector")
    if not label:
        return None

    td_label = label.find_parent("td")
    td_value = td_label.find_next_sibling("td") if td_label else None
    if not td_value:
        return None

    a = td_value.find("a", href=True)
    if not a:
        return None

    return {"link": a["href"], "name": a.get_text(strip=True)}
