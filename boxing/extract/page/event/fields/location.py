"""Extract event location from HTML."""

import re
import html as htmlmod
from bs4 import BeautifulSoup
from typing import Optional


def extract(soup: BeautifulSoup) -> Optional[str]:
    """
    Extract event location from event page HTML.

    Args:
        soup: BeautifulSoup object of the event page

    Returns:
        str: Event location or None if not found
    """
    # Event header block (cleanest source)
    header_b = soup.select_one("#eventResults thead td.noHeight b")
    if header_b:
        parts = [a.get_text(strip=True) for a in header_b.select("a")]
        if parts:
            return ", ".join(parts)

    # Fallback: parse the text inside the shareUrl() onclick (contains the same location)
    share_link = soup.select_one('.shareBox a[onclick*="shareUrl("]')
    if share_link and share_link.has_attr("onclick"):
        m = re.search(r"BoxRec Event: ([^']+)", share_link["onclick"])
        if m:
            return htmlmod.unescape(m.group(1).strip())

    return None
