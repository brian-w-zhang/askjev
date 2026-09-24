"""Open Extended Jungian Type Scales (Open Psychometrics, CC BY-NC-SA 4.0): bipolar "which describes
you better?" pairs. The 32 scored items of OEJTS 1.2, plus the screened items from the development page's
Appendix A that discriminate strongly on exactly one dichotomy."""

from __future__ import annotations

import html
import re
from pathlib import Path
from typing import Iterator

import httpx

from askjev.model import Question

NAME = "oejts"
LICENSE = "CC BY-NC-SA 4.0 (Open Psychometrics, OEJTS)"
DEV_URL = "https://openpsychometrics.org/tests/OJTS/development/"
PDF_URL = "https://openpsychometrics.org/tests/OJTS/development/OEJTS1.2.pdf"

# Appendix A selection: largest mean-level difference >= STRONG on one dichotomy, all others < WEAK.
STRONG, WEAK = 0.9, 0.5

DICHOTOMY = {"IE": ("I", "E", "ei"), "SN": ("S", "N", "sn"), "FT": ("F", "T", "tf"), "JP": ("J", "P", "jp")}

# OEJTS 1.2 (OEJTS1.2.pdf): item, left pole, right pole, dichotomy, sign in the scoring equation.
# "+" means the right pole is the high letter (E, N, T, P); "-" means it is the low letter (I, S, F, J).
V12 = [
    ("Q1", "makes lists", "relies on memory", "JP", "+"),
    ("Q2", "sceptical", "wants to believe", "FT", "-"),
    ("Q3", "bored by time alone", "needs time alone", "IE", "-"),
    ("Q4", "accepts things as they are", "unsatisfied with the ways things are", "SN", "+"),
    ("Q5", "keeps a clean room", "just puts stuff where ever", "JP", "+"),
    ("Q6", 'thinks "robotic" is an insult', "strives to have a mechanical mind", "FT", "+"),
    ("Q7", "energetic", "mellow", "IE", "-"),
    ("Q8", "prefer to take multiple choice test", "prefer essay answers", "SN", "+"),
    ("Q9", "chaotic", "organized", "JP", "-"),
    ("Q10", "easily hurt", "thick-skinned", "FT", "+"),
    ("Q11", "works best in groups", "works best alone", "IE", "-"),
    ("Q12", "focused on the present", "focused on the future", "SN", "+"),
    ("Q13", "plans far ahead", "plans at the last minute", "JP", "+"),
    ("Q14", "wants people's respect", "wants their love", "FT", "-"),
    ("Q15", "gets worn out by parties", "gets fired up by parties", "IE", "+"),
    ("Q16", "fits in", "stands out", "SN", "+"),
    ("Q17", "keeps options open", "commits", "JP", "-"),
    ("Q18", "wants to be good at fixing things", "wants to be good at fixing people", "FT", "-"),
    ("Q19", "talks more", "listens more", "IE", "-"),
    ("Q20", "when describing an event, will tell people what happened",
     "when describing an event, will tell people what it meant", "SN", "+"),
    ("Q21", "gets work done right away", "procrastinates", "JP", "+"),
    ("Q22", "follows the heart", "follows the head", "FT", "+"),
    ("Q23", "stays at home", "goes out on the town", "IE", "+"),
    ("Q24", "wants the big picture", "wants the details", "SN", "-"),
    ("Q25", "improvises", "prepares", "JP", "-"),
    ("Q26", "bases morality on justice", "bases morality on compassion", "FT", "-"),
    ("Q27", "finds it difficult to yell very loudly",
     "yelling to others when they are far away comes naturally", "IE", "+"),
    ("Q28", "theoretical", "empirical", "SN", "-"),
    ("Q29", "works hard", "plays hard", "JP", "+"),
    ("Q30", "uncomfortable with emotions", "values emotions", "FT", "-"),
    ("Q31", "likes to perform in front of other people", "avoids public speaking", "IE", "-"),
    ("Q32", 'likes to know "who?", "what?", "when?"', 'likes to know "why?"', "SN", "+"),
]

# Poles that are not standalone or have typos in Appendix A.
POLE_FIX = {
    "loves it": "loves being photographed",
    "sees the glass as glass half full": "sees the glass as half full",
    "sees it as half empty": "sees the glass as half empty",
    "has a system so that does not happen": "has a system so they never misplace their keys",
    "gives complements": "gives compliments",
    "tell it straight up": "tells it straight up",
    "keep room door closed": "keeps their room door closed",
    "leaves door open": "leaves their room door open",
    "like to listen to stories": "likes to listen to stories",
    "rather be first mate": "prefers to be first mate",
}
# Readable keys where the automatic ones would be unclear.
KEY_FIX = {
    'likes to know "who?", "what?", "when?"': "who_what_when",
    'likes to know "why?"': "why",
    "finds it difficult to yell very loudly": "hard_to_yell_loudly",
    "yelling to others when they are far away comes naturally": "yells_easily",
    "when describing an event, will tell people what happened": "tells_what_happened",
    "when describing an event, will tell people what it meant": "tells_what_it_meant",
    'thinks "robotic" is an insult': "robotic_is_insult",
    "strives to have a mechanical mind": "mechanical_mind",
    "wants to be good at fixing things": "fixing_things",
    "wants to be good at fixing people": "fixing_people",
    "cares if something is good or bad": "good_or_bad",
    "cares if something is true or false": "true_or_false",
    "likes to perform in front of other people": "likes_performing",
    "wants people's respect": "wants_respect",
    "wants their love": "wants_love",
    "unsatisfied with the ways things are": "unsatisfied_with_things",
    "prefer to take multiple choice test": "multiple_choice_tests",
    "prefer essay answers": "essay_answers",
    "has difficulty explaining their ideas": "struggles_explaining_ideas",
}
MAX_KEY = 30
STOP = {"the", "a", "an", "to", "with", "by", "on", "of", "their", "they", "it", "is", "as", "in", "so"}
FILLER = {"prefer", "prefers", "rather", "to", "be", "like", "likes", "the", "a", "their", "they"}


def fetch(raw_dir: Path) -> None:
    headers = {"User-Agent": "Mozilla/5.0 (askjev research)"}
    for url, name in ((DEV_URL, "development.html"), (PDF_URL, "OEJTS1.2.pdf")):
        out = raw_dir / name
        if not out.exists():
            r = httpx.get(url, headers=headers, follow_redirects=True, timeout=60)
            r.raise_for_status()
            out.write_bytes(r.content)


def _clean(p: str) -> str:
    p = html.unescape(re.sub(r"<[^>]+>", "", p)).replace("\\", "").replace("’", "'")
    p = re.sub(r"\s+", " ", p).strip().rstrip(";").strip()
    return POLE_FIX.get(p, p)


def _appendix(raw_dir: Path) -> list[tuple[str, str, str, str, float]]:
    """(left, right, dichotomy, letter scoring higher / nearer the right pole, mean diff) for strong items."""
    t = (raw_dir / "development.html").read_text(encoding="utf-8", errors="replace")
    tb = t[t.index('id="screenedtable"'):]
    tb = tb[: tb.index("</table>")]
    out = []
    for row in re.findall(r"(?s)<tr>(.*?)</tr>", tb):
        tds = re.findall(r"(?s)<td[^>]*>(.*?)</td>", row)
        if len(tds) != 5 or ";" not in tds[0]:
            continue
        left, right = re.split(r";\s*(?:<br\s*/?>)?", tds[0], maxsplit=1)
        vals = []
        for v in tds[1:]:
            v = html.unescape(re.sub(r"<[^>]+>", "", v)).strip()
            m = re.match(r"([0-9.]+)\s*([A-Z])", v)
            vals.append((float(m.group(1)), m.group(2)) if m else (0.0, ""))
        order = sorted(range(4), key=lambda i: -vals[i][0])
        if vals[order[0]][0] >= STRONG and vals[order[1]][0] < WEAK:
            dich = list(DICHOTOMY)[order[0]]
            out.append((_clean(left), _clean(right), dich, vals[order[0]][1], vals[order[0]][0]))
    return out


def _sig(p: str) -> str:
    return " ".join(w for w in re.findall(r"[a-z]+", p.lower()) if w not in FILLER)


def _key(p: str, other: str) -> str:
    if p in KEY_FIX:
        return KEY_FIX[p]
    a, b = re.findall(r"[a-z0-9]+", p.lower()), re.findall(r"[a-z0-9]+", other.lower())
    i = 0
    while i < min(len(a), len(b)) - 1 and a[i] == b[i]:
        i += 1
    if "_".join(a[:5]) == "_".join(b[:5]):  # same opening words: keep only the part that differs
        a = a[i:]
    k = "_".join(a)
    if len(k) > MAX_KEY:
        words = [w for w in a if w not in STOP] or a
        k = ""
        for w in words:
            if len(k) + len(w) + 1 > MAX_KEY:
                break
            k = f"{k}_{w}" if k else w
    return k


def _cap(p: str) -> str:
    return p[:1].upper() + p[1:]


def normalize(raw_dir: Path) -> Iterator[Question]:
    rows = []  # (left, right, dichotomy, right_letter, instrument, item_id, extra_meta)
    for qid, left, right, dich, sign in V12:
        lo, hi, _ = DICHOTOMY[dich]
        rows.append((left, right, dich, hi if sign == "+" else lo, "OEJTS 1.2", qid, {"scoring_sign": sign}))
    for left, right, dich, letter, diff in _appendix(raw_dir):
        rows.append((left, right, dich, letter, "OEJTS development Appendix A", f"{left} | {right}", {"mean_diff": diff}))

    seen = set()
    for left, right, dich, right_letter, instrument, item_id, extra in rows:
        sig = frozenset((_sig(left), _sig(right)))
        if sig in seen:
            continue
        seen.add(sig)
        lo, hi, node = DICHOTOMY[dich]
        left_letter = lo if right_letter == hi else hi
        kl, kr = _key(left, right), _key(right, left)
        if kl == kr:
            continue
        yield Question(
            text="Which describes you better?",
            primitive="choice",
            hemisphere="self",
            kind="personality",
            origin="dataset",
            source=NAME,
            options={kl: _cap(left), kr: _cap(right)},
            node_hint=f"self.personality.type.{node}",
            human_text="Which describes most people better?",
            source_item_id=item_id,
            license=LICENSE,
            meta={"instrument": instrument, "dichotomy": dich, "poles": {kl: left_letter, kr: right_letter}, **extra},
        )
