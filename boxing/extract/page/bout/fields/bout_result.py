"""Extract bout_result from HTML."""

import re
from bs4 import BeautifulSoup
from typing import Optional


def extract(soup: BeautifulSoup) -> Optional[str]:
    """
    Extract bout_result from bout page HTML.

    Args:
        soup: BeautifulSoup object of the bout page

    Returns:
        str: bout_result data or None if not found
    """
    badge = soup.select_one("table.dataTable div.boutResult")
    if badge:
        cls = set(badge.get("class", []))
        class_map = {
            "bgW": "win",
            "bgL": "loss",
            "bgD": "draw",
            "bgNC": "no-contest",
            "bgN": "no-contest",
        }
        for k, v in class_map.items():
            if k in cls:
                return v

        text = badge.get_text(strip=True).upper()
        if "NO CONTEST" in text or re.search(r"\bNC\b", text):
            return "no-contest"
        if "DRAW" in text:
            return "draw"

    return None
