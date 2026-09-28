"""Classic reasoning traps and fresh isomorphs (docs/15 E23; docs/experiments/reasoning_*.md).

Six trap families, each as the famous published version plus isomorphs written for this project (same structure,
new story and numbers), so a model that has memorized the famous answer can be told apart from one that reasons:
the conjunction fallacy (Linda; Tversky & Kahneman 1983), base-rate neglect (the taxi cab; Tversky & Kahneman 1982),
Monty Hall, the birthday problem, the gambler's fallacy, and the Cognitive Reflection Test (Frederick 2005).

Human data: only where a study reports the split for the same question. The Linda two-option version has one:
Tversky & Kahneman 1983 report that 85% of 142 respondents chose the conjunction, stored as a human distribution.
The others keep what the studies report in meta (the taxi cab's median answer, 80%) or a note, never a made-up
distribution. Every item has a right answer (truth) and, where one exists, the intuitive wrong answer (meta.lure).
Some isomorphs are deliberate controls where the famous rule does not apply (a host who opens a door at random; a
base rate of 50%; a coin of unknown fairness), marked meta.control.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterator

from askjev.model import HumanDist, Question

NAME = "reasoning_traps"
NODE = "world.science.psychology_neuroscience.cognition.judgment_biases"
NODE_PROB = "world.science.mathematics.probability"
LICENSE = "Classic problems transcribed from the cited studies (research use with citation); isomorphs authored for this project"
PCT = {f"p{v:03d}": f"{v}%" for v in range(0, 101, 5)}


def fetch(raw_dir: Path) -> None:
    """Nothing to download: the classic items are transcribed from the papers below, the isomorphs are written here."""


def _q(text, options, family, item, truth, *, classic=False, lure=None, node=NODE, human=None, control=False,
       note=None, **meta) -> Question:
    return Question(
        text=text, primitive="choice", hemisphere="world", kind="factual", origin="dataset" if classic else "synthetic",
        source=NAME, options=options, node_hint=node, truth=truth, license=LICENSE, source_item_id=f"{family}:{item}",
        human=human or [],
        meta={"experiment": "reasoning_traps", "family": family, "item": item, "classic": classic, "lure": lure,
              "control": control, **({"human_note": note} if note else {}), **meta})


# ---- conjunction (Linda) ----------------------------------------------------------------------------------------------
LINDA = ("Linda is 31 years old, single, outspoken, and very bright. She majored in philosophy. As a student, she was "
         "deeply concerned with issues of discrimination and social justice, and also participated in anti-nuclear "
         "demonstrations. Which is more probable?")
CONJ = [  # (item, description, single, conjunction)
    ("hiker", "Tom is 28. He spends every weekend in the mountains, trains at a climbing gym three nights a week and "
              "reads climbing magazines. Which is more probable?",
     "Tom is an accountant", "Tom is an accountant who goes rock climbing"),
    ("violinist", "Maria studied at a music conservatory, practices the violin every day and spends her holidays at "
                  "music festivals. Which is more probable?",
     "Maria works in a bank", "Maria works in a bank and plays in an amateur orchestra"),
    ("tinkerer", "Sam is quiet, spends his evenings writing code and building gadgets, and runs a small electronics "
                 "blog. Which is more probable?",
     "Sam is a history teacher", "Sam is a history teacher who writes code as a hobby"),
    ("farm", "Anna is 55. She grew up on a farm, keeps chickens and bakes her own bread every week. Which is more "
             "probable?",
     "Anna lives in a big city", "Anna lives in a big city and grows vegetables on her balcony"),
    ("chef", "Kenji trained as a chef in Osaka, spends his free time at food markets and writes a cooking newsletter. "
             "Which is more probable?",
     "Kenji works as a nurse", "Kenji works as a nurse and cooks elaborate dinners for his friends"),
    ("flood", "Think about the coming year. Which is more probable?",
     "A flood somewhere in North America in which more than 1,000 people drown",
     "An earthquake in California that causes a flood in which more than 1,000 people drown"),
]

# ---- base rates (taxi cab) --------------------------------------------------------------------------------------------
TAXI = ("A cab was involved in a hit-and-run accident at night. Two cab companies, the Green and the Blue, operate in "
        "the city. 85% of the cabs in the city are Green and 15% are Blue. A witness identified the cab as Blue. The "
        "court tested the witness under the same conditions as that night and found that the witness identified each "
        "color correctly 80% of the time and failed 20% of the time. What is the probability that the cab involved "
        "was Blue rather than Green?")
BASE = [  # (item, text, base rate, hit rate, false-alarm rate, control)
    ("buses", "30% of a town's buses are red and 70% are white. At dusk, a witness says the bus that hit a mailbox was "
              "red. Tests show the witness names a bus's color correctly 70% of the time in that light. What is the "
              "probability that the bus was red?", 0.30, 0.70, 0.30, False),
    ("machines", "In a factory, 20% of the parts come from Machine B and 80% from Machine A. An inspector who says which "
                 "machine made a part is right 90% of the time. She says a defective part came from Machine B. What is "
                 "the probability that it did?", 0.20, 0.90, 0.10, False),
    ("test", "A rare condition affects 5% of the people who come to a clinic. A test for it gives the right result 90% "
             "of the time, whether or not a person has the condition. A patient tests positive. What is the "
             "probability that the patient has the condition?", 0.05, 0.90, 0.10, False),
    ("screening", "1% of the people screened for a disease have it. The screening test catches 95% of the people who "
                  "have it, and wrongly flags 5% of the people who don't. A person is flagged. What is the probability "
                  "that they have the disease?", 0.01, 0.95, 0.05, False),
    ("fifty_fifty", "Half of the parcels at a depot are fragile and half are not. A scanner labels a parcel's "
                       "fragility correctly 80% of the time. It labels a parcel fragile. What is the probability that "
                       "it is fragile?", 0.50, 0.80, 0.20, True),
]

# ---- Monty Hall ---------------------------------------------------------------------------------------------------------
MONTY_OPTS = {"stay": "Stay with the first choice", "switch": "Switch", "no_difference": "It makes no difference"}
MONTY = ("You are on a game show and given the choice of three doors. Behind one door is a car; behind the others, "
         "goats. You pick door No. 1, and the host, who knows what is behind the doors and always opens a door with a "
         "goat, opens door No. 3, which has a goat. He then says: \"Do you want to pick door No. 2?\" Is it to your "
         "advantage to switch your choice?")
MONTY_ISO = [  # (item, text, truth, control)
    ("four_doors", "A game show has four doors, with a prize behind one. You pick a door. The host, who knows where the "
                   "prize is and always does this, opens two of the other three doors, both empty, and offers you the "
                   "one remaining closed door instead of yours. Is it to your advantage to switch?", "switch", False),
    ("ignorant_host", "A game show has three doors, with a prize behind one. You pick a door. The host does not know "
                      "where the prize is; he opens one of the other two doors at random, and it happens to be empty. "
                      "He offers you the other closed door. Is it to your advantage to switch?", "no_difference", True),
    ("boxes", "Three sealed boxes sit on a table and one holds a gold coin. You point to one box. The dealer, who "
              "knows which box holds the coin and always does this, lifts one of the two boxes you didn't point to "
              "and shows it is empty. You may now take the other unopened box instead. Is it to your advantage to "
              "change?", "switch", False),
    ("cards", "Three cards lie face down; one is the ace of hearts. You put your finger on one card. Your friend, who "
              "has seen the cards and always does this, turns over one of the other two cards, showing it is not the "
              "ace. You may keep your card or take the last face-down card. Is it to your advantage to switch?",
     "switch", False),
]
PRISONERS = ("Three prisoners, A, B and C, are told that one of them, chosen at random, will be pardoned. A asks the "
             "guard, who knows who will be pardoned, to name one of the other two who will not be. The guard, who "
             "always names a prisoner who will not be pardoned (choosing at random if both won't be), says \"B\". "
             "What is the chance now that A will be pardoned?")
THIRDS = {"one_third": "1 in 3", "one_half": "1 in 2", "two_thirds": "2 in 3"}

# ---- birthday -----------------------------------------------------------------------------------------------------------
BDAY_OPTS = {"b2_9": "2 to 9", "b10_19": "10 to 19", "b20_29": "20 to 29", "b30_49": "30 to 49", "b50_99": "50 to 99",
             "b100_182": "100 to 182", "b183": "183 or more"}
SMALL = lambda top: {f"n{i}": str(i) for i in range(2, top)} | {f"n{top}": f"{top} or more"}  # noqa: E731

# ---- gambler's fallacy --------------------------------------------------------------------------------------------------
GAMBLER = [  # (item, text, options, truth, lure, classic, control)
    ("coin", "A fair coin has come up heads five times in a row. On the next toss, which is more likely?",
     {"heads": "Heads", "tails": "Tails", "equal": "Heads and tails are equally likely"}, "equal", "tails", True, False),
    ("roulette", "At a fair roulette wheel, red has come up eight spins in a row. On the next spin, leaving green "
                 "aside, which is more likely?",
     {"red": "Red", "black": "Black", "equal": "Red and black are equally likely"}, "equal", "black", False, False),
    ("family", "A couple has four children, all boys. They are expecting a fifth. Which is more likely?",
     {"boy": "A boy", "girl": "A girl", "equal": "A boy and a girl are about equally likely"}, "equal", "girl", False, False),
    ("lottery", "In a fair lottery six numbers are drawn from 1 to 49. Which draw is more likely?",
     {"sequence": "1, 2, 3, 4, 5, 6", "mixed": "7, 19, 23, 31, 38, 44", "equal": "Both are equally likely"},
     "equal", "mixed", False, False),
    ("unknown_coin", "You find an old coin and have no idea whether it is fair. You toss it 20 times and it lands heads "
                     "all 20 times. On the next toss, which is more likely?",
     {"heads": "Heads", "tails": "Tails", "equal": "Heads and tails are equally likely"}, "heads", "equal", False, True),
]

# ---- cognitive reflection -----------------------------------------------------------------------------------------------
CRT = [  # (family item, text, options, truth, lure, classic)
    ("bat_ball", "A bat and a ball cost $1.10 in total. The bat costs $1.00 more than the ball. How much does the ball "
                 "cost?", {"c05": "5 cents", "c10": "10 cents", "c15": "15 cents", "c55": "55 cents"}, "c05", "c10", True),
    ("pen_notebook", "A notebook and a pen cost $2.20 in total. The notebook costs $2.00 more than the pen. How much "
                     "does the pen cost?", {"c10": "10 cents", "c20": "20 cents", "c30": "30 cents", "c110": "$1.10"},
     "c10", "c20", False),
    ("drink_sandwich", "A sandwich and a drink cost $5.40 in total. The sandwich costs $5.00 more than the drink. How "
                       "much does the drink cost?", {"c20": "20 cents", "c40": "40 cents", "c50": "50 cents", "c270": "$2.70"},
     "c20", "c40", False),
    ("widgets", "If it takes 5 machines 5 minutes to make 5 widgets, how long would it take 100 machines to make 100 "
                "widgets?", {"m5": "5 minutes", "m20": "20 minutes", "m100": "100 minutes", "m500": "500 minutes"},
     "m5", "m100", True),
    ("printers", "If 3 printers take 3 hours to print 3 books, how long would it take 60 printers to print 60 books?",
     {"h1": "1 hour", "h3": "3 hours", "h20": "20 hours", "h60": "60 hours"}, "h3", "h60", False),
    ("bakers", "If 8 bakers bake 8 cakes in 8 hours, how long would it take 2 bakers to bake 2 cakes?",
     {"h2": "2 hours", "h4": "4 hours", "h8": "8 hours", "h16": "16 hours"}, "h8", "h2", False),
    ("lily_pads", "In a lake, there is a patch of lily pads. Every day, the patch doubles in size. If it takes 48 days "
                  "for the patch to cover the entire lake, how long would it take for the patch to cover half of the "
                  "lake?", {"d12": "12 days", "d24": "24 days", "d46": "46 days", "d47": "47 days"}, "d47", "d24", True),
    ("bacteria", "Bacteria in a jar double in number every minute. The jar is full after 60 minutes. After how many "
                 "minutes was it half full?", {"m30": "30 minutes", "m45": "45 minutes", "m58": "58 minutes",
                                               "m59": "59 minutes"}, "m59", "m30", False),
    ("mold", "A patch of mold triples in area every day. It covers a whole slice of bread on day 12. On which day did "
             "it cover a third of the slice?", {"d4": "Day 4", "d6": "Day 6", "d10": "Day 10", "d11": "Day 11"},
     "d11", "d4", False),
]
CRT_FAMILY = {"bat_ball": "bat_ball", "pen_notebook": "bat_ball", "drink_sandwich": "bat_ball", "widgets": "widgets",
              "printers": "widgets", "bakers": "widgets", "lily_pads": "lily_pads", "bacteria": "lily_pads", "mold": "lily_pads"}


def _bayes(base, hit, fa):
    return base * hit / (base * hit + (1 - base) * fa)


def _pct_key(x: float) -> str:
    return f"p{int(5 * round(100 * x / 5)):03d}"


def normalize(raw_dir: Path) -> Iterator[Question]:
    # conjunction
    yield _q(LINDA, {"bank_teller": "Linda is a bank teller",
                     "feminist_bank_teller": "Linda is a bank teller and is active in the feminist movement"},
             "conjunction", "linda", "bank_teller", classic=True, lure="feminist_bank_teller",
             human=[HumanDist(population="Undergraduates, two-option version (Tversky & Kahneman 1983)",
                              distribution={"feminist_bank_teller": 0.85, "bank_teller": 0.15}, n=142,
                              source="Tversky & Kahneman 1983, Psychological Review 90:293-315: 85% of 142 chose the conjunction")])
    for item, desc, single, both in CONJ:
        yield _q(desc, {"single": single, "conjunction": both}, "conjunction", item, "single", lure="conjunction")
    # base rates
    yield _q(TAXI, PCT, "base_rate", "taxi_cab", _pct_key(_bayes(0.15, 0.8, 0.2)), classic=True, lure="p080",
             node=NODE_PROB, exact=round(_bayes(0.15, 0.8, 0.2), 4), ordered=True,
             note="Tversky & Kahneman 1982 (in Kahneman, Slovic & Tversky, Judgment under Uncertainty): the median and "
                  "modal answer was 80%; the Bayesian answer is 41%.", human_median=80)
    for item, text, b, h, fa, control in BASE:
        p = _bayes(b, h, fa)
        yield _q(text, PCT, "base_rate", item, _pct_key(p), lure=None if control else _pct_key(h), node=NODE_PROB, exact=round(p, 4),
                 ordered=True, control=control)
    # Monty Hall
    yield _q(MONTY, MONTY_OPTS, "monty_hall", "classic", "switch", classic=True, lure="no_difference", node=NODE_PROB,
             note="Most people stay or say it makes no difference (Granberg & Brown 1995; Krauss & Wang 2003); no split "
                  "for this exact wording is stored.")
    for item, text, truth, control in MONTY_ISO:
        yield _q(text, MONTY_OPTS, "monty_hall", item, truth, lure="stay" if truth == "switch" else "switch",
                 node=NODE_PROB, control=control)
    yield _q(PRISONERS, THIRDS, "monty_hall", "three_prisoners", "one_third", lure="one_half", node=NODE_PROB,
             note="Gardner's three prisoners problem (1959), the Monty Hall problem's older twin.")
    # birthday
    yield _q("How many people must be in a room for the chance that at least two of them share a birthday to be more "
             "than 50%? (Ignore leap years; every day of the year is equally likely.)", BDAY_OPTS, "birthday", "classic",
             "b20_29", classic=True, lure="b183", node=NODE_PROB, exact=23, ordered=True)
    yield _q("How many people must be in a room for the chance that at least two of them were born in the same month "
             "to be more than 50%? (Assume all twelve months are equally likely.)", SMALL(13), "birthday", "months",
             "n5", lure="n6", node=NODE_PROB, exact=5, ordered=True)
    yield _q("How many people must be in a room for the chance that at least two of them were born on the same day of "
             "the week to be more than 50%? (Assume all seven days are equally likely.)", SMALL(8), "birthday", "weekdays",
             "n4", lure=None, node=NODE_PROB, exact=4, ordered=True)
    yield _q("In a room of 60 people, what is the chance that at least two of them share a birthday? (Ignore leap "
             "years; every day is equally likely.)", PCT, "birthday", "sixty", "p100", lure="p015", node=NODE_PROB,
             exact=0.9941, ordered=True)
    # gambler's fallacy
    for item, text, opts, truth, lure, classic, control in GAMBLER:
        yield _q(text, opts, "gambler", item, truth, classic=classic, lure=lure, node=NODE_PROB, control=control,
                 note="The streak is evidence about a coin of unknown fairness, so heads is the better bet." if control else None)
    # cognitive reflection
    for item, text, opts, truth, lure, classic in CRT:
        yield _q(text, opts, "crt", item, truth, classic=classic, lure=lure, crt_item=CRT_FAMILY[item],
                 note="Frederick 2005 (Journal of Economic Perspectives 19:25-42): the intuitive wrong answer is the most "
                      "common error." if classic else None)
