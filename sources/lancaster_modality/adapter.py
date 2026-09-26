"""Lancaster Sensorimotor Norms (Lynott, Connell, Brysbaert, Brand & Carney 2020), truth-based Choice questions.

Two question families over common English words, both anchored to the norms' mean ratings (0-5, "to what extent do
you experience WORD by <sense>"), never to an invented distribution:

- dominant: 'Through which sense do you mostly experience "thunder"?' over the six perceptual modalities; truth = the
  dominant modality, kept only when its mean beats the runner-up by >= MIN_GAP. The pool is ~78% visual, so visual
  words are capped at the number of non-visual words.
- pair_<sense>: 'Which do you experience more through smell: "X" or "Y"?'; truth = the word with the higher mean,
  kept only when the means differ by >= PAIR_GAP and the lower word still has some of that sense (>= PAIR_LOW_MIN),
  so the pair is not "perfume vs algebra".

The existing `lancaster` source asks per-sense Score questions (with a normal-approximated distribution); this source
adds the categorical "which sense" judgment it lacks. Word pool: single lowercase words that most raters knew and that
are common (SUBTLEX-US count from Brysbaert et al. 2014, downloaded alongside).
"""

from __future__ import annotations

import csv
import importlib.util
import re
import sys
from pathlib import Path
from typing import Iterator

import httpx

from askjev.model import Question
from askjev.sampling import env_int, hash_order

_spec = importlib.util.spec_from_file_location(
    "sources.concreteness", Path(__file__).parents[1] / "concreteness" / "adapter.py")
_c = importlib.util.module_from_spec(_spec)
sys.modules["sources.concreteness"] = _c
_spec.loader.exec_module(_c)

NAME = "lancaster_modality"
FILE = "Lancaster_sensorimotor_norms_for_39707_words.csv"
URL = "https://osf.io/download/48wsc/"  # OSF node rwhs6 (Data component of 7emr6)
LICENSE = "CC BY 4.0 (Lynott, Connell, Brysbaert, Brand & Carney 2020)"
SALT = "lancaster_modality-20260926"
NODE = "world.science.psychology_neuroscience.perception"

TARGET_DOMINANT = env_int("TARGET_LANCASTER_MODALITY_DOMINANT", 2400)
TARGET_PAIR = env_int("TARGET_LANCASTER_MODALITY_PAIR", 500)  # per sense
MIN_KNOWN = 0.95  # Percent_known.perceptual
MIN_SUBTLEX = 30  # raw SUBTLEX-US count (51M tokens), about 0.6 per million
MIN_MAX = 3.0  # dominant question: the winning sense must be clearly present
MIN_GAP = 1.0  # dominant question: winner minus runner-up
PAIR_HIGH_MIN = 2.5  # pair question: the higher word's mean on that sense
PAIR_LOW_MIN = 1.0  # pair question: the lower word's mean on that sense
PAIR_GAP = 1.5
PAIR_MIN_CONC = 3.5  # pair question: Brysbaert concreteness (1-5), so both words name something experienceable
DOM_MIN_CONC = 3.0  # dominant question: concreteness floor (interoceptive words like "thirst" sit around 3-3.5)
DOM_MIN_CONC_VISUAL = 4.0  # visual words are plentiful, so only clearly concrete ones
PAIR_MAX_USES = 3  # a word appears in at most this many pairs per sense

# Lancaster column -> (option key, option description, "through <x>" phrase for the pair question)
SENSES = {
    "Visual": ("sight", "Seeing it", "sight"),
    "Auditory": ("hearing", "Hearing it", "hearing"),
    "Haptic": ("touch", "Feeling it through touch", "touch"),
    "Gustatory": ("taste", "Tasting it", "taste"),
    "Olfactory": ("smell", "Smelling it", "smell"),
    "Interoceptive": ("body_sensation", "Sensations inside your body, like hunger, pain, tiredness or a racing heart",
                      "sensations inside your body"),
}
OPTIONS = {key: desc for key, desc, _ in SENSES.values()}
DOMINANT_TEXT = 'Through which sense do you mostly experience "{w}"?'
DOMINANT_HUMAN = 'Through which sense do most people mostly experience "{w}"?'
PAIR_TEXT = 'Which do you experience more through {s}: "{a}" or "{b}"?'
PAIR_HUMAN = 'Which do most people experience more through {s}: "{a}" or "{b}"?'


def fetch(raw_dir: Path) -> None:
    out = raw_dir / FILE
    if not out.exists():
        r = httpx.get(URL, follow_redirects=True, timeout=300)
        r.raise_for_status()
        out.write_bytes(r.content)
    _c.fetch_brysbaert(raw_dir)


def _pool(raw_dir: Path) -> dict[str, dict]:
    brys = _c.read_brysbaert(raw_dir / _c.FILE)
    out = {}
    with open(raw_dir / FILE, newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            w = r["Word"].lower()
            b = brys.get(w)
            if (b is None or b["bigram"] or not re.fullmatch(r"[a-z]{3,}", w) or _c.SLURS.match(w)
                    or b["subtlex"] < MIN_SUBTLEX or float(r["Percent_known.perceptual"]) < MIN_KNOWN):
                continue
            out[w] = {
                "means": {dim: float(r[f"{dim}.mean"]) for dim in SENSES},
                "sds": {dim: float(r[f"{dim}.SD"]) for dim in SENSES},
                "n": int(float(r["N_known.perceptual"])),
                "conc": b["conc_m"],
                "subtlex": b["subtlex"],
            }
    return out


def _flags(*words: str) -> dict:
    fl = sorted({f for w in words for f in _c.word_flags(w)})
    return {"flags": fl} if fl else {}


def _dominant(pool: dict[str, dict]) -> Iterator[Question]:
    qual: dict[str, list[str]] = {"visual": [], "other": []}
    for w, d in pool.items():
        ranked = sorted(d["means"].items(), key=lambda kv: -kv[1])
        (top, m1), (_, m2) = ranked[0], ranked[1]
        if d["conc"] < (DOM_MIN_CONC_VISUAL if top == "Visual" else DOM_MIN_CONC):
            continue
        if m1 >= MIN_MAX and m1 - m2 >= MIN_GAP:
            qual["visual" if top == "Visual" else "other"].append(w)
    other = hash_order(qual["other"], lambda w: w, SALT + "|dom")
    visual = hash_order(qual["visual"], lambda w: w, SALT + "|dom")
    n_other = min(len(other), TARGET_DOMINANT // 2)
    picked = other[:n_other] + visual[: min(n_other, TARGET_DOMINANT - n_other)]
    print(f"{NAME}: dominant pool {len(qual['other'])} non-visual + {len(qual['visual'])} visual; "
          f"{len(picked)} picked")
    for w in sorted(picked):
        d = pool[w]
        ranked = sorted(d["means"].items(), key=lambda kv: -kv[1])
        yield Question(
            text=DOMINANT_TEXT.format(w=w),
            primitive="choice",
            hemisphere="world",
            kind="perception",
            origin="template",
            source=NAME,
            options=OPTIONS,
            node_hint=NODE,
            human_text=DOMINANT_HUMAN.format(w=w),
            source_item_id=f"{w.upper()}:dominant",
            license=LICENSE,
            truth=SENSES[ranked[0][0]][0],
            template_id=f"{NAME}.dominant",
            meta={
                **_flags(w),
                "word": w,
                "means_0_5": {SENSES[k][0]: round(v, 3) for k, v in d["means"].items()},
                "gap": round(ranked[0][1] - ranked[1][1], 3),
                "n_raters": d["n"],
                "subtlex_count": d["subtlex"],
                "truth_rule": f"dominant perceptual modality; winner >= {MIN_MAX} and beats runner-up by >= {MIN_GAP}",
            },
        )


def _pairs(pool: dict[str, dict], dim: str) -> Iterator[Question]:
    key, _, phrase = SENSES[dim]
    cands = [w for w, d in pool.items() if d["conc"] >= PAIR_MIN_CONC]
    high = hash_order([w for w in cands if pool[w]["means"][dim] >= PAIR_HIGH_MIN], lambda w: w, f"{SALT}|{dim}|hi")
    low_all = hash_order([w for w in cands if pool[w]["means"][dim] >= PAIR_LOW_MIN], lambda w: w, f"{SALT}|{dim}|lo")
    uses: dict[str, int] = {}
    seen: set[frozenset] = set()
    out = []
    # round-robin over the high words so every one gets a partner before any gets a second
    for rnd in range(PAIR_MAX_USES):
        for h in high:
            if len(out) >= TARGET_PAIR:
                break
            if uses.get(h, 0) >= PAIR_MAX_USES:
                continue
            mh = pool[h]["means"][dim]
            start = int.from_bytes(f"{h}|{rnd}".encode(), "little") % max(len(low_all), 1)
            for i in range(len(low_all)):
                lo = low_all[(start + i) % len(low_all)]
                if lo == h or uses.get(lo, 0) >= PAIR_MAX_USES or frozenset((h, lo)) in seen:
                    continue
                if mh - pool[lo]["means"][dim] >= PAIR_GAP:
                    seen.add(frozenset((h, lo)))
                    uses[h] = uses.get(h, 0) + 1
                    uses[lo] = uses.get(lo, 0) + 1
                    out.append((h, lo))
                    break
    print(f"{NAME}: pair_{key}: {len(high)} high words, {len(low_all)} candidates, {len(out)} pairs")
    for h, lo in out:
        a, b = hash_order([h, lo], lambda w: w, f"{SALT}|{dim}|order")
        yield Question(
            text=PAIR_TEXT.format(s=phrase, a=a, b=b),
            primitive="choice",
            hemisphere="world",
            kind="perception",
            origin="template",
            source=NAME,
            options={a: None, b: None},
            node_hint=NODE,
            human_text=PAIR_HUMAN.format(s=phrase, a=a, b=b),
            source_item_id=f"{a.upper()}|{b.upper()}:{dim}",
            license=LICENSE,
            truth=h,
            template_id=f"{NAME}.pair_{key}",
            meta={
                **_flags(a, b),
                "sense": key,
                "means_0_5": {w: round(pool[w]["means"][dim], 3) for w in (a, b)},
                "sds": {w: round(pool[w]["sds"][dim], 3) for w in (a, b)},
                "n_raters": {w: pool[w]["n"] for w in (a, b)},
                "truth_rule": f"higher mean on {dim}; gap >= {PAIR_GAP}, lower mean >= {PAIR_LOW_MIN}",
            },
        )


def normalize(raw_dir: Path) -> Iterator[Question]:
    pool = _pool(raw_dir)
    print(f"{NAME}: {len(pool)} common known single words")
    yield from _dominant(pool)
    for dim in SENSES:
        yield from _pairs(pool, dim)
