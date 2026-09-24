"""ETHICS commonsense morality (Hendrycks et al. 2021, MIT): short first-person scenarios labeled for whether
the narrator's action is clearly morally wrong."""

from __future__ import annotations

import csv
import importlib.util
import random
import re
import tarfile
from pathlib import Path
from typing import Iterator

import httpx

from askjev.model import Question

NAME = "ethics_cs"
URL = "https://people.eecs.berkeley.edu/~hendrycks/ethics.tar"
LICENSE = "MIT (hendrycks/ethics)"
TARGET = 4000
SEED = 20260924
MAX_CHARS = 300
FILES = {"train": "cm_train.csv", "test": "cm_test.csv"}
DIR = Path("ethics") / "commonsense"

# Content filters shared with scruples; the political pattern with scruples_anecdotes.
_spec = importlib.util.spec_from_file_location(
    "sources.scruples_anecdotes", Path(__file__).parents[1] / "scruples_anecdotes" / "adapter.py"
)
A = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(A)
F = A.F


def fetch(raw_dir: Path) -> None:
    if all((raw_dir / DIR / f).exists() for f in FILES.values()):
        return
    out = raw_dir / "ethics.tar"
    if not out.exists():
        r = httpx.get(URL, follow_redirects=True, timeout=600)
        r.raise_for_status()
        out.write_bytes(r.content)
    with tarfile.open(out) as tf:
        members = [m for m in tf.getmembers() if m.name.startswith("ethics/commonsense/")]
        tf.extractall(raw_dir, members=members, filter="data")


def normalize(raw_dir: Path) -> Iterator[Question]:
    pools: dict[bool, list] = {True: [], False: []}
    seen = set()
    for split, fname in FILES.items():
        with open(raw_dir / DIR / fname, encoding="utf-8", newline="") as fh:
            for i, r in enumerate(csv.DictReader(fh)):
                s = re.sub(r"\s+", " ", r["input"]).strip()
                if r["is_short"] != "True" or not s or len(s) > MAX_CHARS:
                    continue
                key = s.lower()
                if key in seen:
                    continue
                sexual = A.is_sexual(s)
                if A.drop(s, sexual):
                    continue
                seen.add(key)
                pools[r["label"] == "1"].append((split, i, s, sexual))

    # Balanced: half clearly wrong, half not, seeded; the other class fills any shortfall.
    rng = random.Random(SEED)
    for p in pools.values():
        rng.shuffle(p)
    half = TARGET // 2
    picked = [(True, x) for x in pools[True][:half]] + [(False, x) for x in pools[False][:half]]
    rest = [(True, x) for x in pools[True][half:]] + [(False, x) for x in pools[False][half:]]
    picked += rest[: TARGET - len(picked)]
    picked.sort(key=lambda t: (t[1][0], t[1][1]))

    for wrong, (split, i, s, sexual) in picked:
        flags = ["sensitive"] if (sexual or F.SELF_HARM.search(s) or F.VIOLENT.search(s)) else []
        if A.POLITICAL.search(s):
            flags.append("political")
        yield Question(
            text="Is the narrator's action in `scenario` clearly wrong?",
            primitive="noul",
            hemisphere="self",
            kind="values",
            origin="dataset",
            source=NAME,
            state={"scenario": s},
            node_hint="self.values.everyday_ethics",
            human_text="Would most people say the narrator's action in `scenario` is clearly wrong?",
            source_item_id=f"{split}:{i}",
            license=LICENSE,
            truth=wrong,
            meta={"split": split} | ({"flags": flags} if flags else {}),
        )
