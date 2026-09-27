"""Wikidata internet memes and viral videos: which of two is better known, and which appeared first.

Source: Wikidata (CC0) via QLever (fallback WDQS), the same endpoints wikidata_g4 / wikidata_companies use:
items that are an instance of internet meme (Q2927074) or viral video (Q1030329) or any subclass of them (image
macro, copypasta, exploitable comic, internet challenge, rage comic, YouTube Poop...), with their English label,
description, all P31 classes, sitelink count, English Wikipedia article, and inception (P571) / publication date
(P577). Popularity: English Wikipedia pageviews (Wikimedia REST API, public, no key), user agents, all access,
2023-01..2025-12 (36 months).

Pool: items with an English Wikipedia article whose P31 classes and description mark them as a meme or viral
video first (not a film, video game, number, drug, toy brand, fictional character, person, song release, religion
or law/adage), English label unique, Latin script. Dropped outright: shock sites, pornographic or antisemitic
items and other hate symbols. Political memes (named politicians, wars, elections) are flagged "political" and
sexual or graphic ones "sensitive".

Templates (node memes.classic_eras):
1. better_known (<= WIKIDATA_MEMES_KNOWN): "Which internet meme is better known: A or B?" (viral video / mixed
   wording). Truth = more pageviews, only when the ratio >= 3 and the sitelink count agrees (not lower for the
   winner). Each item in at most MAX_PAIRS pairs.
2. came_first (<= WIKIDATA_MEMES_FIRST): "Which internet meme appeared first: A or B?" from the earliest of
   inception / publication date; years at least MIN_GAP apart. Each item in at most MAX_PAIRS pairs.
"""

from __future__ import annotations

import json
import re
import time
import unicodedata
import urllib.parse
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Iterator

import httpx

from askjev.model import Question
from askjev.sampling import env_int, hash_order

NAME = "wikidata_memes"
QLEVER = "https://qlever.dev/api/wikidata"
WDQS = "https://query.wikidata.org/sparql"
PV = ("https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/all-access/user/"
      "{title}/monthly/2023010100/2025123100")
UA = "askjev/0.1 (https://github.com/brian-w-zhang/askjev) research"
LICENSE = "CC0 (Wikidata); popularity from Wikimedia pageviews API (CC0)"
SALT = "wikidata_memes.v1"
N_KNOWN = env_int("WIKIDATA_MEMES_KNOWN", 2000)
N_FIRST = env_int("WIKIDATA_MEMES_FIRST", 1200)
MAX_PAIRS = 10
PV_RATIO = 3.0
MIN_GAP = 3
NODE = "world.society.internet_culture.memes.classic_eras"
PREFIXES = """PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX wikibase: <http://wikiba.se/ontology#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX schema: <http://schema.org/>
"""
ROOTS = "wd:Q2927074 wd:Q1030329"
QUERIES = {
    "items": "SELECT ?item ?root ?label ?desc ?sl ?enw ?inc ?pub WHERE { VALUES ?root { " + ROOTS + " } "
             "?cls wdt:P279* ?root . ?item wdt:P31 ?cls . ?item wikibase:sitelinks ?sl . "
             "?item rdfs:label ?label FILTER(LANG(?label) = \"en\") "
             "OPTIONAL { ?item schema:description ?desc FILTER(LANG(?desc) = \"en\") } "
             "OPTIONAL { ?enw schema:about ?item ; schema:isPartOf <https://en.wikipedia.org/> } "
             "OPTIONAL { ?item wdt:P571 ?inc } OPTIONAL { ?item wdt:P577 ?pub } }",
    "classes": "SELECT DISTINCT ?item ?c ?cl WHERE { VALUES ?root { " + ROOTS + " } ?cls wdt:P279* ?root . "
               "?item wdt:P31 ?cls . ?item wdt:P31 ?c . OPTIONAL { ?c rdfs:label ?cl FILTER(LANG(?cl) = \"en\") } }",
}
# P31 classes that mean the item is primarily something else (film, game, number, product, character...).
OTHER_CLASS = re.compile(r"^(film|feature film|film series|video game|.*\bnumber|positive integer|.*integer|drug|brand|"
                         r"product model|food product|principle|epigrammatic law|adage|theorem|human|music genre|"
                         r"art genre|literary genre|genre|conspiracy theory|website|type of website|shock site|mascot|"
                         r"caricature|pejorative|political campaign|Mario franchise character|annual event|"
                         r"anime and manga term|stock character|slur|hate symbol)$", re.I)
DROP_DESC = re.compile(r"\b(shock site|pornograph\w*|orgasm|sexual\w*|antisemit\w*|racis\w*|hate symbol|slur|nazi\w*|"
                       r"white supremac\w*|pedophil\w*|paedophil\w*|gore|murder\w*|suicid\w*|killing|shooting|islamic state|"
                       r"isis|jihad\w*|terroris\w*|nasheed|beheading)\b", re.I)
DROP_LABEL = re.compile(r"\b(pedobear|goatse|rule 34|ahegao|happy merchant|tubgirl|lemon party|2 girls|1 cup|"
                        r"meatspin|blue waffle|loli\w*|shota\w*|nigg\w*|fag\w*|fuck\w*|pussy|ligma|sugma|deez nuts|"
                        r"elon musk salute|santorum|horny)\b", re.I)
POLITICAL = re.compile(r"\b(trump|obama|biden|clinton|hillary|putin|zelensk\w*|bernie|sanders|kamala|harris|"
                       r"election\w*|politic\w*|president\w*|russia\w*|ukrain\w*|israel\w*|palestin\w*|war\b|"
                       r"warship|battle|soldier\w*|military|protest\w*|propaganda|party|parliament|minister|"
                       r"king|queen|monarch|dictator|covfefe|alternative facts|brandon|maga|alt-right|incel\w*|"
                       r"pejorative|social justice|feminis\w*|boomer|immigra\w*|refugee\w*|hugo ch[aá]vez|"
                       r"juan carlos|kim jong|xi jinping|winnie|tiananmen|taiwan|hong kong|brexit|capitol|nafo|"
                       r"musk|kony|epstein|area 51|ted cruz|liz truss|lettuce|soy ?boy|karen|woke|charlie kirk|kirkification)\b", re.I)
SENSITIVE = re.compile(r"\b(dick\w*|necrophil\w*|sex\w*|nude\w*|naked|porn\w*|abstinence|masturbat\w*|fuck\w*|death|died|dead|kill\w*|"
                       r"drug\w*|cannabis|marijuana|weed|suicid\w*|violen\w*|blood\w*|disgust\w*|horror|scream\w*|"
                       r"gun\w*|shoot\w*|terror\w*|anus|penis|vagina|breast\w*|vomit\w*|poop|feces|shit|gyat|hawk tuah|"
                       r"netflix and chill|behead\w*|bitch\w*|miscarriage|gorilla|harambe|loss|ass|thicc|rizz)\b", re.I)


DESC_YEAR = re.compile(r"^(?:\w+ )?((?:19[89]|20[0-2])\d)(?:[–-]\d{2,4})? (?:\w+ )?(?:internet|viral|meme|online|youtube)|"
                       r"(?:emerged|originated|went viral|became popular|popularized|popularised|created|uploaded|"
                       r"posted|released) (?:\w+ ){0,3}in ((?:19[89]|20[0-2])\d)\b", re.I)


def _sparql(query: str) -> list[dict]:
    for attempt, ep in enumerate([QLEVER, WDQS, QLEVER, WDQS]):
        time.sleep(1.0)
        try:
            r = httpx.post(ep, data={"query": PREFIXES + query}, timeout=180,
                           headers={"User-Agent": UA, "Accept": "application/sparql-results+json"})
            if r.status_code == 200:
                rows = r.json()["results"]["bindings"]
                return [{k: v["value"].rsplit("/", 1)[-1] if v.get("type") == "uri" and k != "enw" else v["value"]
                         for k, v in b.items()} for b in rows]
        except (httpx.TimeoutException, httpx.TransportError, ValueError):
            pass
        time.sleep(5 * (attempt + 1))
    raise RuntimeError(f"sparql failed: {query[:100]}")


def _pageviews(url: str) -> int | None:
    title = url.rsplit("/wiki/", 1)[-1]
    title = urllib.parse.quote(urllib.parse.unquote(title), safe="")
    for attempt in range(4):
        time.sleep(0.25)
        try:
            r = httpx.get(PV.format(title=title), timeout=20, headers={"User-Agent": UA})
            if r.status_code == 200:
                return sum(int(x["views"]) for x in r.json()["items"])
            if r.status_code == 404:  # no views recorded in the window
                return 0
        except (httpx.TimeoutException, httpx.TransportError, ValueError):
            pass
        time.sleep(15 * (attempt + 1))  # 429s: back off hard
    return None


def fetch(raw_dir: Path) -> None:
    raw_dir.mkdir(parents=True, exist_ok=True)
    for name, q in QUERIES.items():
        out = raw_dir / f"{name}.json"
        if not out.exists():
            out.write_text(json.dumps(_sparql(q), ensure_ascii=False))
    pv_path = raw_dir / "pageviews.json"
    pv: dict[str, int] = json.loads(pv_path.read_text()) if pv_path.exists() else {}
    urls = sorted({r["enw"] for r in json.loads((raw_dir / "items.json").read_text()) if r.get("enw")} - set(pv))
    log = open(raw_dir / "fetch.log", "a")
    with ThreadPoolExecutor(2) as ex:
        for i, (u, v) in enumerate(zip(urls, ex.map(_pageviews, urls))):
            if v is not None:
                pv[u] = v
            if i % 50 == 0:
                log.write(f"pageviews {i}/{len(urls)}\n")
                log.flush()
                pv_path.write_text(json.dumps(pv, ensure_ascii=False))
    pv_path.write_text(json.dumps(pv, ensure_ascii=False))
    log.write(f"pageviews done: {len(pv)}\n")
    log.close()


def _slug(name: str) -> str:
    s = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().lower()
    s = re.sub(r"&", " and ", s)
    return re.sub(r"[^a-z0-9]+", "_", s).strip("_")


def _year(s: str | None) -> int | None:
    m = re.match(r"^(-?\d{4})", s or "")
    return int(m.group(1)) if m else None


FUNNEL: Counter = Counter()


def _items(raw_dir: Path) -> list[dict]:
    pv = json.loads((raw_dir / "pageviews.json").read_text())
    classes: dict[str, set[str]] = defaultdict(set)
    for r in json.loads((raw_dir / "classes.json").read_text()):
        classes[r["item"]].add(r.get("cl") or r["c"])
    acc: dict[str, dict] = {}
    for r in json.loads((raw_dir / "items.json").read_text()):
        d = acc.setdefault(r["item"], {"id": r["item"], "label": r["label"], "desc": r.get("desc") or "",
                                       "sl": int(r["sl"]), "enw": r.get("enw"), "roots": set(), "years": set()})
        d["roots"].add(r["root"])
        for k in ("inc", "pub"):
            if _year(r.get(k)):
                d["years"].add(_year(r[k]))
    labels = Counter(d["label"].lower() for d in acc.values())
    out = []
    for d in acc.values():
        FUNNEL["items"] += 1
        d["label"] = re.sub(r"\s*\((?:meme|internet meme|video)\)$", "", d["label"], flags=re.I)
        lab, desc = d["label"], d["desc"]
        meme_classes = {"internet meme", "viral video", "image macro", "copypasta", "exploitable comic strip",
                        "exploitable meme", "exploitable image macro", "reaction image", "cat meme", "Internet challenge",
                        "rage comic", "YouTube Poop", "image macro series", "flash mob", "viral phenomenon"}
        other = [c for c in classes[d["id"]] if c not in meme_classes]
        if not d["enw"] or d["enw"] not in pv:
            FUNNEL["drop_no_enwiki"] += 1
            continue
        if any(OTHER_CLASS.search(c) or re.fullmatch(r"Q\d+", c) for c in other):
            FUNNEL["drop_other_class"] += 1
            continue
        if DROP_DESC.search(desc) or DROP_LABEL.search(lab):
            FUNNEL["drop_offensive"] += 1
            continue
        if labels[lab.lower()] > 1 or not _slug(lab) or not all(ord(c) < 0x250 for c in lab) or len(lab) > 60:
            FUNNEL["drop_label"] += 1
            continue
        if re.search(r"\b(film directed|video game (developed|by|published)|natural number|recreational drug|"
                     r"brand of|character (from|in)|album by|company|television series|anime series)\b", desc, re.I):
            FUNNEL["drop_desc_other"] += 1
            continue
        d["pv"] = pv[d["enw"]]
        d["year"] = min(d["years"]) if d["years"] and max(d["years"]) - min(d["years"]) <= 1 else None
        d["year_from"] = "P571/P577" if d["year"] else None
        if not d["years"]:  # no date statement: the English description often dates the meme ("2011 Internet meme")
            m = DESC_YEAR.search(desc)
            if m:
                d["year"], d["year_from"] = int(m.group(1) or m.group(2)), "description"
        d["kind"] = "viral video" if d["roots"] == {"Q1030329"} else "internet meme"
        text = f"{lab} {desc}"
        d["flags"] = [f for f, rx in (("political", POLITICAL), ("sensitive", SENSITIVE)) if rx.search(text)]
        out.append(d)
    FUNNEL["pool"] = len(out)
    return out


def _wording(a: dict, b: dict, verb: str) -> str:
    what = f"{a['kind']}" if a["kind"] == b["kind"] else "of these internet phenomena"
    return f"Which {what} {verb}: \"{a['label']}\" or \"{b['label']}\"?"


def _desc(d: dict, dated: bool) -> str | None:
    """Option description: label + Wikidata description, to tell "Thriller" the meme from the album. For
    came_first a description with a year in it would give the answer away, so it is left out."""
    desc = d["desc"].strip()
    if not desc or (dated and re.search(r"\d{4}", desc)) or desc.lower() in {"internet meme", "viral video", "meme"}:
        return None
    if len(desc) > 110:
        desc = desc[:110].rsplit(" ", 1)[0].rstrip(",;:") + "..."
    return f"{d['label']}: {desc}"


def _pairs(items: list[dict], ok, cap: int, salt: str) -> list[tuple[dict, dict]]:
    pairs = [(a, b) for i, a in enumerate(items) for b in items[i + 1:] if ok(a, b)]
    uses: Counter = Counter()
    out = []
    for a, b in hash_order(pairs, lambda p: f"{p[0]['id']}|{p[1]['id']}", salt):
        if len(out) >= cap:
            break
        if uses[a["id"]] >= MAX_PAIRS or uses[b["id"]] >= MAX_PAIRS or _slug(a["label"]) == _slug(b["label"]):
            continue
        uses[a["id"]] += 1
        uses[b["id"]] += 1
        out.append((a, b))
    return out


def _q(tid: str, text: str, a: dict, b: dict, win: dict, meta: dict) -> Question:
    first, second = hash_order([a, b], lambda x: x["id"], SALT + ".order")
    flags = sorted(set(a["flags"]) | set(b["flags"]))
    return Question(
        text=_wording(first, second, text), primitive="choice", hemisphere="world", kind="evaluative" if tid == "better_known" else "factual",
        origin="wikidata-fact", source=NAME,
        options={_slug(x["label"]): _desc(x, tid == "came_first") for x in (first, second)},
        node_hint=NODE, source_item_id=f"{tid}:{a['id']}-{b['id']}", license=LICENSE, truth=_slug(win["label"]),
        template_id=f"wikidata_memes.{tid}",
        meta={"qids": [first["id"], second["id"]], **meta, **({"flags": flags} if flags else {})},
    )


def normalize(raw_dir: Path) -> Iterator[Question]:
    items = sorted(_items(raw_dir), key=lambda d: d["id"])

    def known_ok(a, b):
        hi, lo = (a, b) if a["pv"] >= b["pv"] else (b, a)
        return lo["pv"] >= 1000 and hi["pv"] >= 20000 and hi["pv"] >= PV_RATIO * lo["pv"] and hi["sl"] >= lo["sl"]

    for a, b in _pairs(items, known_ok, N_KNOWN, SALT + ".known"):
        win = a if a["pv"] > b["pv"] else b
        first, second = hash_order([a, b], lambda x: x["id"], SALT + ".order")
        yield _q("better_known", "is better known", a, b, win,
                 {"enwiki_pageviews_2023_2025": [first["pv"], second["pv"]], "sitelinks": [first["sl"], second["sl"]]})

    dated = [d for d in items if d["year"] and 1998 <= d["year"] <= 2026]  # older dates are the source, not the meme
    for a, b in _pairs(dated, lambda a, b: abs(a["year"] - b["year"]) >= MIN_GAP, N_FIRST, SALT + ".first"):
        win = a if a["year"] < b["year"] else b
        first, second = hash_order([a, b], lambda x: x["id"], SALT + ".order")
        yield _q("came_first", "appeared first", a, b, win, {"years": [first["year"], second["year"]],
                                                             "year_from": [first["year_from"], second["year_from"]]})
