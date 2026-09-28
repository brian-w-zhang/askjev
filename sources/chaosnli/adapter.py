"""Does a sentence follow from another? 100 people per item (ChaosNLI; research pass 2, idea 9).

Human data: ChaosNLI (Nie, Zhou & Bansal 2020, EMNLP; CC BY-NC 4.0): 100 new crowd labels for each of 1,514 SNLI
and 1,599 MNLI development items (entailment / neutral / contradiction). The point of the set is the split: some
items get 95 of 100 votes, some split three ways. 600 items are sampled evenly across the range of disagreement
(entropy terciles within each of SNLI and MNLI), so the split can be compared with Jev's probabilities.
Used for non-commercial research, per the license.
"""

from __future__ import annotations

import json
import random
import urllib.request
from pathlib import Path
from typing import Iterator

from askjev.model import HumanDist, Question

NAME = "chaosnli"
NODE = "world.society.languages.sentence_inference"
LICENSE = "CC BY-NC 4.0 (ChaosNLI, Nie, Zhou & Bansal 2020); non-commercial research use"
URL = "https://huggingface.co/datasets/earino/chaosnli/resolve/main/raw/"
FILES = ["chaosNLI_snli.jsonl", "chaosNLI_mnli_m.jsonl"]
OPTIONS = {"follows": "The second sentence is true, given the first",
           "unrelated": "The second sentence might or might not be true; the first doesn't settle it",
           "contradicts": "The second sentence is false, given the first"}
KEYS = {"e": "follows", "n": "unrelated", "c": "contradicts"}
PER_SET = 300


def fetch(raw_dir: Path) -> None:
    for f in FILES:
        if not (raw_dir / f).exists():
            urllib.request.urlretrieve(URL + f, raw_dir / f)


def normalize(raw_dir: Path) -> Iterator[Question]:
    for f in FILES:
        rows = sorted((json.loads(line) for line in open(raw_dir / f)), key=lambda r: (r["entropy"], r["uid"]))
        third = len(rows) // 3
        rng = random.Random(f)
        picks = [r for k in range(3) for r in rng.sample(rows[k * third:(k + 1) * third], PER_SET // 3)]
        for r in picks:
            ex = r["example"]
            yield Question(
                text=f'First sentence: "{ex["premise"]}"\nSecond sentence: "{ex["hypothesis"]}"\n'
                     "Taking the first sentence as true, what does it tell you about the second?",
                primitive="choice", hemisphere="world", kind="perception", origin="dataset", source=NAME,
                options=OPTIONS, node_hint=NODE, license=LICENSE, source_item_id=f"{f.split('_')[1].split('.')[0]}:{r['uid']}",
                truth=KEYS[r["majority_label"]],
                human=[HumanDist(population="ChaosNLI crowd workers (100 per item)",
                                 distribution={KEYS[k]: v / 100 for k, v in r["label_counter"].items()},
                                 n=sum(r["label_counter"].values()), source="ChaosNLI v1.0 label_counter")],
                meta={"experiment": "chaosnli", "set": "snli" if "snli" in f else "mnli", "entropy": round(r["entropy"], 4),
                      "old_label": KEYS.get(r["old_label"], r["old_label"])})
