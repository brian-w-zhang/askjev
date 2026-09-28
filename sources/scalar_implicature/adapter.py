"""Does "good" mean "not excellent"? Scalar implicature across ~160 scales (research pass 2, idea 1).

Human data: three published scalar-diversity experiments, as compiled by Hu, Levy, Degen & Schuster 2023
("Expectations over unspoken alternatives predict pragmatic inferences", github.com/jennhu/expectations-over-alternatives,
cross-scale/human_data): van Tiel, van Miltenburg, Zevakhina & Geurts 2016 (43 scales, Table 3, Exp. 2 with
non-neutral subjects), Gotzner, Solt & Benz 2018 (70 adjective scales, Tables A1-A2) and Pankratz & van Tiel 2021
(50 adjective scales, OSF t3b4u). In each, people read 'Mary says: "The food is good."' and answered whether they
would conclude that, according to Mary, the food is not excellent; the rate is the share who said yes. Jev gets the
same question.

van Tiel et al. used three sentences per scale and report one rate for the scale, so each of the three becomes a
question carrying that rate. The ten verb, quantifier and adverb scales are transcribed by hand from the paper's
sentences (their "X, but not Y" constructions don't split mechanically); few/none is left out (a double negative).
"""

from __future__ import annotations

import csv
import urllib.request
from pathlib import Path
from typing import Iterator

from askjev.model import HumanDist, Question

NAME = "scalar_implicature"
NODE = "world.society.languages.word.scalar_implicature"
LICENSE = ("Published experimental results (van Tiel et al. 2016; Gotzner et al. 2018; Pankratz & van Tiel 2021) as "
           "compiled by Hu et al. 2023 (no license stated); used for private, non-commercial research")
BASE = "https://raw.githubusercontent.com/jennhu/expectations-over-alternatives/HEAD/cross-scale/human_data/"
FILES = ["vt16.csv", "g18.csv", "pvt21.csv"]
STUDY = {"vt16": "van Tiel et al. 2016 (Exp. 2)", "g18": "Gotzner et al. 2018", "pvt21": "Pankratz & van Tiel 2021"}

# van Tiel et al. 2016 non-adjective scales: (weak statement, what the inference would conclude)
VT_VERBS = {
    "believe/know": [("The student believes it.", "the student does not know it"),
                     ("The mother believes it.", "the mother does not know it")],
    "dislike/loathe": [("The boy dislikes broccoli.", "the boy does not loathe broccoli"),
                       ("The teacher dislikes fighting.", "the teacher does not loathe fighting")],
    "like/love": [("The princess likes dancing.", "the princess does not love dancing"),
                  ("The actress likes the movie.", "the actress does not love the movie")],
    "may/will": [("This lawyer may appear in person.", "this lawyer will not appear in person"),
                 ("The teacher may come.", "the teacher will not come")],
    "may/have to": [("The boy may watch television.", "the boy does not have to watch television")],
    "participate/win": [("The freshman participated.", "the freshman did not win")],
    "some/all": [("The bartender saw some of the cars.", "the bartender did not see all of the cars"),
                 ("The nurse saw some of the signs.", "the nurse did not see all of the signs")],
    "sometimes/always": [("The assistant is sometimes angry.", "the assistant is not always angry"),
                         ("The director is sometimes late.", "the director is not always late")],
    "start/finish": [("The athlete started.", "the athlete did not finish"),
                     ("The dancer started.", "the dancer did not finish")],
    "try/succeed": [("The candidate tried.", "the candidate did not succeed"),
                    ("The athlete tried.", "the athlete did not succeed")],
}
COPULAS = ("is", "are", "was", "were")


def fetch(raw_dir: Path) -> None:
    for f in FILES:
        if not (raw_dir / f).exists():
            urllib.request.urlretrieve(BASE + f, raw_dir / f)


def _split(construction: str) -> tuple[str, str] | None:
    """'the food is adequate, but not good.' -> ('The food is adequate.', 'the food is not good')."""
    s = construction.strip().rstrip(".")
    if ", but not " not in s:
        return None
    left, strong = s.split(", but not ", 1)
    words = left.split()
    cop = next((i for i, w in enumerate(words) if w in COPULAS), None)
    if cop is None or cop == 0:
        return None
    subj = " ".join(words[:cop])
    weak = left[0].upper() + left[1:] + "."
    if words[0] in ("It", "He", "She", "The", "That", "This", "These", "Those"):  # mid-sentence in the question
        subj = subj[0].lower() + subj[1:]
    return weak, f"{subj} {words[cop]} not {strong}"


def _q(weak: str, neg: str, study: str, scale: str, rate: float, k: int, **meta) -> Question:
    return Question(
        text=f'Mary says: "{weak}" Would you conclude from this that, according to Mary, {neg}?',
        primitive="noul", hemisphere="world", kind="perception", origin="dataset", source=NAME, node_hint=NODE,
        license=LICENSE, source_item_id=f"{study}:{scale}:{k}",
        human=[HumanDist(population=f"English speakers in {STUDY[study]}", distribution={"true": rate, "false": 1 - rate},
                         n=None, source=f"{STUDY[study]}, per-scale inference rate (compiled by Hu et al. 2023)")],
        meta={"experiment": "scalar_implicature", "study": study, "scale": scale, "rate": rate, **meta})


def normalize(raw_dir: Path) -> Iterator[Question]:
    for r in csv.DictReader(open(raw_dir / "vt16.csv")):
        scale, rate = r["scale_id"], float(r["si_nonneutral"]) / 100
        kind = "adjective" if r["adj"] == "1" else r["pos"]
        if scale in VT_VERBS:
            items = VT_VERBS[scale]
        elif r["adj"] == "1":
            items = [x for x in (_split(r[f"nonneutral{i}_scalar_construction"]) for i in (1, 2, 3)) if x]
        else:
            continue  # few/none
        for k, (weak, neg) in enumerate(items):
            yield _q(weak, neg, "vt16", scale, rate, k, word_class=kind)
    for r in csv.DictReader(open(raw_dir / "g18.csv")):
        x = _split(r["scalar_construction"])
        if x:
            yield _q(*x, "g18", r["scale_id"], float(r["si_rate"]), 0, word_class="adjective",
                     extreme=r["extreme"] == "extreme")
    for r in csv.DictReader(open(raw_dir / "pvt21.csv")):
        weak, neg = r["weak_sentence"].strip(), r["strong_sentence"].strip().rstrip(".")
        yield _q(weak if weak.endswith(".") else weak + ".", neg, "pvt21", f"{r['weak_adj']}/{r['strong_adj']}",
                 float(r["SI_rate"]), 0, word_class="adjective", extreme=r["extreme"] == "1")
