"""People & documents: record matching and job-title classification, from three public benchmarks.

Templates (all with truth):
- "er.same_product" / "er.same_paper": Noul "Do `record_a` and `record_b` describe the same product /
  paper?" over DeepMatcher benchmark pairs (Mudgal et al., SIGMOD 2018; Magellan group, UW-Madison):
  Structured Amazon-Google and Walmart-Amazon (products), DBLP-ACM (papers). Truth = the pair label.
  Non-matches are the benchmarks' blocked candidates (records that look alike), so they are hard
  negatives. -> machine.documents.entity_resolution
- "people.same_person": Noul "Do `record_a` and `record_b` refer to the same person?" over FEBRL
  dataset 4 (Christen 2008): 5,000 synthetic Australian person records (4a) and one corrupted
  duplicate of each (4b: typos, missing fields, swapped values). Truth = same rec number. Negatives
  pair an original with another person's duplicate that shares its surname, else its postcode, else
  its suburb (hard negatives, deterministic). -> machine.people.duplicate_records
- "people.occupation_group": Choice "Which occupation group does `job_title` belong to?" over the 23
  SOC major groups, from O*NET 29.2 Alternate Titles (job titles as employers and job seekers write
  them, each mapped to an O*NET-SOC occupation). Only titles that map to a single major group are
  kept. Truth = that group. -> machine.people.lead_fit (persona / function classification of a contact).

Sampling: every part is ordered by a salted hash of a stable key and the first k are taken, so a larger
target always contains a smaller one.
"""

from __future__ import annotations

import csv
import html
import io
import json
import zipfile
from collections import defaultdict
from pathlib import Path
from typing import Iterator

import httpx

from askjev.model import Question
from askjev.sampling import env_int, hash_order

NAME = "people_docs"
DM = "http://pages.cs.wisc.edu/~anhai/data1/deepmatcher_data/Structured/{path}_exp_data.zip"
ER_SETS = {  # zip stem -> (entity noun, template id)
    "Amazon-Google/amazon_google": ("product", "er.same_product"),
    "Walmart-Amazon/walmart_amazon": ("product", "er.same_product"),
    "DBLP-ACM/dblp_acm": ("paper", "er.same_paper"),
}
FEBRL = "https://raw.githubusercontent.com/J535D165/recordlinkage/master/recordlinkage/datasets/febrl/{f}"
ONET = "https://www.onetcenter.org/dl_files/database/db_29_2_text/Alternate%20Titles.txt"

TARGET = env_int("TARGET_PEOPLE_DOCS", 2500)
# Shares of TARGET: per ER dataset, FEBRL, O*NET titles.
SHARE = {"er": 0.16, "febrl": 0.24, "onet": 0.28}
MAX_CHARS = 1500
LICENSES = {
    "er": "DeepMatcher benchmark datasets (research use)",
    "febrl": "BSD-3-Clause (recordlinkage); FEBRL synthetic data",
    "onet": "CC-BY-4.0 (O*NET 29.2 Database, USDOL/ETA)",
}

SAME = {
    "product": {"true": "Both records are the same product (same item, edition and version)",
                "false": "They are different products, even if similar or from the same maker"},
    "paper": {"true": "Both records are the same publication",
              "false": "They are different publications, even if on a similar topic or by the same authors"},
    "person": {"true": "Both records are the same individual, allowing for typos, missing fields and changes",
               "false": "They are two different people"},
}

SOC = {  # SOC major group code -> (key, official group name)
    "11": ("management", "Management"),
    "13": ("business_finance", "Business and financial operations"),
    "15": ("computer_math", "Computer and mathematical"),
    "17": ("architecture_engineering", "Architecture and engineering"),
    "19": ("science", "Life, physical, and social science"),
    "21": ("community_social_service", "Community and social service"),
    "23": ("legal", "Legal"),
    "25": ("education_library", "Educational instruction and library"),
    "27": ("arts_media_sports", "Arts, design, entertainment, sports, and media"),
    "29": ("healthcare_practitioner", "Healthcare practitioners and technical"),
    "31": ("healthcare_support", "Healthcare support"),
    "33": ("protective_service", "Protective service"),
    "35": ("food_service", "Food preparation and serving"),
    "37": ("cleaning_grounds", "Building and grounds cleaning and maintenance"),
    "39": ("personal_care", "Personal care and service"),
    "41": ("sales", "Sales and related"),
    "43": ("office_admin", "Office and administrative support"),
    "45": ("farming_fishing_forestry", "Farming, fishing, and forestry"),
    "47": ("construction_extraction", "Construction and extraction"),
    "49": ("installation_repair", "Installation, maintenance, and repair"),
    "51": ("production", "Production"),
    "53": ("transportation_moving", "Transportation and material moving"),
    "55": ("military", "Military specific"),
}
SOC_OPTIONS = {k: v for k, v in SOC.values()}
FEBRL_FIELDS = ["given_name", "surname", "street_number", "address_1", "address_2", "suburb", "postcode", "state",
                "date_of_birth", "soc_sec_id"]


def fetch(raw_dir: Path) -> None:
    files = {f"{p.split('/')[1]}_exp_data.zip": DM.format(path=p) for p in ER_SETS}
    files |= {f: FEBRL.format(f=f) for f in ("dataset4a.csv", "dataset4b.csv")}
    files["alt_titles.txt"] = ONET
    for name, url in files.items():
        out = raw_dir / name
        if out.exists():
            continue
        r = httpx.get(url, follow_redirects=True, timeout=300)
        r.raise_for_status()
        out.write_bytes(r.content)


def _q(tid, prim, text, options, shape, node, state, truth, item, part, **meta) -> Question:
    return Question(
        text=text, primitive=prim, hemisphere="machine", origin="dataset", source=NAME, options=options,
        state=state, shape=shape, node_hint=node, template_id=tid, source_item_id=item,
        license=LICENSES[part], truth=truth, meta=meta,
    )


def _record(row: dict) -> dict:
    # DBLP-ACM carries HTML entities, space-separated by the benchmark's tokenizer ("gr &#233; gory"). Only the
    # entity is decoded ("gr é gory"): rejoining is ambiguous ("zo &#233; lacroix" is "zoé lacroix").
    out = {}
    for k, v in row.items():
        v = html.unescape(" ".join(str(v or "").split()))
        if k != "id" and v.strip():
            out[k] = v
    return out


def _balanced(pos: list, neg: list, n: int, key, salt: str) -> list:
    half = n // 2
    p = hash_order(pos, key, salt + ".pos")[:half]
    return p + hash_order(neg, key, salt + ".neg")[: n - len(p)]


# ------------------------------------------------------------------------------ entity resolution
def _er(raw_dir: Path) -> Iterator[Question]:
    n = round(TARGET * SHARE["er"])
    for path, (noun, tid) in ER_SETS.items():
        stem = path.split("/")[1]
        with zipfile.ZipFile(raw_dir / f"{stem}_exp_data.zip") as z:
            names = {Path(m).name: m for m in z.namelist()}

            def read(f: str) -> list[dict]:
                return list(csv.DictReader(io.StringIO(z.read(names[f]).decode("utf-8", "replace"))))

            a = {r["id"]: _record(r) for r in read("tableA.csv")}
            b = {r["id"]: _record(r) for r in read("tableB.csv")}
            pairs: dict[tuple[str, str], tuple[str, bool]] = {}
            for split in ("train", "valid", "test"):
                for r in read(f"{split}.csv"):
                    pairs.setdefault((r["ltable_id"], r["rtable_id"]), (split, r["label"] == "1"))
        pos, neg = [], []
        seen: set[str] = set()
        for (la, rb), (split, match) in sorted(pairs.items()):
            ra, rr = a.get(la), b.get(rb)
            if not ra or not rr or len(str(ra)) + len(str(rr)) > MAX_CHARS:
                continue
            key = json.dumps([ra, rr], sort_keys=True)  # tables contain duplicate records
            if key in seen:
                continue
            seen.add(key)
            (pos if match else neg).append((la, rb, split, match, ra, rr))
        dataset = stem
        for la, rb, split, match, ra, rr in sorted(_balanced(pos, neg, n, lambda x: (x[0], x[1]), f"er.{dataset}")):
            yield _q(tid, "noul", f"Do `record_a` and `record_b` describe the same {noun}?", SAME[noun], "verify",
                     "machine.documents.entity_resolution", {"record_a": ra, "record_b": rr}, match,
                     f"{dataset}:{split}:{la}:{rb}", "er", dataset=dataset, split=split)


# ------------------------------------------------------------------------------ FEBRL people
def _febrl(raw_dir: Path) -> Iterator[Question]:
    def load(f: str) -> dict[str, dict]:
        rows = csv.DictReader(open(raw_dir / f, newline="", encoding="utf-8"), skipinitialspace=True)
        out = {}
        for r in rows:
            num = r["rec_id"].split("-")[1]
            out[num] = {k: (r.get(k) or "").strip() for k in FEBRL_FIELDS}
        return out

    orig, dup = load("dataset4a.csv"), load("dataset4b.csv")
    nums = sorted(set(orig) & set(dup), key=int)
    index: dict[str, dict[str, list[str]]] = {f: defaultdict(list) for f in ("surname", "postcode", "suburb")}
    for num in nums:
        for f in index:
            if dup[num][f]:
                index[f][dup[num][f]].append(num)

    pos = [(num, num) for num in nums]
    neg = []
    for num in nums:
        for f in index:  # hard negative: another person's duplicate sharing surname, else postcode, else suburb
            others = [o for o in index[f].get(orig[num][f], []) if o != num]
            if others:
                neg.append((num, hash_order(others, str, f"febrl.{num}")[0]))
                break
    n = round(TARGET * SHARE["febrl"])
    clean = lambda r: {k: v for k, v in r.items() if v}  # noqa: E731
    for a, b in sorted(_balanced(pos, neg, n, lambda x: x, "febrl"), key=lambda x: (int(x[0]), int(x[1]))):
        yield _q("people.same_person", "noul", "Do `record_a` and `record_b` refer to the same person?", SAME["person"],
                 "verify", "machine.people.duplicate_records", {"record_a": clean(orig[a]), "record_b": clean(dup[b])},
                 a == b, f"febrl4:rec-{a}-org:rec-{b}-dup-0", "febrl", dataset="febrl4", synthetic=True)


# ------------------------------------------------------------------------------ O*NET job titles
def _onet(raw_dir: Path) -> Iterator[Question]:
    groups: dict[str, set[str]] = defaultdict(set)
    shown: dict[str, str] = {}
    with open(raw_dir / "alt_titles.txt", encoding="utf-8") as fh:
        for r in csv.DictReader(fh, delimiter="\t"):
            title = " ".join(r["Alternate Title"].split())
            key = title.lower()
            groups[key].add(r["O*NET-SOC Code"][:2])
            shown.setdefault(key, title)
    by_group: dict[str, list[str]] = defaultdict(list)
    for key, gs in groups.items():
        if len(gs) == 1 and 3 <= len(key) <= 120:
            by_group[next(iter(gs))].append(key)
    order = {g: hash_order(v, str, f"onet.{g}") for g, v in by_group.items()}
    n = round(TARGET * SHARE["onet"])
    picked: list[tuple[str, str]] = []
    depth = 0
    while len(picked) < n and depth < max(len(v) for v in order.values()):
        for g in sorted(order):  # round-robin across the 23 groups; small groups run out first
            if depth < len(order[g]) and len(picked) < n:
                picked.append((g, order[g][depth]))
        depth += 1
    for g, key in sorted(picked, key=lambda x: (x[0], x[1])):
        yield _q("people.occupation_group", "choice", "Which occupation group does `job_title` belong to?", SOC_OPTIONS,
                 "classify", "machine.people.lead_fit", {"job_title": shown[key]}, SOC[g][0], f"onet29.2:{key}", "onet",
                 soc_major_group=g, dataset="onet_alternate_titles_29.2")


def normalize(raw_dir: Path) -> Iterator[Question]:
    yield from _er(raw_dir)
    yield from _febrl(raw_dir)
    yield from _onet(raw_dir)
