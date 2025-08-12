"""Extract matchmaker from HTML."""

from bs4 import BeautifulSoup
from typing import Optional


def extract(soup: BeautifulSoup) -> Optional[str]:
    """
    Extract matchmaker from bout page HTML.

    Args:
        soup: BeautifulSoup object of the bout page

    Returns:
        str: matchmaker data or None if not found
    """
    role_row = None
    for tr in soup.find_all("tr"):
        b = tr.find("b")
        if b and b.get_text(strip=True).lower() == "matchmaker":
            role_row = tr
            break

    people = []
    if role_row:
        tds = role_row.find_all("td")
        if len(tds) >= 2:
            for a in tds[1].find_all("a", href=True):
                name = a.get_text(strip=True)
                link = a["href"]
                if name:
                    people.append({"link": link, "name": name})
        if not people:
            td_with_b = b.find_parent("td")
            next_td = td_with_b.find_next_sibling("td") if td_with_b else None

            # fallback for weird nesting/colspans: use the nearest <tr> that actually holds the label/value pair
            if not next_td:
                inner_tr = b.find_parent(
                    "tr"
                )  # this is the <tr> inside the nested table if present
                if inner_tr:
                    # only direct children to avoid re-grabbing nested tds
                    tds = inner_tr.find_all("td", recursive=False)
                    # find the td that contains our <b> and take the following td
                    for i, td in enumerate(tds):
                        if td.find(
                            "b",
                            string=lambda s: s and s.strip().lower() == "matchmaker",
                        ):
                            if i + 1 < len(tds):
                                next_td = tds[i + 1]
                            break

            if next_td:
                for a in next_td.find_all("a", href=True):
                    name = a.get_text(strip=True)
                    link = a["href"]
                    if name:
                        people.append({"link": link, "name": name})
    return people if people else None
