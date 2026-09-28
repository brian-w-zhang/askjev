"""How apt and how familiar is a two-word metaphor ("dark thoughts"), next to literal twins ("fan brush")?
(research pass 2, idea 3.)

Human data: "Metaphors in context and in isolation: Familiarity, aptness, concreteness, metaphoricity, and structure
norms for 300 two-word expressions" (2025; article CC BY 4.0; data OSF xk3j9, no license stated on the project).
Crowd raters (about 25 per item) rated each expression on 1-7 scales, in isolation and inside a sentence. The
trial-level files (df_apt.csv, df_fam.csv) give the full distribution of ratings per expression; the isolation
ratings are used, because the question shows the expression alone. 93 of the 300 are literal expressions, the
contrast for the metaphors.

Aptness was defined to raters as "the extent to which the vehicle captures important features of the topic";
familiarity as "the extent to which participants had heard or read each expression in the past", 1 truly not
familiar to 7 very familiar. The seven level descriptions are this project's, anchored on those definitions.
"""

from __future__ import annotations

import csv
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterator

from askjev.model import HumanDist, Question

NAME = "metaphor_norms"
NODE = "world.society.languages.word.metaphors"
LICENSE = "Article CC BY 4.0; data from OSF xk3j9 (no license stated on the project); used for non-commercial research"
FILES = {"Norms.csv": "kg6uh", "df_apt.csv": "hwk8g", "df_fam.csv": "2p9jk"}
APT = ["Not apt at all: the first word captures nothing important about what it describes",
       "Barely apt: the link is strained",
       "Slightly apt: a weak link",
       "Somewhat apt: the link works but is ordinary",
       "Fairly apt: it captures something real",
       "Very apt: it captures important features well",
       "Perfectly apt: it captures exactly what matters"]
FAM = ["Truly unfamiliar: I have never heard or read it",
       "Very unfamiliar: I might have come across it once",
       "Rather unfamiliar: rarely heard or read",
       "Somewhat familiar: now and then",
       "Fairly familiar: I have heard or read it a fair amount",
       "Very familiar: I come across it often",
       "Extremely familiar: a set phrase everyone knows"]


def fetch(raw_dir: Path) -> None:
    for f, k in FILES.items():
        if not (raw_dir / f).exists():
            urllib.request.urlretrieve(f"https://osf.io/download/{k}/", raw_dir / f)


def _dists(path: Path) -> dict[str, Counter]:
    out: dict[str, Counter] = defaultdict(Counter)
    for r in csv.DictReader(open(path, encoding="utf-8-sig")):
        if r["context"] == "0" and r["rating"].strip():
            out[r["item"]][str(int(float(r["rating"])) - 1)] += 1
    return out


def normalize(raw_dir: Path) -> Iterator[Question]:
    norms = {r["item"]: r for r in csv.DictReader(open(raw_dir / "Norms.csv", encoding="utf-8-sig"))}
    apt, fam = _dists(raw_dir / "df_apt.csv"), _dists(raw_dir / "df_fam.csv")
    for item, r in sorted(norms.items()):
        phrase = f"{r['modifier']} {r['head']}"
        meta = {"experiment": "metaphors", "item": item, "phrase": phrase, "literal": r["literalness"] == "yes",
                "structure": r["structure"], "vehicle_position": r["vehicle_position"], "topic": r["topic"],
                "apt_isolation": float(r["APTi"]), "apt_context": float(r["APTc"]), "fam_isolation": float(r["FAMi"]),
                "metaphoricity": float(r["MET"])}
        for set_, dists, levels, text in (
                ("aptness", apt, APT, f'How apt is the expression "{phrase}": how well does the describing word capture '
                                      "important features of what it describes?"),
                ("familiarity", fam, FAM, f'How familiar is the expression "{phrase}": how often have you heard or read it?')):
            c = dists.get(item)
            if not c:
                continue
            tot = sum(c.values())
            yield Question(
                text=text, primitive="score", hemisphere="world", kind="perception", origin="dataset", source=NAME,
                options=levels, node_hint=NODE, license=LICENSE, source_item_id=f"{set_}:{item}",
                human=[HumanDist(population="Crowd raters, expression shown in isolation (OSF xk3j9)",
                                 distribution={str(i): c.get(str(i), 0) / tot for i in range(7)}, n=tot,
                                 source=f"df_{'apt' if set_ == 'aptness' else 'fam'}.csv, context = 0, ratings 1-7")],
                meta={**meta, "set": set_})
