"""Extract boxer_b_side from HTML."""

import re
from bs4 import BeautifulSoup
from typing import Optional

BOXER_LINK_RE = re.compile(
    r"^(?:https?://(?:www\.)?boxrec\.com)?/en/box-(?:pro|am)/(\d+)(?:/|$)"
)


def extract(soup: BeautifulSoup) -> Optional[str]:
    """
    Extract boxer_b_side from bout page HTML.

    Args:
        soup: BeautifulSoup object of the bout page

    Returns:
        str: boxer_b_side data or None if not found
    """
    table = soup.select_one("table.dataTable")
    if not table:
        return None

    bout_tr = None
    for tr in table.find_all("tr"):
        if tr.select_one("div.boutResult"):
            bout_tr = tr
            break
    if not bout_tr:
        return None

    tds = bout_tr.find_all("td", recursive=False)
    if not tds:
        return None
    left_td = tds[2]

    a_tag = None
    for a in left_td.find_all("a", href=True):
        if BOXER_LINK_RE.search(a["href"]):
            a_tag = a
            break
    if not a_tag:
        return None

    m = BOXER_LINK_RE.search(a_tag["href"])
    if not m:
        return None

    return {"boxrecId": m.group(1), "name": a_tag.get_text(strip=True)}
