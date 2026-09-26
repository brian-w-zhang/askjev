"""The bouba/kiki effect across 25 languages (Ćwiek, Fuchs, Draxler et al. 2022, Phil. Trans. R. Soc. B 377:20200390).

917 speakers of 25 languages each heard one spoken word, "bouba" or "kiki", and picked the round or the spiky shape
it names. Two Choice questions (one per word) with the real choice shares: pooled over all participants, plus one
distribution per language with at least MIN_N participants for that word. No truth: this is a crossmodal
association, not a fact; the congruent answer (bouba -> round, kiki -> spiky) is in meta.
"""

from __future__ import annotations

import csv
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterator

import httpx

from askjev.model import HumanDist, Question

NAME = "bouba_kiki"
FILE = "web_by_trial.csv"
URL = "https://osf.io/download/cvygf/"  # OSF w7crs, data/web_by_trial.csv
LICENSE = "No explicit license on OSF w7crs (public data); article CC BY 4.0 (Ćwiek et al. 2022)"
MIN_N = 10
NODE = "world.science.psychology_neuroscience.perception"
SRC = "Ćwiek et al. 2022, bouba/kiki web experiment (OSF w7crs)"

TEXT = ('Picture two shapes side by side: one round and blob-like with smooth curves, the other spiky with sharp '
        'points. Which one would you call "{w}"?')
HUMAN_TEXT = ('Picture two shapes side by side: one round and blob-like with smooth curves, the other spiky with sharp '
              'points. Which one would most people call "{w}"?')
OPTIONS = {"round_shape": "The round, blob-like shape with smooth curves",
           "spiky_shape": "The spiky shape with sharp points"}
RESP = {"bouba": "round_shape", "kiki": "spiky_shape"}  # Resp names the shape the participant picked


def fetch(raw_dir: Path) -> None:
    out = raw_dir / FILE
    if not out.exists():
        r = httpx.get(URL, follow_redirects=True, timeout=300)
        r.raise_for_status()
        out.write_bytes(r.content)


def _dist(c: Counter) -> dict[str, float]:
    n = sum(c.values())
    return {k: c[k] / n for k in OPTIONS}


def normalize(raw_dir: Path) -> Iterator[Question]:
    by_word: dict[str, Counter] = defaultdict(Counter)
    by_lang: dict[tuple[str, str], Counter] = defaultdict(Counter)
    lang_name: dict[str, str] = {}
    with open(raw_dir / FILE, newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if r["Condition"] not in RESP or r["Resp"] not in RESP:
                continue
            pick = RESP[r["Resp"]]
            by_word[r["Condition"]][pick] += 1
            by_lang[(r["Condition"], r["Language"])][pick] += 1
            lang_name[r["Language"]] = r["Name"]
    for w in ("bouba", "kiki"):
        human = [HumanDist(population=f"25 language groups pooled (web experiment)", distribution=_dist(by_word[w]),
                           n=sum(by_word[w].values()), source=SRC)]
        for (ww, lang), c in sorted(by_lang.items()):
            if ww == w and sum(c.values()) >= MIN_N:
                human.append(HumanDist(population=f"{lang_name[lang]} speakers ({lang})", distribution=_dist(c),
                                       n=sum(c.values()), source=SRC))
        print(f"{NAME}: {w}: n={sum(by_word[w].values())}, {len(human) - 1} languages with n >= {MIN_N}")
        yield Question(
            text=TEXT.format(w=w),
            primitive="choice",
            hemisphere="world",
            kind="perception",
            origin="dataset",
            source=NAME,
            options=OPTIONS,
            node_hint=NODE,
            human_text=HUMAN_TEXT.format(w=w),
            source_item_id=w,
            license=LICENSE,
            template_id=f"{NAME}.shape",
            human=human,
            meta={"word": w, "congruent": RESP[w],
                  "note": "participants heard the word spoken and saw two drawn shapes; one trial per participant"},
        )
