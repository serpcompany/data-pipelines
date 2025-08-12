"""Extract bout_division from HTML."""

import re
from bs4 import BeautifulSoup
from typing import Optional


def extract(soup: BeautifulSoup) -> Optional[str]:
    """
    Extract bout_division from bout page HTML.

    Args:
        soup: BeautifulSoup object of the bout page

    Returns:
        str: bout_division data or None if not found
    """
    # Find the cell that includes the sport tag (e.g., "Box-pro")
    sport_div = soup.select_one("div.sportDiv")
    if not sport_div:
        return None

    cell = sport_div.parent  # the <td> that contains division, rounds, and sport
    # Build a clean string without the sport label (Box-pro/Box-am/etc.)
    cleaned = " ".join(
        t for t in cell.stripped_strings if not t.lower().startswith("box-")
    )
    # Expect something like: "Heavy 12 Rounds"
    m = re.search(r"^(.*?)\s+\d+\s*Rounds?\b", cleaned, flags=re.I)
    return m.group(1).strip() if m else None
