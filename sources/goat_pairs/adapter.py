"""G3 GOAT pairs: for each category, the top 25 entities by Wikidata sitelinks, one Choice per unordered pair."""

from __future__ import annotations

import itertools
import json
import re
import time
import unicodedata
from pathlib import Path
from typing import Iterator

import httpx

from askjev.model import Question

NAME = "goat_pairs"
SPARQL = "https://query.wikidata.org/sparql"
QLEVER = "https://qlever.dev/api/wikidata"
UA = "askjev/0.1 (github.com/brian-w-zhang/askjev)"
LICENSE = "CC0"
TOP = 25
POOL = 80  # candidates pulled per category before filtering
PREFIXES = """PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX wikibase: <http://wikiba.se/ontology#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
"""

# Candidate patterns bind ?item; ranking is always by sitelinks. `cap` = (property, max items sharing one
# value), keeping one franchise/artist from filling a list. `exclude` = QIDs dropped with the reason
# noted: sitelink-inflated outliers, people famous for something other than the category, contested
# entities, and non-members of the class. `rename` = display names for long corporate/official labels.
CATEGORIES: dict[str, dict] = {
    "films": {
        "where": "?item wdt:P31 wd:Q11424 .",
        "text": "Which is the better film?", "node": "world.arts.film", "cap": ("P179", 2),
    },
    "tv_series": {
        "where": "?item wdt:P31 wd:Q5398426 .",
        "text": "Which is the better TV series?", "node": "world.arts.television",
        "exclude": {"Q8172269": "sitelink-inflated (Liv and Maddie)"},
    },
    "video_games": {
        "where": "?item wdt:P31 wd:Q7889 .",
        "text": "Which is the better video game?", "node": "world.sports.video_games", "cap": ("P179", 2),
        "exclude": {"Q23648408": "unreleased (Grand Theft Auto VI)"},
    },
    "books": {
        "where": "?item wdt:P31 wd:Q7725634 ; wdt:P7937 wd:Q8261 .",
        "text": "Which is the better book?", "node": "world.arts.books", "cap": ("P179", 2),
    },
    "albums": {
        "where": "?item wdt:P31 wd:Q482994 .",
        "text": "Which is the better album?", "node": "world.arts.music", "cap": ("P175", 2), "by": "P175",
        "exclude_by": {"Q23471": "sitelink-inflated (Lordi)"},
    },
    "bands": {
        "where": "?item wdt:P31 wd:Q215380 .",
        "text": "Which is the better band?", "node": "world.arts.music",
        "exclude": {"Q23471": "sitelink-inflated (Lordi)"},
    },
    "singers": {
        # at least 5 albums credited, so actors/poets tagged "singer" drop out
        "where": "?item wdt:P31 wd:Q5 ; wdt:P106 wd:Q177220 . { SELECT ?item WHERE { ?w wdt:P31 wd:Q482994 ; "
                 "wdt:P175 ?item } GROUP BY ?item HAVING (COUNT(?w) >= 5) }",
        "text": "Who is the greater singer?", "node": "world.arts.music", "person": True,
        "exclude": {"Q383541": "sitelink-inflated (Basshunter)", "Q4612": "known as actor (Marlene Dietrich)",
                    "Q36268": "known as actor (Brigitte Bardot)", "Q6105": "known as TV host (Hebe Camargo)",
                    "Q40096": "known as actor (Will Smith)", "Q221310": "sitelink-inflated (Anggun)",
                    "Q1362169": "sitelink-inflated (Agnez Mo)"},
    },
    "painters": {
        # at least 20 paintings attributed in Wikidata
        "where": "?item wdt:P31 wd:Q5 ; wdt:P106 wd:Q1028181 . { SELECT ?item WHERE { ?w wdt:P31 wd:Q3305213 ; "
                 "wdt:P170 ?item } GROUP BY ?item HAVING (COUNT(?w) >= 20) }",
        "text": "Who is the greater painter?", "node": "world.arts.visual_art", "person": True,
        "exclude": {"Q7241": "known as poet (Rabindranath Tagore)", "Q179126": "known as critic (John Ruskin)",
                    "Q47842": "political figure (Empress Dowager Cixi)", "Q134958": "known as poet (Taras Shevchenko)", "Q7724": "known as writer (August Strindberg)"},
    },
    "paintings": {
        "where": "?item wdt:P31 wd:Q3305213 .",
        "text": "Which is the better painting?", "node": "world.arts.visual_art", "cap": ("P170", 3),
    },
    "soccer_players": {
        "where": "?item wdt:P31 wd:Q5 ; wdt:P106 wd:Q937857 .",
        "text": "Who is the greater soccer player?", "node": "world.sports.soccer.clubs_players", "person": True,
        "exclude": {"Q34670": "known as writer (Albert Camus)", "Q7085": "known as physicist (Niels Bohr)",
                    "Q4573": "known as actor (Sean Connery)", "Q44980": "known as manager (Alex Ferguson)",
                    "Q79983": "known as manager (José Mourinho)", "Q18391": "known as writer (Elie Wiesel)",
                    "Q173139": "head of state (George Weah)", "Q57641": "politician (Viktor Orbán)"},
    },
    "soccer_clubs": {
        "where": "?item wdt:P31 wd:Q476028 .",
        "text": "Which is the greater soccer club?", "node": "world.sports.soccer.clubs_players",
        "exclude": {"Q478317": "sitelink-inflated (Coritiba)", "Q2674": "sitelink-inflated (Palermo)"},
        "rename": {"Q8682": "Real Madrid", "Q35933": "Corinthians", "Q207373": "Colo-Colo", "Q17479": "Flamengo",
                   "Q6601875": "Fenerbahçe"},
    },
    "tennis_players": {
        # P564 (singles record) marks professional players; drops royals tagged "tennis player"
        "where": "?item wdt:P31 wd:Q5 ; wdt:P106 wd:Q10833314 ; wdt:P564 ?rec .",
        "text": "Who is the greater tennis player?", "node": "world.sports.individual_sports", "person": True,
    },
    "f1_drivers": {
        "where": "?item wdt:P31 wd:Q5 ; wdt:P106 wd:Q10841764 .",
        "text": "Who is the greater Formula One driver?", "node": "world.sports.motorsport", "person": True,
        "exclude": {"Q172724": "not a driver of note (Bernie Ecclestone)"},
    },
    "cities": {
        "where": "?item wdt:P31/wdt:P279* wd:Q515 .",
        "text": "Which city would you rather visit?", "node": "world.places.cities",
        "exclude": {"Q1218": "contested (Jerusalem)", "Q43387": "sitelink-inflated (Edirne)",
                    "Q19689": "sitelink-inflated (Tirana)", "Q4361": "sitelink-inflated (Curitiba)",
                    "Q237": "a country (Vatican City)", "Q235": "a country (Monaco)"},
        "flag": {"Q649", "Q1899"},  # Moscow, Kyiv
    },
    "countries": {
        "where": "?item wdt:P31 wd:Q3624078 . MINUS { ?item wdt:P576 ?end }",
        "text": "Which country would you rather visit?", "node": "world.places.countries",
        "exclude": {"Q865": "contested (Taiwan)", "Q219060": "contested (Palestine)", "Q1246": "contested (Kosovo)"},
        "rename": {"Q148": "China"},
        "flag": {"Q159", "Q212", "Q801", "Q794"},  # Russia, Ukraine, Israel, Iran
    },
    "cuisines": {
        "where": "?item wdt:P31 wd:Q1968435 .",
        "text": "Which cuisine do you prefer?", "node": "world.food.cuisines",
        "rename": {"Q40578": "American cuisine", "Q792312": "Belgian cuisine"},
    },
    "dishes": {
        "where": "?item wdt:P31 wd:Q746549 .",
        "text": "Which dish would you rather eat?", "node": "world.food.dishes_ingredients",
        "exclude": {"Q192892": "a drink (ayran)", "Q827654": "a drink (lassi)", "Q523224": "not a dish (cooked rice)"},
    },
    "board_games": {
        "where": "?item wdt:P31 wd:Q131436 .",
        "text": "Which board game would you rather play?", "node": "world.sports.board_card_games",
        "exclude": {"Q1128406": "a way of playing chess (correspondence chess)", "Q750693": "a family of games (tafl)"},
        "rename": {"Q17271": "Catan"},
    },
    "car_brands": {
        "where": "?item wdt:P31 wd:Q786820 .",
        "text": "Which car brand do you prefer?", "node": "world.tech.vehicles",
        "exclude": {"Q27571": "sitelink-inflated (Donkervoort)", "Q6039733": "sitelink-inflated (Togg)",
                    "Q156578": "a group, not a brand (Volkswagen Group)", "Q81965": "a group, not a brand (General Motors)",
                    "Q181114": "a group, not a brand (Stellantis North America)"},
        "rename": {"Q23317": "Audi", "Q44294": "Ford", "Q181642": "Suzuki", "Q29637": "Škoda", "Q55931": "Hyundai",
                   "Q27530": "Mercedes-Benz", "Q30055": "Jaguar", "Q27074": "Aston Martin", "Q234803": "Rolls-Royce",
                   "Q36033": "Mitsubishi", "Q35349": "Kia"},
    },
    "scientists": {
        "where": "VALUES ?occ { wd:Q901 wd:Q169470 wd:Q170790 wd:Q593644 wd:Q864503 wd:Q11063 } "
                 "?item wdt:P31 wd:Q5 ; wdt:P106 ?occ .",
        "text": "Who is the greater scientist?", "node": "world.science.scientists_discoveries", "person": True,
        "kind": "evaluative",
        "exclude": {"Q762": "known as painter (Leonardo da Vinci)", "Q5879": "known as writer (Goethe)",
                    "Q9312": "known as philosopher (Immanuel Kant)", "Q9353": "known as philosopher (John Locke)",
                    "Q567": "politician (Angela Merkel)", "Q7416": "politician (Margaret Thatcher)",
                    "Q5580": "known as painter (Albrecht Dürer)", "Q9317": "an economist (John Maynard Keynes)"},
    },
    "programming_languages": {
        "where": "?item wdt:P31/wdt:P279* wd:Q9143 .",
        "text": "Which programming language do you prefer?", "node": "world.tech.software_programming",
        "exclude": {"Q46441": "a stylesheet language (CSS)", "Q8811": "a markup language (HTML)",
                    "Q165436": "a class of languages (assembly language)", "Q5301": "a typesetting system (TeX)",
                    "Q344266": "a framework (Active Server Pages)", "Q2115": "a markup language (XML)"},
        "rename": {"Q2378": "Visual Basic"},
    },
    "mammals": {
        "where": "?item wdt:P31 wd:Q16521 ; wdt:P105 wd:Q7432 ; wdt:P171* wd:Q7377 .",
        "text": "Which animal do you like more?", "node": "world.nature.mammals", "common_name": True,
    },
}


def _sparql(query: str) -> list[dict]:
    """QLever first (the transitive and aggregate queries time out on WDQS), WDQS as the fallback."""
    query = PREFIXES + query
    for endpoint, timeout in ((QLEVER, 90), (SPARQL, 60), (QLEVER, 120), (SPARQL, 60)):
        try:
            r = httpx.get(endpoint, params={"query": query}, timeout=timeout, follow_redirects=True,
                          headers={"User-Agent": UA, "Accept": "application/sparql-results+json"})
        except httpx.TimeoutException:
            continue
        if r.status_code != 200:
            time.sleep(5)
            continue
        return [{k: v["value"].rsplit("/", 1)[-1] if v.get("type") == "uri" else v["value"] for k, v in b.items()}
                for b in r.json()["results"]["bindings"]]
    raise RuntimeError("wikidata sparql failed on QLever and WDQS")


def _values(ids: list[str]) -> str:
    return " ".join(f"wd:{q}" for q in ids)


def _labels(ids: list[str]) -> dict[str, str]:
    """English label, else the language-neutral `mul` label."""
    out: dict[str, dict[str, str]] = {}
    for i in range(0, len(ids), 200):
        rows = _sparql(f"""SELECT ?item ?l (LANG(?l) AS ?lang) WHERE {{ VALUES ?item {{ {_values(ids[i : i + 200])} }}
  ?item rdfs:label ?l FILTER(LANG(?l) IN ("en", "mul")) }}""")
        for r in rows:
            out.setdefault(r["item"], {})[r["lang"]] = r["l"]
    return {q: v.get("en") or v.get("mul") for q, v in out.items()}


def _claims(ids: list[str], prop: str) -> dict[str, list[str]]:
    rows = _sparql(f"SELECT ?item ?v WHERE {{ VALUES ?item {{ {_values(ids)} }} ?item wdt:{prop} ?v }}")
    out: dict[str, list[str]] = {}
    for r in rows:
        out.setdefault(r["item"], []).append(r["v"])
    return {q: sorted(set(v)) for q, v in out.items()}


def _query(cat: dict) -> str:
    return f"SELECT DISTINCT ?item ?sitelinks WHERE {{ {cat['where']} ?item wikibase:sitelinks ?sitelinks . }} " \
           f"ORDER BY DESC(?sitelinks) ?item LIMIT {POOL}"


def fetch(raw_dir: Path) -> None:
    """SPARQL only (labels and claims too): the entity API rate-limits bulk label pulls."""
    for name, cat in CATEGORIES.items():
        out = raw_dir / f"{name}.json"
        if out.exists():
            continue
        rows = _sparql(_query(cat))
        ids = list(dict.fromkeys(r["item"] for r in rows))
        labels = _labels(ids)
        props = [p for p in (cat.get("cap", (None,))[0], cat.get("by")) if p]
        if cat.get("common_name"):
            props.append("P225")
        claims = {p: _claims(ids, p) for p in props}
        items = {q: {"label": labels.get(q), **{p: claims[p].get(q, []) for p in props}} for q in ids}
        by = cat.get("by")
        extra = sorted({v for it in items.values() for v in it.get(by, [])}) if by else []
        names = _labels(extra) if extra else {}
        out.write_text(json.dumps({"rows": rows, "items": items, "names": names}, ensure_ascii=False, indent=1))
        time.sleep(1)


def _latin(s: str) -> bool:
    return all(not ch.isalpha() or unicodedata.name(ch, "").startswith("LATIN") for ch in s)


def _display(label: str) -> str:
    return label[0].upper() + label[1:]


def _slug(name: str) -> str:
    s = name.replace("++", " plus plus").replace("#", " sharp")
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "_", s).strip("_")


def _top(name: str, cat: dict, raw_dir: Path) -> list[dict]:
    data = json.loads((raw_dir / f"{name}.json").read_text())
    exclude, rename = cat.get("exclude", {}), cat.get("rename", {})
    cap_prop, cap_n = cat.get("cap", (None, 0))
    seen_q, seen_slug, groups, out = set(), set(), {}, []
    for r in data["rows"]:
        q = r["item"]
        it = data["items"].get(q) or {}
        label = rename.get(q) or it.get("label")
        if q in seen_q or q in exclude or not label:
            continue
        seen_q.add(q)
        if not _latin(label) or "(" in label or (cat.get("person") and re.search(r"\d", label)):
            continue
        if cat.get("common_name") and label in it.get("P225", []):  # only a scientific name, no English one
            continue
        name_ = _display(label)
        slug = _slug(name_)
        if not slug or slug in seen_slug:
            continue
        by = [data["names"].get(v) for v in it.get(cat["by"], [])] if cat.get("by") else []
        if cat.get("by"):
            if len(by) != 1 or not by[0] or set(it[cat["by"]]) & set(cat.get("exclude_by", {})):  # compilations / uncredited: skip
                continue
            name_ = f"{name_} ({by[0]})"
        if cap_prop:
            keys = it.get(cap_prop, [])
            if any(groups.get(k, 0) >= cap_n for k in keys):
                continue
            for k in keys:
                groups[k] = groups.get(k, 0) + 1
        seen_slug.add(slug)
        out.append({"qid": q, "name": name_, "slug": slug, "sitelinks": int(r["sitelinks"])})
        if len(out) == TOP:
            break
    return out


def normalize(raw_dir: Path) -> Iterator[Question]:
    for name, cat in CATEGORIES.items():
        items = _top(name, cat, raw_dir)
        flag = cat.get("flag", set())
        for a, b in itertools.combinations(sorted(items, key=lambda x: (x["name"].casefold(), x["qid"])), 2):
            meta = {"qid_a": a["qid"], "qid_b": b["qid"], "sitelinks_a": a["sitelinks"], "sitelinks_b": b["sitelinks"],
                    "category": name, "pair": True}
            if {a["qid"], b["qid"]} & flag:
                meta["flags"] = ["political"]
            yield Question(
                text=cat["text"],
                primitive="choice",
                hemisphere="world",
                kind=cat.get("kind", "taste"),
                origin="template",
                source=NAME,
                options={a["slug"]: a["name"], b["slug"]: b["name"]},
                node_hint=cat["node"],
                source_item_id=f"{name}:{a['qid']}-{b['qid']}",
                license=LICENSE,
                template_id=f"g3.{name}",
                meta=meta,
            )


if __name__ == "__main__":  # preview: uv run python sources/goat_pairs/adapter.py
    from askjev.config import RAW

    for n, c in CATEGORIES.items():
        top = _top(n, c, RAW / NAME)
        print(f"{n} ({len(top)}): " + "; ".join(f"{t['name']} [{t['sitelinks']}]" for t in top))
