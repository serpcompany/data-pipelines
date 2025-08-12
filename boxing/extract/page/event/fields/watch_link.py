"""Extract watch_link from HTML."""

from urllib.parse import unquote
from bs4 import BeautifulSoup
from typing import Optional, List


def extract(soup: BeautifulSoup) -> Optional[str]:
    """
    Extract watch_link from event page HTML.

    Args:
        soup: BeautifulSoup object of the event page

    Returns:
        str/List: watch_link data or None if not found
    """
    watch_link = None

    # Anchor immediately following the TV icon
    tv_icon = soup.select_one("i.fa-tv")
    if tv_icon:
        a = tv_icon.find_next("a", href=True)
        if a:
            watch_link = a["href"]

    # Fallback: any anchor whose visible text contains "view on"
    if not watch_link:
        for a in soup.select("a[href]"):
            if "view on" in a.get_text(strip=True).lower():
                watch_link = a["href"]
                break

    # If it's an affiliate link with an embedded "destination:", decode the real target
    if watch_link and "destination:" in watch_link:
        watch_link = unquote(watch_link.split("destination:")[-1])

    return watch_link
