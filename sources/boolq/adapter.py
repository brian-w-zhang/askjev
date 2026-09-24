"""BoolQ (Clark et al., NAACL 2019): real, naturally occurring Google yes/no queries, as general-knowledge Noul.

The question is asked without its Wikipedia passage, so only questions that stand on their own are kept:
anything pointing at unseen context ("this", "the show"), season/episode/plot/character trivia, time-sensitive
questions ("will there be", "still"), and any question with a digit are dropped. Casing is restored from the
passage and its title; node_hint comes from the title's disambiguator and a keyword lexicon over title + question.
"""

from __future__ import annotations

import re
from collections import Counter
from pathlib import Path
from typing import Iterator

import httpx
import polars as pl

from askjev.model import Question
from askjev.sampling import env_int, top_up

NAME = "boolq"
BASE = "https://huggingface.co/api/datasets"
FILES = {  # google/boolq is canonical; hugo/boolq is the same rows in the same order plus the Wikipedia title
    "train.parquet": f"{BASE}/google/boolq/parquet/default/train/0.parquet",
    "validation.parquet": f"{BASE}/google/boolq/parquet/default/validation/0.parquet",
    "titles_train.parquet": f"{BASE}/hugo/boolq/parquet/default/train/0.parquet",
    "titles_validation.parquet": f"{BASE}/hugo/boolq/parquet/default/validation/0.parquet",
}
LICENSE = "CC BY-SA 3.0"
TARGET = env_int("TARGET_BOOLQ", 6000)
SALT = "boolq-20260924"

# --- filters -------------------------------------------------------------------------------------------------
DIGIT = re.compile(r"\d")
CONTEXT = re.compile(  # needs the passage, a specific show's plot, or a moment in time
    r"\b(this|these|that one|the (show|series|movie|film|book|novel|game|song|album|episode|story|article|passage|"
    r"character|characters|author|finale|end|ending|last one)|season|seasons|episode\w*|finale|spoiler\w*|"
    r"character\w*|sequel\w*|prequel\w*|remake|reboot|renewed|cancell?ed|another|next|a new|the new|still|currently|"
    r"anymore|yet|upcoming|coming (out|back)|come out|going to|will there|gonna|any more|part two|"
    r"die|dies|died|dead|death|killed|kill|get together|end up|ends up|marry|married|pregnant|baby|"
    r"break up|get back together|leave the|left the|return|returns|back on|come back|comes back|"
    r"eliminated|voted off|stay together|love interest|finished for good|for good|second (movie|film|book|part|one))\b",
    re.I,
)
SLUR = re.compile(r"\b(nigg\w*|fag\w*|retard\w*|tranny)\b", re.I)
SENSITIVE = re.compile(r"\b(sex\w*|porn\w*|nude\w*|naked|prostitut\w*|suicid\w*|rape\w*|incest)\b", re.I)
POLITICAL = re.compile(
    r"\b(abortion|gun control|second amendment|death penalty|capital punishment|immigra\w*|refugee\w*|"
    r"republican\w*|democrat\w*|trump|obama|clinton|israel\w*|palestin\w*|gaza|same.sex|gay marriage|"
    r"marijuana|cannabis|weed|brexit|electoral college|gerrymander\w*|guns?|firearms?|handguns?|rifles?|executed)\b",
    re.I,
)
FICTIONAL_UNIVERSE = re.compile(  # title disambiguators that mark an in-universe character or place
    r"\((character|.*characters?|.*comics|middle-earth|star wars|star trek|harry potter|marvel.*|dc.*|"
    r"metal gear|pok[eé]mon|the walking dead|game of thrones|a song of ice and fire)\)$",
    re.I,
)
WORK_TITLE = re.compile(r"\((.*\bseason\b.*|.*episodes?|list of .*)\)|^list of .*(episodes|characters)", re.I)
SHOW_DISAMBIG = re.compile(  # "(Grey's Anatomy)", "(Friends)": a named work, not a category
    r"\(([A-Z][^)]*)\)$"
)
CATEGORY_WORD = re.compile(
    r"\b(film|films|tv|series|show|song|album|novel|book|game|comics?|band|musical|play|opera|miniseries|franchise|"
    r"magazine|newspaper|company|brand|restaurant|ride|coin|mascot|constellation|drink|dog|horse|genus|plant|"
    r"sport|sports|football|basketball|baseball|hockey|golf|tennis|chess|rugby|cricket|law|state|city|country|river|"
    r"u\.s\.|us|uk|united states|united kingdom|canada|australia|new zealand|ireland|india|philippines|england|"
    r"scotland|wales|texas|california|new york.*|florida|europe|asia|africa)\b",
    re.I,
)
WH = re.compile(r"^(what|which|who|whom|whose|when|where|why|how)\b", re.I)


FICTIONAL_SUBJECT = re.compile(r"\bfictional\b|\b(is|was) a (main |recurring |minor )?character\b", re.I)


def keep(question: str, title: str, passage: str = "") -> bool:
    q = question.strip()
    if FICTIONAL_SUBJECT.search(passage[:300]):  # the article is about a fictional character or place
        return False
    if DIGIT.search(q) or SLUR.search(q) or WH.match(q) or len(q.split()) < 4:
        return False
    if CONTEXT.search(q) or FICTIONAL_UNIVERSE.search(title) or WORK_TITLE.search(title):
        return False
    m = SHOW_DISAMBIG.search(title)
    if m and not CATEGORY_WORD.search(m.group(1)):  # e.g. "Meredith Grey (Grey's Anatomy)"
        return False
    return True


# --- casing --------------------------------------------------------------------------------------------------
WORD = re.compile(r"[A-Za-z][A-Za-z'’.-]*[A-Za-z]|[A-Za-z]")
ALWAYS = {"i": "I", "tv": "TV", "uk": "UK", "usa": "USA", "u.s.": "U.S.", "dna": "DNA", "nba": "NBA", "nfl": "NFL",
          "nhl": "NHL", "mlb": "MLB", "fifa": "FIFA", "uefa": "UEFA", "nasa": "NASA", "fbi": "FBI", "cia": "CIA",
          "eu": "EU", "un": "UN", "nato": "NATO", "hiv": "HIV", "aids": "AIDS", "pc": "PC", "ps": "PS", "wwe": "WWE",
          "english": "English", "american": "American", "british": "British", "christmas": "Christmas",
          "god": "God", "bible": "Bible", "christian": "Christian", "jewish": "Jewish", "muslim": "Muslim",
          "catholic": "Catholic", "islam": "Islam", "canadian": "Canadian", "australian": "Australian",
          "european": "European", "africa": "Africa", "america": "America", "europe": "Europe", "asia": "Asia",
          "earth": "Earth", "monday": "Monday", "sunday": "Sunday", "january": "January", "december": "December"}
# Multi-word names cased even when the passage does not spell them out.
NAMES = ["United States", "United Kingdom", "New Zealand", "New York", "New Jersey", "New Mexico", "New England",
         "New Orleans", "New Hampshire", "North America", "South America", "North Carolina", "South Carolina",
         "North Dakota", "South Dakota", "West Virginia", "South Africa", "North Korea", "South Korea",
         "Great Britain", "Northern Ireland", "Los Angeles", "San Francisco", "Las Vegas", "Hong Kong",
         "Puerto Rico", "Saudi Arabia", "Sri Lanka", "Costa Rica", "World War", "Super Bowl", "World Cup",
         "Premier League", "Champions League", "Harry Potter", "Star Wars", "Star Trek", "Game of Thrones",
         "Supreme Court", "Middle East", "European Union", "Soviet Union", "Roman Empire", "Middle Ages"]
# Lowercase words that look like proper nouns in passages but should stay lowercase in a question.
STAY = {"a", "an", "the", "and", "or", "of", "in", "on", "at", "to", "for", "is", "are", "was", "were", "do", "does",
        "did", "can", "could", "be", "it", "as", "by", "with", "from", "same", "not", "no", "yes", "all", "one",
        "there", "has", "have", "had", "may", "will", "would", "should", "must", "us", "its", "his", "her", "he",
        "she", "they", "their", "you", "your", "we", "our", "if", "so", "than", "then", "but", "up", "out", "into",
        "over", "under", "about", "after", "before", "between", "during", "without", "within", "man", "men",
        "woman", "women", "king", "queen", "prince", "princess", "lord", "lady", "saint", "st", "mount", "lake",
        "river", "sea", "ocean", "island", "city", "state", "north", "south", "east", "west", "new", "old", "great",
        "little", "big", "black", "white", "red", "blue", "green", "day", "world", "war", "house", "national",
        "united", "states", "kingdom", "republic", "university", "college", "school", "church", "court", "law",
        "act", "party", "league", "cup", "club", "team", "game", "games", "series", "show", "film", "movie", "book",
        "album", "song", "band", "part", "general", "president", "first", "second", "last", "best", "age"}


LEAD = {"the", "a", "an", "in", "on", "at", "it", "this", "his", "her", "its", "after", "before", "during", "when",
        "while", "as", "by", "for", "from", "with", "since", "although", "however", "both", "each", "many", "some"}
RUN = re.compile(r"[A-Z][\w'’.&-]*(?:\s+(?:(?:of|the|and|de|du|la|von|van|da|del)\s+)*[A-Z][\w'’.&-]*)+")


def _prose(passage: str) -> str:
    return re.sub(r"\([^()]*\)", " ", passage)  # drops pronunciations, IPA, and asides


def case_map(passage: str, title: str) -> tuple[list[tuple[str, str]], dict[str, str]]:
    """Capitalized multi-word names (longest first) and single words the passage writes capitalized mid-sentence
    at least twice as often as lowercase; the title counts as a name, its first word as a mid-sentence use."""
    text = _prose(passage)
    title = re.sub(r"\s*\([^)]*\)$", "", title)
    names: set[str] = set()
    upper: Counter[str] = Counter()
    lower: Counter[str] = Counter()
    forms: dict[str, Counter[str]] = {}
    for sent in [*re.split(r"(?<=[.!?])\s+", text), title]:
        for m in RUN.finditer(sent):
            words = m.group(0).split()
            while words and words[0].lower() in LEAD:
                words = words[1:]
            if len(words) >= 2:
                names.add(" ".join(words))
        for i, m in enumerate(WORD.finditer(sent)):
            w, lw = m.group(0), m.group(0).lower()
            if w == lw:
                lower[lw] += 1
            elif i > 0 or sent is title:
                upper[lw] += 1
                forms.setdefault(lw, Counter())[w] += 1
    single = {lw: forms[lw].most_common(1)[0][0] for lw in upper
              if lw not in STAY and upper[lw] >= 2 * lower[lw]}
    names.update(NAMES)
    return sorted(((n.lower(), n) for n in names), key=lambda x: -len(x[0])), single


def restore_case(question: str, passage: str, title: str) -> str:
    names, single = case_map(passage, title)
    q = " ".join(question.split()).rstrip(" ?")
    for low, cased in names:
        q = re.sub(rf"(?<![\w'’]){re.escape(low)}(?![\w'’])", cased, q)

    def fix(m: re.Match) -> str:
        w = m.group(0)
        if w != w.lower():  # already cased by a name
            return w
        return ALWAYS.get(w) or single.get(w) or w

    q = WORD.sub(fix, q)
    q = re.sub(r"\bthe us\b", "the US", q)
    return q[0].upper() + q[1:] + "?"


# --- node hints ----------------------------------------------------------------------------------------------
# Title disambiguators first ("(film)", "(TV series)", "(association football)"), then keyword rules over
# "title | question" in order; the first match wins. world.society is the last resort.
DISAMBIG = [
    (r"film|movie", "world.arts.film"),
    (r"tv series|miniseries|game show|tv program|talk show|sitcom|soap opera|reality", "world.arts.television"),
    (r"song|album|band|singer|rapper|musician|opera", "world.arts.music"),
    (r"novel|book|poem|short story|play\b", "world.arts.books"),
    (r"musical", "world.arts.theatre_dance"),
    (r"video game|\bgame\b", "world.sports.video_games"),
    (r"card game|board game|chess", "world.sports.board_card_games"),
    (r"association football|soccer", "world.sports.soccer"),
    (r"american football|gridiron", "world.sports.american_football"),
    (r"basketball", "world.sports.basketball"),
    (r"baseball", "world.sports.baseball"),
    (r"ice hockey|rugby|cricket|volleyball|lacrosse", "world.sports.other_team_sports"),
    (r"golf|tennis|swimming|athletics|skiing|cycling|gymnastics", "world.sports.individual_sports"),
    (r"boxing|wrestling|mma|martial", "world.sports.combat_sports"),
    (r"racing|formula|nascar", "world.sports.motorsport"),
    (r"actor|actress|comedian|tv personality|presenter|model", "world.arts.celebrities"),
    (r"restaurant|drink|food|dish|beverage|cocktail|chocolate bar", "world.food"),
    (r"dog|cat|horse|bird|fish|genus|plant|animal", "world.nature"),
    (r"ride|roller coaster|theme park|amusement", "world.places.landmarks"),
    (r"company|brand|store|retailer|airline", "world.money.companies_brands"),
    (r"law|legal|criminal|case law|court", "world.society.crime_law"),
    (r"medicine|disease|drug|anatomy", "world.health"),
    (r"mathematics|geometry|statistics", "world.science.mathematics"),
    (r"physics|mechanics", "world.science.physics"),
    (r"chemistry|chemical|element", "world.science.chemistry"),
    (r"biology", "world.science.biology_genetics"),
    (r"constellation|star|planet|astronomy", "world.science.astronomy_space"),
    (r"coin|currency", "world.money.economics"),
    (r"subway|metro|railway|station|airport|highway|road|bridge", "world.places.travel"),
]

RULES = [  # (pattern, node); keep alternatives whole words: a bare "\w*" suffix catches unrelated words
    (
        r"\b(films?|movies?|actors?|actress|oscars?|academy award|box office|pixar|disney movie|"
        r"marvel cinematic|director|hollywood|screenplay|cinema)\b",
        "world.arts.film",
    ),
    (
        r"\b(tv|television|sitcom|netflix|hbo|abc|nbc|cbs|fox network|bbc|itv|channel|broadcast|aired?|air on|"
        r"soap opera|game show|reality show|talk show|cartoon|anime|simpsons|family guy|survivor|big brother|"
        r"idol|x factor|got talent|dancing with the stars|the voice|bachelor\w*)\b",
        "world.arts.television",
    ),
    (
        r"\b(songs?|sing|sings|sang|singer|albums?|bands?|music\w*|rapper|rap|hip hop|guitar|piano|violin|"
        r"drums?|orchestra|symphony|composer|beatles|elvis|grammy|lyrics|billboard|jazz|blues|rock and roll|"
        r"opera|concert|anthem|choir|scales?|key signature|major key|minor key|chords?|ukulele|cello|flute|"
        r"saxophone|trumpet|chord|octave)\b",
        "world.arts.music",
    ),
    (
        r"\b(novel\w*|books?|author|wrote|writer|poem\w*|poet|shakespeare|tolkien|harry potter|literature|"
        r"fiction|chapter|dickens|austen|hemingway|library|publish\w*|comic book|manga)\b",
        "world.arts.books",
    ),
    (
        r"\b(painting|painter|paint|sculpt\w*|artist|art|museum|gallery|picasso|van gogh|da vinci|mona lisa|"
        r"michelangelo|photograph\w*|drawing|tattoo)\b",
        "world.arts.visual_art",
    ),
    (r"\b(broadway|musical|theatre|theater|ballet|dance|dancing|opera house|west end|stage play)\b", "world.arts.theatre_dance"),
    (r"\b(comedy|comedian|stand.up|sketch)\b", "world.arts.comedy"),
    (
        r"\b(fashion industry|fashion designer\w*|fashion\w* brand|clothing|clothes|dress|shirt|jeans|shoe\w*|"
        r"boots?|hat|tie|suit|wear|wore|designer|jewel\w*|diamond ring|makeup|lipstick|perfume|handbag|gucci|"
        r"nike|adidas)\b",
        "world.arts.fashion",
    ),
    (r"\b(architect\w*|building|skyscraper|cathedral|tower|castle|palace|house style|gothic|design)\b", "world.arts.architecture_design"),
    (r"\b(celebrit\w*|famous|kardashian|royal family|prince harry|meghan)\b", "world.arts.celebrities"),
    (r"\b(nba|basketball|dunk|three.pointer|lebron|michael jordan|lakers|celtics|ncaa tournament|march madness)\b", "world.sports.basketball"),
    (
        r"\b(soccer|fifa|world cup|premier league|la liga|uefa|champions league|goalkeeper|offside|"
        r"penalty kick|penalty shoot.?out|mls|football club|fc|manchester|liverpool|arsenal|chelsea|barcelona|"
        r"real madrid|messi|ronaldo|pele)\b",
        "world.sports.soccer",
    ),
    (
        r"\b(nfl|super bowl|quarterback|touchdown|field goal|american football|college football|punt|fumble|"
        r"linebacker|end zone|packers|cowboys|patriots|steelers)\b",
        "world.sports.american_football",
    ),
    (
        r"\b(baseball|mlb|world series|home run|pitcher|inning|yankees|red sox|dodgers|cubs|strike ?out|"
        r"umpire)\b",
        "world.sports.baseball",
    ),
    (
        r"\b(hockey|nhl|stanley cup|rugby|cricket|volleyball|lacrosse|handball|water polo|netball|softball|"
        r"afl|australian rules|hurling|curling)\b",
        "world.sports.other_team_sports",
    ),
    (
        r"\b(golf|pga|the masters|tennis|wimbledon|grand slam|swim\w*|olympic\w*|marathon|track and field|"
        r"gymnast\w*|ski|skis|skiing|skier\w*|snowboard\w*|figure skating|surf|surfing|surfer\w*|cycling|"
        r"tour de france|bowling|darts|snooker|pool table|archery|fencing|rowing|triathlon|decathlon|diving)\b",
        "world.sports.individual_sports",
    ),
    (r"\b(boxing|boxer|ufc|mma|wrestl\w*|wwe|karate|judo|taekwondo|kickboxing|martial arts?)\b", "world.sports.combat_sports"),
    (r"\b(nascar|formula one|formula one|f1|indy|racing|grand prix|le mans|rally)\b", "world.sports.motorsport"),
    (
        r"\b(video games?|xbox|playstation|nintendo|wii|minecraft|fortnite|call of duty|pokemon|zelda|mario|"
        r"sims|grand theft auto|gta|skyrim|elder scrolls|console|gamer|multiplayer|dlc)\b",
        "world.sports.video_games",
    ),
    (
        r"\b(chess|checkmate|poker|blackjack|monopoly|scrabble|board game|card game|deck of cards|bridge game|"
        r"solitaire|dominoes|backgammon|uno|yahtzee|risk game|dice)\b",
        "world.sports.board_card_games",
    ),
    (r"\b(sports?|athlete|referee|stadium|coach|playoffs?|championship|tournament|team)\b", "world.sports"),
    (
        r"\b(beer|wine|whiskey|whisky|vodka|rum|gin|tequila|bourbon|brandy|champagne|cider|liquor|alcohol\w*|"
        r"cocktail|sake|ale|lager|brew\w*)\b",
        "world.food.alcoholic_drinks",
    ),
    (
        r"\b(coffee|tea|soda|juice|coke|coca.cola|pepsi|dr pepper|root beer|sprite|lemonade|milk|drink|drinks|"
        r"energy drink|espresso|latte|water bottle)\b",
        "world.food.nonalcoholic_drinks",
    ),
    (
        r"\b(cake|cookie\w*|bak\w*|dessert|candy|chocolate|pastry|pie|bread|flour|yeast|sugar|ice cream|"
        r"pudding|frosting|dough|muffin|donut|doughnut|brownie)\b",
        "world.food.baking_sweets",
    ),
    (
        r"\b(restaurant\w*|mcdonald\w*|burger king|kfc|starbucks|subway restaurant|wendy'?s|taco bell|"
        r"chick.fil.a|domino'?s|pizza hut|chipotle|fast food|diner|menu)\b",
        "world.food.restaurants",
    ),
    (r"\b(cook\w*|recipe|grill\w*|fry|fried|boil\w*|roast\w*|oven|microwave|marinat\w*|kitchen)\b", "world.food.cooking"),
    (r"\b(cuisine|sushi|pasta|pizza|curry|taco|burrito|dish)\b", "world.food.cuisines"),
    (
        r"\b(food|eat|eating|fruit|vegetable\w*|meat|beef|pork|chicken|egg\w*|cheese|butter|sauce|spice\w*|"
        r"salt|pepper|rice|bean\w*|nuts?|corn|potato\w*|tomato\w*|onion|garlic|oil|vinegar|honey|mushroom\w*|"
        r"seafood|shrimp|lobster|crab|oyster|sausage|bacon|ham|steak|jerky|syrup|jam|jelly|peanut\w*|"
        r"almond\w*|apples?|banana\w*|orange\w*|lemon\w*|berr\w*|grape\w*|melon|avocado|olives?|cereal|"
        r"snack\w*|gelatin|tofu|ketchup|mustard|mayonnaise|salsa|soup|sandwich|hot dog|hamburger)\b",
        "world.food.dishes_ingredients",
    ),
    (r"\b(vitamin\w*|protein|calorie\w*|diet\w*|nutri\w*|carbs?|carbohydrates?|fiber|gluten|cholesterol|sodium)\b", "world.health.nutrition"),
    (r"\b(exercise|workout|muscle\w*|gym|jogging|weight lifting|yoga|push.?ups?|cardio|stretch\w*)\b", "world.health.fitness"),
    (
        r"\b(depress\w*|anxiety|mental|bipolar|schizophren\w*|adhd|autism|ptsd|ocd|therapy|psychiatr\w*|"
        r"phobia)\b",
        "world.health.mental_health",
    ),
    (r"\b(sleep\w*|insomnia|dream\w*|aging|menopause|nap)\b", "world.health.sleep_aging"),
    (
        r"\b(shampoo|soap|toothpaste|deodorant|hair|skin care|shav\w*|nail polish|lotion|sunscreen|"
        r"teeth whitening|hygiene|shower gel)\b",
        "world.health.personal_care",
    ),
    (
        r"\b(cancer|diabetes|disease|virus|flu|infection|syndrome|disorder|allerg\w*|asthma|hepatitis|hiv|"
        r"aids|malaria|measles|herpes|std|tumor|stroke|heart attack|arthritis|contagious|symptom\w*|fever|"
        r"pain)\b",
        "world.health.diseases",
    ),
    (
        r"\b(drug|drugs|medicine|medication|pills?|antibiotic\w*|vaccin\w*|surgery|doctor|nurse|hospital|"
        r"prescription|dose|aspirin|ibuprofen|tylenol|acetaminophen|insulin|steroid\w*|anesthe\w*|transplant|"
        r"x.ray|mri|blood test|over the counter|hydroxyzine|opioid\w*)\b",
        "world.health.medicine",
    ),
    (
        r"\b(human body|blood|bone\w*|heart|lungs?|liver|kidney\w*|stomach|intestine\w*|muscle|nerve\w*|"
        r"organs?|artery|vein\w*|cells?|spine|skull|eye\w*|ears?|tooth|teeth|tongue|pregnan\w*|gland\w*|"
        r"hormone\w*|appendix|tonsils?|gallbladder|pancreas|spleen|bladder|uterus|rib\w*|joint\w*|excretory|"
        r"immune|brain|spinal|neurons?|nervous system|cerebellum|cerebral|limbic|membrane|epithelium|nasal|neck|"
        r"umbilical|amniotic|placenta|nipples?|areola|testicles?|glucose|abdomen|pelvis|skin|wrist|ankle|knee)\b",
        "world.health.human_body",
    ),
    (
        r"\b(dogs?|puppy|puppies|cats?|kitten\w*|breed\w*|pitbull|poodle|labrador|retriever|terrier|"
        r"shepherd dog|hamster|guinea pig|goldfish|pet|pets)\b",
        "world.nature.pets_breeds",
    ),
    (
        r"\b(birds?|eagle|hawk|owl|parrot|penguin\w*|blackbirds?|bluebirds?|beaks?|feathers?|ostrich|chicken\w*|duck\w*|goose|swan|crow|raven|pigeon|"
        r"dove|robin|sparrow|flamingo|peacock|turkey vulture|vulture|hummingbird|falcon|emu|kiwi bird)\b",
        "world.nature.birds",
    ),
    (
        r"\b(shark\w*|whale\w*|dolphin\w*|fish|octopus|squid|jellyfish|seal\w*|sea lion|walrus|coral|starfish|"
        r"stingray|eel|salmon|tuna|trout|reef|orca|manatee)\b",
        "world.nature.sea_life",
    ),
    (
        r"\b(snake\w*|lizard\w*|reptile\w*|turtle\w*|tortoise\w*|crocodile\w*|alligator\w*|frog\w*|toad\w*|"
        r"insect\w*|spider\w*|bee|bees|wasp\w*|ant|ants|mosquito\w*|butterfl\w*|moths?|beetle\w*|tick|ticks|"
        r"scorpion\w*|worm\w*|snail\w*|bug|bugs|cockroach\w*|flies|termite\w*|gecko|iguana|chameleon|"
        r"salamander|amphibian\w*|venom\w*)\b",
        "world.nature.reptiles_insects",
    ),
    (
        r"\b(mammal\w*|lions?|tigers?|bears?|wolf|wolves|fox|foxes|deer|elk|moose|horses?|cows?|cattle|pigs?|"
        r"piglets?|sheep|goat\w*|monkey\w*|apes?|gorilla\w*|chimp\w*|elephant\w*|giraffe\w*|zebra\w*|rhino\w*|"
        r"hippo\w*|kangaroo\w*|koala\w*|panda\w*|rabbit\w*|mouse|mice|rat|rats|squirrel\w*|bat|bats|badger\w*|"
        r"wolverine\w*|raccoon\w*|skunk\w*|otter\w*|beaver\w*|camel\w*|llama\w*|donkey\w*|mule\w*|bison|"
        r"buffalo|cheetah\w*|leopard\w*|jaguar\w*|hyena\w*|lynx|bobcat\w*|cougar\w*|possum|opossum|platypus|"
        r"hedgehog|animal\w*|species|primate\w*|rodent\w*|marsupial\w*)\b",
        "world.nature.mammals",
    ),
    (
        r"\b(plants?|trees?|flowers?|rose\w*|tulip\w*|grass|moss|fern\w*|cactus|cacti|mushroom\w*|fungus|"
        r"fungi|mold|seeds?|leaf|leaves|oak|pine|maple|palm tree|bamboo|ivy|poison ivy|weeds?|algae|shrub\w*|"
        r"vines?|herbs?|photosynthesis|pollen)\b",
        "world.nature.plants_fungi",
    ),
    (
        r"\b(weather|climate|rain|rainfall|raining|rainy|snow\w*|hurricane\w*|tornado\w*|storm\w*|thunder\w*|"
        r"lightning|hail|winds?|windy|temperature|monsoon|drought|flood\w*|fog|humidity|clouds|cloudy|"
        r"global warming|el ni[nñ]o|season of the year|winter|summer|spring equinox|solstice|equinox)\b",
        "world.nature.weather_climate",
    ),
    (
        r"\b(rocks|igneous|metamorphic|mineral\w*|volcano\w*|earthquake\w*|crystal\w*|diamond\w*|gold|silver|"
        r"granite|marble|quartz|fossil\w*|lava|magma|tectonic|sediment\w*|geolog\w*|gems?|gemstones?|ruby|"
        r"sapphire|emerald|coal|limestone|sandstone|erosion|continental drift)\b",
        "world.nature.geology",
    ),
    (
        r"\b(extinct\w*|endangered|conservation|ecosystem\w*|habitat\w*|national park|wildlife|rainforest|"
        r"deforestation|pollution|recycl\w*|invasive)\b",
        "world.nature.ecosystems_conservation",
    ),
    (
        r"\b(planet\w*|moon|sun|stars|galaxy|galaxies|universe|solar system|mars|venus|jupiter|saturn|mercury|"
        r"neptune|uranus|pluto|comet\w*|asteroid\w*|meteor\w*|black hole|nasa|astronaut\w*|orbit\w*|telescope|"
        r"space station|constellation\w*|eclipse|light year|big bang|milky way|space)\b",
        "world.science.astronomy_space",
    ),
    (
        r"\b(dna|genes?|genetic\w*|genom\w*|genetic\w*|chromosome\w*|evolution|evolve\w*|bacteria\w*|cell|"
        r"protein|enzyme\w*|organism\w*|biolog\w*|mitosis|meiosis|rna|mutation\w*|inherit\w*|clone\w*|"
        r"virus\w*)\b",
        "world.science.biology_genetics",
    ),
    (
        r"\b(chemical\w*|chemistry|elements?|atom\w*|molecule\w*|acid\w*|ph|compound\w*|periodic table|oxygen|"
        r"hydrogen|carbon|nitrogen|helium|sodium|chlorine|metals?|metallic|iron|copper|aluminum|aluminium|"
        r"steel|alloy\w*|oxid\w*|react\w*|salt water|ethanol|methane|plastic\w*|rubber|glass|polymer\w*|"
        r"isotope\w*|radioactive|uranium|mercury poisoning)\b",
        "world.science.chemistry",
    ),
    (
        r"\b(physics|gravity|energy|velocity|speed of|mass|weight|momentum|friction|magnet\w*|electric\w*|"
        r"voltage|circuit\w*|sound|wave\w*|frequency|radiation|heat|temperature|thermodynamic\w*|quantum|"
        r"relativity|newton|einstein|nuclear|atomic|laser|pressure|vacuum|density|boiling point|freez\w*|"
        r"melt\w*|torque|engine|horsepower|kinetic|potential energy|joule|watt|mechanic\w*|lens|lenses|optic\w*|reflection|refraction|shadows?|mirror\w*|prism|real image|focal)\b",
        "world.science.physics",
    ),
    (
        r"\b(maths?|mathemat\w*|number|numbers|prime numbers?|equation|algebra|geometry|triangle\w*|square|circle|"
        r"angle\w*|polygon\w*|odd numbers?|integer\w*|fraction\w*|decimal|infinity|probability|statistic\w*|"
        r"calculus|derivative|matrix|divisible|parallel\w*|rectangle|rhombus|trapezoid|parallelogram|hexagon|"
        r"pentagon|symmetr\w*|irrational|rational|pi|addition|subtraction|multiplication|division|order of operations|"
        r"units? of measure\w*|metric|imperial units?|litres?|liters?|quarts?|gallons?|inch|inches|kilogram\w*)\b",
        "world.science.mathematics",
    ),
    (
        r"\b(psycholog\w*|memory|conscious\w*|emotion\w*|personality|iq|intelligence|behavior\w*|cognitive|"
        r"placebo|hypnosis|deja vu)\b",
        "world.science.psychology_neuroscience",
    ),
    (
        r"\b(ghost\w*|ufo\w*|alien\w*|bigfoot|loch ness|bermuda triangle|paranormal|psychic\w*|haunted|"
        r"conspiracy|atlantis|area 51|zodiac|astrology|horoscope)\b",
        "world.science.fringe_mysteries",
    ),
    (
        r"\b(scientist\w*|discover\w*|invent|invented|invention\w*|inventor\w*|nobel prize|experiment\w*|"
        r"theory|darwin|edison|tesla|curie|galileo|scien\w*)\b",
        "world.science.scientists_discoveries",
    ),
    (r"\b(ai|artificial intelligence|robot\w*|machine learning|neural network|siri|alexa|chatbot)\b", "world.tech.ai"),
    (
        r"\b(facebook|instagram|twitter|snapchat|tiktok|youtube|reddit|linkedin|social media|tweet\w*|hashtag|"
        r"whatsapp|pinterest|tumblr|vine app)\b",
        "world.tech.social_media",
    ),
    (
        r"\b(internet|website|web|online|email|e.mail|google|wifi|wi.fi|browser|url|domain|ip address|"
        r"download\w*|stream\w*|amazon prime|netflix account|hulu|spotify|ebay|paypal|wikipedia)\b",
        "world.tech.internet_web",
    ),
    (
        r"\b(software|program\w*|code|coding|java|python|javascript|html|linux|windows|operating system|app|"
        r"apps|android|ios|microsoft office|excel|word document|database|algorithm\w*|compiler|api|sql|c\+\+|"
        r"virus scan|antivirus|firmware|bitcoin|blockchain|encrypt\w*)\b",
        "world.tech.software_programming",
    ),
    (
        r"\b(computer\w*|laptop\w*|cpu|processor\w*|gpu|graphics card|ram|hard drive|ssd|usb|motherboard|"
        r"keyboard|mouse pad|monitor|printer|macbook|pc|chips?|microchips?|hdmi|bluetooth|intel|amd|nvidia)\b",
        "world.tech.computers_hardware",
    ),
    (
        r"\b(phone\w*|iphone\w*|smartphone\w*|ipad\w*|tablet\w*|camera\w*|headphone\w*|tv set|remote control|"
        r"smartwatch|fitbit|kindle|gps|drone\w*|gadget\w*|battery|batteries|charger)\b",
        "world.tech.gadgets",
    ),
    (
        r"\b(cell tower|computer networks?|mobile networks?|cellular networks?|telecom\w*|verizon|at&t|"
        r"t.mobile|sprint|landline|4g|5g|lte|broadband|satellite|radio|fiber optic|sim card|roaming)\b",
        "world.tech.telecom_networks",
    ),
    (
        r"\b(cars?|trucks?|vehicle\w*|automobile\w*|motorcycle\w*|bicycle\w*|bike\w*|driv\w*|engine|tires?|"
        r"tyres?|transmission|mph|toyota|honda|ford|chevrolet|chevy|bmw|mercedes|audi|volkswagen|jeep|dodge|"
        r"ferrari|porsche|lamborghini|nissan|hyundai|kia|subaru|mazda|tesla model|electric car|airplane\w*|"
        r"planes?|aircraft|jets?|boeing|airbus|helicopter\w*|ships?|boat\w*|submarine\w*|trains?|"
        r"locomotive\w*|tank|license plate|seat belt|airbag\w*|diesel|gasoline|petrol)\b",
        "world.tech.vehicles",
    ),
    (
        r"\b(apple inc|microsoft|amazon|google inc|samsung|sony|ibm|oracle|dell|hp|facebook inc|uber|lyft|"
        r"airbnb|tech company|silicon valley)\b",
        "world.tech.companies",
    ),
    (
        r"\b(bridge\w*|dam|tunnel\w*|canal\w*|engineer\w*|invention\w*|machine\w*|motor\w*|pump\w*|turbine\w*|"
        r"generator\w*|solar panel\w*|wind turbine\w*|nuclear power|power plant|electricity|wire\w*|tool\w*|"
        r"locks?|clock\w*|elevator\w*|escalator\w*|welding|3d print\w*)\b",
        "world.tech.engineering_inventions",
    ),
    (
        r"\b(world war|ww1|ww2|wwi|wwii|civil war|revolutionary war|vietnam war|korean war|war of|battle\w*|"
        r"army|armies|navy|soldier\w*|military|troops|invasion|d.day|pearl harbor|nazi\w*|holocaust|hitler|"
        r"napoleon\w*|cold war|wars?)\b",
        "world.history.wars_battles",
    ),
    (
        r"\b(ancient|egypt\w* pharaoh|pharaoh\w*|pyramid\w*|roman empire|rome|romans|greek\w*|greece|"
        r"sparta\w*|mesopotamia|babylon\w*|persian empire|aztec\w*|maya\w*|inca\w*|caesar|cleopatra|"
        r"gladiator\w*|bronze age|iron age|stone age|prehistoric|dinosaur\w*|neanderthal\w*)\b",
        "world.history.ancient",
    ),
    (
        r"\b(medieval|middle ages|knight\w*|viking\w*|crusade\w*|feudal|castle\w*|plague|black death|"
        r"byzantine|ottoman\w*|samurai|shogun\w*|genghis|mongol\w*)\b",
        "world.history.medieval",
    ),
    (
        r"\b(renaissance|colonial\w*|colon(y|ies)|pilgrims?|mayflower|columbus|conquistador\w*|slave\w*|"
        r"slavery|founding fathers?|declaration of independence|american revolution|french revolution|"
        r"tudor\w*|elizabethan|king henry|queen elizabeth i)\b",
        "world.history.early_modern",
    ),
    (
        r"\b(industrial revolution|victorian|titanic|prohibition|great depression|suffrage|lincoln|wild west|"
        r"gold rush)\b",
        "world.history.modern",
    ),
    (
        r"\b(civil rights|moon landing|apollo|berlin wall|soviet\w*|ussr|kennedy|martin luther king|"
        r"beatlemania|space race|sixties|woodstock)\b",
        "world.history.postwar",
    ),
    (
        r"\b(histor\w*|king|queen|emperor|empire|dynasty|monarch\w*|royal\w*|pope\w*|reign\w*|throne|century|"
        r"era)\b",
        "world.history.figures",
    ),
    (
        r"\b(stocks?|invest\w*|dividend\w*|mutual fund\w*|401k|ira|roth|hedge fund\w*|stock market|nasdaq|"
        r"dow jones|s&p|index fund\w*|etf\w*|broker\w*|portfolio)\b",
        "world.money.investing",
    ),
    (
        r"\b(credit card\w*|debit card\w*|credit score|bank account\w*|checking account|savings account|"
        r"loan\w*|debt|mortgage\w*|interest rate|tax|taxes|taxed|taxation|taxable|irs|refund|social security|"
        r"pension|budget\w*|insurance|medicare|medicaid|paycheck|salary|wage\w*|atm|cheque|overdraft|"
        r"bankrupt\w*|w.?2|w.?4|tipping)\b",
        "world.money.personal_finance",
    ),
    (
        r"\b(real estate|property|landlord|tenant\w*|rent|rents|rental|rented|renting|lease\w*|house price|"
        r"home owner\w*|homeowner\w*|condo\w*|deed|escrow|realtor)\b",
        "world.money.real_estate",
    ),
    (
        r"\b(job\w*|career\w*|employ\w*|hire|hiring|fired|resign\w*|overtime|work visa|workplace|minimum wage|"
        r"profession\w*|occupation|lawyer\w*|nurse practitioner|teacher\w*|firefighter\w*|police officer\w*)\b",
        "world.money.careers",
    ),
    (r"\b(startup\w*|entrepreneur\w*|small business|llc|incorporat\w*|sole proprietor\w*)\b", "world.money.entrepreneurship"),
    (
        r"\b(company|companies|brands?|branded|corporation|inc|owned by|subsidiary|manufactur\w*|walmart|"
        r"target store|costco|coca.cola company|nestle|kraft|unilever|procter|ikea|lego|toys r us|sears|kmart|"
        r"macy'?s|retailer|store\w*|shop\w*|products?|trademark\w*|logo)\b",
        "world.money.companies_brands",
    ),
    (
        r"\b(econom\w*|inflation|recession|gdp|currency|currencies|dollar\w*|euros?|eurozone|pound sterling|"
        r"yen|peso\w*|money|coins?|penny|pennies|nickel|dime|quarter dollar|bank\w*|federal reserve|trade|"
        r"tariff\w*|supply and demand|market|price\w*|capitalism|socialism|communism|costs?|profit\w*|revenue|accounting|depreciation)\b",
        "world.money.economics",
    ),
    (
        r"\b(language\w*|speak|spoken|dialect\w*|word\w*|spell\w*|grammar|mandarin|cantonese|latin|farsi|"
        r"hebrew|greek language|gaelic|irish language|swahili|sign language|alphabet|letter\w*|"
        r"vowel\w*|pronoun\w*|noun\w*|verb\w*|adjective\w*|plural|synonym\w*|translat\w*|accent\w*|slang|"
        r"idiom\w*)\b",
        "world.society.languages",
    ),
    (
        r"\b(school\w*|college\w*|universit\w*|degree\w*|student\w*|teacher\w*|education\w*|exam\w*|act test|"
        r"gpa|ivy league|harvard|oxford|cambridge|yale|stanford|graduat\w*|diploma|kindergarten|high school|"
        r"homeschool\w*|tuition|scholarship\w*|bachelor'?s|master'?s|phd|doctorate)\b",
        "world.society.education",
    ),
    (
        r"\b(christmas|easter|halloween|thanksgiving|hanukkah|diwali|ramadan|new year\w*|valentine\w*|"
        r"holiday\w*|tradition\w*|festival\w*|birthday\w*|wedding\w*|funeral\w*|customs?|celebrat\w*|santa|"
        r"tooth fairy|easter bunny|st patrick|mardi gras|cinco de mayo|independence day|fourth of july|"
        r"memorial day|labor day|boxing day|groundhog)\b",
        "world.society.holidays_traditions",
    ),
    (
        r"\b(myth\w*|legend\w*|folklore|folk tale|fairy tale\w*|dragon\w*|unicorn\w*|zeus|thor|odin|hercules|"
        r"greek god\w*|norse|mermaid\w*|vampire\w*|werewolf|werewolves|goblin\w*|elf|elves|trolls?|fairy|"
        r"fairies|king arthur|robin hood|excalibur|holy grail)\b",
        "world.society.mythology_folklore",
    ),
    (
        r"\b(god|gods|religio\w*|church\w*|bible|biblical|jesus|christ|christian\w*|catholic\w*|protestant\w*|"
        r"baptist\w*|lutheran\w*|methodist\w*|mormon\w*|lds|jehovah\w*|orthodox|islam\w*|muslim\w*|quran|"
        r"koran|mosque\w*|jews?|jewish|juda\w*|torah|synagogue\w*|rabbis?|hindu\w*|buddhis\w*|buddha|sikh\w*|"
        r"pope|priest\w*|angels?|heaven|hell|sin|sins|prayer\w*|pray|baptism|communion|monks?|nuns?|"
        r"apostle\w*|prophet\w*|moses|abraham|noah|adam and eve|genesis|gospel\w*|testament|scripture\w*|lent|"
        r"sabbath|kosher|halal|atheis\w*|agnostic)\b",
        "world.society.world_religions",
    ),
    (
        r"\b(philosoph\w*|plato|aristotle|socrates|kant|nietzsche|descartes|confucius|ethics|existential\w*|"
        r"stoic\w*|utilitarian\w*)\b",
        "world.society.philosophy_thinkers",
    ),
    (
        r"\b(legal|illegal|law|laws|lawful|court\w*|judge\w*|jury|juries|crime\w*|criminal\w*|felony|felonies|"
        r"misdemeanor\w*|arrest\w*|police|prison\w*|jail\w*|trial|sue|sued|lawsuit\w*|attorney\w*|lawyer\w*|"
        r"constitution\w*|amendment\w*|rights|miranda|warrant\w*|parole|probation|bail|custody|divorce\w*|"
        r"marriage license|drinking age|age of consent|license|licence|permit\w*|citizenship|citizen\w*|"
        r"dual citizen\w*|copyright\w*|patent\w*|contract\w*|tort\w*|liable|liability|"
        r"good samaritan|self.defense|dui|dwi|speeding|traffic\w*|supreme court|federal court|statute\w*)\b",
        "world.society.crime_law",
    ),
    (
        r"\b(news\w*|newspaper\w*|journalis\w*|magazine\w*|media|reporter\w*|cnn|fox news|msnbc|"
        r"new york times|washington post|pulitzer)\b",
        "world.society.media_news",
    ),
    (
        r"\b(president\w*|prime minister\w*|congress\w*|senat\w*|parliament\w*|government\w*|governor\w*|"
        r"mayor\w*|election\w*|elected|vote\w*|voting|political|politic\w*|democra\w*|monarchy|"
        r"constitutional|cabinet|legislat\w*|federal|state government|electoral|veto\w*|impeach\w*|"
        r"united nations|nato|european union|eu|un|embassy|ambassador\w*|treaty|treaties|commonwealth|"
        r"territor(y|ies)|sovereign\w*|independence|secretary of state|supreme leader|dictator\w*)\b",
        "world.society.politics_government",
    ),
    (
        r"\b(racial|ethnic\w*|gender|transgender|lgbt\w*|census|population|demographic\w*|nationality|"
        r"native american\w*|indigenous|aboriginal\w*|immigrant\w*|minority|minorities|millennial\w*|"
        r"baby boomer\w*|left.handed|twins?)\b",
        "world.society.identity_demographics",
    ),
    (
        r"\b(continent\w*|europe|asia|africa|antarctica|oceania|north america|south america|latin america|"
        r"middle east|scandinavia\w*|caribbean|balkan\w*|siberia|sahara|mediterranean|arctic|antarctic|"
        r"hemisphere|equator|british isles|great britain|iberia\w*|pacific islands?|polynesia\w*)\b",
        "world.places.continents_regions",
    ),
    (
        r"\b(river\w*|lakes?|mountain\w*|mount|ocean\w*|seas?|island\w*|desert\w*|canyon\w*|valley\w*|"
        r"waterfall\w*|glacier\w*|peninsula\w*|bay|gulf|strait|cape|coasts?|coastal|coastline|beach\w*|forest\w*|jungle|"
        r"plateau|volcano|caves?|cliff\w*|swamp\w*|delta|tributar\w*|everest|amazon river|nile|mississippi|"
        r"great lakes|rockies|rocky mountains|alps|himalaya\w*|time zone\w*|latitude|longitude|borders?|bordering|bordered|"
        r"geograph\w*|landlocked|trench|mariana|deepest|highest point)\b",
        "world.places.physical_geography",
    ),
    (
        r"\b(statue of liberty|eiffel tower|great wall|taj mahal|stonehenge|colosseum|big ben|golden gate|"
        r"mount rushmore|grand canyon|niagara falls|disney ?world|disneyland|universal studios|theme park\w*|"
        r"roller coaster\w*|landmark\w*|monument\w*|memorial|museum|zoo|palace|castle|white house|"
        r"empire state|times square|central park|hollywood sign|wonder of the world|world heritage)\b",
        "world.places.landmarks",
    ),
    (
        r"\b(travel\w*|tourist\w*|tourism|airport\w*|flight\w*|airline\w*|passports?|visas?|schengen|hotel\w*|cruise\w*|"
        r"vacation\w*|train station|railway|subway|metro|underground|tube|oyster card|highway\w*|"
        r"interstate\w*|toll\w*|road\w*|route\w*|bus|amtrak|ferry|ferries|border crossing)\b",
        "world.places.travel",
    ),
    (
        r"\b(city|cities|town\w*|new york|london|paris|tokyo|los angeles|chicago|san francisco|las vegas|"
        r"boston|seattle|miami|toronto|vancouver|montreal|sydney|melbourne|berlin|rome|madrid|barcelona|"
        r"dublin|edinburgh|hong kong|singapore|dubai|moscow|beijing|shanghai|mumbai|delhi|washington dc|"
        r"district of columbia|vatican|neighborhood|borough|county|counties|suburb\w*|village\w*|"
        r"municipal\w*)\b",
        "world.places.cities",
    ),
    (
        r"\b(countr(y|ies)|province\w*|england|scotland|wales|ireland|northern ireland|uk|united kingdom|"
        r"britain|france|germany|spain|italy|portugal|netherlands|holland|belgium|switzerland|austria|sweden|"
        r"norway|denmark|finland|iceland|poland|russia|ukraine|greece|turkey|egypt|israel|iran|iraq|"
        r"afghanistan|pakistan|india|china|japan|korea|vietnam|thailand|philippines|indonesia|malaysia|"
        r"australia|new zealand|canada|mexico|brazil|argentina|chile|peru|colombia|cuba|jamaica|puerto rico|"
        r"haiti|south africa|nigeria|kenya|ethiopia|morocco|saudi arabia|alaska|hawaii|texas|california|"
        r"florida|new jersey|ohio|georgia|virginia|carolina|michigan|pennsylvania|illinois|massachusetts|"
        r"arizona|nevada|utah|colorado|oregon|washington state|canadian|british|australian|mexican|irish|"
        r"scottish|french|german|italian|spanish|japanese|chinese|indian|russian)\b",
        "world.places.countries",
    ),
]
DISAMBIG_RE = [(re.compile(p, re.I), n) for p, n in DISAMBIG]
RULES_RE = [(re.compile(p, re.I), n) for p, n in RULES]


DEFINITION = re.compile(r"\b(?:is|was|are|were)\s+(?:a|an|the|one of the)\s+([^.;]{0,60})", re.I)
# Named-place rules are scored on the title and question only: passages mention countries and cities in passing.
NAMED_PLACES = {"world.places.countries", "world.places.cities", "world.places.continents_regions"}
FIELD = re.compile(r"^In ([a-z][a-z ,-]{2,40}),", re.I)


def node_hint(question: str, title: str, passage: str = "") -> str:
    """The title's disambiguator if it names a category; otherwise every keyword rule scores its matches in the
    passage's definitional phrase and field ("In music, ..."; weight 4), the title (3), the question (2), and the
    first sentence (1). Highest total wins, ties go to the earlier rule; world.society if nothing matches."""
    m = re.search(r"\(([^)]*)\)\s*$", title)
    if m:
        for rx, node in DISAMBIG_RE:
            if rx.search(m.group(1)):
                return node
    first = re.split(r"(?<=[.!?])\s+", _prose(passage).strip(), maxsplit=1)[0][:400]
    d, f = DEFINITION.search(first), FIELD.search(first)
    texts = [
        (4, " | ".join(x.group(1) for x in (d, f) if x)),
        (3, re.sub(r"\s*\([^)]*\)$", "", title)),
        (2, question),
        (1, first),
    ]
    scores: Counter[str] = Counter()
    order: dict[str, int] = {}
    for i, (rx, node) in enumerate(RULES_RE):
        order.setdefault(node, i)
        for w, t in texts:
            if w in (4, 1) and node in NAMED_PLACES:
                continue
            if t and rx.search(t):
                scores[node] += w
    if not scores:
        return "world.society"
    return min(scores, key=lambda n: (-scores[n], order[n]))


def fetch(raw_dir: Path) -> None:
    for name, url in FILES.items():
        out = raw_dir / name
        if out.exists():
            continue
        r = httpx.get(url, follow_redirects=True, timeout=300)
        r.raise_for_status()
        out.write_bytes(r.content)


def _pool(raw_dir: Path) -> list[dict]:
    pool, seen = [], set()
    for split in ("train", "validation"):
        df = pl.read_parquet(raw_dir / f"{split}.parquet").with_row_index("row")
        titles = pl.read_parquet(raw_dir / f"titles_{split}.parquet")
        if df["question"].to_list() != titles["question"].to_list():
            raise ValueError(f"boolq: {split} titles are not aligned with google/boolq")
        for (row, q, a, passage), title in zip(df.select("row", "question", "answer", "passage").iter_rows(),
                                               titles["title"]):
            q = " ".join(q.split()).strip(" ?").lower()
            if q in seen or not keep(q, title, passage):
                continue
            seen.add(q)
            pool.append({"id": f"{split}:{row}", "q": q, "answer": bool(a), "passage": passage, "title": title})
    return pool


def normalize(raw_dir: Path) -> Iterator[Question]:
    picked = top_up([], _pool(raw_dir), TARGET, lambda x: x["id"], SALT)
    for it in sorted(picked, key=lambda x: (x["id"].split(":")[0], int(x["id"].split(":")[1]))):
        text = restore_case(it["q"], it["passage"], it["title"])
        flags = []
        if POLITICAL.search(it["q"]):
            flags.append("political")
        if SENSITIVE.search(it["q"]):
            flags.append("sensitive")
        meta = {"wikipedia_title": it["title"], "query": it["q"]}
        if flags:
            meta["flags"] = flags
        yield Question(
            text=text,
            primitive="noul",
            hemisphere="world",
            kind="factual",
            origin="dataset",
            source=NAME,
            node_hint=node_hint(it["q"], it["title"], it["passage"]),
            source_item_id=it["id"],
            license=LICENSE,
            truth=it["answer"],
            meta=meta,
        )
