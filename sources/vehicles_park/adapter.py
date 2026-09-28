"""No vehicles in the park: does a rule mean its words or its purpose? (Struchiner, Hannikainen & Almeida 2020.)

Human data: Struchiner, Hannikainen & de Almeida 2020, "An experimental guide to vehicles in the park", Judgment and
Decision Making 15(3):312-329; data and stimuli at https://osf.io/7ft6e (no license stated; used for non-commercial
research). Participants (Brazilian adults, in Portuguese; the English stimuli are the authors' own translations on
OSF) read a rule and the incident that prompted it, then judged cases where the text and the purpose of the rule come
apart. Study 1: "no dogs in the restaurant" with 8 cases. Study 2: four rules (shoes, cars in the park, sleeping in
the station, smartphones in class), each with a core case, an overinclusive one (text broken, purpose kept), an
underinclusive one (purpose broken, text kept) and an off-topic one; cells missing from the data are left out.
Respondents flagged by the authors for knowing the first author's research are excluded.
"""

from __future__ import annotations

import csv
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterator

from askjev.model import HumanDist, Question

NAME = "vehicles_park"
NODE = "world.society.crime_law.law.rule_interpretation"
LICENSE = "OSF 7ft6e (Struchiner, Hannikainen & Almeida 2020), no license stated; non-commercial research use"
FILES = {"study1.csv": "https://osf.io/download/3vqar/", "study2.csv": "https://osf.io/download/mab8q/"}
Q = "Did the person break the rule?"

DOGS = ("One day, a black dog called Angus ran, jumped around, barked and ate off the floor in a restaurant. Such case "
        "was thought to be the paradigm of something to be avoided in the future: behaviors that cause nuisances to "
        "customers. Thus, the restaurant's owners created a rule: \"no dogs in the restaurant\".")
STUDY1 = {  # case code: (text, text broken?, purpose broken?)
    "core": ("A man enters the restaurant with a dog that runs, jumps, barks and eats food from the floor.", True, True),
    "gato": ("A man enters the restaurant with his pet cat.", False, None),
    "kid_saco": ("A kid enters the restaurant carrying a goldfish inside a plastic bag filled with water, which was "
                 "bought moments before at the pet shop near the restaurant.", False, False),
    "kid_toy": ("A kid enters the restaurant with a cutting edge toy: an extremely realistic robot dog, identical to a "
                "real dog and who acts like a real dog: it barks, jumps, drools and walks on four paws.", False, True),
    "man_dead_dog": ("A man enters the restaurant bringing a taxidermied dog, which he takes everywhere he goes as a way "
                     "to keep close to his old buddy.", None, False),
    "man_pig": ("A man comes to the restaurant with what seems to be a pig. Actually, it's his dog dressed in an "
                "extremely realistic costume. We only realize that the man is accompanied by a dog - and not a pig - "
                "because he barks somewhat frequently.", True, True),
    "kid_quiet_dog": ("A child enters the restaurant carrying a purse containing what seems to be a teddy bear. Actually, "
                      "it's her dog, who doesn't bark and barely moves, being easily mistaken for a toy.", True, False),
    "cao_guia": ("A blind man arrives at the restaurant with his seeing eye dog, for which he holds documentation "
                 "proving special training that ensures he won't cause nuisances to the other customers in the "
                 "restaurant.", True, False),
}
RULES = {
    "shoes": ("One day, John entered Mary's house with dirty feet, dirtying the carpets Mary had in her living room. Mary, "
              "weighing the seriousness of the situation and aiming to keep her house clean, established that \"no one "
              "can enter my home wearing shoes\".",
              {"core": "A person enters the house wearing dirty boots.",
               "over": "A person enters the house wearing very clean shoes that she just bought, unboxed and put on at "
                       "the house's entrance hall.",
               "under": "A person enters the house barefoot, but with very dirty feet.",
               "offtopic": "A person enters the house barefoot and with clean feet."}),
    "car": ("One day, at the local park, there was a tragic accident involving a pedestrian and a car. The park's "
            "administrator, attending to the seriousness of the situation and aiming to avoid accidents that can imperil "
            "parkgoers' physical integrity, established that: \"no cars are allowed inside the park\".",
            {"core": "A person enters the park in his car.", "over": "A kid enters the park and plays with his toy car.",
             "under": "A person enters the park in his motorbike.", "offtopic": "A person walks into the park."}),
    "train_station": ("A group of people slept at the benches of the train station every night. The train station "
                      "administrator, weighing the seriousness of the situation and aiming to avoid that people would use "
                      "the station benches as their homes, established that \"no sleeping is allowed on the station's "
                      "benches\".",
                      {"core": "A homeless person sleeps at the train station's benches every night.",
                       "over": "A busy businessman is waiting for his train sitting on a bench at the station. However, "
                               "he is very tired because of all the work he has done all day and falls asleep for about 5 "
                               "minutes.",
                       "under": "A homeless person spends 12 hours a day sitting on a bench at the station, without, "
                                "however, ever sleeping there.",
                       "offtopic": "A person enters the station and buys tickets for the next train."}),
    "cellphone": ("Classes at a given school were frequently disrupted by students using their smartphones. The school's "
                  "principal, aiming that students should pay attention to their classes, established that \"no "
                  "smartphones are allowed in the classroom\".",
                  {"core": "A student is texting in his smartphone instead of paying attention to his class.",
                   "over": "An assignment requires the use of a calculator and a student is using his smartphone "
                           "calculator in order to complete the required assignment.",
                   "under": "A student is using his tablet to play videogames during class.",
                   "offtopic": "A student is paying close attention to class."}),
}
POP = "Brazilian adults (Struchiner, Hannikainen & Almeida 2020, Study {s}; in Portuguese)"


def fetch(raw_dir: Path) -> None:
    for f, u in FILES.items():
        if not (raw_dir / f).exists():
            urllib.request.urlretrieve(u, raw_dir / f)


def _q(rule_text, case_text, votes: Counter, study, cid, **meta) -> Question:
    n = votes["1"] + votes["0"]
    return Question(
        text=f"{rule_text}\n\n{case_text}\n\n{Q}", primitive="noul", hemisphere="self", kind="values", origin="dataset",
        source=NAME, options=None, node_hint=NODE, license=LICENSE, source_item_id=f"study{study}:{cid}",
        human=[HumanDist(population=POP.format(s=study), distribution={"true": votes["1"] / n, "false": votes["0"] / n},
                         n=n, source=f"OSF 7ft6e study{study}.csv, rule-violation judgment")],
        meta={"experiment": "vehicles_park", "study": study, **meta})


def normalize(raw_dir: Path) -> Iterator[Question]:
    v1: dict[str, Counter] = defaultdict(Counter)
    for r in csv.DictReader(open(raw_dir / "study1.csv")):
        v1[r["case"]][r["rule"]] += 1
    for cid, (case, text_broken, purpose_broken) in STUDY1.items():
        yield _q(DOGS, case, v1[cid], 1, cid, rule="dogs", case=cid, text_broken=text_broken, purpose_broken=purpose_broken)
    v2: dict[tuple, Counter] = defaultdict(Counter)
    for r in csv.DictReader(open(raw_dir / "study2.csv")):
        if r["flagged_for_exclusion"] == "0":
            v2[(r["case_rule"], r["category"])][r["rule_violation"]] += 1
    cat = {"core": (True, True), "over": (True, False), "under": (False, True), "offtopic": (False, False)}
    for rid, (rule, cases) in RULES.items():
        for c, case in cases.items():
            if sum(v2[(rid, c)].values()) >= 20:
                yield _q(rule, case, v2[(rid, c)], 2, f"{rid}-{c}", rule=rid, case=c,
                         text_broken=cat[c][0], purpose_broken=cat[c][1])
