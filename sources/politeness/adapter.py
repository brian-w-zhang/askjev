"""How polite is a request? Wikipedia editors' requests rated by crowd workers (research pass 2, docs/13 #9).

Human data: the Stanford Politeness Corpus v1.01 (Danescu-Niculescu-Mizil, Sudhof, Jurafsky, Leskovec & Potts 2013,
ACL): 4,353 requests from Wikipedia editors' talk pages, each rated by 5 MTurk workers from 1 (very impolite) to 25
(very polite) (Readme.txt, `Score[1-5]`). The five ratings are put into five even bins (1-5, 6-10, 11-15, 16-20,
21-25) that match Jev's five described levels. 500 requests are sampled evenly across the corpus's normalized score
(100 per quintile), so rude, neutral and very polite requests are all represented.
"""

from __future__ import annotations

import csv
import random
import urllib.request
import zipfile
from pathlib import Path
from typing import Iterator

from askjev.model import HumanDist, Question

NAME = "politeness"
NODE = "world.society.languages.politeness"
LICENSE = ("Stanford Politeness Corpus v1.01 (Danescu-Niculescu-Mizil et al. 2013), released by the authors for research; "
           "redistributed in ConvoKit under CC BY 4.0")
URL = "https://www.cs.cornell.edu/~cristian/Politeness_files/Stanford_politeness_corpus.zip"
FILE = "Stanford_politeness_corpus/wikipedia.annotated.csv"
LEVELS = ["Rude: the other editor would feel insulted or attacked by it",
          "Curt or pushy: noticeably impolite, though not insulting",
          "Neutral: a plain request, neither polite nor impolite",
          "Polite: considerate and courteous",
          "Very polite: warm, gracious and deferential"]
PER_QUINTILE = 100


def fetch(raw_dir: Path) -> None:
    if not (raw_dir / FILE).exists():
        urllib.request.urlretrieve(URL, raw_dir / "spc.zip")
        zipfile.ZipFile(raw_dir / "spc.zip").extractall(raw_dir)


def _bin(score: int) -> str:
    return str(min(4, (max(1, min(25, score)) - 1) // 5))


def normalize(raw_dir: Path) -> Iterator[Question]:
    rows = sorted(csv.DictReader(open(raw_dir / FILE, encoding="utf-8")), key=lambda r: (float(r["Normalized Score"]), r["Id"]))
    k = len(rows) // 5
    rng = random.Random(2013)
    for qi in range(5):
        for r in sorted(rng.sample(rows[qi * k:(qi + 1) * k], PER_QUINTILE), key=lambda r: r["Id"]):
            scores = [int(r[f"Score{i}"]) for i in range(1, 6)]
            dist = {str(i): 0.0 for i in range(5)}
            for s in scores:
                dist[_bin(s)] += 1 / len(scores)
            yield Question(
                text="One Wikipedia editor wrote the request in `request` to another editor on their talk page. How polite is it?",
                state={"request": r["Request"]}, primitive="score", hemisphere="world", kind="perception", origin="dataset",
                source=NAME, options=LEVELS, node_hint=NODE, license=LICENSE, source_item_id=f"wikipedia:{r['Id']}",
                human=[HumanDist(population="MTurk workers (Danescu-Niculescu-Mizil et al. 2013), 5 per request",
                                 distribution=dist, n=len(scores),
                                 source="Stanford Politeness Corpus v1.01 wikipedia.annotated.csv Score1-5 (1-25), put in five even bins")],
                meta={"experiment": "politeness", "mean_score": sum(scores) / len(scores), "scores": scores,
                      "normalized_score": float(r["Normalized Score"]), "quintile": qi})
