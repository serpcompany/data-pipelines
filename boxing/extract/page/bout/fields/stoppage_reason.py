"""Extract stoppage_reason from HTML."""

from bs4 import BeautifulSoup
from typing import Optional


def extract(soup: BeautifulSoup) -> Optional[str]:
    """
    Extract stoppage_reason from bout page HTML.

    Args:
        soup: BeautifulSoup object of the bout page

    Returns:
        str: stoppage_reason data or None if not found
    """
    reason = None

    # Try the main header table for a boutResult pill that has the unique inline centering style
    data_table = soup.select_one("div.page table.dataTable") or soup.select_one(
        "table.dataTable"
    )
    if data_table:
        tag = data_table.select_one('div.boutResult[style*="margin:0 auto"]')

        # Fallback: first boutResult whose parent td is the middle column (often width ~16% & centered)
        if not tag:
            for div in data_table.select("div.boutResult"):
                td = div.find_parent("td")
                if td and (
                    "16%" in (td.get("width") or "")
                    or "text-align:center" in (td.get("style") or "")
                ):
                    tag = div
                    break

        # Fallback: first boutResult in the header rows, excluding ones inside the small 'clearTable' blocks (last-6 lists)
        if not tag:
            for div in data_table.select("div.boutResult"):
                if not div.find_parent("table", {"class": "clearTable"}):
                    tag = div
                    break

        if tag:
            reason = tag.get_text(strip=True)

    if reason and reason.lower() in ["w", "l", "d", "ud", "sd", "tko", "ko", "pko"]:
        # Normalize common single-letter results to full forms
        reason = {
            "w": None,
            "l": None,
            "d": None,
            "ud": "unanimous decision",
            "sd": "split decision",
            "tko": "technical knockout",
            "ko": "knockout",
            "pko": "technical knockout",
        }.get(reason.lower(), reason)

    return reason
