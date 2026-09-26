"""Wikidata companies (money L1): which of two well-known companies employs more people, and the country
a company is headquartered in. Truth from Wikidata (P1128 employees, P159 headquarters -> P17 country)."""

from __future__ import annotations

import json
import re
import time
import unicodedata
from pathlib import Path
from typing import Iterator

import httpx

from askjev.model import Question
from askjev.sampling import env_int, hash_order

NAME = "wikidata_companies"
QLEVER = "https://qlever.dev/api/wikidata"
WDQS = "https://query.wikidata.org/sparql"
UA = "askjev/0.1 (github.com/brian-w-zhang/askjev)"
LICENSE = "CC0 (Wikidata)"
SALT = "wikidata_companies.v1"
N_EMPLOYEES = env_int("WIKIDATA_COMPANIES_EMPLOYEES", 1500)
N_HQ = env_int("WIKIDATA_COMPANIES_HQ", 1500)
MIN_SL = 25
MAX_PAIRS = 6
PREFIXES = """PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX wikibase: <http://wikiba.se/ontology#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
"""
# company, public company, enterprise, business, airline, bank, automobile manufacturer, brand-owning conglomerate
CLASSES = "wd:Q783794 wd:Q891723 wd:Q6881511 wd:Q4830453 wd:Q46970 wd:Q22687 wd:Q786820 wd:Q778575 wd:Q1589009"
QUERIES = {
    "companies": "SELECT ?item ?sl ?label ?emp ?hqc WHERE { { SELECT DISTINCT ?item ?sl WHERE { VALUES ?cls { "
                 + CLASSES + " } ?item wdt:P31 ?cls . ?item wikibase:sitelinks ?sl . } ORDER BY DESC(?sl) LIMIT 6000 } "
                 "?item rdfs:label ?label . FILTER(LANG(?label) = \"en\") OPTIONAL { ?item wdt:P1128 ?emp } "
                 "OPTIONAL { ?item wdt:P159 ?hq . ?hq wdt:P17 ?hqc } MINUS { ?item wdt:P576 ?end } }",
    "countries": "SELECT ?c ?label ?cont ?t WHERE { VALUES ?t { wd:Q3624078 wd:Q6256 } ?c wdt:P31 ?t . ?c wdt:P30 ?cont . "
                 "?c rdfs:label ?label . FILTER(LANG(?label) = \"en\") MINUS { ?c wdt:P576 ?end } }",
}
TECH_WORDS = re.compile(r"\b(software|semiconductor|Microsoft|Google|Apple|Intel|Nvidia|Samsung|Sony|Huawei|Xiaomi|"
                        r"IBM|Oracle|Cisco|Dell|HP|Lenovo|Meta|Facebook|Amazon|Tencent|Alibaba|Baidu|OpenAI|Netflix|"
                        r"Spotify|Uber|Airbnb|Tesla|AMD|Qualcomm|SAP|Adobe|Nokia|Ericsson|Toshiba|Panasonic|LG|"
                        r"Fujitsu|NEC|TSMC|ByteDance|PayPal|eBay|Yahoo|Twitter|X Corp|Snap|Zoom|Salesforce)\b")
POLITICAL_COUNTRIES = {"Q159", "Q212", "Q801", "Q794"}  # Russia, Ukraine, Israel, Iran
DISPUTED = {"Q865", "Q219060", "Q1246"}  # Taiwan, Palestine, Kosovo: never truth or distractor
DEMONYM = {"Q30": ["America", "American", "US", "U.S."], "Q145": ["Britain", "British", "UK", "England", "English",
           "Scotland", "Scottish", "Wales", "Welsh"], "Q142": ["France", "French", "Paris"], "Q183": ["Germany", "German",
           "Deutsche", "Deutschland"], "Q17": ["Japan", "Japanese", "Nippon", "Tokyo"], "Q148": ["China", "Chinese",
           "Sino"], "Q38": ["Italy", "Italian", "Italia"], "Q29": ["Spain", "Spanish", "España", "Iberia"],
           "Q16": ["Canada", "Canadian"], "Q408": ["Australia", "Australian", "Qantas"], "Q668": ["India", "Indian",
           "Bharat"], "Q155": ["Brazil", "Brasil", "Brazilian"], "Q159": ["Russia", "Russian", "Rossiya"],
           "Q884": ["Korea", "Korean"], "Q39": ["Swiss", "Switzerland"], "Q55": ["Dutch", "Netherlands", "Holland"],
           "Q34": ["Sweden", "Swedish", "Svenska"], "Q20": ["Norway", "Norwegian", "Norsk"], "Q35": ["Denmark", "Danish",
           "Danske"], "Q33": ["Finland", "Finnish", "Finnair"], "Q96": ["Mexico", "Mexican", "México"],
           "Q45": ["Portugal", "Portuguese"], "Q40": ["Austria", "Austrian"], "Q31": ["Belgium", "Belgian"],
           "Q43": ["Turkey", "Turkish", "Türk"], "Q36": ["Poland", "Polish", "Polska"], "Q27": ["Ireland", "Irish"],
           "Q41": ["Greece", "Greek", "Hellenic"], "Q851": ["Saudi"], "Q878": ["Emirates", "Dubai", "Abu Dhabi"],
           "Q252": ["Indonesia", "Garuda"], "Q334": ["Singapore"], "Q928": ["Philippine"], "Q869": ["Thai"],
           "Q881": ["Vietnam"], "Q833": ["Malaysia"], "Q664": ["New Zealand"], "Q258": ["South Africa"],
           "Q79": ["Egypt"], "Q414": ["Argentin"], "Q298": ["Chile"], "Q739": ["Colombia"], "Q419": ["Peru"],
           "Q843": ["Pakistan"], "Q794": ["Iran"], "Q801": ["Israel", "El Al"], "Q212": ["Ukrain"],
           "Q28": ["Hungar", "Magyar"], "Q213": ["Czech"], "Q218": ["Romania"], "Q219": ["Bulgaria"],
           "Q1028": ["Morocco", "Maroc"], "Q1033": ["Nigeria"], "Q114": ["Kenya"], "Q115": ["Ethiopia"]}


def _sparql(query: str) -> list[dict]:
    for attempt, ep in enumerate([QLEVER, WDQS, QLEVER, WDQS]):
        time.sleep(1.0)
        try:
            r = httpx.post(ep, data={"query": PREFIXES + query}, timeout=180,
                           headers={"User-Agent": UA, "Accept": "application/sparql-results+json"})
            if r.status_code == 200:
                rows = r.json()["results"]["bindings"]
                return [{k: v["value"].rsplit("/", 1)[-1] if v.get("type") == "uri" else v["value"]
                         for k, v in b.items()} for b in rows]
        except (httpx.TimeoutException, ValueError):
            pass
        time.sleep(5 * (attempt + 1))
    raise RuntimeError(f"sparql failed: {query[:100]}")


def fetch(raw_dir: Path) -> None:
    for name, q in QUERIES.items():
        out = raw_dir / f"{name}.json"
        if not out.exists():
            out.write_text(json.dumps(_sparql(q), ensure_ascii=False))


def _slug(name: str) -> str:
    s = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().lower()
    s = re.sub(r"&", " and ", s)
    return re.sub(r"[^a-z0-9]+", "_", s).strip("_")


def _companies(raw_dir: Path, countries: dict) -> list[dict]:
    acc: dict[str, dict] = {}
    for r in json.loads((raw_dir / "companies.json").read_text()):
        d = acc.setdefault(r["item"], {"id": r["item"], "sl": int(r["sl"]), "label": r["label"], "emp": set(), "hq": set()})
        if r.get("emp"):
            d["emp"].add(float(r["emp"]))
        if r.get("hqc"):
            d["hq"].add(r["hqc"])
    labels = [d["label"] for d in acc.values()]
    out = []
    for d in sorted(acc.values(), key=lambda d: (-d["sl"], d["id"])):
        lab = d["label"]
        if d["sl"] < MIN_SL or labels.count(lab) > 1 or "(" in lab or not _slug(lab) or not all(ord(c) < 0x250 for c in lab):
            continue
        emp = sorted(d["emp"])
        d["employees"] = emp[-1] if emp and emp[-1] >= 50 and emp[-1] <= 1.3 * emp[0] else None
        d["country"] = next(iter(d["hq"])) if len(d["hq"]) == 1 and next(iter(d["hq"])) in countries else None
        d["node"] = "world.tech.companies" if TECH_WORDS.search(lab) else "world.money.companies_brands"
        out.append(d)
    return out


def _fmt(x: float) -> str:
    return f"{int(x):,}"


def _employees(cos: list[dict]) -> Iterator[Question]:
    pool = [c for c in cos if c["employees"]]
    pairs = [(a, b) for i, a in enumerate(pool) for b in pool[i + 1:]]
    uses: dict[str, int] = {}
    taken = 0
    for a, b in hash_order(pairs, lambda p: f"{p[0]['id']}|{p[1]['id']}", SALT + ".emp"):
        if taken >= N_EMPLOYEES:
            break
        hi, lo = (a, b) if a["employees"] > b["employees"] else (b, a)
        if hi["employees"] < 3 * lo["employees"]:
            continue
        if uses.get(a["id"], 0) >= MAX_PAIRS or uses.get(b["id"], 0) >= MAX_PAIRS:
            continue
        ka, kb = _slug(a["label"]), _slug(b["label"])
        if ka == kb:
            continue
        uses[a["id"]] = uses.get(a["id"], 0) + 1
        uses[b["id"]] = uses.get(b["id"], 0) + 1
        taken += 1
        first, second = hash_order([a, b], lambda x: x["id"], SALT + ".order")
        node = a["node"] if a["node"] == b["node"] else "world.money.companies_brands"
        flags = ["political"] if {a["country"], b["country"]} & POLITICAL_COUNTRIES else []
        yield Question(
            text=f"Which company employs more people: {first['label']} or {second['label']}?",
            primitive="choice", hemisphere="world", kind="factual", origin="wikidata-fact", source=NAME,
            options={_slug(first["label"]): first["label"], _slug(second["label"]): second["label"]},
            node_hint=node, source_item_id=f"emp:{a['id']}-{b['id']}", license=LICENSE, truth=_slug(hi["label"]),
            template_id="wikidata_companies.more_employees",
            meta={"qids": [a["id"], b["id"]], "employees": [a["employees"], b["employees"]],
                  **({"flags": flags} if flags else {})},
        )


def _hq(cos: list[dict], countries: dict, sovereign: set) -> Iterator[Question]:
    by_cont: dict[str, list[str]] = {}
    for c, (_, conts) in countries.items():
        for ct in conts:
            by_cont.setdefault(ct, []).append(c)
    # rank countries by how many companies are based there: distractors are plausible business homes
    weight: dict[str, int] = {}
    for c in cos:
        if c["country"]:
            weight[c["country"]] = weight.get(c["country"], 0) + 1
    taken = 0
    for co in hash_order([c for c in cos if c["country"]], lambda c: c["id"], SALT + ".hq"):
        if taken >= N_HQ:
            break
        c = co["country"]
        name, conts = countries[c]
        words = DEMONYM.get(c, []) + [name]
        if any(re.search(rf"\b{re.escape(w)}", co["label"], re.I) for w in words):
            continue
        ok = [x for x in sovereign if x != c and x not in POLITICAL_COUNTRIES and weight.get(x, 0) >= 5]
        same = sorted({x for x in ok if countries[x][1] & conts}, key=lambda x: (-weight.get(x, 0), x))[:10]
        if len(same) < 6:  # thin continent (North America): top business homes elsewhere fill in
            same += sorted((x for x in ok if x not in same), key=lambda x: (-weight.get(x, 0), x))[:6 - len(same)]
        names = {name}
        distract = []
        for x in hash_order(same, lambda x: f"{co['id']}|{x}", SALT + ".hqd"):
            if countries[x][0] not in names:
                names.add(countries[x][0])
                distract.append(x)
            if len(distract) == 3:
                break
        if len(distract) < 3:
            continue
        opts = hash_order([c, *distract], lambda x: f"{co['id']}|{x}", SALT + ".hqo")
        flags = ["political"] if set(opts) & POLITICAL_COUNTRIES else []
        taken += 1
        yield Question(
            text=f"In which country is the company {co['label']} headquartered?",
            primitive="choice", hemisphere="world", kind="factual", origin="wikidata-fact", source=NAME,
            options={_slug(countries[o][0]): countries[o][0] for o in opts},
            node_hint=co["node"], source_item_id=f"hq:{co['id']}", license=LICENSE, truth=_slug(name),
            template_id="wikidata_companies.hq_country",
            meta={"qid": co["id"], "country": c, **({"flags": flags} if flags else {})},
        )


def normalize(raw_dir: Path) -> Iterator[Question]:
    countries: dict[str, tuple[str, set]] = {}
    sovereign: set[str] = set()  # distractors: sovereign states only (no Greenland, Curaçao...)
    for r in json.loads((raw_dir / "countries.json").read_text()):
        if r["c"] in DISPUTED:
            continue
        if r["t"] == "Q3624078" or r["c"] in {"Q55", "Q35"}:  # the Netherlands/Denmark proper are typed "country"
            sovereign.add(r["c"])
        name, conts = countries.get(r["c"], (r["label"], set()))
        conts.add(r["cont"])
        countries[r["c"]] = (name, conts)
    rename = {"People's Republic of China": "China", "Kingdom of the Netherlands": "Netherlands",
              "Kingdom of Denmark": "Denmark"}
    countries = {c: (rename.get(n, n), conts) for c, (n, conts) in countries.items()}
    cos = _companies(raw_dir, countries)
    yield from _employees(cos)
    yield from _hq(cos, countries, sovereign)
