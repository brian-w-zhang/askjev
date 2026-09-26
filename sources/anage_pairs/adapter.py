"""AnAge (Human Ageing Genomic Resources) life-history pairs: which of two well-known animals lives longer,
carries its young longer, has eggs that take longer to hatch, has more young at once, or matures later."""

from __future__ import annotations

import csv
import io
import itertools
import json
import re
import time
import unicodedata
import zipfile
from pathlib import Path
from typing import Iterator

import httpx

from askjev.model import Question
from askjev.sampling import env_int, hash_order

NAME = "anage_pairs"
URL = "https://genomics.senescence.info/species/dataset.zip"
QLEVER = "https://qlever.dev/api/wikidata"
UA = "askjev/0.1 (github.com/brian-w-zhang/askjev)"
LICENSE = "CC BY 3.0 (AnAge, Human Ageing Genomic Resources; de Magalhaes et al. 2024, NAR); Wikidata sitelinks CC0"
SALT = "anage_pairs.v1"
TARGET = env_int("TARGET_ANAGE_PAIRS", 5000)
MAX_PER_SPECIES = 12
# Wikidata sitelinks floor per class: keeps the widely known species (bot-made wikis inflate small birds and fish).
MIN_SITELINKS = {"Mammalia": 45, "Aves": 50, "Reptilia": 35, "Amphibia": 25, "Teleostei": 25, "Chondrichthyes": 25}
DEFAULT_MIN_SITELINKS = 30

# (template, AnAge column, ratio, share of TARGET, text, applies-to filter)
TEMPLATES = [
    ("longevity", "Maximum longevity (yrs)", 2.0, 0.40,
     "Which animal has the longer maximum recorded lifespan: the {a} or the {b}?", None),
    ("gestation", "Gestation/Incubation (days)", 1.5, 0.15,
     "Which animal's pregnancy lasts longer: the {a} or the {b}?", {"Mammalia"}),
    ("incubation", "Gestation/Incubation (days)", 1.5, 0.15,
     "Whose eggs take longer to hatch: the {a} or the {b}?", {"Aves", "Reptilia"}),
    ("litter", "Litter/Clutch size", 2.0, 0.15,
     "Which animal usually has more young in a single litter or clutch: the {a} or the {b}?", {"Mammalia", "Aves", "Reptilia"}),
    ("maturity", "Female maturity (days)", 2.0, 0.15,
     "Which animal takes longer to become old enough to breed: the {a} or the {b}?", None),
]
FISH = {"Teleostei", "Chondrichthyes", "Chondrostei", "Holostei", "Cephalaspidomorphi", "Actinopterygii", "Dipnoi",
        "Coelacanthi", "Cladistei"}
ORDER_NODE = {"Primates": "world.nature.mammals.primate", "Rodentia": "world.nature.mammals.rodent"}
CLASS_NODE = {"Mammalia": "world.nature.mammals.mammal", "Aves": "world.nature.birds.bird",
              "Reptilia": "world.nature.reptiles_insects.reptile", "Amphibia": "world.nature.reptiles_insects.amphibian",
              "Insecta": "world.nature.reptiles_insects.insect", "Bivalvia": "world.nature.sea_life.mollusca",
              "Cephalopoda": "world.nature.sea_life.mollusca", "Gastropoda": "world.nature.sea_life.mollusca",
              "Malacostraca": "world.nature.sea_life.crustacean"}
SKIP = {"Homo sapiens"}
RENAME = {"Clangula hyemalis": "long-tailed duck"}  # AnAge/Wikidata variants retired or ambiguous


def _sparql(query: str) -> list[dict]:
    for attempt in range(4):
        time.sleep(1.0)
        try:
            r = httpx.post(QLEVER, data={"query": query}, timeout=120,
                           headers={"User-Agent": UA, "Accept": "application/sparql-results+json"})
            if r.status_code == 200:
                return r.json()["results"]["bindings"]
        except (httpx.TimeoutException, ValueError):
            pass
        time.sleep(5 * (attempt + 1))
    raise RuntimeError("qlever failed")


def _rows(raw_dir: Path) -> list[dict]:
    with zipfile.ZipFile(raw_dir / "dataset.zip") as z:
        text = z.read("anage_data.txt").decode("latin1")
    return list(csv.DictReader(io.StringIO(text), delimiter="\t"))


def fetch(raw_dir: Path) -> None:
    z = raw_dir / "dataset.zip"
    if not z.exists():
        r = httpx.get(URL, timeout=120, follow_redirects=True)
        r.raise_for_status()
        z.write_bytes(r.content)
    names = sorted({f"{x['Genus']} {x['Species']}" for x in _rows(raw_dir)})
    lab = raw_dir / "labels.json"
    if not lab.exists():
        labels: dict[str, str] = {}
        for i in range(0, len(names), 500):
            vals = " ".join(json.dumps(n) for n in names[i:i + 500])
            q = ("PREFIX wdt: <http://www.wikidata.org/prop/direct/> PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> "
                 "SELECT ?name ?label WHERE { VALUES ?name { " + vals + " } ?item wdt:P225 ?name . "
                 "?item rdfs:label ?label . FILTER(LANG(?label) = \"en\") }")
            for b in _sparql(q):
                labels.setdefault(b["name"]["value"], b["label"]["value"])
        lab.write_text(json.dumps(labels, sort_keys=True, ensure_ascii=False))
    out = raw_dir / "sitelinks.json"
    if out.exists():
        return
    sl: dict[str, int] = {}
    for i in range(0, len(names), 500):
        vals = " ".join(json.dumps(n) for n in names[i:i + 500])
        q = ("PREFIX wdt: <http://www.wikidata.org/prop/direct/> PREFIX wikibase: <http://wikiba.se/ontology#> "
             "SELECT ?name ?sl WHERE { VALUES ?name { " + vals + " } ?item wdt:P225 ?name . ?item wikibase:sitelinks ?sl }")
        for b in _sparql(q):
            n = b["name"]["value"]
            sl[n] = max(sl.get(n, 0), int(b["sl"]["value"]))
    out.write_text(json.dumps(sl, sort_keys=True))


def _slug(name: str) -> str:
    s = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "_", s).strip("_")


def _num(v: str) -> float | None:
    try:
        x = float(v)
    except (TypeError, ValueError):
        return None
    return x if x > 0 else None


def _group(sp: dict) -> str:
    return "fish" if sp["class"] in FISH else sp["class"]


def _node(sp: dict) -> str:
    if sp["order"] in ORDER_NODE:
        return ORDER_NODE[sp["order"]]
    if sp["class"] in FISH:
        return "world.nature.sea_life.fish"
    return CLASS_NODE.get(sp["class"], "world.nature")


def _species(raw_dir: Path) -> list[dict]:
    sl = json.loads((raw_dir / "sitelinks.json").read_text())
    labels = json.loads((raw_dir / "labels.json").read_text())
    out, seen = [], set()
    for x in _rows(raw_dir):
        binom = f"{x['Genus']} {x['Species']}"
        # Wikidata's English label keeps proper-noun capitals only ("Greenland shark", "lion"); AnAge's is
        # sentence-cased and sometimes odd ("Ziege"). Prefer Wikidata's unless it is the binomial.
        wd = labels.get(binom, "")
        common = RENAME.get(binom) or (wd if wd and wd.lower() != binom.lower() else "")
        cased = bool(common)
        common = re.sub(r"\s+", " ", common or x["Common name"] or "").strip()
        if binom in SKIP or not common or common.lower() == binom.lower() or "(" in common or "," in common:
            continue
        if x["Data quality"] not in {"acceptable", "high"}:
            continue
        if sl.get(binom, 0) < MIN_SITELINKS.get(x["Class"], DEFAULT_MIN_SITELINKS):
            continue
        key = _slug(common)
        if not key or key in seen:
            continue
        seen.add(key)
        out.append({"id": x["HAGRID"], "binom": binom, "common": common if cased else _running(common),
                    "key": key, "class": x["Class"], "order": x["Order"], "sl": sl.get(binom, 0),
                    **{t[1]: _num(x[t[1]]) for t in TEMPLATES}})
    return out


# First words that are place/person names and keep their capital in running text.
PROPER_FIRST = {"African", "American", "Asian", "Australian", "European", "Indian", "Chinese", "Japanese", "Siberian",
                "Arctic", "Antarctic", "Atlantic", "Pacific", "Andean", "Amazon", "Bengal", "Galapagos", "Komodo",
                "Nile", "Canada", "Canadian", "Cape", "California", "Californian", "Mexican", "Brazilian", "Egyptian",
                "Madagascar", "Malagasy", "Himalayan", "Tibetan", "Mongolian", "Arabian", "Persian", "Barbary", "Bactrian",
                "Sumatran", "Bornean", "Javan", "Philippine", "Cuban", "Caribbean", "Mediterranean", "Alpine", "Eurasian",
                "Iberian", "Scottish", "Irish", "English", "Russian", "Florida", "Texas", "Virginia", "Carolina",
                "Guinea", "Congo", "Tasmanian", "New", "North", "South", "East", "West", "Northern", "Southern",
                "Eastern", "Western", "Central", "Hawaiian", "Chilean", "Patagonian", "Senegal", "Sri", "Sudan", "Somali",
                "Ethiopian", "Kenyan", "Nubian", "Magellanic", "Humboldt", "Adelie", "Emperor", "King", "Victoria",
                "Mandarin", "Muscovy", "Pekin", "Rhesus", "Barbados", "Jamaican", "Japan", "Spanish", "Greek", "Italian",
                "Burmese", "Indochinese", "Malayan", "Malay", "Sunda", "Oriental", "Moluccan", "Chinese", "Gila"}


def _running(name: str) -> str:
    """Common name as it reads mid-sentence: 'Lion' -> 'lion', 'Komodo dragon' and "Sundevall's jird" unchanged."""
    first = name.split()[0]
    if first in PROPER_FIRST or first.endswith("'s") or first.isupper():
        return name
    return name[0].lower() + name[1:]


def normalize(raw_dir: Path) -> Iterator[Question]:
    species = sorted(_species(raw_dir), key=lambda s: s["id"])
    for tid, col, ratio, share, text, classes in TEMPLATES:
        pool = [s for s in species if s[col] and (classes is None or s["class"] in classes)]
        # incubation is an egg question: AnAge mixes gestation/incubation in one column, so the class filter decides
        pairs = [(a, b) for a, b in itertools.combinations(pool, 2) if _group(a) == _group(b)]
        k = round(TARGET * share)
        uses: dict[str, int] = {}
        taken = 0
        for a, b in hash_order(pairs, lambda p: f"{p[0]['id']}|{p[1]['id']}", f"{SALT}.{tid}"):
            if taken >= k:
                break
            va, vb = a[col], b[col]
            hi, lo = (a, b) if va > vb else (b, a)
            if max(va, vb) < ratio * min(va, vb):
                continue
            if uses.get(a["id"], 0) >= MAX_PER_SPECIES or uses.get(b["id"], 0) >= MAX_PER_SPECIES:
                continue
            uses[a["id"]] = uses.get(a["id"], 0) + 1
            uses[b["id"]] = uses.get(b["id"], 0) + 1
            taken += 1
            na, nb = _node(a), _node(b)
            node = na if na == nb else ("world.nature.mammals" if a["class"] == "Mammalia" else CLASS_NODE.get(a["class"], "world.nature"))
            yield Question(
                text=text.format(a=a["common"], b=b["common"]),
                primitive="choice", hemisphere="world", kind="factual", origin="template", source=NAME,
                options={a["key"]: f"{a['common']} ({a['binom']})", b["key"]: f"{b['common']} ({b['binom']})"},
                node_hint=node, source_item_id=f"{tid}:{a['id']}-{b['id']}", license=LICENSE,
                truth=hi["key"], template_id=f"anage_pairs.{tid}",
                meta={"hagrid": [a["id"], b["id"]], "values": [va, vb], "field": col},
            )
