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
from askjev.sampling import env_int

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


# Wave 4 categories, appended after the originals. ASKJEV_TARGET_GOAT_PAIRS picks how many categories run
# (300 pairs each, in this order): unset = the original 22 (6,600 rows, byte-identical), 11100 = all 37.
# `only` = a hand-picked allowlist (QIDs, still ranked by sitelinks) where the occupation tag is too noisy for an
# exclude list (Wikidata tags Marx, Einstein, Picasso and Mao as poets/philosophers); `pool` = candidates pulled.
_POETS = ("Q692 Q5879 Q1067 Q535 Q1398 Q7200 Q7241 Q16867 Q5679 Q5676 Q7198 Q7071 Q501 Q5683 Q7011 Q6197 Q35900 "
          "Q44403 Q34189 Q6240 Q1401 Q41513 Q37767 Q43347 Q79759 Q81438 Q17892 Q493 Q41408 Q93343 Q45546 Q76483 "
          "Q168728")
_PHILOSOPHERS = ("Q868 Q4604 Q859 Q913 Q9068 Q9358 Q9312 Q9191 Q6527 Q1399 Q8018 Q9333 Q9353 Q9438 Q9047 Q34670 "
                 "Q9364 Q8011 Q9235 Q7197 Q33760 Q35802 Q1430 Q38193 Q9391 Q6512 Q37621 Q37160 Q2054 Q43216 Q48301")
WAVE4_CATEGORIES: dict[str, dict] = {
    "composers": {
        # at least 5 credited symphonies, operas, concertos, sonatas, quartets or other compositions
        "where": "?item wdt:P31 wd:Q5 ; wdt:P106 wd:Q36834 . { SELECT ?item WHERE { ?w wdt:P86 ?item ; wdt:P31 ?t . "
                 "VALUES ?t { wd:Q9734 wd:Q58483083 wd:Q35760 wd:Q131269 wd:Q2994303 wd:Q207628 wd:Q182906 "
                 "wd:Q211025 } } GROUP BY ?item HAVING (COUNT(DISTINCT ?w) >= 5) }",
        "text": "Who is the greater composer?", "node": "world.arts.music.musicians_bands", "person": True,
    },
    "film_directors": {
        # at least 8 directed films
        "where": "?item wdt:P31 wd:Q5 ; wdt:P106 wd:Q2526255 . { SELECT ?item WHERE { ?f wdt:P31 wd:Q11424 ; "
                 "wdt:P57 ?item } GROUP BY ?item HAVING (COUNT(?f) >= 8) }",
        "text": "Who is the greater film director?", "node": "world.arts.film.filmmakers_actors", "person": True,
        "exclude": {"Q8704": "known as producer (Walt Disney)", "Q5603": "known as artist (Andy Warhol)",
                    "Q36970": "known as actor (Jackie Chan)", "Q23844": "known as actor (George Clooney)",
                    "Q40026": "known as actor (Sylvester Stallone)", "Q127330": "known as musician (Frank Zappa)",
                    "Q83158": "known as poet (Jean Cocteau)", "Q104049": "known as actor (Sidney Poitier)",
                    "Q44221": "known as actor (Sean Penn)", "Q59215": "known as actor (Robert Redford)"},
    },
    "poets": {
        "where": "?item wdt:P31 wd:Q5 ; wdt:P106 wd:Q49757 ; wdt:P800 ?w .",
        "text": "Who is the greater poet?", "node": "world.arts.books.authors", "person": True, "pool": 150,
        "only": set(_POETS.split()),
    },
    "philosophers": {
        "where": "?item wdt:P31 wd:Q5 ; wdt:P106 wd:Q4964182 .",
        "text": "Who is the greater philosopher?", "node": "world.society.philosophy_thinkers", "person": True,
        "kind": "evaluative", "pool": 150, "only": set(_PHILOSOPHERS.split()),
    },
    "architects": {
        # at least 5 buildings credited
        "where": "?item wdt:P31 wd:Q5 ; wdt:P106 wd:Q42973 . { SELECT ?item WHERE { ?b wdt:P84 ?item } "
                 "GROUP BY ?item HAVING (COUNT(?b) >= 5) }",
        "text": "Who is the greater architect?", "node": "world.arts.architecture_design", "person": True,
        "exclude": {"Q5592": "known as painter and sculptor (Michelangelo)", "Q11812": "head of state (Thomas Jefferson)",
                    "Q5597": "known as painter (Raphael)", "Q46830": "known as scientist (Robert Hooke)",
                    "Q20882": "an engineer (Gustave Eiffel)", "Q128027": "known as painter and biographer (Giorgio Vasari)"},
    },
    "fashion_designers": {
        # singers, actors, models, TV personalities, politicians and businesspeople with a clothing line drop out
        "where": "?item wdt:P31 wd:Q5 ; wdt:P106 wd:Q3501317 . MINUS { ?item wdt:P106 ?o . VALUES ?o { wd:Q177220 "
                 "wd:Q33999 wd:Q10800557 wd:Q10798782 wd:Q82955 wd:Q947873 wd:Q2405480 wd:Q4610556 wd:Q639669 "
                 "wd:Q2259451 wd:Q43845 wd:Q245068 wd:Q488111 wd:Q753110 wd:Q18814623 } }",
        "text": "Who is the greater fashion designer?", "node": "world.arts.fashion", "person": True,
        "exclude": {"Q231776": "known as dancer (Margot Fonteyn)", "Q231121": "known as artist (Yayoi Kusama)",
                    "Q234601": "known as sculptor (Vera Mukhina)", "Q214666": "known as painter (Léon Bakst)",
                    "Q232391": "known as painter (Natalia Goncharova)", "Q232972": "known as painter (Sonia Delaunay)",
                    "Q312631": "known as artist (Alexander Rodchenko)", "Q221454": "known as tennis player (René Lacoste)",
                    "Q312639": "known as tennis player (Fred Perry)", "Q322060": "known as writer (Douglas Coupland)",
                    "Q22997426": "public figure (Akshata Murty)", "Q259594": "known as painter (Lyubov Popova)",
                    "Q45870": "known as interior designer (Gauri Khan)", "Q38785": "known as painter (Mikhail Larionov)",
                    "Q449173": "public figure (Carolyn Bessette-Kennedy)",
                    "Q111588744": "known as artist (Lyubov Panchenko)"},
    },
    "operas": {
        "where": "?item wdt:P31 wd:Q58483083 ; wdt:P136 wd:Q1344 .",
        "text": "Which is the better opera?", "node": "world.arts.music.albums_songs", "cap": ("P86", 3), "by": "P86",
    },
    "animated_series": {
        "where": "?item wdt:P31 wd:Q117467246 .",
        "text": "Which is the better animated series?", "node": "world.arts.television.cartoons_anime",
        "cap": ("P179", 1),
        "exclude": {"Q104750296": "sitelink-inflated (Go, Dog. Go!)",
                    "Q16494556": "sitelink-inflated (As Aventuras de Gui & Estopa)"},
    },
    "video_game_consoles": {
        # concrete console models (product model / console model), subclasses of video game console
        "where": "VALUES ?t { wd:Q10929058 wd:Q62008942 wd:Q115187350 } ?item wdt:P31 ?t ; "
                 "wdt:P279/wdt:P279* wd:Q8076 .",
        "text": "Which video game console do you prefer?", "node": "world.sports.video_games",
        "rename": {"Q744987": "Magnavox Odyssey"},
    },
    "sports_cars": {
        "where": "?item wdt:P31 wd:Q3231690 ; wdt:P279 wd:Q274586 .",
        "text": "Which sports car would you rather drive?", "node": "world.tech.vehicles",
        "exclude": {"Q1463050": "a sedan (Tesla Model S)"},
    },
    "dog_breeds": {
        "where": "?item wdt:P31 wd:Q39367 .",
        "text": "Which dog breed do you like more?", "node": "world.nature.pets_breeds",
        "exclude": {"Q38584": "a wild canid (dingo)"},
    },
    "national_parks": {
        "where": "?item wdt:P31 wd:Q46169 .",
        "text": "Which national park would you rather visit?", "node": "world.places.physical_geography",
        "exclude": {"Q80344": "a mountain (Mount Olympus)"},
        "rename": {"Q235878": "Keoladeo National Park"},
    },
    "islands": {
        # islands that are not themselves sovereign states
        "where": "?item wdt:P31 wd:Q23442 . MINUS { ?item wdt:P31 wd:Q3624078 }",
        "text": "Which island would you rather visit?", "node": "world.places.physical_geography",
        "exclude": {"Q23666": "most of a country (Great Britain)", "Q22890": "a country's island (Ireland)",
                    "Q14056": "uninhabited, closed to visitors (Jan Mayen)", "Q23408": "uninhabited (Bouvet Island)",
                    "Q25359": "uninhabited (Navassa Island)", "Q22502": "contested (Taiwan Island)"},
    },
    "cathedrals": {
        "where": "?item wdt:P31/wdt:P279* wd:Q2977 .",
        "text": "Which cathedral would you rather visit?", "node": "world.places.landmarks",
    },
    "stadiums": {
        "where": "?item wdt:P31/wdt:P279* wd:Q483110 .",
        "text": "Which stadium would you rather watch a game in?", "node": "world.places.landmarks",
        "exclude": {"Q10285": "an ancient amphitheatre (Colosseum)"},
    },
}
PAIRS_PER_CATEGORY = TOP * (TOP - 1) // 2
N_CATEGORIES = env_int("TARGET_GOAT_PAIRS", len(CATEGORIES) * PAIRS_PER_CATEGORY) // PAIRS_PER_CATEGORY
ACTIVE = dict(list((CATEGORIES | WAVE4_CATEGORIES).items())[:N_CATEGORIES])


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
           f"ORDER BY DESC(?sitelinks) ?item LIMIT {cat.get('pool', POOL)}"


def fetch(raw_dir: Path) -> None:
    """SPARQL only (labels and claims too): the entity API rate-limits bulk label pulls."""
    for name, cat in ACTIVE.items():
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
        if q in seen_q or q in exclude or not label or ("only" in cat and q not in cat["only"]):
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
    for name, cat in ACTIVE.items():
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

    for n, c in ACTIVE.items():
        top = _top(n, c, RAW / NAME)
        print(f"{n} ({len(top)}): " + "; ".join(f"{t['name']} [{t['sitelinks']}]" for t in top))
