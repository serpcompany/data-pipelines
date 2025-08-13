"""Extract boxer_a_side_record from HTML."""

from bs4 import BeautifulSoup
from typing import Optional


def extract(soup: BeautifulSoup) -> Optional[str]:
    """
    Extract boxer_a_side_record from bout page HTML.

    Args:
        soup: BeautifulSoup object of the bout page

    Returns:
        str: boxer_a_side_record data or None if not found
    """
    # Find the row where the middle cell says "WLD"
    wld_cell = soup.find(
        "td", string=lambda s: isinstance(s, str) and s.strip() == "WLD"
    )
    if not wld_cell:
        raise ValueError("Couldn't find the WLD row in the page.")

    tr = wld_cell.find_parent("tr")
    tds = tr.find_all("td")
    if len(tds) < 3:
        raise ValueError("Unexpected table structure for the WLD row.")

    left_td = tds[0]

    def grab_num(cls):
        el = left_td.find("span", class_=cls)
        return (
            int(el.get_text(strip=True))
            if el and el.get_text(strip=True).isdigit()
            else 0
        )

    wins = grab_num("textWon")
    losses = grab_num("textLost")
    draws = grab_num("textDraw")

    return f"{wins}-{losses}-{draws}"
