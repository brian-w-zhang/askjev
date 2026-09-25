"""Lancaster Sensorimotor Norms: "How much do you experience X by <sense>?" for 60 concrete words x 5 senses."""

from __future__ import annotations

import csv
import math
from pathlib import Path
from typing import Iterator

import importlib.util
import re
import sys

import httpx

from askjev.model import HumanDist, Question
from askjev.sampling import env_int, top_up

_spec = importlib.util.spec_from_file_location(
    "sources.concreteness", Path(__file__).parents[1] / "concreteness" / "adapter.py")
_c = importlib.util.module_from_spec(_spec)
sys.modules["sources.concreteness"] = _c
_spec.loader.exec_module(_c)

NAME = "lancaster"
FILE = "Lancaster_sensorimotor_norms_for_39707_words.csv"
URL = "https://osf.io/download/48wsc/"  # OSF node rwhs6 (Data component of 7emr6)
LICENSE = "CC BY 4.0 (Lynott, Connell, Brysbaert, Brand & Carney 2020)"
TARGET_V1 = 300  # 60 words x 5 senses, kept as-is so their ids stay stable
TARGET = env_int("TARGET_LANCASTER", TARGET_V1)  # Phase 6: 2,000 (400 words); wave 3: 10,000 (2,000 words)
MIN_PERCEPTUAL = 3.5
MIN_KNOWN = 0.8
MIN_SD = 0.3  # floor so a unanimous 0.0 mean still gives a proper (near point-mass) distribution
# Wave 3 pool, used only once the hand-written LEXICON is exhausted: common concrete words from the whole norms,
# judged common/concrete by Brysbaert et al. 2014 (SUBTLEX-US count and concreteness, downloaded alongside).
MIN_KNOWN_V3 = 0.95
MIN_CONCRETE_V3 = 4.0  # of 5
MIN_SUBTLEX_V3 = 100  # raw SUBTLEX-US count, about 2 per million

# 60 common concrete words, hand-picked to spread across senses and topics. word -> node_hint.
WORDS = {
    **dict.fromkeys(
        "lemon onion garlic cheese bread chocolate strawberry banana bacon pepper honey popcorn".split(),
        "world.food.dishes_ingredients",
    ),
    **dict.fromkeys("coffee tea milk".split(), "world.food.nonalcoholic_drinks"),
    **dict.fromkeys("beer wine".split(), "world.food.alcoholic_drinks"),
    **dict.fromkeys("dog cat horse cow elephant lion".split(), "world.nature.mammals"),
    **dict.fromkeys("owl parrot crow".split(), "world.nature.birds"),
    **dict.fromkeys("shark whale crab".split(), "world.nature.sea_life"),
    **dict.fromkeys("snake bee mosquito lizard".split(), "world.nature.reptiles_insects"),
    **dict.fromkeys("rose pine grass mushroom lavender cactus".split(), "world.nature.plants_fungi"),
    **dict.fromkeys("thunder rain snow wind".split(), "world.nature.weather_climate"),
    **dict.fromkeys("rock sand".split(), "world.nature.geology"),
    **dict.fromkeys("ocean volcano".split(), "world.places.physical_geography"),
    **dict.fromkeys("piano drum violin trumpet".split(), "world.arts.music"),
    **dict.fromkeys("hammer knife sandpaper".split(), "world.tech.engineering_inventions"),
    "siren": "world.tech.gadgets",
    **dict.fromkeys("soap perfume smoke".split(), "world.science.chemistry"),
    "ice": "world.science.physics",
    "velvet": "world.arts.fashion",
}

# Phase 6 candidate lexicon: common concrete nouns by world node (the first node listing a word wins). Only
# words in the norms with Max_strength.perceptual >= MIN_PERCEPTUAL and Percent_known >= MIN_KNOWN qualify;
# ASKJEV_TARGET_LANCASTER / 5 words are used, WORDS first, then qualifying lexicon words in salted-hash order.
LEXICON = {
    "world.food.dishes_ingredients": """apple orange grape peach pear plum cherry lime mango pineapple watermelon melon coconut
        kiwi apricot blueberry raspberry blackberry cranberry fig date raisin avocado tomato potato carrot cabbage lettuce
        spinach celery cucumber broccoli cauliflower pumpkin corn pea bean peanut walnut almond olive radish beet turnip
        ginger cinnamon vanilla mint basil parsley sage rosemary thyme oregano nutmeg clove curry mustard ketchup vinegar
        salt sugar butter cream yogurt egg rice pasta noodle soup stew sausage ham steak beef pork chicken turkey lamb
        salmon tuna shrimp lobster oyster sardine anchovy pizza burger sandwich taco salad toast pancake waffle cereal
        porridge jam jelly syrup gravy sauce mayonnaise pickle salami bagel pretzel chili horseradish wasabi tofu
        mushroom leek asparagus artichoke zucchini eggplant grapefruit tangerine lemonade""",
    "world.food.baking_sweets": """cake cookie biscuit pie muffin cupcake doughnut croissant brownie candy caramel toffee
        fudge marshmallow lollipop licorice icecream custard pudding meringue gingerbread frosting icing cheesecake
        tart scone crumpet sorbet""",
    "world.food.nonalcoholic_drinks": "juice soda cola cocoa smoothie milkshake espresso cappuccino",
    "world.food.alcoholic_drinks": "whiskey vodka rum gin brandy champagne cider tequila sherry",
    "world.nature.mammals": """tiger bear wolf fox deer rabbit mouse rat squirrel monkey gorilla chimpanzee zebra giraffe
        hippo rhinoceros camel kangaroo koala panda sheep goat pig donkey bat hedgehog skunk moose buffalo leopard
        cheetah otter beaver badger raccoon mole llama""",
    "world.nature.birds": """eagle hawk falcon pigeon dove duck goose swan chicken rooster hen peacock penguin ostrich
        flamingo sparrow robin seagull vulture woodpecker hummingbird canary turkey""",
    "world.nature.sea_life": "dolphin octopus squid jellyfish lobster seal walrus starfish clam mussel eel coral seaweed",
    "world.nature.reptiles_insects": """frog toad turtle tortoise crocodile alligator spider ant wasp hornet butterfly moth
        beetle ladybird cockroach fly flea cricket grasshopper caterpillar worm snail slug scorpion""",
    "world.nature.pets_breeds": "puppy kitten hamster goldfish poodle",
    "world.nature.plants_fungi": """tulip daisy lily sunflower orchid violet dandelion ivy moss fern oak maple willow
        palm bamboo seed leaf bark thorn nettle hay clover jasmine blossom petal""",
    "world.nature.weather_climate": """lightning fog hail storm cloud rainbow sunshine frost drizzle blizzard hurricane
        tornado breeze mist thunderstorm""",
    "world.nature.geology": "stone pebble gravel clay mud dirt dust soil marble granite crystal diamond gold silver lava",
    "world.places.physical_geography": """river lake mountain beach forest desert waterfall cave island valley cliff
        glacier jungle swamp meadow sea stream pond hill""",
    "world.arts.music": """guitar flute harp saxophone cello trombone clarinet accordion harmonica tuba banjo bell
        whistle song choir orchestra melody xylophone tambourine cymbal bagpipes""",
    "world.arts.visual_art": "painting sculpture paint canvas crayon chalk ink statue",
    "world.arts.fashion": """silk wool cotton leather denim fur lace satin scarf glove sweater jacket boot sandal
        necklace ring bracelet lipstick""",
    "world.tech.engineering_inventions": """saw drill screwdriver wrench nail screw axe shovel rope chain wire magnet
        scissors needle clock lamp candle ladder wheel engine""",
    "world.tech.gadgets": "telephone radio television camera alarm microphone headphones speaker keyboard doorbell",
    "world.tech.vehicles": "car truck bus train motorcycle bicycle airplane helicopter boat ship tractor ambulance horn",
    "world.science.chemistry": "bleach ammonia sulfur rust acid vinegar gasoline petrol chlorine glue wax plastic rubber",
    "world.science.physics": "fire steam flame spark echo explosion laser heat",
    "world.health.human_body": "sweat blood tongue skin hair tooth nose ear eye lip hand heartbeat sneeze cough yawn burp",
    "world.health.personal_care": "shampoo toothpaste deodorant lotion cologne razor towel sponge bath shower",
    "world.health.medicine": "bandage syringe pill medicine antiseptic",
    "world.society.holidays_traditions": "fireworks firework balloon cracker bonfire",
    "world.places.landmarks": "castle lighthouse fountain bridge tower",
    "world.sports.individual_sports": "trampoline skateboard ski",
    "world.sports.other_team_sports": "ball whistle",
}
AMBIGUOUS = {  # homographs or near-duplicates: never used even though listed
    "date", "fly", "mole", "ring", "cracker", "slug", "palm", "violet", "bark", "saw", "seal", "bat", "speaker", "firework",
}

# dimension column -> (gerund used in the question, noun used in the levels)
SENSES = {
    "Visual": ("seeing", "sight"),
    "Auditory": ("hearing", "sound"),
    "Gustatory": ("tasting", "taste"),
    "Olfactory": ("smelling", "smell"),
    "Haptic": ("feeling through touch", "touch"),
}


def _levels(gerund: str, noun: str) -> list[str]:
    return [
        f"Not at all: {gerund} plays no part in experiencing it",
        f"Slightly: its {noun} comes up only now and then, as a minor detail",
        f"Moderately: its {noun} is one noticeable part of experiencing it, alongside others",
        f"Strongly: its {noun} is one of the main ways I experience it",
        f"Greatly: {gerund} is central to experiencing it; its {noun} is what it is mostly about",
    ]


def fetch(raw_dir: Path) -> None:
    out = raw_dir / FILE
    if not out.exists():
        r = httpx.get(URL, follow_redirects=True, timeout=300)
        r.raise_for_status()
        out.write_bytes(r.content)
    _c.fetch_brysbaert(raw_dir)  # wave 3 pool (frequency + concreteness)


def _phi(x: float) -> float:
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def discretize(mean: float, sd: float) -> dict[str, float]:
    """Normal(mean, sd) on the 0-5 rating scale, cut into 5 unit bins: <1, 1-2, 2-3, 3-4, >=4 (tails folded in)."""
    sd = max(sd, MIN_SD)
    cdf = [0.0] + [_phi((edge - mean) / sd) for edge in (1, 2, 3, 4)] + [1.0]
    p = [cdf[i + 1] - cdf[i] for i in range(5)]
    s = sum(p)
    return {str(i): v / s for i, v in enumerate(p)}


def _words(rows: dict[str, dict], raw_dir: Path) -> dict[str, str]:
    """WORDS, then (Phase 6) qualifying LEXICON words, then (wave 3) common concrete words from the whole norms,
    each list in salted-hash order, up to TARGET / 5 words in all."""
    k = TARGET // len(SENSES)
    words = dict(list(WORDS.items())[:k])
    cands: dict[str, str] = {}
    for node, ws in LEXICON.items():
        for w in ws.split():
            r = rows.get(w.upper())
            if w in WORDS or w in cands or w in AMBIGUOUS or r is None:
                continue
            if float(r["Max_strength.perceptual"]) >= MIN_PERCEPTUAL and float(r["Percent_known.perceptual"]) >= MIN_KNOWN:
                cands[w] = node
    for w in top_up(list(words), cands, k - len(words), lambda w: w, "lancaster.v2"):
        words[w] = cands[w]
    if len(words) < k:  # wave 3: LEXICON exhausted, so earlier word lists (and their rows) are unchanged
        brys = _c.read_brysbaert(raw_dir / _c.FILE)
        more = []
        for r in rows.values():
            w = r["Word"].lower()
            b = brys.get(w)
            if (b is None or w in words or w in cands or w in AMBIGUOUS or not re.fullmatch(r"[a-z]{3,}", w)
                    or _c.SLURS.match(w)):
                continue
            if (float(r["Max_strength.perceptual"]) >= MIN_PERCEPTUAL and float(r["Percent_known.perceptual"]) >= MIN_KNOWN_V3
                    and b["conc_m"] >= MIN_CONCRETE_V3 and b["subtlex"] >= MIN_SUBTLEX_V3 and b["bigram"] == 0):
                more.append(w)
        for w in top_up(list(words), more, k - len(words), lambda w: w, "lancaster.v3"):
            words[w] = _c.word_node(w)
    return words


def normalize(raw_dir: Path) -> Iterator[Question]:
    with open(raw_dir / FILE, newline="", encoding="utf-8") as fh:
        rows = {r["Word"]: r for r in csv.DictReader(fh)}
    for word, node in _words(rows, raw_dir).items():
        r = rows[word.upper()]
        n = int(float(r["N_known.perceptual"]))
        for dim, (gerund, noun) in SENSES.items():
            mean, sd = float(r[f"{dim}.mean"]), float(r[f"{dim}.SD"])
            yield Question(
                text=f'How much do you experience "{word}" by {gerund}?',
                primitive="score",
                hemisphere="world",
                kind="perception",
                origin="dataset",
                source=NAME,
                options=_levels(gerund, noun),
                node_hint=node,
                human_text=f'How much do most people experience "{word}" by {gerund}?',
                source_item_id=f"{word.upper()}:{dim}",
                license=LICENSE,
                human=[
                    HumanDist(
                        population="Lancaster norms raters",
                        distribution=discretize(mean, sd),
                        n=n,
                        source="Lancaster Sensorimotor Norms (OSF 7emr6)",
                    )
                ],
                meta={
                    **({"flags": fl} if (fl := _c.word_flags(word)) else {}),
                    "word": word,
                    "dimension": dim.lower(),
                    "mean_0_5": mean,
                    "sd": sd,
                    "dominant_perceptual": r["Dominant.perceptual"],
                    "dist_method": f"normal(mean, max(sd,{MIN_SD})) on the 0-5 scale, binned <1,1-2,2-3,3-4,>=4",
                },
            )
