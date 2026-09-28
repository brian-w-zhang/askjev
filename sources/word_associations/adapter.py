"""The first word that comes to mind (docs/15 E42), against the USF free association norms.

Human data: Nelson, McEvoy & Schreiber (2004), "The University of South Florida free association, rhyme, and word
fragment norms" (Behavior Research Methods, Instruments & Computers 36:402-407), Appendix A: for 5,019 cue words,
about 150 students each wrote the first word that came to mind; a response is listed when two or more gave it, with
its share (FSG). Copyright Nelson, McEvoy & Schreiber, published free for research use.
Jev gets the cue with the cue's seven most common responses as options plus "another word", so it chooses rather
than generates; people's distribution is the same seven shares plus everything else. 400 cues, 100 from each quarter
of how predictable the top response is (from 'bread -> butter' to cues with no common answer).
"""

from __future__ import annotations

import random
import urllib.request
from pathlib import Path
from typing import Iterator

from askjev.model import HumanDist, Question

NAME = "word_associations"
NODE = "world.society.languages.word.word_association"
LICENSE = "Copyright Nelson, McEvoy & Schreiber; USF free association norms published free for research use"
URL = "http://w3.usf.edu/FreeAssociation/AppendixA/Cue_Target_Pairs."
PARTS = ["A-B", "C", "D-F", "G-K", "L-O", "P-R", "S", "T-Z"]
TOP, PER_BIN = 7, 100


def fetch(raw_dir: Path) -> None:
    for p in PARTS:
        if not (raw_dir / f"{p}.txt").exists():
            urllib.request.urlretrieve(URL + p, raw_dir / f"{p}.txt")


def cues(raw_dir: Path) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for p in PARTS:
        for line in (raw_dir / f"{p}.txt").read_text(encoding="latin-1").splitlines():
            f = [x.strip() for x in line.split(",")]
            if len(f) < 6 or f[0] in ("CUE", "") or f[0].startswith("<"):
                continue
            try:
                g, fsg = int(f[3]), float(f[5])
            except ValueError:
                continue
            cue, tgt = f[0].lower(), f[1].lower()
            if not tgt.replace("'", "").replace("-", "").replace(" ", "").isalpha() or tgt == cue:
                continue
            c = out.setdefault(cue, {"n": g, "targets": {}})
            c["targets"][tgt] = max(c["targets"].get(tgt, 0.0), fsg)
    return out


def normalize(raw_dir: Path) -> Iterator[Question]:
    cs = {c: v for c, v in cues(raw_dir).items() if len(v["targets"]) >= TOP and c.isalpha() and len(c) > 2}
    ranked = sorted(cs, key=lambda c: (max(cs[c]["targets"].values()), c))
    q = len(ranked) // 4
    rng = random.Random(2004)
    picks = [c for k in range(4) for c in sorted(rng.sample(ranked[k * q:(k + 1) * q], PER_BIN))]
    for cue in picks:
        top = sorted(cs[cue]["targets"].items(), key=lambda x: -x[1])[:TOP]
        dist = {t: s for t, s in top}
        dist["another_word"] = max(0.0, 1 - sum(dist.values()))
        tot = sum(dist.values())
        yield Question(
            text=f'What is the first word that comes to mind when you hear the word "{cue}"?', primitive="choice",
            hemisphere="world", kind="perception", origin="dataset", source=NAME,
            options={**{t: None for t, _ in top}, "another_word": "Some other word"}, node_hint=NODE, license=LICENSE,
            source_item_id=cue,
            human=[HumanDist(population="University of South Florida students (Nelson et al. 2004)",
                             distribution={k: v / tot for k, v in dist.items()}, n=cs[cue]["n"],
                             source="USF free association norms, Appendix A (FSG = share giving each response)")],
            meta={"experiment": "word_associations", "cue": cue, "top_share": top[0][1],
                  "quartile": ranked.index(cue) // q})
