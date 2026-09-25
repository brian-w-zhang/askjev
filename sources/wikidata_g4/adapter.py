"""G4 Wikidata facts: categorical Choice questions (4 options, truth + 3 same-type distractors) about well-known
entities (>= 40 sitelinks): continents, countries, citizenship, scientific field, sport, official language,
capitals, birth century."""

from __future__ import annotations

import hashlib
import json
import random
import re
import time
import unicodedata
from pathlib import Path
from typing import Iterator

import httpx

from askjev.model import Question
from askjev.sampling import env_int, hash_order

NAME = "wikidata_g4"
WDQS = "https://query.wikidata.org/sparql"
QLEVER = "https://qlever.dev/api/wikidata"
UA = "askjev/0.1 (https://github.com/brian-w-zhang/askjev; research, cached pulls)"
LICENSE = "CC0 (Wikidata)"
MIN_SL = 40
PER_TEMPLATE = env_int("WIKIDATA_G4_PER_TEMPLATE", 1500)
SALT = "wikidata_g4.v1"
PREFIXES = """PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX wikibase: <http://wikiba.se/ontology#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX p: <http://www.wikidata.org/prop/>
PREFIX psv: <http://www.wikidata.org/prop/statement/value/>
"""
EN = 'FILTER(LANG(?{v}) = "en")'

# ---------------------------------------------------------------------------------------------- queries
# (name, endpoint order, query). Small class lists go to WDQS first; the human / city / landmark pulls
# rank millions of items by sitelinks and time out on WDQS (60 s), so they go to QLever first.
SOVEREIGN = "?item wdt:P31 wd:Q3624078 . MINUS { ?item wdt:P576 ?end }"
FIRST_LEVEL = "?item wdt:P31/wdt:P279* wd:Q10864048 . MINUS { ?item wdt:P576 ?end }"


def _top(pattern: str, limit: int) -> str:
    return f"{{ SELECT ?item ?sl WHERE {{ {pattern} ?item wikibase:sitelinks ?sl . }} ORDER BY DESC(?sl) LIMIT {limit} }}"


CITIES = _top("?item wdt:P31/wdt:P279* wd:Q515 .", 40000)
LANDMARKS = _top("?item wdt:P31/wdt:P279* wd:Q811979 .", 8000)
HUMANS = _top("?item wdt:P31 wd:Q5 .", 25000)


def _base(where: str) -> str:
    return f"SELECT DISTINCT ?item ?sl ?label WHERE {{ {where} OPTIONAL {{ ?item rdfs:label ?label {EN.format(v='label')} }} }}"


def _prop(where: str, path: str) -> str:
    return (f"SELECT DISTINCT ?item ?v ?vl WHERE {{ {where} ?item {path} ?v . "
            f"OPTIONAL {{ ?v rdfs:label ?vl {EN.format(v='vl')} }} }}")


SMALL, HEAVY = ("wdqs", "qlever"), ("qlever", "wdqs")
QUERIES: list[tuple[str, tuple[str, str], str]] = [
    ("countries", SMALL, _base(SOVEREIGN + " ?item wikibase:sitelinks ?sl .")),
    ("countries_P30", SMALL, _prop(SOVEREIGN, "wdt:P30")),
    ("countries_P36", SMALL, _prop(SOVEREIGN, "wdt:P36")),
    ("countries_P37", SMALL, _prop(SOVEREIGN, "wdt:P37")),
    ("countries_P47", SMALL, _prop(SOVEREIGN, "wdt:P47")),
    ("states", SMALL, _base(FIRST_LEVEL + " ?item wikibase:sitelinks ?sl .")),
    ("states_P17", SMALL, _prop(FIRST_LEVEL, "wdt:P17")),
    ("states_P36", SMALL, _prop(FIRST_LEVEL, "wdt:P36")),
    ("cities", HEAVY, _base(CITIES)),
    ("cities_P17", HEAVY, _prop(CITIES, "wdt:P17")),
    ("cities_state", HEAVY, f"SELECT DISTINCT ?item ?v WHERE {{ {CITIES} ?item wdt:P131+ ?v . "
                           f"?v wdt:P31/wdt:P279* wd:Q10864048 . }}"),
    ("landmarks", HEAVY, _base(LANDMARKS)),
    ("landmarks_P17", HEAVY, _prop(LANDMARKS, "wdt:P17")),
    ("landmarks_P31", HEAVY, _prop(LANDMARKS, "wdt:P31")),
    ("humans", HEAVY, _base(HUMANS)),
    ("humans_P27", HEAVY, _prop(HUMANS, "wdt:P27")),
    ("humans_P106", HEAVY, _prop(HUMANS, "wdt:P106")),
    ("humans_P641", HEAVY, _prop(HUMANS, "wdt:P641")),
    ("humans_birth_country", HEAVY, _prop(HUMANS, "wdt:P19/wdt:P17")),
    ("humans_P569", HEAVY, f"SELECT DISTINCT ?item ?t ?pr WHERE {{ {HUMANS} ?item p:P569/psv:P569 ?n . "
                          f"?n wikibase:timeValue ?t ; wikibase:timePrecision ?pr . }}"),
]


def _sparql(query: str, order: tuple[str, str]) -> list[dict]:
    urls = {"wdqs": WDQS, "qlever": QLEVER}
    for attempt, ep in enumerate(order * 2):
        time.sleep(1.0)  # <= 1 request/s
        try:
            r = httpx.get(urls[ep], params={"query": PREFIXES + query}, timeout=90, follow_redirects=True,
                          headers={"User-Agent": UA, "Accept": "application/sparql-results+json"})
            if r.status_code != 200:
                time.sleep(5 * (attempt + 1))
                continue
            rows = r.json()["results"]["bindings"]  # a WDQS timeout arrives as truncated JSON
        except (httpx.TimeoutException, ValueError):
            continue
        return [{k: v["value"].rsplit("/", 1)[-1] if v.get("type") == "uri" else v["value"] for k, v in b.items()}
                for b in rows]
    raise RuntimeError(f"wikidata sparql failed: {query[:120]}")


def fetch(raw_dir: Path) -> None:
    for name, order, query in QUERIES:
        out = raw_dir / f"{name}.json"
        if not out.exists():
            out.write_text(json.dumps(_sparql(query, order), ensure_ascii=False))


# ---------------------------------------------------------------------------------------------- vocab
CONTINENTS = {"Q15": "africa", "Q48": "asia", "Q46": "europe", "Q49": "north_america", "Q18": "south_america",
              "Q55643": "oceania", "Q538": "oceania", "Q3960": "oceania"}  # Eurasia/Antarctica: unused
CONTINENT_NODE = {"africa": "africa", "asia": "asia", "europe": "europe", "north_america": "americas",
                  "south_america": "americas", "oceania": "oceania"}
# Realm-level sovereign states whose places carry the constituent country in P17.
ALIAS = {"Q55": "Q29999", "Q35": "Q756617"}
RENAME = {"Q29999": "Netherlands", "Q756617": "Denmark", "Q148": "China"}
CONTINENT_OVERRIDE = {"Q29999": "europe", "Q756617": "europe"}
# Disputed or partially recognized states and occupied/contested territory: flag political, never a distractor.
DISPUTED = {"Q865", "Q219060", "Q1246", "Q801", "Q40362", "Q23681", "Q23427", "Q23334", "Q907112"}
# Location questions whose truth is itself contested (Jerusalem sites, anything placed in Palestine) are skipped,
# and a few non-landmarks that pass the type filter.
SKIP_LOCATED_COUNTRY = {"Q219060"}
SKIP_LANDMARK = {"Gethsemane", "Gehenna", "Western Wall", "Dome of the Rock", "Al-Aqsa Mosque", "Temple Mount",
                 "Church of the Holy Sepulchre", "Mount of Olives", "Rosetta Stone"}
DISPUTED_WORDS = re.compile(r"\b(Jerusalem|Crimea|Kashmir|Gaza|West Bank|Golan|Donetsk|Luhansk|Taiwan|Tibet)\b")
# Countries with a separate seat of government or a well-known co-capital: never offer that city as a
# wrong answer for the capital.
CO_SEATS = {"Q29999": {"The Hague"}, "Q962": {"Cotonou"}, "Q1008": {"Abidjan"}, "Q924": {"Dar es Salaam"},
            "Q833": {"Putrajaya"}, "Q298": {"Valparaíso"}, "Q236": {"Cetinje"}, "Q928": {"Quezon City"},
            "Q967": {"Bujumbura"}, "Q230": {"Kutaisi"}, "Q1033": {"Lagos"}, "Q232": {"Almaty"},
            "Q43": {"Istanbul"}, "Q843": {"Karachi"}, "Q183": {"Bonn"}, "Q695": {"Koror"}, "Q702": {"Kolonia"}}
# Capitals too unsettled for a single truth: Equatorial Guinea (Malabo vs Ciudad de la Paz), Nauru (no official capital).
SKIP_CAPITAL = {"Q983", "Q697"}
LANGUAGE_RENAME = {"Putonghua": "Mandarin Chinese"}

# Scientific occupation -> field key. `FAMILY` groups fields that overlap, so they are never distractors
# for each other.
FIELDS = {"Q169470": "physics", "Q593644": "chemistry", "Q170790": "mathematics", "Q864503": "biology",
          "Q11063": "astronomy", "Q188094": "economics", "Q212980": "psychology", "Q520549": "geology",
          "Q2374149": "botany", "Q350979": "zoology", "Q82594": "computer_science", "Q4773904": "anthropology",
          "Q2306091": "sociology", "Q14467526": "linguistics", "Q2919046": "biochemistry"}
FIELD_LABEL = {"computer_science": "computer science"}
FIELD_FAMILY = [{"biology", "botany", "zoology", "biochemistry"}, {"physics", "astronomy"},
                {"sociology", "anthropology"}, {"mathematics", "computer_science"}, {"chemistry", "biochemistry"}]
# Other occupations a scientist may also carry without making their field ambiguous.
SCI_GENERIC = {"Q901", "Q1650915", "Q1622272", "Q121594", "Q3400985", "Q205375", "Q81096", "Q36180", "Q15980158",
               "Q37226", "Q1231865", "Q18805", "Q482980", "Q18814623", "Q11774202", "Q333634", "Q16742096",
               "Q3055126", "Q19350898", "Q1930187", "Q42603"}

# P641 sport -> (key, display, node). `SPORT_FAMILY` groups close sports that are never distractors for each other.
SPORTS = {
    "Q2736": ("soccer", "soccer (association football)", "world.sports.soccer.clubs_players"),
    "Q847": ("tennis", None, "world.sports.individual_sports"),
    "Q542": ("athletics", "athletics (track and field)", "world.sports.individual_sports"),
    "Q5372": ("basketball", None, "world.sports.basketball"),
    "Q5386": ("auto_racing", "auto racing", "world.sports.motorsport"),
    "Q1968": ("auto_racing", "auto racing", "world.sports.motorsport"),  # Formula One: a kind of auto racing
    "Q328716": ("motorcycle_racing", "motorcycle racing", "world.sports.motorsport"),
    "Q178678": ("kickboxing", None, "world.sports.combat_sports"),
    "Q7856": ("rallying", None, "world.sports.motorsport"),
    "Q718": ("chess", None, "world.sports.board_card_games"),
    "Q131359": ("professional_wrestling", "professional wrestling", "world.sports.combat_sports"),
    "Q32112": ("boxing", None, "world.sports.combat_sports"),
    "Q114466": ("mixed_martial_arts", "mixed martial arts", "world.sports.combat_sports"),
    "Q11419": ("karate", None, "world.sports.combat_sports"),
    "Q11420": ("judo", None, "world.sports.combat_sports"),
    "Q36389": ("taekwondo", None, "world.sports.combat_sports"),
    "Q12100": ("fencing", None, "world.sports.individual_sports"),
    "Q31920": ("swimming", "competitive swimming", "world.sports.individual_sports"),
    "Q3609": ("cycling", None, "world.sports.individual_sports"),
    "Q41323": ("american_football", "American football", "world.sports.american_football"),
    "Q186222": ("alpine_skiing", "alpine skiing", "world.sports.individual_sports"),
    "Q179687": ("cross_country_skiing", "cross-country skiing", "world.sports.individual_sports"),
    "Q166788": ("biathlon", None, "world.sports.individual_sports"),
    "Q7718": ("ski_jumping", "ski jumping", "world.sports.individual_sports"),
    "Q41466": ("ice_hockey", "ice hockey", "world.sports.other_team_sports"),
    "Q5369": ("baseball", None, "world.sports.baseball"),
    "Q326827": ("gymnastics", "artistic gymnastics", "world.sports.individual_sports"),
    "Q5377": ("golf", None, "world.sports.individual_sports"),
    "Q38108": ("figure_skating", "figure skating", "world.sports.individual_sports"),
    "Q192431": ("speed_skating", "speed skating", "world.sports.individual_sports"),
    "Q5375": ("cricket", None, "world.sports.other_team_sports"),
    "Q7291": ("badminton", None, "world.sports.individual_sports"),
    "Q3930": ("table_tennis", "table tennis", "world.sports.individual_sports"),
    "Q11015": ("snooker", None, "world.sports.individual_sports"),
    "Q1734": ("volleyball", None, "world.sports.other_team_sports"),
    "Q83462": ("weightlifting", None, "world.sports.individual_sports"),
    "Q5849": ("rugby_union", "rugby union", "world.sports.other_team_sports"),
    "Q8418": ("handball", None, "world.sports.other_team_sports"),
}
# Athlete occupation (P106) -> the P641 sport it implies; P641 is missing on many athletes.
OCC_SPORT = {
    "Q937857": "Q2736", "Q10833314": "Q847", "Q11513337": "Q542", "Q3665646": "Q5372", "Q10349745": "Q5386",
    "Q10841764": "Q5386", "Q10873124": "Q718", "Q13474373": "Q131359", "Q2309784": "Q3609", "Q11338576": "Q32112",
    "Q4009406": "Q542", "Q10843402": "Q31920", "Q4144610": "Q186222", "Q19204627": "Q41323", "Q4439155": "Q542",
    "Q6665249": "Q11420", "Q10871364": "Q5369", "Q9017214": "Q11419", "Q11774891": "Q41466", "Q13381753": "Q542",
    "Q13382603": "Q7718", "Q13219587": "Q38108", "Q13382533": "Q36389", "Q12299841": "Q5375",
    "Q13381572": "Q326827", "Q3014296": "Q328716", "Q13382460": "Q542", "Q13382608": "Q179687",
    "Q11607585": "Q114466", "Q16029547": "Q166788", "Q11303721": "Q5377", "Q10842936": "Q7856",
    "Q13382122": "Q542", "Q11296761": "Q178678", "Q14089670": "Q5849", "Q10866633": "Q192431",
    "Q17165321": "Q11015", "Q13381376": "Q83462", "Q13381863": "Q12100", "Q13381428": "Q542",
    "Q13141064": "Q7291", "Q18510502": "Q542", "Q16947675": "Q326827", "Q12840545": "Q8418", "Q13381689": "Q542",
    "Q13724897": "Q542", "Q13464497": "Q542", "Q15117302": "Q1734", "Q15117395": "Q3609", "Q13382519": "Q3930",
    "Q17405793": "Q542", "Q13848274": "Q542", "Q21141393": "Q542", "Q21141381": "Q542", "Q18534714": "Q542",
}
SPORT_FAMILY = [{"auto_racing", "rallying", "motorcycle_racing"},
                {"professional_wrestling", "boxing", "mixed_martial_arts", "karate", "judo", "taekwondo", "kickboxing"},
                {"alpine_skiing", "cross_country_skiing", "biathlon", "ski_jumping"},
                {"figure_skating", "speed_skating"}, {"tennis", "table_tennis", "badminton"},
                {"soccer", "american_football", "rugby_union"}]
SPORT_CAP = {"soccer": 350}  # famous footballers dominate the >= 40-sitelink pool

SPORT_NODE = {k: node for k, _, node in SPORTS.values()}
SPORT_DISPLAY = {k: d for k, d, _ in SPORTS.values()}
POLITICIAN = {"Q82955", "Q372436", "Q2285706", "Q83307", "Q1238570"}
OCC_NODES = [  # first match wins
    (POLITICIAN, "world.society.politics_government"),
    ({"Q177220", "Q639669", "Q36834", "Q488205", "Q2252262", "Q855091", "Q486748", "Q753110", "Q158852",
      "Q55960555", "Q183945", "Q15981151"}, "world.arts.music.musicians_bands"),
    ({"Q33999", "Q10800557", "Q10798782", "Q2526255", "Q28389", "Q3282637", "Q2259451", "Q2405480"},
     "world.arts.film.filmmakers_actors"),
    ({"Q36180", "Q6625963", "Q49757", "Q214917", "Q4853732", "Q18844224", "Q482980"}, "world.arts.books.authors"),
    ({"Q169470"}, "world.science.physics.physicists"),
    (set(FIELDS) | {"Q901"}, "world.science.scientists_discoveries"),
    ({"Q1028181", "Q1281618", "Q483501", "Q33231", "Q3391743", "Q42973"}, "world.arts.visual_art"),
    ({"Q4964182"}, "world.society"),
    ({"Q116", "Q2304859", "Q1097498", "Q47064", "Q189290", "Q1402561", "Q11900058"}, "world.history.figures"),
]
# Occupations that make a person famous for something other than sport (P641 on actors, directors... is noise).
NON_SPORT = set().union(*(g for g, node in OCC_NODES if not node.startswith(("world.society.politics", "world.history"))))
ORD = {1: "st", 2: "nd", 3: "rd", 21: "st"}

LANDMARK_TYPE = re.compile(
    r"museum|palace|castle|château|cathedral|church|basilica|mosque|temple|bridge|tower|skyscraper|stadium|"
    r"archaeolog|monument|memorial|statue|pyramid|fortress|\bfort\b|citadel|abbey|monastery|opera house|theatre|"
    r"concert hall|arch\b|wall\b|mausoleum|tomb|observatory|ruins|ancient|square|gate|lighthouse|dam\b|canal|"
    r"shrine|wonder|landmark|palazzo|heritage|necropolis|amphitheatre|arena|venue|residence|colossal|"
    r"sculpture|pagoda|wat\b|stupa|synagogue|tunnel|garden|park\b|theme park|circuit|racing track|parliament|"
    r"library|pitch|cemetery|mission|chapel|minaret|sanctuary", re.I)
NOT_LANDMARK = re.compile(
    r"\b(city|town|village|settlement|municipality|commune|comune|airport|aerodrome|airbase|business|company|"
    r"enterprise|organization|organisation|chain|publisher|university|school|institute|neighborhood|"
    r"populated place|urban area|district|parish|island|telescope|spacecraft|ship|store|label|brand|"
    r"producer|brewery|distillery|seaport|port|destroyed|demolished|lost|former|defunct)\b|Wonder of the Ancient World",
    re.I)


# ---------------------------------------------------------------------------------------------- helpers
def _load(raw_dir: Path, name: str) -> list[dict]:
    return json.loads((raw_dir / f"{name}.json").read_text())


def _base_rows(raw_dir: Path, name: str) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for r in _load(raw_dir, name):
        it = out.setdefault(r["item"], {"sl": int(r["sl"]), "label": None})
        it["label"] = it["label"] or r.get("label")
    return out


def _values(raw_dir: Path, name: str, labels: dict[str, str] | None = None) -> dict[str, set[str]]:
    out: dict[str, set[str]] = {}
    for r in _load(raw_dir, name):
        out.setdefault(r["item"], set()).add(r["v"])
        if labels is not None and r.get("vl"):
            labels.setdefault(r["v"], r["vl"])
    return out


def _latin(s: str) -> bool:
    return all(not ch.isalpha() or unicodedata.name(ch, "").startswith("LATIN") for ch in s)


def _clean(label: str | None, person: bool = False) -> bool:
    if not label or re.fullmatch(r"Q\d+", label) or "(" in label or not _latin(label):
        return False
    return not (person and re.search(r"\d", label))


TRANSLIT = str.maketrans({"Đ": "D", "đ": "d", "Ø": "O", "ø": "o", "Ł": "L", "ł": "l", "ß": "ss", "Æ": "AE",
                          "æ": "ae", "Œ": "OE", "œ": "oe", "Þ": "Th", "þ": "th", "Ð": "D", "ð": "d", "ı": "i"})


def _slug(name: str) -> str:
    s = unicodedata.normalize("NFKD", name.translate(TRANSLIT)).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "_", s).strip("_")


def _rng(*parts: object) -> random.Random:
    return random.Random(int(hashlib.sha256("|".join(map(str, (SALT, *parts))).encode()).hexdigest()[:16], 16))


def _choice(tid: str, qid: str, truth: tuple[str, str | None], pool: list[tuple[str, str | None]]) -> tuple[dict, str] | None:
    """Truth + 3 distractors drawn from `pool` (distinct keys), shuffled deterministically."""
    seen, cands = {truth[0]}, []
    for k, d in pool:
        if k not in seen:
            seen.add(k)
            cands.append((k, d))
    if len(cands) < 3:
        return None
    r = _rng(tid, qid)
    opts = [truth, *r.sample(sorted(cands), 3)]
    r.shuffle(opts)
    return {k: d for k, d in opts}, truth[0]


class World:
    """Everything the templates need, loaded from the cached SPARQL pulls."""

    def __init__(self, raw_dir: Path):
        self.labels: dict[str, str] = {}
        c = _base_rows(raw_dir, "countries")
        self.country_label = {q: RENAME.get(q) or it["label"] for q, it in c.items()}
        p30 = _values(raw_dir, "countries_P30")
        self.continent: dict[str, str] = {}
        self.continents: dict[str, set[str]] = {}
        for q in c:
            conts = {CONTINENTS[v] for v in p30.get(q, ()) if v in CONTINENTS}
            if q in CONTINENT_OVERRIDE:
                conts = {CONTINENT_OVERRIDE[q]}
            self.continents[q] = conts
            if len(conts) == 1 and not (p30.get(q, set()) - set(CONTINENTS)):
                self.continent[q] = next(iter(conts))
        self.countries = {q: c[q] for q in c if _clean(self.country_label[q])}
        self.capital = _values(raw_dir, "countries_P36", self.labels)
        self.language = _values(raw_dir, "countries_P37", self.labels)
        self.borders = _values(raw_dir, "countries_P47")

        self.cities = _base_rows(raw_dir, "cities")
        self.city_country = {q: {ALIAS.get(v, v) for v in vs} for q, vs in _values(raw_dir, "cities_P17").items()}
        self.city_state = _values(raw_dir, "cities_state")
        self.states = _base_rows(raw_dir, "states")
        self.state_country = {q: {ALIAS.get(v, v) for v in vs} for q, vs in _values(raw_dir, "states_P17").items()}
        self.state_capital = _values(raw_dir, "states_P36", self.labels)
        self.landmarks = _base_rows(raw_dir, "landmarks")
        self.landmark_country = {q: {ALIAS.get(v, v) for v in vs} for q, vs in _values(raw_dir, "landmarks_P17").items()}
        lt_labels: dict[str, str] = {}
        self.landmark_types = _values(raw_dir, "landmarks_P31", lt_labels)
        self.type_label = lt_labels

        self.humans = _base_rows(raw_dir, "humans")
        self.citizenship = {q: {ALIAS.get(v, v) for v in vs} for q, vs in _values(raw_dir, "humans_P27").items()}
        self.birth_country = {q: {ALIAS.get(v, v) for v in vs} for q, vs in _values(raw_dir, "humans_birth_country").items()}
        self.occupations = _values(raw_dir, "humans_P106")
        self.sports = _values(raw_dir, "humans_P641")
        self.birth_years: dict[str, set[int]] = {}
        self.birth_precise: dict[str, bool] = {}
        for r in _load(raw_dir, "humans_P569"):
            t = r["t"]
            if t.startswith("-") or not re.match(r"\d{4}-", t):
                self.birth_years.setdefault(r["item"], set()).add(-1)
                continue
            self.birth_years.setdefault(r["item"], set()).add(int(t[:4]))
            self.birth_precise[r["item"]] = self.birth_precise.get(r["item"], True) and int(r["pr"]) >= 9

        # Ambiguous names: a label shared by two entities of the same kind (or a city named like a country/state).
        def dups(rows: dict[str, dict]) -> set[str]:
            seen: dict[str, int] = {}
            for it in rows.values():
                if it["label"]:
                    seen[it["label"]] = seen.get(it["label"], 0) + 1
            return {k for k, n in seen.items() if n > 1}

        self.dup_city = dups(self.cities) | set(self.country_label.values()) | {
            it["label"] for it in self.states.values() if it["label"]}
        self.dup_state = dups(self.states) | set(self.country_label.values())
        self.dup_human = dups(self.humans)
        self.dup_landmark = dups(self.landmarks)

    # -- pools
    def distractor_countries(self, truth: str) -> list[tuple[str, str]]:
        conts = self.continents.get(truth) or set()
        return [(_slug(self.country_label[q]), self.country_label[q]) for q in sorted(self.countries)
                if q != truth and q not in DISPUTED and self.continents.get(q, set()) & conts]

    def country_opt(self, q: str) -> tuple[str, str]:
        return _slug(self.country_label[q]), self.country_label[q]

    def person_node(self, q: str, born: int | None) -> str:
        occ = self.occupations.get(q, set())
        sp = sorted(self.sport_keys(q) & set(SPORT_NODE))
        if len(sp) == 1 and not occ & (POLITICIAN | NON_SPORT):
            return SPORT_NODE[sp[0]]
        for group, node in OCC_NODES:
            if occ & group:
                return node
        return "world.history.figures" if born is not None and born < 1900 else "world.arts.celebrities"

    def sport_keys(self, q: str) -> set[str]:
        """Sports from P641 plus athlete occupations; P641 values outside SPORTS count too (they make it ambiguous)."""
        ids = set(self.sports.get(q, ())) | {OCC_SPORT[o] for o in self.occupations.get(q, ()) if o in OCC_SPORT}
        return {SPORTS[i][0] if i in SPORTS else i for i in ids}

    def born(self, q: str) -> int | None:
        ys = self.birth_years.get(q, set())
        return next(iter(ys)) if len(ys) == 1 and -1 not in ys else None

    def person_ok(self, q: str) -> bool:
        it = self.humans[q]
        return it["sl"] >= MIN_SL and _clean(it["label"], person=True) and it["label"] not in self.dup_human

    def person_flags(self, q: str, extra: set[str] | None = None) -> list[str]:
        flags = set(extra or ())
        born = self.born(q)
        if self.occupations.get(q, set()) & POLITICIAN and (born is None or born >= 1900):
            flags.add("political")
        return sorted(flags)


def _q(text: str, options: dict, truth: str, node: str, tid: str, qid: str, meta: dict) -> Question:
    return Question(
        text=text,
        primitive="choice",
        hemisphere="world",
        kind="factual",
        origin="wikidata-fact",
        source=NAME,
        options=options,
        truth=truth,
        node_hint=node,
        source_item_id=f"{tid}:{qid}",
        license=LICENSE,
        template_id=f"g4.{tid}",
        meta={"qid": qid, **{k: v for k, v in meta.items() if v}},
    )


# ---------------------------------------------------------------------------------------------- templates
def _continents(w: World, cities: list[str]) -> Iterator[Question]:
    all_conts = sorted(set(CONTINENTS.values()))
    label = {k: k.replace("_", " ").title() for k in all_conts}
    pool = [(k, None) for k in all_conts]
    for q in sorted(w.countries, key=lambda q: (-w.countries[q]["sl"], q)):
        cont = w.continent.get(q)
        if not cont:
            continue
        name = w.country_label[q]
        opts, truth = _choice("continent", q, (cont, None), pool)
        flags = ["political"] if q in DISPUTED else []
        yield _q(f"Which continent is {name} in?", opts, truth, f"world.places.countries.{CONTINENT_NODE[cont]}",
                 "continent", q, {"entity": name, "entity_type": "country", "truth_label": label[cont], "flags": flags})
    for q in cities:
        (country,) = w.city_country[q]
        cont = w.continent[country]
        name = w.cities[q]["label"]
        opts, truth = _choice("continent", q, (cont, None), pool)
        flags = ["political"] if country in DISPUTED or DISPUTED_WORDS.search(name) else []
        yield _q(f"Which continent is the city of {name} in?", opts, truth, "world.places.cities", "continent", q,
                 {"entity": name, "entity_type": "city", "country": w.country_label[country],
                  "truth_label": label[cont], "flags": flags})


def _eligible_cities(w: World) -> list[str]:
    out = []
    for q, it in w.cities.items():
        name, cs = it["label"], w.city_country.get(q, set())
        if it["sl"] < MIN_SL or not _clean(name) or name in w.dup_city or len(cs) != 1:
            continue
        (country,) = cs
        if country not in w.countries or country not in w.continent or country in SKIP_LOCATED_COUNTRY:
            continue
        if w.country_label[country].casefold() in name.casefold():  # "Mexico City", "Kuwait City"
            continue
        out.append(q)
    return sorted(out, key=lambda q: (-w.cities[q]["sl"], q))


def _located(w: World, cities: list[str]) -> Iterator[Question]:
    landmarks = []
    for q, it in w.landmarks.items():
        name, cs = it["label"], w.landmark_country.get(q, set())
        types = {w.type_label.get(t, "") for t in w.landmark_types.get(q, ())}
        if it["sl"] < MIN_SL or not _clean(name) or name in w.dup_landmark or len(cs) != 1 or q in w.cities:
            continue
        if not any(LANDMARK_TYPE.search(t) for t in types) or any(NOT_LANDMARK.search(t) for t in types):
            continue
        (country,) = cs
        if country not in w.countries or w.country_label[country].casefold() in name.casefold():
            continue
        if country in SKIP_LOCATED_COUNTRY or name in SKIP_LANDMARK:
            continue
        landmarks.append(q)
    items = [("landmark", q) for q in sorted(landmarks, key=lambda q: (-w.landmarks[q]["sl"], q))]
    items += [("city", q) for q in cities]
    for kind, q in items[:PER_TEMPLATE]:
        if kind == "landmark":
            name, (country,) = w.landmarks[q]["label"], w.landmark_country[q]
            name = name[0].upper() + name[1:]  # "avenue des Champs-Élysées"
            text, node = f"In which country is the landmark {name} located?", "world.places.landmarks"
        else:
            name, (country,) = w.cities[q]["label"], w.city_country[q]
            text, node = f"In which country is the city of {name}?", "world.places.cities"
        res = _choice("country_of", q, w.country_opt(country), w.distractor_countries(country))
        if not res:
            continue
        flags = ["political"] if country in DISPUTED or DISPUTED_WORDS.search(name) else []
        yield _q(text, res[0], res[1], node, "country_of", q,
                 {"entity": name, "entity_type": kind, "truth_label": w.country_label[country], "flags": flags})


def _citizenship(w: World) -> Iterator[Question]:
    n = 0
    for q in sorted(w.humans, key=lambda q: (-w.humans[q]["sl"], q)):
        if n >= PER_TEMPLATE:
            break
        cs, born = w.citizenship.get(q, set()), w.born(q)
        if not w.person_ok(q) or len(cs) != 1 or born is None or born < 1900:
            continue
        (country,) = cs
        if country not in w.countries or w.birth_country.get(q) != {country}:
            continue
        res = _choice("citizenship", q, w.country_opt(country), w.distractor_countries(country))
        if not res:
            continue
        name = w.humans[q]["label"]
        n += 1
        yield _q(f"Which country is {name} from?", res[0], res[1], w.person_node(q, born), "citizenship", q,
                 {"entity": name, "entity_type": "person", "truth_label": w.country_label[country], "born": born,
                  "flags": w.person_flags(q, {"political"} if country in DISPUTED else set())})


def _field(w: World) -> Iterator[Question]:
    keys = sorted(set(FIELDS.values()))
    n = 0
    for q in sorted(w.humans, key=lambda q: (-w.humans[q]["sl"], q)):
        if n >= PER_TEMPLATE:
            break
        occ = w.occupations.get(q, set())
        fields = {FIELDS[o] for o in occ if o in FIELDS}
        if not w.person_ok(q) or len(fields) != 1 or occ - set(FIELDS) - SCI_GENERIC:
            continue
        (field,) = fields
        banned = set().union(*(f for f in FIELD_FAMILY if field in f), {field})
        pool = [(k, FIELD_LABEL.get(k)) for k in keys if k not in banned]
        res = _choice("field", q, (field, FIELD_LABEL.get(field)), pool)
        if not res:
            continue
        name = w.humans[q]["label"]
        n += 1
        node = "world.science.physics.physicists" if field == "physics" else "world.science.scientists_discoveries"
        yield _q(f"What is the primary field of {name}?", res[0], res[1], node, "field", q,
                 {"entity": name, "entity_type": "person", "truth_label": field, "born": w.born(q),
                  "flags": w.person_flags(q)})


def _sport(w: World) -> Iterator[Question]:
    per: dict[str, int] = {}
    n = 0
    all_sports = sorted({(k, d) for k, d, _ in SPORTS.values()})
    for q in sorted(w.humans, key=lambda q: (-w.humans[q]["sl"], q)):
        if n >= PER_TEMPLATE:
            break
        sp = w.sport_keys(q)
        if not w.person_ok(q) or len(sp) != 1 or next(iter(sp)) not in SPORT_NODE:
            continue
        if w.occupations.get(q, set()) & NON_SPORT:
            continue
        key = next(iter(sp))
        disp, node = SPORT_DISPLAY[key], SPORT_NODE[key]
        if per.get(key, 0) >= SPORT_CAP.get(key, PER_TEMPLATE):
            continue
        banned = set().union(*(f for f in SPORT_FAMILY if key in f), {key})
        res = _choice("sport", q, (key, disp), [(k, d) for k, d in all_sports if k not in banned])
        if not res:
            continue
        per[key] = per.get(key, 0) + 1
        n += 1
        name = w.humans[q]["label"]
        yield _q(f"Which sport is {name} known for?", res[0], res[1], node, "sport", q,
                 {"entity": name, "entity_type": "person", "truth_label": disp or key, "flags": w.person_flags(q)})


def _language(w: World) -> Iterator[Question]:
    single = {q: next(iter(v)) for q, v in w.language.items() if len(v) == 1 and q in w.countries}
    lang_label = {l: LANGUAGE_RENAME.get(w.labels.get(l), w.labels.get(l)) for l in set(single.values())}
    for q in sorted(single, key=lambda q: (-w.countries[q]["sl"], q)):
        lang, cont = single[q], w.continent.get(q)
        if not _clean(lang_label[lang]) or not cont:
            continue
        # distractors: official languages elsewhere on the same continent, minus the neighbors' languages
        near = {l for b in w.borders.get(q, ()) for l in w.language.get(b, ())}
        pool = sorted({(_slug(lang_label[l]), lang_label[l]) for c, l in single.items()
                       if l != lang and l not in near and w.continent.get(c) == cont and _clean(lang_label[l])})
        if len(pool) < 3:
            pool = sorted({(_slug(lang_label[l]), lang_label[l]) for l in set(single.values())
                           if l != lang and l not in near and _clean(lang_label[l])})
        name = w.country_label[q]
        res = _choice("language", q, (_slug(lang_label[lang]), lang_label[lang]), pool)
        if not res:
            continue
        flags = ["political"] if q in DISPUTED else []
        yield _q(f"What is the official language of {name}?", res[0], res[1],
                 f"world.places.countries.{CONTINENT_NODE[cont]}", "language", q,
                 {"entity": name, "entity_type": "country", "truth_label": lang_label[lang], "flags": flags})


def _capital(w: World) -> Iterator[Question]:
    city_rank = sorted(w.cities, key=lambda q: (-w.cities[q]["sl"], q))
    by_country: dict[str, list[str]] = {}
    by_state: dict[str, list[str]] = {}
    for q in city_rank:
        name = w.cities[q]["label"]
        if not _clean(name) or w.cities[q]["sl"] < 20:
            continue
        cs = w.city_country.get(q, set())
        if len(cs) == 1:
            by_country.setdefault(next(iter(cs)), []).append(q)
        for s in w.city_state.get(q, ()):
            by_state.setdefault(s, []).append(q)

    def pick(cands: list[str], capital: str, cap_label: str, banned: set[str]) -> list[tuple[str, str]]:
        out, seen = [], {cap_label.casefold()}
        for c in cands:
            lab = w.cities[c]["label"]
            if c == capital or lab.casefold() in seen or lab in banned:
                continue
            seen.add(lab.casefold())
            out.append((_slug(lab), lab))
            if len(out) == 3:
                break
        return out

    n = 0
    for q in sorted(w.countries, key=lambda q: (-w.countries[q]["sl"], q)):
        caps = w.capital.get(q, set())
        cont = w.continent.get(q) or next(iter(w.continents.get(q) or {"europe"}))
        if len(caps) != 1 or q in SKIP_CAPITAL:
            continue
        (cap,) = caps
        cap_label, name = w.labels.get(cap), w.country_label[q]
        if not _clean(cap_label) or cap_label.casefold() in name.casefold() or name.casefold() in cap_label.casefold():
            continue
        pool = pick(by_country.get(q, []), cap, cap_label, CO_SEATS.get(q, set()))
        if len(pool) < 3:  # small states: capitals of same-continent countries
            pool = [(_slug(w.labels[c2]), w.labels[c2]) for o in sorted(w.countries) if o != q and o not in DISPUTED
                    and w.continent.get(o) == cont for c2 in w.capital.get(o, ()) if _clean(w.labels.get(c2))]
        res = _choice("capital", q, (_slug(cap_label), cap_label), pool)
        if not res:
            continue
        n += 1
        flags = ["political"] if q in DISPUTED else []
        yield _q(f"What is the capital of {name}?", res[0], res[1], f"world.places.countries.{CONTINENT_NODE.get(cont, 'europe')}",
                 "capital", q, {"entity": name, "entity_type": "country", "truth_label": cap_label, "flags": flags})
    states = sorted((q for q, it in w.states.items() if it["sl"] >= STATE_MIN_SL),
                    key=lambda q: (-w.states[q]["sl"], q))
    siblings: dict[str, list[str]] = {}
    for q in states:
        cs = w.state_country.get(q, set())
        if len(cs) == 1:
            siblings.setdefault(next(iter(cs)), []).append(q)
    for q in states:
        if n >= PER_TEMPLATE:
            break
        name, cs, caps = w.states[q]["label"], w.state_country.get(q, set()), w.state_capital.get(q, set())
        if not _clean(name) or name in w.dup_state or len(cs) != 1 or len(caps) != 1:
            continue
        (country,), (cap,) = cs, caps
        cap_label = w.labels.get(cap)
        if country not in w.countries or not _clean(cap_label):
            continue
        if cap_label.casefold() in name.casefold() or name.casefold() in cap_label.casefold():
            continue
        pool = pick(by_state.get(q, []), cap, cap_label, set())
        if len(pool) < 3:
            pool = [(_slug(w.labels[c2]), w.labels[c2]) for s in siblings.get(country, []) if s != q
                    for c2 in w.state_capital.get(s, ()) if _clean(w.labels.get(c2)) and c2 != cap]
        res = _choice("capital", q, (_slug(cap_label), cap_label), pool)
        if not res:
            continue
        n += 1
        cont = w.continent.get(country, "europe")
        country_name = w.country_label[country]
        flags = ["political"] if country in DISPUTED or DISPUTED_WORDS.search(name) else []
        yield _q(f"What is the capital of {name}, {country_name}?", res[0], res[1],
                 f"world.places.countries.{CONTINENT_NODE[cont]}", "capital", q,
                 {"entity": name, "entity_type": "first-level subdivision", "country": country_name,
                  "truth_label": cap_label, "flags": flags})


def _century_label(c: int) -> str:
    return f"{c}{ORD.get(c, 'th')} century"


def _century(w: World) -> Iterator[Question]:
    per: dict[int, int] = {}
    n = 0
    for q in sorted(w.humans, key=lambda q: (-w.humans[q]["sl"], q)):
        if n >= PER_TEMPLATE:
            break
        born = w.born(q)
        if not w.person_ok(q) or born is None or not w.birth_precise.get(q) or not (1 <= born <= 2000):
            continue
        if born % 100 in (0, 1):  # boundary years read differently under the 1801-1900 vs 1800s conventions
            continue
        c = (born - 1) // 100 + 1
        if per.get(c, 0) >= CENTURY_CAP.get(c, PER_TEMPLATE):
            continue
        near = [x for x in (c - 1, c + 1, c - 2, c + 2, c - 3, c + 3) if 1 <= x <= 21][:4]
        pool = [(f"{x}{ORD.get(x, 'th')}_century", f"{_century_label(x)} ({(x - 1) * 100 + 1}-{x * 100})") for x in near]
        res = _choice("century", q, (f"{c}{ORD.get(c, 'th')}_century", f"{_century_label(c)} ({(c - 1) * 100 + 1}-{c * 100})"), pool)
        if not res:
            continue
        per[c] = per.get(c, 0) + 1
        n += 1
        name = w.humans[q]["label"]
        yield _q(f"In which century was {name} born?", res[0], res[1], w.person_node(q, born), "century", q,
                 {"entity": name, "entity_type": "person", "truth_label": _century_label(c), "born": born,
                  "flags": w.person_flags(q)})


STATE_MIN_SL = 60  # first-level subdivisions: bot-created wikis inflate provinces of a few countries
CENTURY_CAP = {20: 500, 19: 400}  # keep the century template from being mostly 20th-century people


def normalize(raw_dir: Path) -> Iterator[Question]:
    w = World(raw_dir)
    cities = _eligible_cities(w)
    # Cities alternate between the continent and country templates (most famous first) so none is asked twice.
    n_countries = sum(1 for q in w.countries if w.continent.get(q))
    cont_cities, loc_cities = cities[0::2], cities[1::2]
    yield from _continents(w, cont_cities[: max(0, PER_TEMPLATE - n_countries)])
    yield from _located(w, loc_cities)
    yield from _citizenship(w)
    yield from _field(w)
    yield from _sport(w)
    yield from _language(w)
    yield from _capital(w)
    yield from _century(w)
