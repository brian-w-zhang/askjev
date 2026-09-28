"""How honest are people in each profession? Gallup's Honesty and Ethics poll (research pass 2, idea 24).

Human data: Gallup's annual "Honesty/Ethics in Professions" toplines (news.gallup.com/poll/1654), scraped from the
published page: the share of US adults rating each profession's honesty and ethical standards very high, high,
average, low or very low, for the latest poll (December 2025) and each earlier year a profession was asked.
Politicians and roles tied to politics or religion are left out (members of Congress, journalists, police officers,
clergy, labor union leaders), per the project's no-politics rule. Two sets: the current rating as Gallup asked it
(the five answers, "no opinion" dropped and the rest renormalized), and the share rating a profession high or very
high in a given earlier year (5% bins, the truth from the trend table).
"""

from __future__ import annotations

import html
import re
import urllib.request
from pathlib import Path
from typing import Iterator

from askjev.model import HumanDist, Question

NAME = "gallup_honesty"
NODE = "world.money.careers.profession_honesty"
LICENSE = "Gallup toplines (news.gallup.com), used with attribution for non-commercial research"
URL = "https://news.gallup.com/poll/1654/honesty-ethics-professions.aspx"
FILE = "honesty-ethics-professions.html"
DROP = {"Members of Congress", "Journalists", "Police officers", "Clergy", "Labor union leaders"}
LEVELS = ["Very low honesty and ethical standards", "Low honesty and ethical standards",
          "Average honesty and ethical standards", "High honesty and ethical standards",
          "Very high honesty and ethical standards"]
PCT = {f"p{v:03d}": f"{v}%" for v in range(0, 101, 5)}
YEARS = [2000, 2005, 2010, 2015, 2020]
MONTHS = {m: i for i, m in enumerate(["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], 1)}


def fetch(raw_dir: Path) -> None:
    if not (raw_dir / FILE).exists():
        req = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0"})
        (raw_dir / FILE).write_bytes(urllib.request.urlopen(req).read())


def _num(s: str) -> float:
    return 0.0 if s.strip() == "*" else float(s)


def parse(raw_dir: Path) -> tuple[dict, dict]:
    """(current, history): current = {profession: [vh, h, avg, low, vlow, no_opinion]} from the latest table;
    history = {profession: [(poll label, year, [vh, h, avg, low, vlow, no], vh+h), ...]}."""
    s = (raw_dir / FILE).read_text(encoding="utf-8", errors="ignore")
    t = html.unescape(re.sub(r"<[^>]+>", " | ", s))
    t = re.sub(r"(\s*\|\s*)+", " | ", t)
    cur_block = t.split("Ethical Standards Table |", 1)[1].split('" scrolling', 1)[0]
    cur = {}
    for m in re.finditer(r"\| ([A-Z][A-Za-z .'-]+?) \| ([\d*]+) \| ([\d*]+) \| ([\d*]+) \| ([\d*]+) \| ([\d*]+) \| ([\d*]+)", cur_block):
        cur[m.group(1).strip()] = [_num(m.group(i)) for i in range(2, 8)]
    hist = {}
    for block in t.split("Honesty/Ethics in Professions > ")[1:]:
        name, rest = block.split(" |", 1)
        name = name.strip()
        if name == "Ethical Standards Table":
            continue
        rows = []
        for m in re.finditer(r"\| ((\d{4}) ([A-Z][a-z]{2})[^|]*?) \| ([\d*]+) \| ([\d*]+) \| ([\d*]+) \| ([\d*]+) \| ([\d*]+) \| ([\d*]+) \| ([\d*]+)",
                             rest.split('" scrolling', 1)[0]):
            rows.append((m.group(1).strip(), int(m.group(2)), [_num(m.group(i)) for i in range(4, 10)], _num(m.group(10))))
        hist[name] = rows
    return cur, hist


def _pct_key(v: float) -> str:
    return f"p{min(100, max(0, int(5 * round(v / 5)))):03d}"


def normalize(raw_dir: Path) -> Iterator[Question]:
    cur, hist = parse(raw_dir)
    for prof, vals in cur.items():
        if prof in DROP:
            continue
        rated = vals[:5]
        tot = sum(rated) or 1
        dist = {str(4 - i): v / tot for i, v in enumerate(rated)}  # Gallup lists very high first; levels run low to high
        yield Question(
            text=f"How would you rate the honesty and ethical standards of people in this field: {prof.lower()}?",
            human_text=f"How would most Americans rate the honesty and ethical standards of people in this field: {prof.lower()}?",
            primitive="score", hemisphere="world", kind="evaluative", origin="dataset", source=NAME, options=LEVELS,
            node_hint=NODE, license=LICENSE, source_item_id=f"current:{prof}",
            human=[HumanDist(population="US adults (Gallup, December 2025)", distribution=dict(sorted(dist.items())),
                             n=None, source="Gallup Honesty/Ethics in Professions, Dec 1-15 2025; 'no opinion' dropped")],
            meta={"experiment": "profession_honesty", "set": "current", "profession": prof, "high_share": rated[0] + rated[1]})
    by_name = {k.lower(): v for k, v in hist.items()}
    for prof in cur:
        if prof in DROP:
            continue
        rows = by_name.get(prof.lower(), [])
        for y in YEARS:
            near = sorted((r for r in rows if abs(r[1] - y) <= 1), key=lambda r: (abs(r[1] - y), -r[1]))
            if not near:
                continue
            label, year, _, high = near[0]
            month = label.split()[1]
            yield Question(
                text=f"In Gallup's poll of {month} {year}, what share of Americans rated the honesty and ethical standards "
                     f"of {prof.lower()} as \"very high\" or \"high\"?",
                primitive="choice", hemisphere="world", kind="factual", origin="dataset", source=NAME, options=PCT,
                node_hint=NODE, license=LICENSE, source_item_id=f"history:{prof}:{label}", truth=_pct_key(high),
                meta={"experiment": "profession_honesty", "set": "history", "profession": prof, "year": year,
                      "poll": label, "high_share": high, "ordered": True})
