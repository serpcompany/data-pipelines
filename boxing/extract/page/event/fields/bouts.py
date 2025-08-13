"""Extract bouts from HTML."""

import re
from bs4 import BeautifulSoup
from typing import Optional, List

RESULT_MAP = {
    "W": "win",
    "L": "loss",
    "D": "draw",
    "NC": "no-contest",
}


def _text(el, sep: str = " "):
    """
    Robust get_text across bs4 versions:
    - Newer bs4 accepts sep=
    - Older bs4 expects separator=
    """
    if not el:
        return ""
    try:
        return el.get_text(sep=sep, strip=True)
    except TypeError:
        # Older BeautifulSoup versions use 'separator' kw instead of 'sep'
        try:
            return el.get_text(separator=sep, strip=True)
        except TypeError:
            # Worst case: fall back to default and strip manually
            return (el.get_text() or "").strip()


def _parse_person(cell):
    """Return {name, id, url} for a <td> with an <a class='personLink'>."""
    out = {"name": "", "id": None, "url": None}
    if not cell:
        return out
    a = cell.find("a", class_="personLink")
    if a:
        name = _text(a).rstrip("*")  # names sometimes have a trailing *
        out["name"] = name
        href = a.get("href", "")
        out["url"] = (
            f"https://boxrec.com{href}" if href.startswith("/") else href or None
        )
        m = re.search(r"/box-pro/(\d+)", href)
        if m:
            out["id"] = m.group(1)
    else:
        out["name"] = _text(cell).rstrip("*")
    return out


def _parse_record(cell):
    """Return 'W-L-D' from the record cell."""
    if not cell:
        return None
    wins = cell.find("span", class_="textWon")
    losses = cell.find("span", class_="textLost")
    draws = cell.find("span", class_="textDraw")
    if wins and losses and draws:
        return f"{_text(wins)}-{_text(losses)}-{_text(draws)}"
    return None


def _parse_form(cell):
    """Return recent form string like 'WWLWDX' based on l6w/l6l/l6d/l6x svgs."""
    if not cell:
        return None
    out = []
    for img in cell.find_all("img"):
        src = img.get("src", "")
        if "l6w" in src:
            out.append("W")
        elif "l6l" in src:
            out.append("L")
        elif "l6d" in src:
            out.append("D")
        elif "l6x" in src:
            out.append("X")
    return "".join(out) if out else None


def _parse_result(cell):
    """
    Return dict with:
      code (e.g., 'W-KO' or 'W'), outcome ('win'/'loss'/'draw'/'no-contest'),
      method ('ko','tko','decision','dq','rtd','pts','nc', or raw),
      winner_side ('a'/'b'/None)
    """
    out = {"code": None, "outcome": None, "method": None, "winner_side": None}
    if not cell:
        return out
    div = cell.find("div", class_=re.compile(r"\bboutResult\b"))
    if not div:
        return out
    code = _text(div)  # e.g., "W-UD", "L-UD", "W-KO", or just "W"
    out["code"] = code
    parts = code.split("-", 1)
    side = parts[0] if parts else ""
    meth = parts[1].upper() if len(parts) > 1 else ""

    # winner side based on left fighter perspective
    if side == "W":
        out["winner_side"] = "a"
    elif side == "L":
        out["winner_side"] = "b"
    elif side == "D":
        out["winner_side"] = None

    # normalize outcome/method
    out["outcome"] = RESULT_MAP.get(side, None)
    if meth in ("KO",):
        out["method"] = "ko"
    elif meth in ("TKO",):
        out["method"] = "tko"
    elif meth in ("UD", "MD", "SD", "DEC"):
        out["method"] = "decision"
    elif meth in ("PTS",):
        out["method"] = "pts"  # points (often equivalent to decision)
    elif meth in ("DQ",):
        out["method"] = "dq"
    elif meth in ("RTD",):
        out["method"] = "rtd"
    elif meth in ("NC",):
        out["method"] = "nc"
    else:
        out["method"] = meth.lower() if meth else None

    return out


def _parse_rounds(cell):
    """Return ended_round, scheduled_rounds from '5/12' style text."""
    if not cell:
        return None, None
    txt = _text(cell)
    m = re.match(r"(\d+)\s*/\s*(\d+)", txt)
    if m:
        return int(m.group(1)), int(m.group(2))
    # fallback: if only a number like '10/10' is not matched due to whitespace weirdness
    nums = re.findall(r"\d+", txt)
    if len(nums) == 2:
        return int(nums[0]), int(nums[1])
    return None, None


def _parse_gender(cell):
    if not cell:
        return None
    if cell.find("i", class_=re.compile(r"fa-venus")):
        return "female"
    if cell.find("i", class_=re.compile(r"fa-mars")):
        return "male"
    return None


def _parse_rating(cell):
    if not cell:
        return None
    return len(cell.select("i.fas.fa-star"))


def _parse_links(action_cell, bout_id=None):
    """Return dict of scorecard/wiki/bout URLs + ids if present."""
    out = {
        "scorecard_url": None,
        "wiki_url": None,
        "bout_url": None,
        "bout_id": bout_id,
    }
    if not action_cell:
        return out
    a_score = action_cell.find("a", href=re.compile(r"/en/scoring/\d+"))
    if a_score:
        href = a_score["href"]
        out["scorecard_url"] = f"https://boxrec.com{href}"
    a_wiki = action_cell.find("a", href=re.compile(r"/wiki/"))
    if a_wiki:
        href = a_wiki["href"]
        out["wiki_url"] = f"https://boxrec.com{href}"
    a_bout = action_cell.find("a", href=re.compile(r"/en/event/\d+/\d+"))
    if a_bout:
        href = a_bout["href"]
        out["bout_url"] = f"https://boxrec.com{href}"
        m = re.search(r"/en/event/\d+/(\d+)", href)
        if m:
            out["bout_id"] = m.group(1)
    return out


def _parse_officials_and_extras(sr_tr):
    """Parse time/ref/judges/titles/notes from the second row."""
    out = {
        "end_time": None,
        "referee": None,  # {name,id,url}
        "judges": [],  # [{name,id,url,score}]
        "titles": [],  # [{name,id,url,supervisor:{name,id,url}}]
        "notes": None,
    }
    if not sr_tr:
        return out

    td = sr_tr.find("td")
    if not td:
        return out

    whole_text = td.get_text(" ", strip=True)

    # time 1:52 etc
    tm = re.search(r"\b(\d{1,2}:\d{2})\b", whole_text)
    if tm:
        out["end_time"] = tm.group(1)

    # referee
    a_ref = td.find("a", href=re.compile(r"/en/referee/\d+"))
    if a_ref:
        href = a_ref["href"]
        m = re.search(r"/referee/(\d+)", href)
        out["referee"] = {
            "name": _text(a_ref),
            "id": m.group(1) if m else None,
            "url": f"https://boxrec.com{href}",
        }

    # judges and scores
    for a in td.find_all("a", href=re.compile(r"/en/judge/\d+")):
        href = a["href"]
        m = re.search(r"/judge/(\d+)", href)
        # score is typically the text node right after the anchor, like " 39-37"
        score = ""
        sib = a.next_sibling
        if sib and isinstance(sib, str):
            score = sib.strip()
        # If not found, try to fish a "number-number" right after in the TD text
        if not score:
            after = td.get_text()[td.get_text().find(a.get_text()) :]
            ms = re.search(r"\b(\d{1,3}\s*-\s*\d{1,3})\b", after)
            score = ms.group(1) if ms else ""
        out["judges"].append(
            {
                "name": _text(a),
                "id": m.group(1) if m else None,
                "url": f"https://boxrec.com{href}",
                "score": score or None,
            }
        )

    # titles
    title_div = td.find("div", class_=re.compile(r"titleColor"))
    if title_div:
        for a_t in title_div.find_all("a", href=re.compile(r"/en/title/\d+")):
            t_href = a_t["href"]
            t_idm = re.search(r"/title/(\d+)/", t_href)
            # supervisor: next <a> with /supervisor/ under the same 'line'
            sup_a = a_t.find_next("a", href=re.compile(r"/en/supervisor/\d+"))
            sup = None
            if sup_a:
                s_href = sup_a["href"]
                s_idm = re.search(r"/supervisor/(\d+)", s_href)
                sup = {
                    "name": _text(sup_a),
                    "id": s_idm.group(1) if s_idm else None,
                    "url": f"https://boxrec.com{s_href}",
                }
            out["titles"].append(
                {
                    "name": _text(a_t),
                    "id": t_idm.group(1) if t_idm else None,
                    "url": f"https://boxrec.com{t_href}",
                    "supervisor": sup,
                }
            )

    # notes
    note_divs = [
        d
        for d in td.find_all("div")
        if not d.get("class") or "titleColor" not in " ".join(d.get("class"))
    ]
    if note_divs:
        candidate = _text(note_divs[-1])
        out["notes"] = candidate or None

    return out


def extract(soup: BeautifulSoup) -> List[dict]:
    """
    Extract bouts from event page HTML.

    Args:
        soup: BeautifulSoup object of the event page

    Returns:
        List[dict]: parsed bouts
    """
    bouts = []

    table = soup.find("table", id="eventResults")
    if not table:
        return bouts

    # Each bout is contained in its own <tbody id="bId{boutId}">
    for tb in table.find_all("tbody", id=re.compile(r"^bId\d+")):
        main_tr = tb.find("tr", id=re.compile(r"^\d+$")) or tb.find("tr")
        if not main_tr:
            continue
        cells = main_tr.find_all("td")

        # Accept both the "wide" layout with 15+ tds and the "compact" layout with ~12 tds
        layout = "wide" if len(cells) >= 15 else "compact" if len(cells) >= 12 else None
        if layout is None:
            # unknown/unsupported layout; skip safely
            continue

        # primary identifiers
        bout_id = main_tr.get("id")
        sr_tr = tb.find("tr", id=re.compile(r"^second"))

        if layout == "wide":
            # Old / wide layout (weights + rounds columns present)
            a_person = _parse_person(cells[0])
            a_weight = _text(cells[1]) or None
            a_record = _parse_record(cells[2])
            a_form = _parse_form(cells[3])

            result = _parse_result(cells[4])
            ended_round, scheduled_rounds = _parse_rounds(cells[5])

            b_person = _parse_person(cells[6])
            b_weight = _text(cells[7]) or None
            b_record = _parse_record(cells[8])
            b_form = _parse_form(cells[9])

            sport = _text(cells[10]) or None
            gender = _parse_gender(cells[11])
            weight_class = _text(cells[12]) or None
            rating = _parse_rating(cells[13])

            links = _parse_links(cells[14], bout_id=bout_id)

        else:
            # New / compact layout (no explicit weights/rounds columns)
            a_person = _parse_person(cells[0])
            a_weight = None
            a_record = _parse_record(cells[1])
            a_form = _parse_form(cells[2])

            result = _parse_result(cells[3])
            ended_round, scheduled_rounds = (None, None)

            b_person = _parse_person(cells[4])
            b_weight = None
            b_record = _parse_record(cells[5])
            b_form = _parse_form(cells[6])

            sport = _text(cells[7]) or None
            gender = _parse_gender(cells[8])
            weight_class = _text(cells[9]) or None
            rating = _parse_rating(cells[10])

            links = _parse_links(cells[11], bout_id=bout_id)

        # officials + extras from second row
        extras = _parse_officials_and_extras(sr_tr)

        # compute winner/loser names/ids
        winner = loser = None
        person_a_winner = person_b_winner = None
        if result["winner_side"] == "a":
            winner = a_person
            loser = b_person
            person_a_winner = True
            person_b_winner = False
        elif result["winner_side"] == "b":
            winner = b_person
            loser = a_person
            person_a_winner = False
            person_b_winner = True

        bout_obj = {
            "bout_id": links.get("bout_id") or bout_id,
            "sport": sport,
            "gender": gender,
            "weight_class": weight_class,
            "rating": rating,
            "ended_round": ended_round,
            "scheduled_rounds": scheduled_rounds,
            "end_time": extras.get("end_time"),
            "result_code": result["code"],
            "outcome": result["outcome"],
            "method": result["method"],
            "winner": winner,
            "loser": loser,
            "a_side": {
                "name": a_person["name"],
                "id": a_person["id"],
                "url": a_person["url"],
                "weight": a_weight,
                "record": a_record,
                "recent_form": a_form,
                "is_winner": person_a_winner,
            },
            "b_side": {
                "name": b_person["name"],
                "id": b_person["id"],
                "url": b_person["url"],
                "weight": b_weight,
                "record": b_record,
                "recent_form": b_form,
                "is_winner": person_b_winner,
            },
            "referee": extras.get("referee"),
            "judges": extras.get("judges"),
            "titles": extras.get("titles"),
            "notes": extras.get("notes"),
            "links": {
                "scorecard": links.get("scorecard_url"),
                "wiki": links.get("wiki_url"),
                "bout": links.get("bout_url"),
            },
        }

        bouts.append(bout_obj)

    return bouts
