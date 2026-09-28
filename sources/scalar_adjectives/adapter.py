"""Which of two related adjectives is stronger ("good" vs "great"), against three gold orderings (docs/13 experiment 4).

Gold data: the scalar-adjective scales collected in Cocos et al. 2018 ("Learning Scalar Adjective Intensity from
Paraphrases", EMNLP; github.com/acocos/scalar-adj, MIT): de Melo & Bansal 2013 (87 half-scales ordered by
linguists), Wilkinson & Oates 2016 (21), and Cocos et al.'s crowd set (79, ordered by crowd workers). Each file is one
half-scale from weakest to strongest; words on the same line are tied. Every pair of words on different lines
becomes one question; the stronger word is the truth.
"""

from __future__ import annotations

import json
import urllib.request
from itertools import combinations
from pathlib import Path
from typing import Iterator

from askjev.model import Question

NAME = "scalar_adjectives"
NODE = "world.society.languages.word.adjective_intensity"
LICENSE = "MIT (acocos/scalar-adj; gold scales from de Melo & Bansal 2013, Wilkinson & Oates 2016, Cocos et al. 2018)"
REPO = "https://raw.githubusercontent.com/acocos/scalar-adj/master/"
SETS = {"demelo": "de Melo & Bansal 2013", "wilkinson": "Wilkinson & Oates 2016", "crowd": "Cocos et al. 2018 crowd"}


def fetch(raw_dir: Path) -> None:
    if all((raw_dir / s).exists() for s in SETS):
        return
    tree = json.load(urllib.request.urlopen("https://api.github.com/repos/acocos/scalar-adj/git/trees/master?recursive=1"))
    for t in tree["tree"]:
        p = t["path"]
        if p.endswith(".rankings") and "/gold_rankings/" in p:
            s = p.split("/")[2]
            (raw_dir / s).mkdir(exist_ok=True)
            urllib.request.urlretrieve(REPO + p, raw_dir / s / Path(p).name)


def _scale(path: Path) -> list[list[str]]:
    ranks = []
    for line in path.read_text().splitlines():
        if "\t" in line:
            ranks.append([w.strip() for w in line.split("\t", 1)[1].split("||") if w.strip()])
    return ranks


def normalize(raw_dir: Path) -> Iterator[Question]:
    seen = set()
    for s, label in SETS.items():
        for f in sorted((raw_dir / s).glob("*.rankings")):
            ranks = _scale(f)
            for (i, a), (j, b) in combinations(list(enumerate(ranks)), 2):
                for wa in a:
                    for wb in b:
                        if wa == wb or (wa, wb) in seen or (wb, wa) in seen:
                            continue
                        seen.add((wa, wb))
                        yield Question(
                            text=f'Which word expresses a stronger degree of the same quality: "{wa}" or "{wb}"?',
                            primitive="choice", hemisphere="world", kind="perception", origin="dataset", source=NAME,
                            options={wa: None, wb: None}, node_hint=NODE, truth=wb, license=LICENSE,
                            source_item_id=f"{s}:{f.stem}:{wa}<{wb}",
                            meta={"experiment": "adjective_intensity", "set": s, "gold": label, "scale": f.stem.rstrip("X"),
                                  "gap": j - i, "scale_len": len(ranks)})
