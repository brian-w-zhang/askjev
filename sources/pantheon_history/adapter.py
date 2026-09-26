"""Pantheon (pantheon.world) historical figures: who is better known today (HPI pairs), what each person was
mainly known as (Pantheon occupation), and the present-day country of birth. People born before 1900."""

from __future__ import annotations

import bz2
import io
import itertools
import math
import re
import unicodedata
from pathlib import Path
from typing import Iterator

import httpx
import polars as pl

from askjev.model import Question
from askjev.sampling import env_int, hash_order

NAME = "pantheon_history"
URL = "https://storage.googleapis.com/pantheon-public-data/person_2025_update.csv.bz2"
FILE = "person_2025_update.csv.bz2"
LICENSE = "CC BY-SA 4.0 (Pantheon, pantheon.world; Yu et al. 2016, Scientific Data)"
SALT = "pantheon_history.v1"
N_FAMOUS = env_int("PANTHEON_HISTORY_FAMOUS", 4000)
N_OCCUPATION = env_int("PANTHEON_HISTORY_OCCUPATION", 2500)
N_BIRTH = env_int("PANTHEON_HISTORY_BIRTH", 2500)
TOP_PER_ERA = 1500  # most-remembered people per era considered (recognizable end of the list)
MAX_PAIRS_PER_PERSON = 6

# Pantheon occupation -> (option key, description, group). Groups that commonly overlap in one person
# (a philosopher who was a mathematician, a ruler who led armies) are never offered against each other.
OCC = {
    "POLITICIAN": ("ruler_or_politician", "A ruler, statesman or politician", "politics"),
    "DIPLOMAT": ("diplomat", "A diplomat", "politics"),
    "MILITARY PERSONNEL": ("military_commander", "A military commander or soldier", "military"),
    "EXPLORER": ("explorer", "An explorer or navigator", "explore"),
    "PAINTER": ("painter", "A painter", "visual"),
    "SCULPTOR": ("sculptor", "A sculptor", "visual"),
    "ARCHITECT": ("architect", "An architect", "visual"),
    "PHOTOGRAPHER": ("photographer", "A photographer", "visual"),
    "COMPOSER": ("composer", "A composer of music", "music"),
    "MUSICIAN": ("musician", "A performing musician", "music"),
    "SINGER": ("singer", "A singer", "music"),
    "CONDUCTOR": ("conductor", "An orchestra conductor", "music"),
    "ACTOR": ("actor", "An actor or actress", "stage"),
    "DANCER": ("dancer", "A dancer", "stage"),
    "WRITER": ("writer", "A writer or poet", "letters"),
    "HISTORIAN": ("historian", "A historian", "letters"),
    "JOURNALIST": ("journalist", "A journalist", "letters"),
    "LINGUIST": ("linguist", "A linguist or philologist", "letters"),
    "PHILOSOPHER": ("philosopher", "A philosopher", "philosophy"),
    "RELIGIOUS FIGURE": ("religious_figure", "A religious leader or figure", "religion"),
    "MATHEMATICIAN": ("mathematician", "A mathematician", "science"),
    "PHYSICIST": ("physicist", "A physicist", "science"),
    "CHEMIST": ("chemist", "A chemist", "science"),
    "ASTRONOMER": ("astronomer", "An astronomer", "science"),
    "BIOLOGIST": ("biologist", "A biologist or naturalist", "science"),
    "GEOLOGIST": ("geologist", "A geologist", "science"),
    "GEOGRAPHER": ("geographer", "A geographer or cartographer", "science"),
    "PSYCHOLOGIST": ("psychologist", "A psychologist", "science"),
    "PHYSICIAN": ("physician", "A physician", "medicine"),
    "ECONOMIST": ("economist", "An economist", "economics"),
    "ENGINEER": ("engineer", "An engineer", "engineering"),
    "BUSINESSPERSON": ("businessperson", "A businessperson or industrialist", "business"),
    "SOCIAL ACTIVIST": ("social_activist", "A social activist or reformer", "activism"),
    "ARCHAEOLOGIST": ("archaeologist", "An archaeologist", "science"),
    "CHESS PLAYER": ("chess_player", "A chess player", "games"),
}
CONFLICT = {  # group -> groups never used as its distractors (besides itself)
    "politics": {"military", "religion", "activism", "engineering", "business", "letters", "economics"},
    "military": {"politics", "explore"},
    "explore": {"military", "science"},
    "visual": {"engineering"},
    "music": {"stage"},
    "stage": {"music"},
    "letters": {"philosophy", "religion", "activism", "politics"},
    "philosophy": {"letters", "science", "religion", "economics"},
    "religion": {"philosophy", "letters", "politics"},
    "science": {"philosophy", "medicine", "engineering", "explore"},
    "medicine": {"science"},
    "economics": {"philosophy", "politics", "letters"},
    "engineering": {"science", "visual", "business"},
    "business": {"engineering", "politics"},
    "activism": {"politics", "letters", "religion"},
    "games": set(),
}
FAMOUS_SKIP = {"RELIGIOUS FIGURE"}  # comparing prophets/saints' renown reads as a religious judgment
# Titles that give the occupation away.
TITLE_RE = re.compile(r"\b(Pope|Saint|St\.|King|Queen|Emperor|Empress|Sultan|Pharaoh|Duke|Duchess|Prince|Princess|"
                      r"Tsar|Czar|Caliph|Shah|Khan|Count|Countess|Archduke|Archbishop|Bishop|Cardinal|Lord|Lady|"
                      r"General|Admiral|Marshal|Captain|Sir|Imam|Rabbi|Elector|Margrave|Landgrave|Emir|Doge)\b")
MODERN_ONLY = {"JOURNALIST", "PHOTOGRAPHER", "CONDUCTOR", "PSYCHOLOGIST", "ECONOMIST", "CHESS PLAYER", "ARCHAEOLOGIST",
               "SOCIAL ACTIVIST", "BUSINESSPERSON", "GEOLOGIST"}  # never distractors for people born before 1700
MICROSTATES = {"Vatican City", "Monaco", "San Marino", "Liechtenstein", "Andorra"}  # never distractors
MAX_GROUP_SHARE = {"politics": 0.35}  # rulers dominate the pre-1900 list; keep them from filling better_known
NO_BIRTH_COUNTRY = {"Israel", "Palestine", "State of Palestine", "Kosovo", "Taiwan", "Western Sahara"}
# Country names/demonyms that give the birth country away when they appear in a person's name.
DEMONYMS = {
    "United Kingdom": ["England", "English", "Scotland", "Scottish", "Wales", "Welsh", "Britain", "British", "Ireland"],
    "France": ["France", "French", "Gaul"], "Germany": ["Germany", "German", "Saxony", "Bavaria", "Prussia"],
    "Italy": ["Italy", "Italian", "Sicily", "Naples", "Milan", "Florence", "Venice", "Rome", "Roman"],
    "Spain": ["Spain", "Spanish", "Castile", "Aragon", "León", "Navarre"], "Portugal": ["Portugal", "Portuguese"],
    "Russia": ["Russia", "Russian", "Moscow", "Novgorod", "Kiev", "Kyiv"], "Poland": ["Poland", "Polish"],
    "Sweden": ["Sweden", "Swedish"], "Denmark": ["Denmark", "Danish"], "Norway": ["Norway", "Norwegian"],
    "Austria": ["Austria", "Austrian"], "Hungary": ["Hungary", "Hungarian"], "Greece": ["Greece", "Greek", "Athens", "Sparta", "Macedon"],
    "Netherlands": ["Netherlands", "Dutch", "Holland"], "Belgium": ["Belgium", "Flanders", "Brabant"],
    "Egypt": ["Egypt", "Egyptian"], "Turkey": ["Turkey", "Ottoman", "Constantinople"], "Iran": ["Persia", "Persian", "Iran"],
    "China": ["China", "Chinese"], "Japan": ["Japan", "Japanese"], "India": ["India", "Indian"],
    "United States": ["America", "American"], "Mexico": ["Mexico", "Mexican"], "Brazil": ["Brazil"],
    "Czech Republic": ["Bohemia", "Moravia"], "Czechia": ["Bohemia", "Moravia"], "Ukraine": ["Ukraine", "Kiev", "Kyiv"],
    "Switzerland": ["Swiss"], "Scotland": ["Scotland"], "Serbia": ["Serbia", "Serbian"], "Georgia": ["Georgia"],
    "Armenia": ["Armenia"], "Bulgaria": ["Bulgaria"], "Croatia": ["Croatia"], "Lithuania": ["Lithuania"],
}
CRIMEA = (44.3, 46.3, 32.4, 36.7)


def fetch(raw_dir: Path) -> None:
    out = raw_dir / FILE
    if out.exists():
        return
    r = httpx.get(URL, timeout=300, follow_redirects=True)
    r.raise_for_status()
    out.write_bytes(r.content)


def _slug(name: str) -> str:
    s = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "_", s).strip("_")


def _latin(name: str) -> bool:
    return all(ord(c) < 0x250 or c in "’‘" for c in name)


def _yr(y: int) -> str:
    return f"{-y} BC" if y <= 0 else str(y)


def _span(p: dict) -> str:
    b, d = p["birthyear"], p["deathyear"]
    if d is None:
        return f"born {_yr(b)}"
    if b <= 0 and d <= 0:
        return f"{-b}-{-d} BC"
    if b <= 0 < d:
        return f"{-b} BC-AD {d}"
    return f"{b}-{d}"


def _era(p: dict) -> str:
    b = p["birthyear"]
    return "ancient" if b < 500 else "medieval" if b < 1450 else "early_modern" if b < 1750 else "modern"


def _node(p: dict) -> str:
    b, occ, c, era = p["birthyear"], p["occupation"], p["bplace_country"], _era(p)
    if occ == "MILITARY PERSONNEL":
        return "world.history.military_history"
    if occ in {"INVENTOR", "ENGINEER"}:
        return "world.history.science_tech_history"
    if occ in {"ECONOMIST", "BUSINESSPERSON"}:
        return "world.history.economic_history"
    if era == "ancient":
        if c == "Greece" or (c in {"Turkey", "Italy"} and occ in {"PHILOSOPHER", "MATHEMATICIAN", "WRITER"} and b < -100):
            return "world.history.ancient.ancient_greece"
        if c == "Italy":
            return "world.history.ancient.ancient_rome"
        if c == "Egypt" and b < -30:
            return "world.history.ancient.ancient_egypt"
        return "world.history.ancient"
    if era == "medieval":
        if c == "Mongolia":
            return "world.history.medieval.mongol_empire"
        return "world.history.medieval"
    if era == "early_modern":
        if occ == "EXPLORER" and b < 1650:
            return "world.history.early_modern.age_of_discovery"
        if occ in {"PAINTER", "SCULPTOR", "ARCHITECT"} and b < 1580 and c in {"Italy", "Netherlands", "Belgium", "Germany", "Spain"}:
            return "world.history.early_modern.renaissance"
        if occ in {"MATHEMATICIAN", "PHYSICIST", "ASTRONOMER", "CHEMIST", "BIOLOGIST"} and b < 1700:
            return "world.history.early_modern.scientific_revolution"
        if occ in {"PHILOSOPHER", "WRITER"} and b >= 1680:
            return "world.history.early_modern.age_of_enlightenment"
        return "world.history.early_modern"
    return "world.history.modern.modern_era"


def _people(raw_dir: Path) -> list[dict]:
    df = pl.read_csv(io.BytesIO(bz2.open(raw_dir / FILE).read()), infer_schema_length=200000)
    df = df.filter(
        (pl.col("is_group") == False) & (pl.col("alive") == False) & pl.col("birthyear").is_not_null()  # noqa: E712
        & (pl.col("birthyear") < 1900) & pl.col("occupation").is_in(list(OCC)) & pl.col("hpi").is_not_null()
    )
    counts = df.group_by("name").len()
    dup = set(counts.filter(pl.col("len") > 1)["name"])
    out = []
    for p in df.sort("hpi", "wd_id", descending=[True, False]).iter_rows(named=True):
        n = p["name"]
        if n in dup or not _latin(n) or "(" in n or not _slug(n) or re.search(r"\d", n):
            continue
        out.append(p)
    # Recognizable end: top TOP_PER_ERA per era by HPI.
    keep, per = [], {}
    for p in out:
        e = _era(p)
        if per.get(e, 0) < TOP_PER_ERA:
            per[e] = per.get(e, 0) + 1
            keep.append(p)
    return keep


def _political(p: dict) -> bool:
    return p["occupation"] == "POLITICIAN" and (p["deathyear"] or 0) >= 1945


def _desc(p: dict) -> str:
    return f"{p['name']} ({_span(p)})"


def _famous(people: list[dict]) -> Iterator[Question]:
    pool = [p for p in people if p["occupation"] not in FAMOUS_SKIP]
    pairs = [
        (a, b) for a, b in itertools.combinations(pool, 2)
        if _era(a) == _era(b) and OCC[a["occupation"]][2] == OCC[b["occupation"]][2]
    ]
    uses: dict[str, int] = {}
    group_n: dict[str, int] = {}
    taken = 0
    for a, b in hash_order(pairs, lambda x: f"{x[0]['wd_id']}|{x[1]['wd_id']}", SALT + ".famous"):
        if taken >= N_FAMOUS:
            break
        if uses.get(a["wd_id"], 0) >= MAX_PAIRS_PER_PERSON or uses.get(b["wd_id"], 0) >= MAX_PAIRS_PER_PERSON:
            continue
        grp = OCC[a["occupation"]][2]
        if grp in MAX_GROUP_SHARE and group_n.get(grp, 0) >= MAX_GROUP_SHARE[grp] * N_FAMOUS:
            continue
        hi, lo = (a, b) if a["hpi"] > b["hpi"] else (b, a)
        # A clear gap on the index and on both of its main inputs (language editions, non-English views).
        if hi["hpi"] - lo["hpi"] < 4 or hi["l"] < 1.3 * lo["l"] or \
                (hi["non_en_page_views"] or 0) < 1.5 * (lo["non_en_page_views"] or 1):
            continue
        ka, kb = _slug(a["name"]), _slug(b["name"])
        if ka == kb:
            continue
        uses[a["wd_id"]] = uses.get(a["wd_id"], 0) + 1
        uses[b["wd_id"]] = uses.get(b["wd_id"], 0) + 1
        group_n[grp] = group_n.get(grp, 0) + 1
        taken += 1
        first, second = (a, b) if int(hash_order([0, 1], lambda i: f"{a['wd_id']}{b['wd_id']}{i}", SALT)[0]) == 0 else (b, a)
        flags = ["political"] if _political(a) or _political(b) else []
        yield Question(
            text=f"Who is better known around the world today: {first['name']} or {second['name']}?",
            primitive="choice", hemisphere="world", kind="evaluative", origin="template", source=NAME,
            options={_slug(first["name"]): _desc(first), _slug(second["name"]): _desc(second)},
            node_hint=_node(a) if _node(a) == _node(b) else f"world.history.{_era_node(a)}",
            source_item_id=f"famous:{a['wd_id']}-{b['wd_id']}", license=LICENSE,
            truth=_slug(hi["name"]), template_id="pantheon_history.better_known",
            meta={"wd_ids": [a["wd_id"], b["wd_id"]], "hpi": [round(a["hpi"], 2), round(b["hpi"], 2)],
                  "languages": [a["l"], b["l"]], "occupations": [a["occupation"], b["occupation"]],
                  **({"flags": flags} if flags else {})},
        )


def _era_node(p: dict) -> str:
    return {"ancient": "ancient", "medieval": "medieval", "early_modern": "early_modern", "modern": "modern.modern_era"}[_era(p)]


def _occupation(people: list[dict]) -> Iterator[Question]:
    occs = sorted(OCC)
    taken = 0
    for p in hash_order(people, lambda x: x["wd_id"], SALT + ".occ"):
        if taken >= N_OCCUPATION:
            break
        if TITLE_RE.search(p["name"]) or p["occupation"] == "BUSINESSPERSON":
            continue
        key, _, grp = OCC[p["occupation"]]
        bad = {grp} | CONFLICT[grp]
        cands = [o for o in occs if OCC[o][2] not in bad and not (p["birthyear"] < 1700 and o in MODERN_ONLY)]
        # one distractor per group so the options are clearly different kinds of life
        seen_groups, distract = set(), []
        for o in hash_order(cands, lambda o: f"{p['wd_id']}|{o}", SALT + ".occd"):
            g = OCC[o][2]
            if g in seen_groups:
                continue
            seen_groups.add(g)
            distract.append(o)
            if len(distract) == 3:
                break
        opts = hash_order([p["occupation"], *distract], lambda o: f"{p['wd_id']}|{o}", SALT + ".occo")
        taken += 1
        yield Question(
            text=f"What was {p['name']} ({_span(p)}) mainly known as?",
            primitive="choice", hemisphere="world", kind="factual", origin="template", source=NAME,
            options={OCC[o][0]: OCC[o][1] for o in opts},
            node_hint=_node(p), source_item_id=f"occ:{p['wd_id']}", license=LICENSE, truth=key,
            template_id="pantheon_history.known_as",
            meta={"wd_id": p["wd_id"], "occupation": p["occupation"], "hpi": round(p["hpi"], 2),
                  **({"flags": ["political"]} if _political(p) else {})},
        )


def _centroids(people: list[dict]) -> dict[str, tuple[float, float]]:
    acc: dict[str, list[tuple[float, float]]] = {}
    for p in people:
        if p["bplace_country"] and p["bplace_lat"] is not None:
            acc.setdefault(p["bplace_country"], []).append((p["bplace_lat"], p["bplace_lon"]))
    return {c: (sum(x for x, _ in v) / len(v), sum(y for _, y in v) / len(v)) for c, v in acc.items() if len(v) >= 3}


def _dist(a: tuple[float, float], b: tuple[float, float]) -> float:
    la1, lo1, la2, lo2 = map(math.radians, (*a, *b))
    return math.acos(max(-1.0, min(1.0, math.sin(la1) * math.sin(la2) + math.cos(la1) * math.cos(la2) * math.cos(lo1 - lo2))))


def _birth(people: list[dict]) -> Iterator[Question]:
    cents = _centroids(people)
    countries = sorted(c for c in cents if c not in NO_BIRTH_COUNTRY)
    taken = 0
    for p in hash_order(people, lambda x: x["wd_id"], SALT + ".birth"):
        if taken >= N_BIRTH:
            break
        c = p["bplace_country"]
        if c not in countries or p["birthyear"] < 1000 or p["occupation"] == "RELIGIOUS FIGURE":
            continue
        lat, lon = p["bplace_lat"], p["bplace_lon"]
        if lat is not None and CRIMEA[0] <= lat <= CRIMEA[1] and CRIMEA[2] <= lon <= CRIMEA[3]:
            continue
        words = DEMONYMS.get(c, []) + [c]
        if any(re.search(rf"\b{re.escape(w)}", p["name"]) for w in words):
            continue
        near = sorted((x for x in countries if x != c and x not in MICROSTATES), key=lambda x: _dist(cents[c], cents[x]))[:6]
        distract = hash_order(near, lambda x: f"{p['wd_id']}|{x}", SALT + ".bd")[:3]
        opts = hash_order([c, *distract], lambda x: f"{p['wd_id']}|{x}", SALT + ".bo")
        flags = []
        if _political(p) or {"Russia", "Ukraine"} <= set(opts):
            flags.append("political")
        taken += 1
        yield Question(
            text=f"In which present-day country was {p['name']} ({_span(p)}) born?",
            primitive="choice", hemisphere="world", kind="factual", origin="template", source=NAME,
            options={_slug(o): o for o in opts},
            node_hint=_node(p), source_item_id=f"birth:{p['wd_id']}", license=LICENSE, truth=_slug(c),
            template_id="pantheon_history.birth_country",
            meta={"wd_id": p["wd_id"], "birthplace": p["bplace_name"], "hpi": round(p["hpi"], 2),
                  **({"flags": flags} if flags else {})},
        )


def normalize(raw_dir: Path) -> Iterator[Question]:
    people = _people(raw_dir)
    yield from _famous(people)
    yield from _occupation(people)
    yield from _birth(people)
