"""Extract judges from HTML."""

from bs4 import BeautifulSoup
from typing import Optional


def extract(soup: BeautifulSoup) -> Optional[str]:
    """
    Extract judges from bout page HTML.

    Args:
        soup: BeautifulSoup object of the bout page

    Returns:
        str: judges data or None if not found
    """
    judges = []

    # Find the header cell that says "judges"
    header_td = soup.find(
        lambda tag: tag.name == "td"
        and tag.find("b")
        and tag.find("b").get_text(strip=True).lower() == "judges"
    )
    if not header_td:
        return judges

    header_tr = header_td.find_parent("tr")
    header_table = header_tr.find_parent("table")
    if not header_table:
        return judges

    # Rows after the header (in the same table) contain judge links in the middle <td>
    rows = header_table.find_all("tr")
    try:
        start_idx = rows.index(header_tr) + 1
    except ValueError:
        start_idx = 0

    for tr in rows[start_idx:]:
        tds = tr.find_all("td")
        if len(tds) != 3:
            continue
        center_td = tds[1]
        a = center_td.find("a", href=True)
        if a and "/en/judge/" in a["href"]:
            judges.append({"link": a["href"], "name": a.get_text(strip=True)})

    return judges if judges else None
