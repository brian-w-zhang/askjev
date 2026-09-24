"""Social Chemistry 101 (AllenAI, CC BY-SA 4.0): crowd-written rules of thumb with annotators' estimates of
what share of people agree with each rule."""

from __future__ import annotations

import csv
import importlib.util
import random
import re
import zipfile
from collections import defaultdict
from pathlib import Path
from typing import Iterator

import httpx

from askjev.model import HumanDist, Question

NAME = "social_chem"
URL = "https://storage.googleapis.com/ai2-mosaic-public/projects/social-chemistry/data/social-chem-101.zip"
LICENSE = "CC BY-SA 4.0 (Social Chemistry 101, Forbes et al. 2020)"
TARGET = 6000
SEED = 20260924
TSV = Path("social-chem-101") / "social-chem-101.v1.0.tsv"
MIN_MULTI = 3  # rules of thumb with at least this many rot-agree annotations are sampled first

# Content filters shared with scruples; the political pattern with scruples_anecdotes.
_spec = importlib.util.spec_from_file_location(
    "sources.scruples_anecdotes", Path(__file__).parents[1] / "scruples_anecdotes" / "adapter.py"
)
A = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(A)
F = A.F

# rot-agree buckets in the dataset: <1%, 5-25%, 50%, 75-90%, >99%.
LEVELS = [
    "Practically no one agrees with it",
    "A small minority of people agree with it",
    "About half of people agree with it",
    "A clear majority of people agree with it",
    "Practically everyone agrees with it",
]

# First match wins: relationship context before value topics.
ROUTES = [
    ("self.love.family_parenting", r"parents?|mom|moms|mother|mothers|dad|dads|father|fathers|children|child|kids?|sons?|daughters?|"
     r"siblings?|brothers?|sisters?|grandparents?|grandma|grandpa|family|families|relatives?|in-laws?|aunts?|uncles?|cousins?"),
    ("self.love.romance_partnership", r"husbands?|wife|wives|spouses?|partners?|boyfriends?|girlfriends?|marriage|married|"
     r"marry|significant others?|exes|an ex|your ex|romantic\w*|cheat on"),
    ("self.love.dating_attraction", r"dates?|dating|crush\w*|flirt\w*|attractive|attracted|hook up"),
    ("self.love.friendship", r"friends?|friendships?"),
    ("self.love.workplace_community", r"jobs?|workplace|at work|coworkers?|co-workers?|boss|bosses|employers?|employees?|"
     r"colleagues?|neighbou?rs?|classmates?|roommates?|teachers?|customers?"),
    ("self.values.animals_environment", r"animals?|pets?|dogs?|cats?|environment\w*|litter\w*|recycl\w*|wildlife|nature"),
    ("self.values.honesty_trust", r"lie|lies|lying|lied|liars?|honest\w*|dishonest\w*|truth\w*|trust\w*|secrets?|promises?|"
     r"cheat\w*|deceiv\w*|deception"),
    ("self.values.giving_charity", r"charit\w*|donat\w*|volunteer\w*|homeless|the poor|less fortunate|those in need|"
     r"people in need|strangers?|beggars?"),
    ("self.values.fairness_justice", r"fair|fairly|unfair\w*|equal\w*|deserve\w*|punish\w*|forgiv\w*|justice|revenge"),
]
ROUTES = [(node, re.compile(rf"\b({pat})\b", re.I)) for node, pat in ROUTES]


def fetch(raw_dir: Path) -> None:
    if (raw_dir / TSV).exists():
        return
    out = raw_dir / "social-chem-101.zip"
    if not out.exists():
        r = httpx.get(URL, follow_redirects=True, timeout=600)
        r.raise_for_status()
        out.write_bytes(r.content)
    with zipfile.ZipFile(out) as zf:
        for m in zf.namelist():
            if m.startswith("social-chem-101/") and not m.endswith("/"):
                zf.extract(m, raw_dir)


def _clean(s: str) -> str:
    s = re.sub(r"\s+", " ", s).strip().rstrip(".").strip()
    return s[:1].upper() + s[1:]


def node_for(rot: str, cats: set[str]) -> str:
    for node, rx in ROUTES:
        if rx.search(rot):
            return node
    if "social-norms" in cats:
        return "self.love.etiquette_social_norms"
    if "morality-ethics" in cats:
        return "self.values.everyday_ethics"
    return "self.values"  # advice / description only: placement walks from the Values root


def normalize(raw_dir: Path) -> Iterator[Question]:
    groups: dict[str, dict] = defaultdict(lambda: {"votes": [0] * 5, "bad": 0, "rows": 0, "cats": defaultdict(int),
                                                   "mf": defaultdict(int), "areas": set(), "rot_ids": set()})
    texts: dict[str, str] = {}
    with open(raw_dir / TSV, encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh, delimiter="\t", quoting=csv.QUOTE_NONE):
            if r["rot-agree"] == "" or not r["rot"].strip():
                continue
            rot = _clean(r["rot"])
            key = re.sub(r"\W+", " ", rot.lower()).strip()
            g = groups[key]
            texts.setdefault(key, rot)
            g["votes"][int(r["rot-agree"])] += 1
            g["rows"] += 1
            g["bad"] += r["rot-bad"] == "1"
            for c in filter(None, r["rot-categorization"].split("|")):
                g["cats"][c] += 1
            for m in filter(None, r["rot-moral-foundations"].split("|")):
                g["mf"][m] += 1
            g["areas"].add(r["area"])
            g["rot_ids"].add(r["rot-id"])

    multi, single = [], []
    for key in sorted(groups):
        g, rot = groups[key], texts[key]
        if g["bad"] * 2 >= g["rows"] or len(rot) < 10:
            continue
        sexual = A.is_sexual(rot)
        if A.drop(rot, sexual):
            continue
        (multi if sum(g["votes"]) >= MIN_MULTI else single).append((key, sexual))

    rng = random.Random(SEED)
    rng.shuffle(multi)
    rng.shuffle(single)
    picked = sorted((multi + single)[:TARGET])

    for key, sexual in picked:
        g, rot = groups[key], texts[key]
        n = sum(g["votes"])
        # Categories/foundations: those chosen by at least half of the annotations.
        cats = {c for c, k in g["cats"].items() if 2 * k >= g["rows"]}
        mfs = sorted(m for m, k in g["mf"].items() if 2 * k >= g["rows"])
        flags = ["sensitive"] if (sexual or F.SELF_HARM.search(rot) or F.VIOLENT.search(rot)) else []
        if A.POLITICAL.search(rot):
            flags.append("political")
        rot_ids = sorted(g["rot_ids"])
        yield Question(
            text=f'How many people would agree: "{rot}"?',
            primitive="score",
            hemisphere="self",
            kind="social",
            origin="dataset",
            source=NAME,
            options=LEVELS,
            node_hint=node_for(rot, cats),
            human_text=f'How many people would agree: "{rot}"?',
            source_item_id=rot_ids[0],
            license=LICENSE,
            human=[
                HumanDist(
                    population="Social Chemistry 101 MTurk annotators",
                    distribution={str(i): v / n for i, v in enumerate(g["votes"])},
                    n=n,
                    source="Social Chemistry 101 v1.0 rot-agree (annotator estimate of the share of people who agree)",
                )
            ],
            meta={
                "rot_agree_counts": g["votes"],
                "categorization": sorted(cats),
                "moral_foundations": mfs,
                "areas": sorted(g["areas"]),
                "rot_ids": rot_ids[:10],
                "n_rot_ids": len(rot_ids),
            }
            | ({"flags": flags} if flags else {}),
        )
