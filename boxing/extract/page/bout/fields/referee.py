"""Extract referee from HTML."""

from bs4 import BeautifulSoup
from typing import Optional


def extract(soup: BeautifulSoup) -> Optional[str]:
    """
    Extract referee from bout page HTML.

    Args:
        soup: BeautifulSoup object of the bout page

    Returns:
        str: referee data or None if not found
    """
    label = soup.find(
        lambda tag: tag.name in ("b", "strong")
        and tag.get_text(strip=True).lower() == "referee"
    )
    if not label:
        return None

    # The next <tr> after the "referee" header contains the data
    header_tr = label.find_parent("tr")
    data_tr = header_tr.find_next_sibling("tr") if header_tr else None
    if not data_tr:
        return None

    a = data_tr.find("a", href=True)
    if not a:
        return None

    return {"name": a.get_text(strip=True), "link": a["href"]}
