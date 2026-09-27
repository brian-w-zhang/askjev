"""r/Jokes: which of two jokes posted to Reddit's r/Jokes in the same month got more upvotes.

Source: the r/Jokes dataset (Weller & Seppi, LREC 2020), github.com/orionw/rJokesData, data/preprocessed.csv.gz
(public, no login): 573,335 r/Jokes posts 2008-2019 with the post title, body, final score and timestamp. In that
file the column named `punchline` holds the post title and `body` the post body; the joke as posted is title + body.

Question (World, evaluative, node world.society.internet_culture): "Which joke, `joke_1` or `joke_2`, got more
upvotes on Reddit's r/Jokes?" with both jokes in `state`. Truth = the higher-scored joke.

Pairing: both jokes posted in the same calendar month (the subreddit's size and traffic change a lot over the
years), the winner scored >= MIN_WIN and >= RATIO times the loser, and the loser scored >= MIN_LOSE (a live post
people saw and voted on, not one removed at once). Joke lengths within LEN_RATIO of each other. Each joke is used
once. Reposts are removed: any joke whose normalized text (or its first 80 normalized characters) occurs more than
once in the whole file is dropped, so the same joke never has two different scores.

Filtering is hard because r/Jokes is full of offensive material (shared keyword lists from imgflip_captions plus
joke-specific ones): dropped are slurs, anything sexual or innuendo, politics, ethnic / national / religious-group,
gender-identity and disability jokes, blonde and "women are..." jokes, graphic violence, self-harm, drugs and
profanity. What remains borderline (religion as a setting, death, drinking, mild swearing like "hell" or "damn",
toilet humor) is kept and flagged "sensitive". Reddit meta ("Edit: thanks for the gold", karma, repost, this sub)
is stripped from the end or the joke is dropped, so no text leaks the score.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import importlib.util
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterator

import httpx
import polars as pl

from askjev.model import Question
from askjev.sampling import env_int, hash_order

NAME = "rjokes_pairs"
URL = "https://raw.githubusercontent.com/orionw/rJokesData/master/data/preprocessed.csv.gz"
LICENSE = ("r/Jokes dataset (Weller & Seppi 2020, github.com/orionw/rJokesData): Reddit user content under the "
           "Reddit API terms and User Agreement, research use with citation")
SALT = "rjokes_pairs.v1"
TARGET = env_int("TARGET_RJOKES_PAIRS", 2500)
MIN_WIN = 1000
MIN_LOSE = 10
RATIO = 10.0
LEN_RATIO = 2.0
MIN_LEN, MAX_LEN = 40, 600
NODE = "world.society.internet_culture"

_spec = importlib.util.spec_from_file_location("rjokes_imgflip", Path(__file__).parents[1] / "imgflip_captions" / "adapter.py")
IF = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(IF)

INNUENDO = re.compile(r"\b(wedding night|honeymoon|in bed|laid|hard[- ]?on|bj|suck(s|ed|ing)? (my|his|her|it|on|you)|"
                      r"swallow\w*|spit|gyn[ae]?colog\w*|tampons?|pregnan\w*|nympho\w*|affairs?|cheat(s|ing|ed)? on|"
                      r"mistress\w*|lap ?dance\w*|brothel\w*|escorts?|foreskin|circumcis\w*|vasectom\w*|prostate|"
                      r"proctolog\w*|balls|nuts|screw(s|ed|ing)?|pants|undress\w*|bedroom|virgin\w*|period|"
                      r"sexually|lesbian|bra|breasts?|chest|butt|booty|bum|rear end|behind her|pee|peeing|urinat\w*|"
                      r"blow(s|ing)? (me|him|her)|going down on|eat(s|ing)? (her|out)|wood|stiff|throb\w*|moan\w*|"
                      r"hot chick|hot girl|hot woman|busty|curvy|bikini|shower together|skinny ?dipping|"
                      r"playboy|hustler|gigolo|pimp\w*|madam|nun|nuns|priest|altar boys?|little boys?|g ?spot|under ?age\w*|"
                      r"under (1[0-9]|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|age)|minors?|jail ?bait|"
                      r"younger the better|doggy\w*|jack(s|ing|ed)? off|lovers?|love ?child|pdf|"
                      r"touch(es|ed|ing)? (his|her|a|the|my) (students?|kids?|child|children|boys?|girls?|nephew|niece)|"
                      r"bang(s|ed|ing)?|back ?door|pubic|lick(s|ed|ing)? (me|her|him|it)|hump\w*|"
                      r"cute,? (and )?(thin|young)|clitoris|sexting|spooge|queef\w*|dtf|nsfw)\b", re.I)
GROUP_JOKE = re.compile(r"\b(women|woman's|a woman|wives|feminis\w*|girls are|men are|blonde\w*|redheads?|gingers?|"
                        r"fat (people|chick|girl|woman|women|guy|kid)|ugly (girl|woman|wife|chick)|your mom|yo mama|"
                        r"yo momma|your mama|dead (baby|babies|kids?|children)|orphans?|cripple\w*|"
                        r"retard\w*|special needs|down'?s|cancer|chemo|leukemia|terminal|holocaust|auschwitz|"
                        r"concentration camp|gas chamber|oven|hitler|nazi\w*|isis|al qaeda|terroris\w*|allahu|"
                        r"9/11|twin towers|columbine|school shoot\w*|ethiopia\w*|africa\w*|mexic\w*|china|india|"
                        r"israel\w*|arab\w*|asia\w*|korea\w*|vietnam\w*|iraq\w*|iran\w*|afghan\w*|syria\w*|racis\w*|"
                        r"african[- ]american\w*|colou?red (people|guy|man|woman|folks?)|ghetto|thugs?|watermelon|fried chicken|"
                        r"anti-?vax\w*|vaccin\w*|unvaccinated|abort\w*|confedera\w*|slavery|plantation|(your|yo|ur) (mom|mother|mama|momma)\w*|so fat)\b", re.I)
BORDERLINE = re.compile(r"\b(hell|damn|dammit|crap|piss\w*|ass|asses|arse|bitch\w*|shit\w*|bastard\w*|dead|died|dies|"
                        r"die|dying|death|kill\w*|funeral|coffin|grave|drunk\w*|beer|vodka|whiskey|whisky|"
                        r"alcohol\w*|poop\w*|fart\w*|toilet|diarrh\w*|constipat\w*|jesus|god|heaven|devil|"
                        r"satan|church|pastor|rabbi|pope|moses|bible|religio\w*|christian\w*|catholic\w*|mormon\w*|"
                        r"buddhis\w*|atheist\w*|monks?|angel|st\.? peter|saint peter|blood\w*|cops?|police\w*)\b", re.I)
META = re.compile(r"\b(reddit\w*|redditors?|subreddit|r/\w+|u/\w+|karma|upvot\w*|downvot\w*|up ?vote\w*|repost\w*|"
                  r"gold|gilded|gilding|front ?page|this sub|mods?|OC|cake ?day|throwaway|x-?post|crosspost\w*|"
                  r"edit|edited|tl;?dr|removed|deleted)\b", re.I)
# color words for people: dropped unless the phrase is plainly about a thing ("black hole", "black and white")
COLOR = re.compile(r"\b(black|white|brown|yellow|red)(?:s|'s)?\b(?! (?:and white|and red|and decker|hole|holes|eye|eyes|pepper|"
                   r"magic|plague|death|dog|cat|hair|gate|belt|board|smith|berry|berries|out|coffee|tea|wine|"
                   r"paint|shirt|dress|car|house|snow|christmas|widow|sheep|bear|panther|knight|square|piece|queen|"
                   r"king|bishop|rook|pawn|9|8|card|light|lines?|flag|sox|wings?|sea|nile|wall|walls|noise|"
                   r"lies?|claw|rabbit|stripes?|polar|blood|cells?|dwarf|giant|meat|bread|rice|onion|sauce|chocolate))",
                   re.I)
COLOR_OK = re.compile(r"\b(snow white|red[- ]handed|red light|red ?neck)\b", re.I)
EDIT_TAIL = re.compile(r"\s*(\(|\[)?\s*\b(edit|edit\s*\d|eta|update)\b\s*[:\-].*$", re.I | re.S)


def fetch(raw_dir: Path) -> None:
    out = raw_dir / "preprocessed.csv.gz"
    if out.exists() and out.stat().st_size > 1_000_000:
        return
    raw_dir.mkdir(parents=True, exist_ok=True)
    with httpx.stream("GET", URL, timeout=600, follow_redirects=True) as r:
        r.raise_for_status()
        with open(out, "wb") as fh:
            for chunk in r.iter_bytes():
                fh.write(chunk)


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


def _joke(title: str | None, body: str | None) -> str | None:
    title = (title or "").strip()
    body = (body or "").strip()
    if not title or not body or body.lower() in {"[removed]", "[deleted]"}:
        return None
    body = EDIT_TAIL.sub("", body).strip()
    body = re.sub(r"&amp;", "&", body)
    body = re.sub(r"&[lg]t;", "", body)
    body = re.sub(r"[ \t ]+", " ", body)
    body = re.sub(r"\s*\n\s*(\n\s*)+", "\n", body)
    if not body:
        return None
    return f"{title}\n{body}"


FUNNEL: Counter = Counter()


def _keep(text: str) -> bool:
    for name, rx in (("meta", META), ("slur", IF.SLUR), ("sexual", IF.SEXUAL), ("innuendo", INNUENDO),
                     ("political", IF.POLITICAL), ("group", IF.ETHNIC), ("group", GROUP_JOKE),
                     ("graphic", IF.SENSITIVE)):
        if rx.search(text):
            FUNNEL[f"drop_{name}"] += 1
            return False
    if COLOR.search(COLOR_OK.sub("", text)) and re.search(r"\b(black|white|brown)\b", text, re.I):
        FUNNEL["drop_group"] += 1
        return False
    if re.search(r"https?://|www\.|\.com\b|\*\*|#|\||&nbsp;|&#|\^", text):  # links and markdown tables/headers
        FUNNEL["drop_markup"] += 1
        return False
    if not all(ord(c) < 0x2500 for c in text):  # emoji, box drawing, other scripts
        FUNNEL["drop_charset"] += 1
        return False
    return True


def _jokes(raw_dir: Path) -> list[dict]:
    df = pl.read_csv(raw_dir / "preprocessed.csv.gz", infer_schema_length=10000,
                     schema_overrides={"score": pl.Int64, "date": pl.Float64})
    df = df.filter(pl.col("date").is_not_null() & pl.col("score").is_not_null())
    rows = []
    for title, body, score, date in df.select("punchline", "body", "score", "date").iter_rows():
        text = _joke(title, body)
        if text is None:
            continue
        rows.append((text, int(score), int(date)))
    FUNNEL["with_body"] = len(rows)
    full = Counter(_norm(t) for t, _, _ in rows)
    head = Counter(_norm(t)[:80] for t, _, _ in rows)
    out = []
    for text, score, date in rows:
        n = _norm(text)
        if full[n] > 1 or head[n[:80]] > 1:
            FUNNEL["drop_repost"] += 1
            continue
        if not (MIN_LEN <= len(text) <= MAX_LEN):
            FUNNEL["drop_length"] += 1
            continue
        if not (score >= MIN_WIN or MIN_LOSE <= score <= MIN_WIN / RATIO * 3):
            continue  # can never be paired: not a winner and not a plausible loser
        if not _keep(text):
            continue
        month = dt.datetime.fromtimestamp(date, dt.timezone.utc).strftime("%Y-%m")
        out.append({"id": hashlib.sha1(f"{date}|{n}".encode()).hexdigest()[:16], "text": text, "score": score,
                    "month": month, "date": date})
    FUNNEL["kept"] = len(out)
    return out


def normalize(raw_dir: Path) -> Iterator[Question]:
    by_month: dict[str, list[dict]] = defaultdict(list)
    for j in _jokes(raw_dir):
        by_month[j["month"]].append(j)
    pairs = []
    for month, jokes in sorted(by_month.items()):
        winners = hash_order([j for j in jokes if j["score"] >= MIN_WIN], lambda j: j["id"], SALT + ".win")
        losers = hash_order([j for j in jokes if MIN_LOSE <= j["score"] < MIN_WIN], lambda j: j["id"], SALT + ".lose")
        used: set[str] = set()
        for w in winners:
            for lo in losers:
                if lo["id"] in used or lo["score"] * RATIO > w["score"]:
                    continue
                a, b = sorted((len(w["text"]), len(lo["text"])))
                if b > a * LEN_RATIO:
                    continue
                used.add(lo["id"])
                pairs.append((w, lo))
                break
    FUNNEL["pairs"] = len(pairs)
    for w, lo in hash_order(pairs, lambda p: f"{p[0]['id']}|{p[1]['id']}", SALT + ".pairs")[:TARGET]:
        first, second = hash_order([w, lo], lambda j: j["id"], SALT + ".order")
        flags = ["sensitive"] if BORDERLINE.search(w["text"] + "\n" + lo["text"]) else []
        yield Question(
            text="Which joke, `joke_1` or `joke_2`, got more upvotes on Reddit's r/Jokes?",
            primitive="choice", hemisphere="world", kind="evaluative", origin="dataset", source=NAME,
            options={"joke_1": None, "joke_2": None},
            state={"joke_1": first["text"], "joke_2": second["text"]},
            node_hint=NODE, source_item_id=f"{w['id']}|{lo['id']}", license=LICENSE,
            truth="joke_1" if first is w else "joke_2",
            template_id="rjokes_pairs.more_upvotes",
            meta={"month": w["month"], "scores": [first["score"], second["score"]],
                  **({"flags": flags} if flags else {})},
        )
