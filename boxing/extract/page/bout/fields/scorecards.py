"""Extract scorecards from HTML."""

from bs4 import BeautifulSoup
from typing import Optional


def extract(soup: BeautifulSoup) -> Optional[str]:
    """
    Extract scorecards from bout page HTML.

    Args:
        soup: BeautifulSoup object of the bout page

    Returns:
        str: scorecards data or None if not found
    """
    # Find the header row that has: [scorecard] [judges] [scorecard]
    header_tr = None
    for b in soup.find_all("b"):
        if b.get_text(strip=True).lower() == "judges":
            tr = b.find_parent("tr")
            if tr and tr.find(
                "b", string=lambda s: s and s.strip().lower() == "scorecard"
            ):
                header_tr = tr
                break

    if not header_tr:
        raise RuntimeError("Couldn't find the scorecards header row.")

    # Walk subsequent <tr> rows until the block ends.
    # We'll stop when we hit a row that doesn't contain a judge link.
    scorecards = []
    seen_any = False

    def to_int(text):
        # keep digits only (handles stray whitespace or non-digit chars)
        digits = "".join(ch for ch in text if ch.isdigit())
        return int(digits) if digits else None

    def clean(text: str) -> str:
        # collapse weird whitespace
        return " ".join(text.split())

    for row in header_tr.find_next_siblings("tr"):
        tds = row.find_all("td")
        if len(tds) < 3:
            continue

        left_score = to_int(tds[0].get_text(strip=True))
        right_score = to_int(tds[-1].get_text(strip=True))
        middle = tds[1]
        judge_link = middle.find("a", href=lambda h: h and "/en/judge/" in h)
        judge_name = (
            clean(judge_link.get_text(strip=True))
            if judge_link
            else clean(middle.get_text(strip=True))
        )

        # Decide if this row "looks like" a scorecard row
        if left_score is None or right_score is None or not judge_name:
            if seen_any:
                # we've already started collecting; this likely marks the end of the block
                break
            else:
                # ignore preamble junk
                continue

        scorecards.append(
            {
                "judge": judge_name,
                "boxer_a_score": left_score,
                "boxer_b_score": right_score,
            }
        )
        seen_any = True

    return scorecards if scorecards else None
