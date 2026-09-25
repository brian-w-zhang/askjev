"""Young People Survey (Sabo 2013): Slovak 15-30 year olds rate music genres, movie genres, interests, fears,
habits, and personality statements on 1-5 scales. One Score (or Choice) per item with the respondents' shares,
plus within-block pairwise Choices ("Which would you rather listen to: jazz or metal?") whose human split is the
share of respondents who rated one item higher than the other (ties excluded)."""

from __future__ import annotations

import csv
import itertools
from pathlib import Path
from typing import Iterator

import httpx

from askjev.model import HumanDist, Question
from askjev.sampling import env_int, hash_order

NAME = "young_people_survey"
# Public GitHub copy of the Kaggle files (responses.csv 1,010 x 150, columns.csv); byte-identical copies exist in
# several other repos (e.g. sunitdev/young-people-survey dataset/responses.csv, same 452,332 bytes).
BASE = "https://raw.githubusercontent.com/FHU/young-people-survey/master/"
FILES = ("responses.csv", "columns.csv")
LICENSE = "CC0 1.0 (Young People Survey, Miroslav Sabo, Kaggle 2016); GitHub mirror FHU/young-people-survey"
POP = "Slovak young people aged 15-30 (2013 survey)"
SRC = "Young People Survey (Sabo 2013, Kaggle): share of respondents at each 1-5 rating"
PAIR_SRC = "Young People Survey (Sabo 2013, Kaggle): among respondents who rated the two items differently, share rating each higher"
TARGET_PAIRS = env_int("TARGET_YOUNG_PEOPLE_SURVEY_PAIRS", 5000)  # all within-block pairs (732) by default
SALT = "young_people_survey.v1"

# --- item phrasing: column -> (key, phrase) --------------------------------------------------------------------
MUSIC = {
    "Dance": ("dance_disco_funk", "dance, disco, and funk music"),
    "Folk": ("folk", "folk music"),
    "Country": ("country", "country music"),
    "Classical music": ("classical", "classical music"),
    "Musical": ("musicals", "songs from musicals"),
    "Pop": ("pop", "pop music"),
    "Rock": ("rock", "rock music"),
    "Metal or Hardrock": ("metal_hard_rock", "metal and hard rock"),
    "Punk": ("punk", "punk"),
    "Hiphop, Rap": ("hip_hop_rap", "hip hop and rap"),
    "Reggae, Ska": ("reggae_ska", "reggae and ska"),
    "Swing, Jazz": ("swing_jazz", "swing and jazz"),
    "Rock n roll": ("rock_n_roll", "rock 'n' roll"),
    "Alternative": ("alternative", "alternative music"),
    "Latino": ("latin", "Latin music"),
    "Techno, Trance": ("techno_trance", "techno and trance"),
    "Opera": ("opera", "opera"),
}
MOVIES = {
    "Horror": ("horror", "horror movies"),
    "Thriller": ("thrillers", "thrillers"),
    "Comedy": ("comedies", "comedies"),
    "Romantic": ("romantic_movies", "romantic movies"),
    "Sci-fi": ("sci_fi", "sci-fi movies"),
    "War": ("war_movies", "war movies"),
    "Fantasy/Fairy tales": ("fantasy_fairy_tales", "fantasy and fairy-tale movies"),
    "Animated": ("animated", "animated movies and cartoons"),
    "Documentary": ("documentaries", "documentaries"),
    "Western": ("westerns", "westerns"),
    "Action": ("action", "action movies"),
}
# interest -> (key, phrase, node)
LEISURE, CAREER, PETS = "self.lifestyle.leisure_hobbies", "self.personality.interests", "self.lifestyle.pets"
INTERESTS = {
    "History": ("history", "history", CAREER),
    "Psychology": ("psychology", "psychology", CAREER),
    "Politics": ("politics", "politics", CAREER),
    "Mathematics": ("mathematics", "mathematics", CAREER),
    "Physics": ("physics", "physics", CAREER),
    "Internet": ("the_internet", "the internet", "self.lifestyle.screens_media"),
    "PC": ("computers", "computers (software and hardware)", CAREER),
    "Economy Management": ("economics_management", "economics and management", CAREER),
    "Biology": ("biology", "biology", CAREER),
    "Chemistry": ("chemistry", "chemistry", CAREER),
    "Reading": ("reading_poetry", "reading poetry", LEISURE),
    "Geography": ("geography", "geography", CAREER),
    "Foreign languages": ("foreign_languages", "foreign languages", CAREER),
    "Medicine": ("medicine", "medicine", CAREER),
    "Law": ("law", "law", CAREER),
    "Cars": ("cars", "cars", LEISURE),
    "Art exhibitions": ("art", "art", LEISURE),
    "Religion": ("religion", "religion", CAREER),
    "Countryside, outdoors": ("outdoor_activities", "outdoor activities", LEISURE),
    "Dancing": ("dancing", "dancing", LEISURE),
    "Musical instruments": ("musical_instruments", "playing musical instruments", LEISURE),
    "Writing": ("writing_poetry", "writing poetry", LEISURE),
    "Passive sport": ("recreational_sport", "sport and leisure activities done for fun", LEISURE),
    "Active sport": ("competitive_sport", "playing sport at a competitive level", LEISURE),
    "Gardening": ("gardening", "gardening", LEISURE),
    "Celebrities": ("celebrity_lifestyle", "celebrity lifestyle", "self.lifestyle.screens_media"),
    "Shopping": ("shopping", "shopping", LEISURE),
    "Science and technology": ("science_technology", "science and technology", CAREER),
    "Theatre": ("theatre", "theatre", LEISURE),
    "Fun with friends": ("socializing", "socializing with friends", LEISURE),
    "Adrenaline sports": ("adrenaline_sports", "adrenaline sports", LEISURE),
    "Pets": ("pets", "pets", PETS),
}
FEARS = {
    "Flying": ("flying", "flying"),
    "Storm": ("thunder_lightning", "thunder and lightning"),
    "Darkness": ("darkness", "darkness"),
    "Heights": ("heights", "heights"),
    "Spiders": ("spiders", "spiders"),
    "Snakes": ("snakes", "snakes"),
    "Rats": ("rats_mice", "rats and mice"),
    "Ageing": ("ageing", "growing old"),
    "Dangerous dogs": ("dangerous_dogs", "dangerous dogs"),
    "Fear of public speaking": ("public_speaking", "public speaking"),
}
FEAR_NODE = "self.personality.big_five.neuroticism.fear_worry"

N = "self.personality.big_five.neuroticism."
C = "self.personality.big_five.conscientiousness."
A = "self.personality.big_five.agreeableness."
E = "self.personality.big_five.extraversion."
EM = "self.personality.emotions_stress."
L = "self.lifestyle."
# Likert statements (Strongly disagree 1..5 Strongly agree): column -> (statement, node, kind). Statement text
# follows columns.csv, with its translation typos fixed.
STATEMENTS = {
    "Music": ("I enjoy listening to music.", L + "leisure_hobbies", "taste"),
    "Movies": ("I really enjoy watching movies.", L + "screens_media", "taste"),
    "Healthy eating": ("I live a very healthy lifestyle.", L + "habits_routines", "personality"),
    "Daily events": ("I take notice of what goes on around me.", EM + "mindfulness_awareness", "personality"),
    "Prioritising workload": ("I try to do tasks as soon as possible and not leave them until the last minute.", C + "drive_self_discipline", "personality"),
    "Writing notes": ("I always make a list so I don't forget anything.", C + "order_caution", "personality"),
    "Workaholism": ("I often study or work even in my spare time.", L + "work_study_life", "personality"),
    "Thinking ahead": ("I look at things from all different angles before I go ahead.", C + "order_caution", "personality"),
    "Final judgement": ("I believe that bad people will suffer one day and good people will be rewarded.", "self.mind.luck_fate.luck_and_fate", "values"),
    "Reliability": ("I am reliable at work and always complete all tasks given to me.", C + "drive_self_discipline", "personality"),
    "Keeping promises": ("I always keep my promises.", "self.values.honesty_trust", "personality"),
    "Loss of interest": ("I can fall for someone very quickly and then completely lose interest.", "self.love.romance_partnership.relationship_choices", "personality"),
    "Friends versus money": ("I would rather have lots of friends than lots of money.", "self.values.life_values.personal_priorities", "values"),
    "Funniness": ("I always try to be the funniest one.", "self.personality.humor_style.humor_habits_tastes", "personality"),
    "Fake": ("I can be two-faced sometimes.", "self.personality.dark_side", "personality"),
    "Criminal damage": ("I have damaged things in the past when angry.", N + "temper_moodiness", "personality"),
    "Decision making": ("I take my time to make decisions.", "self.personality.risk_decision_style", "personality"),
    "Elections": ("I always try to vote in elections.", "self.personality.big_five.openness.convention_politics", "personality"),
    "Self-criticism": ("I often think about and regret the decisions I make.", N + "self_consciousness", "personality"),
    "Judgment calls": ("I can tell if people are listening to me or not when I talk to them.", EM + "empathy_social_reading", "personality"),
    "Hypochondria": ("I am a hypochondriac.", N + "fear_worry", "personality"),
    "Empathy": ("I am an empathetic person.", EM + "empathy_social_reading", "personality"),
    "Eating to survive": ("I eat because I have to. I don't enjoy food and eat as fast as I can.", L + "food_preferences", "taste"),
    "Giving": ("I try to give as much as I can to other people at Christmas.", "self.values.giving_charity", "values"),
    "Compassion to animals": ("I don't like seeing animals suffering.", "self.values.animals_environment", "values"),
    "Borrowed stuff": ("I look after things I have borrowed from others.", C + "order_caution", "personality"),
    "Loneliness": ("I feel lonely in life.", EM + "recent_stress_mood", "personality"),
    "Cheating in school": ("I used to cheat at school.", "self.values.honesty_trust", "personality"),
    "Health": ("I worry about my health.", N + "fear_worry", "personality"),
    "Changing the past": ("I wish I could change the past because of the things I have done.", "self.mind.memories_life_story", "personality"),
    "God": ("I believe in God.", "self.mind.big_questions.meaning_human_nature", "values"),
    "Dreams": ("I always have good dreams.", L + "habits_routines", "personality"),
    "Charity": ("I always give to charity.", "self.values.giving_charity", "values"),
    "Number of friends": ("I have lots of friends.", "self.love.friendship.friendship_habits", "personality"),
    "Waiting": ("I am very patient.", A + "trust_modesty_temper", "personality"),
    "New environment": ("I can quickly adapt to a new environment.", "self.personality.big_five.openness", "personality"),
    "Mood swings": ("My moods change quickly.", N + "temper_moodiness", "personality"),
    "Appearence and gestures": ("I am well mannered and I look after my appearance.", L + "style_appearance", "personality"),
    "Socializing": ("I enjoy meeting new people.", E + "sociability_energy", "personality"),
    "Achievements": ("I always let other people know about my achievements.", A + "trust_modesty_temper", "personality"),
    "Responding to a serious letter": ("I think carefully before answering any important letters.", C + "order_caution", "personality"),
    "Children": ("I enjoy children's company.", "self.love.family_parenting", "personality"),
    "Assertiveness": ("I am not afraid to give my opinion if I feel strongly about something.", "self.personality.big_five.extraversion", "personality"),
    "Getting angry": ("I can get angry very easily.", N + "temper_moodiness", "personality"),
    "Knowing the right people": ("I always make sure I connect with the right people.", "self.personality.motivation_ambition", "personality"),
    "Public speaking": ("I have to be well prepared before public speaking.", N + "self_consciousness", "personality"),
    "Unpopularity": ("I will find a fault in myself if people don't like me.", N + "self_consciousness", "personality"),
    "Life struggles": ("I cry when I feel down or things don't go the right way.", EM + "coping_expressing", "personality"),
    "Happiness in life": ("I am 100% happy with my life.", "self.mind.happiness_wellbeing", "personality"),
    "Energy levels": ("I am always full of life and energy.", E + "sociability_energy", "personality"),
    "Small - big dogs": ("I prefer big dangerous dogs to smaller, calmer dogs.", L + "pets", "taste"),
    "Personality": ("I believe all my personality traits are positive.", "self.personality.self_concept", "personality"),
    "Finding lost valuables": ("If I find something that doesn't belong to me, I will hand it in.", "self.values.honesty_trust", "values"),
    "Getting up": ("I find it very difficult to get up in the morning.", L + "habits_routines", "personality"),
    "Interests or hobbies": ("I have many different hobbies and interests.", L + "leisure_hobbies", "personality"),
    "Parents' advice": ("I always listen to my parents' advice.", "self.values.moral_foundations.authority", "values"),
    "Questionnaires or polls": ("I enjoy taking part in surveys.", L + "leisure_hobbies", "taste"),
    "Finances": ("I save all the money I can.", L + "money_habits", "personality"),
    "Shopping centres": ("I enjoy going to large shopping centres.", L + "leisure_hobbies", "taste"),
    "Branded clothing": ("I prefer branded clothing to non-branded.", L + "style_appearance", "taste"),
    "Entertainment spending": ("I spend a lot of money on partying and socializing.", L + "money_habits", "personality"),
    "Spending on looks": ("I spend a lot of money on my appearance.", L + "money_habits", "personality"),
    "Spending on gadgets": ("I spend a lot of money on gadgets.", L + "money_habits", "personality"),
    "Spending on healthy eating": ("I will happily pay more money for good, quality, or healthy food.", L + "money_habits", "personality"),
}
LIKERT = [
    "This does not describe me at all",
    "This describes me a little",
    "This describes me moderately well",
    "This describes me well",
    "This describes me very well",
]

# Categorical items: column -> (text, {raw value: (key, description)} in the survey's order, node)
CHOICES = {
    "Smoking": ("Which best describes your smoking habits?", {
        "never smoked": ("never_smoked", "I have never smoked"),
        "tried smoking": ("tried_smoking", "I have tried smoking"),
        "former smoker": ("former_smoker", "I used to smoke but quit"),
        "current smoker": ("current_smoker", "I smoke now"),
    }, L + "habits_routines"),
    "Alcohol": ("Which best describes your drinking habits?", {
        "never": ("never", "I never drink alcohol"),
        "social drinker": ("social_drinker", "I drink socially"),
        "drink a lot": ("drink_a_lot", "I drink a lot"),
    }, L + "habits_routines"),
    "Punctuality": ("Which best describes your timekeeping?", {
        "i am often early": ("often_early", "I am often early"),
        "i am always on time": ("always_on_time", "I am always on time"),
        "i am often running late": ("often_running_late", "I am often running late"),
    }, L + "habits_routines"),
    "Lying": ("Do you lie to others?", {
        "never": ("never", "I never lie"),
        "only to avoid hurting someone": ("only_to_spare_feelings", "Only to avoid hurting someone"),
        "sometimes": ("sometimes", "I sometimes lie"),
        "everytime it suits me": ("whenever_it_suits_me", "Every time it suits me"),
    }, "self.values.honesty_trust"),
}
ONLINE = ["no time at all", "less than an hour a day", "few hours a day", "most of the day"]
ONLINE_LEVELS = [
    "I spend no time online at all",
    "I spend less than an hour a day online",
    "I spend a few hours a day online",
    "I spend most of the day online",
]
TEMPO_LEVELS = [
    "I almost always choose slow songs over fast ones",
    "I choose slow songs more often than fast ones",
    "I like slow and fast songs about equally",
    "I choose fast songs more often than slow ones",
    "I almost always choose fast songs over slow ones",
]


def _enjoy_levels(x: str, verb: str, it: str) -> list[str]:
    fav = "they're among my favorites" if it == "them" else "it's one of my favorites"
    return [
        f"I don't enjoy {verb} {x} at all",
        f"I mostly dislike {verb} {x}, though I can put up with {it}",
        f"I'm neutral about {x}: I neither seek {it} out nor avoid {it}",
        f"I enjoy {verb} {x} and choose {it} from time to time",
        f"I enjoy {verb} {x} very much; {fav}",
    ]


def _interest_levels(x: str) -> list[str]:
    return [
        f"I'm not interested in {x} at all",
        f"I rarely give {x} any thought",
        f"I find {x} somewhat interesting when it comes up, but I don't seek it out",
        f"I'm interested in {x} and spend some of my free time on it",
        f"I'm very interested in {x}; it's one of my passions",
    ]


PLURAL_FEARS = {"Storm", "Spiders", "Snakes", "Rats", "Dangerous dogs"}


def _fear_levels(x: str, it: str) -> list[str]:
    return [
        f"I'm not afraid of {x} at all",
        f"I feel a little uneasy about {x}, but it passes quickly",
        f"I feel real fear about {x}, but I can handle {it}",
        f"I'm quite afraid of {x} and go out of my way to avoid {it}",
        f"I'm so afraid of {x} that {'they' if it == 'them' else 'it'} can make me panic",
    ]


def fetch(raw_dir: Path) -> None:
    for f in FILES:
        p = raw_dir / f
        if not p.exists():
            r = httpx.get(BASE + f, timeout=120, follow_redirects=True)
            r.raise_for_status()
            p.write_bytes(r.content)


def _load(raw_dir: Path) -> dict[str, list[str]]:
    with open(raw_dir / "responses.csv", newline="", encoding="utf-8") as fh:
        rows = list(csv.reader(fh))
    head = rows[0]
    return {c: [r[i].strip() for r in rows[1:]] for i, c in enumerate(head)}


def _dist(vals: list[str], order: list[str]) -> tuple[dict[str, float], int]:
    xs = [v for v in vals if v in order]
    n = len(xs)
    return {str(k): round(xs.count(o) / n, 4) for k, o in enumerate(order)}, n


LIKERT_RAW = ["1", "2", "3", "4", "5"]


def _score(text, levels, vals, node, kind, col, template, human_text=None, order=None) -> Question:
    dist, n = _dist(vals, order or LIKERT_RAW)
    return Question(
        text=text, primitive="score", hemisphere="self", kind=kind, origin="template", source=NAME,
        options=levels, node_hint=node, source_item_id=col, license=LICENSE, template_id=template,
        human_text=human_text,
        human=[HumanDist(population=POP, distribution=dist, n=n, source=SRC, wave="2013")],
        meta={"column": col},
    )


def normalize(raw_dir: Path) -> Iterator[Question]:
    data = _load(raw_dir)

    # 1. Scores per item
    for col, (_, x) in MUSIC.items():
        yield _score(f"How much do you enjoy listening to {x}?", _enjoy_levels(x, "listening to", "it"), data[col],
                     L + "leisure_hobbies", "taste", col, "young_people_survey.music")
    for col, (_, x) in MOVIES.items():
        yield _score(f"How much do you enjoy watching {x}?", _enjoy_levels(x, "watching", "them"), data[col],
                     L + "screens_media", "taste", col, "young_people_survey.movies")
    for col, (_, x, node) in INTERESTS.items():
        yield _score(f"How interested are you in {x}?", _interest_levels(x), data[col],
                     node, "taste", col, "young_people_survey.interest")
    for col, (_, x) in FEARS.items():
        yield _score(f"How afraid are you of {x}?", _fear_levels(x, "them" if col in PLURAL_FEARS else "it"), data[col],
                     FEAR_NODE, "personality", col, "young_people_survey.fear")
    yield _score("Do you prefer slow songs or fast songs?", TEMPO_LEVELS, data["Slow songs or fast songs"],
                 L + "leisure_hobbies", "taste", "Slow songs or fast songs", "young_people_survey.tempo")
    for col, (stmt, node, kind) in STATEMENTS.items():
        yield _score(f'How well does this statement describe you: "{stmt}"', LIKERT, data[col], node, kind, col,
                     "young_people_survey.statement",
                     human_text=f'How well would most people say this statement describes them: "{stmt}"')
    yield _score("How much time do you spend online?", ONLINE_LEVELS, data["Internet usage"],
                 L + "screens_media", "personality", "Internet usage", "young_people_survey.online", order=ONLINE)
    for col, (text, opts, node) in CHOICES.items():
        vals = [v for v in data[col] if v in opts]
        n = len(vals)
        yield Question(
            text=text, primitive="choice", hemisphere="self", kind="personality", origin="dataset", source=NAME,
            options={k: d for k, d in opts.values()}, node_hint=node, source_item_id=col, license=LICENSE,
            template_id=f"young_people_survey.{col.lower()}",
            human=[HumanDist(population=POP, distribution={k: round(vals.count(raw) / n, 4) for raw, (k, _) in opts.items()},
                             n=n, source="Young People Survey (Sabo 2013, Kaggle): share choosing each answer", wave="2013")],
            meta={"column": col},
        )

    # 2. Within-block pairs
    blocks = [
        ("music", "Which would you rather listen to: {a} or {b}?", {c: (k, x) for c, (k, x) in MUSIC.items()}, L + "leisure_hobbies", "taste"),
        ("movies", "Which would you rather watch: {a} or {b}?", {c: (k, x) for c, (k, x) in MOVIES.items()}, L + "screens_media", "taste"),
        ("interest", "Which are you more interested in: {a} or {b}?", {c: (k, x) for c, (k, x, _) in INTERESTS.items()}, L + "leisure_hobbies", "taste"),
        ("fear", "Which are you more afraid of: {a} or {b}?", FEARS, FEAR_NODE, "personality"),
    ]
    pairs = []
    for block, text, items, node, kind in blocks:
        for a, b in itertools.combinations(items, 2):
            pairs.append((block, text, items, node, kind, a, b))
    for block, text, items, node, kind, a, b in hash_order(pairs, lambda p: f"{p[0]}|{p[5]}|{p[6]}", SALT)[:TARGET_PAIRS]:
        (ka, xa), (kb, xb) = items[a], items[b]
        wa = wb = ties = 0
        for va, vb in zip(data[a], data[b]):
            if va not in LIKERT_RAW or vb not in LIKERT_RAW:
                continue
            if va > vb:
                wa += 1
            elif vb > va:
                wb += 1
            else:
                ties += 1
        n = wa + wb
        if n == 0:
            continue
        opts = dict(sorted([(ka, xa), (kb, xb)]))
        if block == "interest" and INTERESTS[a][2] == INTERESTS[b][2]:
            node = INTERESTS[a][2]  # both academic/career topics, or both media -> that node; mixed -> leisure
        yield Question(
            text=text.format(a=xa, b=xb), primitive="choice", hemisphere="self", kind=kind, origin="template",
            source=NAME, options=opts, node_hint=node, source_item_id=f"{block}|{a}|{b}", license=LICENSE,
            template_id=f"young_people_survey.pair_{block}",
            human=[HumanDist(population=POP, distribution={ka: round(wa / n, 4), kb: round(wb / n, 4)}, n=n,
                             source=PAIR_SRC, wave="2013")],
            meta={"columns": [a, b], "ties": ties},
        )
