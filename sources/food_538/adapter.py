"""FiveThirtyEight food data (CC BY 4.0): candy power ranking pairs, Food World Cup cuisine pairs with the human
split from respondents who rated both, Thanksgiving 2015 dinner customs and steak doneness with survey shares, and
WHO per-capita beer/wine/spirits comparisons."""

from __future__ import annotations

import csv
import hashlib
import itertools
import re
import unicodedata
from pathlib import Path
from typing import Iterator

import httpx

from askjev.model import HumanDist, Question
from askjev.sampling import env_int, hash_order

NAME = "food_538"
BASE = "https://raw.githubusercontent.com/fivethirtyeight/data/master/"
FILES = {
    "candy-data.csv": "candy-power-ranking/candy-data.csv",
    "food-world-cup-data.csv": "food-world-cup/food-world-cup-data.csv",
    "thanksgiving-2015-poll-data.csv": "thanksgiving-2015/thanksgiving-2015-poll-data.csv",
    "steak-risk-survey.csv": "steak-survey/steak-risk-survey.csv",
    "drinks.csv": "alcohol-consumption/drinks.csv",
}
LICENSE = "CC BY 4.0 (FiveThirtyEight data repository)"
SALT = "food_538.v1"
DRINKS_PER_TEMPLATE = env_int("FOOD_538_DRINKS_PER_TEMPLATE", 450)
CANDY_TRUTH_GAP = 10.0  # winpercent points
FWC_MIN_N = 100

CANDY_NAMES = {
    "Chewey Lemonhead Fruit Mix": "Chewy Lemonhead Fruit Mix",
    "Lifesavers big ring gummies": "Life Savers Big Ring Gummies",
    "Peanut butter M&M's": "Peanut Butter M&M's",
    "Peanut M&Ms": "Peanut M&M's",
    "Mr Good Bar": "Mr. Goodbar",
    "Nestle Butterfinger": "Butterfinger",
    "Nestle Crunch": "Nestlé Crunch",
    "Nik L Nip": "Nik-L-Nip",
    "Pixie Sticks": "Pixy Stix",
    "Red vines": "Red Vines",
    "Reese's Peanut Butter cup": "Reese's Peanut Butter Cups",
    "Reese's pieces": "Reese's Pieces",
    "Reese's stuffed with pieces": "Reese's Cups stuffed with Reese's Pieces",
    "Ring pop": "Ring Pop",
    "Skittles original": "Skittles Original",
    "Skittles wildberry": "Skittles Wild Berry",
    "Nestle Smarties": "Nestlé Smarties (candy-coated chocolate)",
    "Smarties candy": "Smarties (US tablet candy)",
    "Strawberry bon bons": "Strawberry Bon Bons",
    "Air Heads": "Airheads",
    "Tootsie Roll Midgies": "Tootsie Roll Midgees",
}
NON_CANDY = {"One dime", "One quarter"}

DRINK_TEMPLATES = [
    ("beer_servings", "beer", "According to World Health Organization estimates, in which country do adults drink more beer per person: {a} or {b}?"),
    ("wine_servings", "wine", "According to World Health Organization estimates, in which country do adults drink more wine per person: {a} or {b}?"),
    ("spirit_servings", "spirits", "According to World Health Organization estimates, in which country do adults drink more spirits (such as vodka, whiskey or rum) per person: {a} or {b}?"),
]
COUNTRY_NAMES = {
    "Antigua & Barbuda": "Antigua and Barbuda", "Bosnia-Herzegovina": "Bosnia and Herzegovina",
    "Cote d'Ivoire": "Ivory Coast", "Cabo Verde": "Cape Verde", "DR Congo": "the Democratic Republic of the Congo",
    "Congo": "the Republic of the Congo", "Russian Federation": "Russia", "St. Kitts & Nevis": "Saint Kitts and Nevis",
    "St. Lucia": "Saint Lucia", "St. Vincent & the Grenadines": "Saint Vincent and the Grenadines",
    "Sao Tome & Principe": "São Tomé and Príncipe", "Trinidad & Tobago": "Trinidad and Tobago",
    "USA": "the United States", "United Kingdom": "the United Kingdom", "United Arab Emirates": "the United Arab Emirates",
    "Netherlands": "the Netherlands", "Philippines": "the Philippines", "Bahamas": "the Bahamas",
    "Czech Republic": "the Czech Republic", "Dominican Republic": "the Dominican Republic",
    "Central African Republic": "the Central African Republic", "Marshall Islands": "the Marshall Islands",
    "Solomon Islands": "the Solomon Islands", "Cook Islands": "the Cook Islands", "Gambia": "the Gambia",
    "Macedonia": "North Macedonia", "Swaziland": "Eswatini", "North Korea": "North Korea",
    "Guinea-Bissau": "Guinea-Bissau", "Timor-Leste": "Timor-Leste", "Comoros": "the Comoros",
    "Maldives": "the Maldives", "Seychelles": "the Seychelles",
}
COUNTRY_SKIP = {"Palestine"}  # contested; not asked


def fetch(raw_dir: Path) -> None:
    with httpx.Client(timeout=120, follow_redirects=True) as client:
        for local, remote in FILES.items():
            out = raw_dir / local
            if out.exists():
                continue
            r = client.get(BASE + remote)
            r.raise_for_status()
            out.write_bytes(r.content)


def _read(path: Path) -> list[list[str]]:
    with open(path, encoding="latin1", newline="") as fh:
        return list(csv.reader(fh))


def _slug(name: str) -> str:
    s = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().lower()
    s = re.sub(r"\(.*?\)", "", s).replace("&", " and ").replace("'", "")
    s = re.sub(r"[^a-z0-9]+", "_", s).strip("_")
    return s[:40].rsplit("_", 1)[0] if len(s) > 40 else s


def _flip(*parts) -> bool:
    return int(hashlib.sha256("|".join(map(str, (SALT, *parts))).encode()).hexdigest(), 16) % 2 == 1


def _candy(raw_dir: Path) -> Iterator[Question]:
    rows = [r for r in csv.DictReader(open(raw_dir / "candy-data.csv", encoding="latin1"))
            if r["competitorname"] not in NON_CANDY]
    candies = {CANDY_NAMES.get(r["competitorname"], r["competitorname"]): float(r["winpercent"]) for r in rows}
    for a, b in itertools.combinations(sorted(candies), 2):
        if _flip("candy", a, b):
            a, b = b, a
        ka, kb = _slug(a), _slug(b)
        gap = candies[a] - candies[b]
        if abs(gap) < CANDY_TRUTH_GAP:
            continue  # near-ties say nothing about the crowd's taste
        yield Question(
            text=f"Which candy would you rather have: {a} or {b}?",
            primitive="choice", hemisphere="self", kind="taste", origin="template", source=NAME,
            options={ka: a, kb: b}, node_hint="self.lifestyle.food_preferences",
            # a taste question has no truth: the crowd's pick is kept as metadata (Jev's taste vs the crowd's)
            source_item_id=f"candy:{ka}:{kb}", license=LICENSE, template_id="food_538.candy",
            meta={"winpercent": {ka: candies[a], kb: candies[b]}, "crowd_pick": ka if gap > 0 else kb},
        )


def _cuisines(raw_dir: Path) -> Iterator[Question]:
    rows = _read(raw_dir / "food-world-cup-data.csv")
    head, data = rows[0], rows[1:]
    cols = {}
    for i, h in enumerate(head):
        m = re.search(r"traditional cuisine of\s*(.+?)[.:]?\s*$", h.replace("\xca", " "))
        if m:
            name = m.group(1).strip()
            cols[name] = i
    ratings = {c: [int(r[i]) if r[i] in "12345" and r[i] else None for r in data] for c, i in cols.items()}
    for a, b in itertools.combinations(sorted(cols), 2):
        if _flip("cuisine", a, b):
            a, b = b, a
        wa = wb = 0.0
        n = 0
        for x, y in zip(ratings[a], ratings[b]):
            if x is None or y is None:
                continue
            n += 1
            if x > y:
                wa += 1
            elif y > x:
                wb += 1
            else:
                wa += 0.5
                wb += 0.5
        if n < FWC_MIN_N:
            continue
        la, lb = _cuisine_label(a), _cuisine_label(b)
        ka, kb = _slug(la), _slug(lb)
        yield Question(
            text=f"Which cuisine do you like more: {la} or {lb}?",
            primitive="choice", hemisphere="self", kind="taste", origin="template", source=NAME,
            options={ka: la, kb: lb}, node_hint="self.lifestyle.food_preferences",
            source_item_id=f"fwc:{ka}:{kb}", license=LICENSE,
            human=[HumanDist(population="US adults (FiveThirtyEight/SurveyMonkey Food World Cup, 2014)",
                             distribution={ka: round(wa / n, 4), kb: round(wb / n, 4)}, n=n,
                             source="share rating each cuisine higher on the 1-5 like scale among respondents who rated both; ties split",
                             wave="2014")],
            template_id="food_538.cuisine",
        )


DEMONYM = {
    "Algeria": "Algerian", "Argentina": "Argentine", "Australia": "Australian", "Belgium": "Belgian",
    "Bosnia and Herzegovina": "Bosnian", "Brazil": "Brazilian", "Cameroon": "Cameroonian", "Chile": "Chilean",
    "Colombia": "Colombian", "Costa Rica": "Costa Rican", "Croatia": "Croatian", "Ecuador": "Ecuadorian",
    "England": "English", "France": "French", "Germany": "German", "Ghana": "Ghanaian", "Greece": "Greek",
    "Honduras": "Honduran", "Iran": "Iranian", "Italy": "Italian", "Ivory Coast": "Ivorian", "Japan": "Japanese",
    "Mexico": "Mexican", "the Netherlands": "Dutch", "Nigeria": "Nigerian", "Portugal": "Portuguese",
    "Russia": "Russian", "South Korea": "Korean", "Spain": "Spanish", "Switzerland": "Swiss",
    "United States": "American", "Uruguay": "Uruguayan", "China": "Chinese", "India": "Indian", "Thailand": "Thai",
    "Turkey": "Turkish", "Cuba": "Cuban", "Ethiopia": "Ethiopian", "Vietnam": "Vietnamese", "Ireland": "Irish",
}


def _cuisine_label(country: str) -> str:
    return f"{DEMONYM[country]} food"


def _thanksgiving(raw_dir: Path) -> Iterator[Question]:
    rows = _read(raw_dir / "thanksgiving-2015-poll-data.csv")
    head, data = rows[0], rows[1:]
    pop = "US adults who celebrate Thanksgiving, describing their own dinner (FiveThirtyEight/SurveyMonkey, 2015)"
    # people who celebrate and answered the main-dish question (the menu block)
    cel = [r for r in data if r[1] == "Yes" and r[2] not in ("", "I don't know")]

    def choice(col: int, text: str, labels: dict[str, str], item: str, node: str):
        counts: dict[str, int] = {}
        for r in cel:
            v = r[col]
            if v in ("", "I don't know"):
                continue
            key = labels.get(v)
            if key is None:
                continue
            counts[key] = counts.get(key, 0) + 1
        n = sum(counts.values())
        opts = {k: None for k in dict.fromkeys(labels.values())}
        dist = {k: round(counts.get(k, 0) / n, 4) for k in opts}
        return Question(
            text=text, primitive="choice", hemisphere="world", kind="social", origin="dataset", source=NAME,
            options=opts, node_hint=node, source_item_id=f"thanksgiving:{item}", license=LICENSE,
            human=[HumanDist(population=pop, distribution=dist, n=n, source="FiveThirtyEight Thanksgiving 2015 poll", wave="2015")],
            template_id=f"food_538.thanksgiving_{item}",
        )

    yield choice(2, "What is the main dish at a typical American Thanksgiving dinner?",
                 {"Turkey": "turkey", "Ham/Pork": "ham_or_pork", "Tofurkey": "tofurkey", "Chicken": "chicken",
                  "Roast beef": "roast_beef", "Turducken": "turducken", "Other (please specify)": "other"},
                 "main_dish", "world.food.dishes_ingredients.meat")
    yield choice(4, "How is the main dish of a typical American Thanksgiving dinner cooked?",
                 {"Baked": "baked", "Roasted": "roasted", "Fried": "fried", "Other (please specify)": "other"},
                 "cooking", "world.food.cooking.cooking")
    yield choice(6, "What kind of stuffing is served at a typical American Thanksgiving dinner?",
                 {"Bread-based": "bread_based", "Rice-based": "rice_based", "None": "no_stuffing",
                  "Other (please specify)": "other"}, "stuffing", "world.food.dishes_ingredients.bread")
    yield choice(8, "What kind of cranberry sauce is served at a typical American Thanksgiving dinner?",
                 {"Canned": "canned", "Homemade": "homemade", "None": "no_cranberry_sauce",
                  "Other (please specify)": "other"}, "cranberry", "world.food.dishes_ingredients")

    def noul(item: str, text: str, yes: int, n: int, node: str):
        return Question(
            text=text, primitive="noul", hemisphere="world", kind="social", origin="template", source=NAME,
            options=None, node_hint=node, source_item_id=f"thanksgiving:{item}", license=LICENSE,
            human=[HumanDist(population=pop, distribution={"true": round(yes / n, 4), "false": round(1 - yes / n, 4)},
                             n=n, source="FiveThirtyEight Thanksgiving 2015 poll (share whose own dinner has it)", wave="2015")],
            template_id=f"food_538.thanksgiving_{item.split(':')[0]}",
        )

    gravy = [r for r in cel if r[10] in ("Yes", "No")]
    yield noul("gravy", "Is gravy usually served at an American Thanksgiving dinner?",
               sum(r[10] == "Yes" for r in gravy), len(gravy), "world.food.dishes_ingredients")

    phrases = {
        "Brussel sprouts": ("Brussels sprouts", "are"), "Carrots": ("carrots", "are"), "Cauliflower": ("cauliflower", "is"),
        "Corn": ("corn", "is"), "Cornbread": ("cornbread", "is"), "Fruit salad": ("fruit salad", "is"),
        "Green beans/green bean casserole": ("green beans or green bean casserole", "are"),
        "Macaroni and cheese": ("macaroni and cheese", "is"), "Mashed potatoes": ("mashed potatoes", "are"),
        "Rolls/biscuits": ("rolls or biscuits", "are"), "Squash": ("squash", "is"),
        "Vegetable salad": ("a vegetable salad", "is"), "Yams/sweet potato casserole": ("yams or sweet potato casserole", "are"),
        "Apple": ("apple pie", "is"), "Buttermilk": ("buttermilk pie", "is"), "Cherry": ("cherry pie", "is"),
        "Chocolate": ("chocolate pie", "is"), "Coconut cream": ("coconut cream pie", "is"), "Key lime": ("key lime pie", "is"),
        "Peach": ("peach pie", "is"), "Pecan": ("pecan pie", "is"), "Pumpkin": ("pumpkin pie", "is"),
        "Sweet Potato": ("sweet potato pie", "is"), "Apple cobbler": ("apple cobbler", "is"), "Blondies": ("blondies", "are"),
        "Brownies": ("brownies", "are"), "Carrot cake": ("carrot cake", "is"), "Cheesecake": ("cheesecake", "is"),
        "Cookies": ("cookies", "are"), "Fudge": ("fudge", "is"), "Ice cream": ("ice cream", "is"),
        "Peach cobbler": ("peach cobbler", "is"),
    }
    blocks = [("side", "Which of these side dishes", "world.food.dishes_ingredients"),
              ("pie", "Which type of pie", "world.food.baking_sweets"),
              ("dessert", "Which of these desserts", "world.food.baking_sweets")]
    for block, prefix, node in blocks:
        cols = [(i, h.rsplit(" - ", 1)[1].strip()) for i, h in enumerate(head) if h.startswith(prefix) and " - " in h]
        cols = [(i, lab) for i, lab in cols if lab in phrases]
        # a respondent answered the block if any option in it (incl. None/Other) is ticked
        block_cols = [i for i, h in enumerate(head) if h.startswith(prefix)]
        answered = [r for r in cel if any(r[i] for i in block_cols)]
        n = len(answered)
        for i, lab in cols:
            thing, verb = phrases[lab]
            yes = sum(1 for r in answered if r[i])
            yield noul(f"{block}:{_slug(lab)}",
                       f"{verb.capitalize()} {thing} usually served at an American Thanksgiving dinner?", yes, n, node)


def _steak(raw_dir: Path) -> Iterator[Question]:
    rows = _read(raw_dir / "steak-risk-survey.csv")[1:]
    labels = {"Rare": "rare", "Medium rare": "medium_rare", "Medium": "medium", "Medium Well": "medium_well", "Well": "well_done"}
    counts = {k: 0 for k in labels.values()}
    for r in rows:
        if r[8] == "Yes" and r[9] in labels:
            counts[labels[r[9]]] += 1
    n = sum(counts.values())
    yield Question(
        text="How do you like your steak cooked?",
        primitive="choice", hemisphere="self", kind="taste", origin="dataset", source=NAME,
        options={k: None for k in counts}, node_hint="self.lifestyle.food_preferences",
        source_item_id="steak:doneness", license=LICENSE,
        human=[HumanDist(population="US adults who eat steak (FiveThirtyEight/SurveyMonkey, 2014)",
                         distribution={k: round(v / n, 4) for k, v in counts.items()}, n=n,
                         source="FiveThirtyEight steak survey", wave="2014")],
        template_id="food_538.steak",
    )


def _drinks(raw_dir: Path) -> Iterator[Question]:
    rows = list(csv.DictReader(open(raw_dir / "drinks.csv", encoding="latin1")))
    for col, what, tmpl in DRINK_TEMPLATES:
        vals = {COUNTRY_NAMES.get(r["country"], r["country"]): int(r[col]) for r in rows
                if r["country"] not in COUNTRY_SKIP and int(r[col]) > 0}
        pairs = [(a, b) for a, b in itertools.combinations(sorted(vals), 2)
                 if max(vals[a], vals[b]) / min(vals[a], vals[b]) >= 2.0 and max(vals[a], vals[b]) >= 20]
        uses: dict[str, int] = {}
        taken = 0
        for a, b in hash_order(pairs, key=lambda p: f"{p[0]}|{p[1]}", salt=f"{SALT}|{col}"):
            if taken >= DRINKS_PER_TEMPLATE:
                break
            if uses.get(a, 0) >= 8 or uses.get(b, 0) >= 8:
                continue
            uses[a] = uses.get(a, 0) + 1
            uses[b] = uses.get(b, 0) + 1
            taken += 1
            if _flip(col, a, b):
                a, b = b, a
            ka, kb = _slug(a), _slug(b)
            truth = ka if vals[a] > vals[b] else kb
            yield Question(
                text=tmpl.format(a=a, b=b),
                primitive="choice", hemisphere="world", kind="factual", origin="template", source=NAME,
                options={ka: a[0].upper() + a[1:], kb: b[0].upper() + b[1:]}, node_hint="world.food.alcoholic_drinks",
                source_item_id=f"drinks:{col}:{ka}:{kb}", license=LICENSE, truth=truth,
                template_id=f"food_538.drinks_{what}",
                meta={"servings_per_person_per_year": {ka: vals[a], kb: vals[b]},
                      "data": "WHO Global Information System on Alcohol and Health, 2010 (via FiveThirtyEight)"},
            )


def normalize(raw_dir: Path) -> Iterator[Question]:
    yield from _candy(raw_dir)
    yield from _cuisines(raw_dir)
    yield from _thanksgiving(raw_dir)
    yield from _steak(raw_dir)
    yield from _drinks(raw_dir)
