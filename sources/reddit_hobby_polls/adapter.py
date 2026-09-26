"""Reddit hobby polls: real native polls with vote counts from hobby, fandom and subculture subreddits.

Source: the Arctic Shift public archive API (https://arctic-shift.photon-reddit.com, no login), the same one
reddit_polls uses. Title cleaning and the whole filter chain (voter facts, crosstabs, context, dated, politics /
sensitive flags, typo check, kind and hemisphere) come from sources/reddit_polls/adapter.py, loaded as a private
module copy; this file only adds the hobby-specific fetch, hobby-phrasing filters, the subreddit -> node map and caps.

Fetch (subreddits picked by a measured poll density, see source.yaml):
- "scan" subs (polls >= ~1.5% of posts): list every post of a month with fields=id,created_utc,selftext,title
  (cheap), keep ids whose selftext carries Reddit's "[View Poll](https://www.reddit.com/poll/...)" marker, then
  hydrate them via /api/posts/ids. Months go in salted-hash order across 2020-2024 and a sub stops once RAW_CAP
  polls are cached or MAX_MONTHS months are done. One file per sub-month.
- "search" subs (sparse polls): full-text search selftext=poll (recall checked equal to a full scan on sample
  days), one page of up to 100 posts per half-year: all ten for three subs, SEARCH_HALVES hash-picked ones for
  the rest. One file per sub-half-year.
Every request has a 20 s timeout and honours the X-RateLimit-Reset header; progress goes to <raw>/fetch.log.
"""

from __future__ import annotations

import datetime as dt
import importlib.util
import json
import re
import threading
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Iterator

import httpx
import polars as pl

from askjev.model import HumanDist, Question
from askjev.sampling import env_int, hash_order

NAME = "reddit_hobby_polls"
BASE_URL = "https://arctic-shift.photon-reddit.com/api/posts"
TARGET = env_int("TARGET_REDDIT_HOBBY_POLLS", 15000)
PER_SUB = env_int("REDDIT_HOBBY_POLLS_PER_SUB", 800)
MIN_VOTES = env_int("REDDIT_HOBBY_POLLS_MIN_VOTES", 50)
RAW_CAP = env_int("REDDIT_HOBBY_POLLS_RAW_CAP", 2000)  # scan subs stop fetching after this many cached polls
SEARCH_HALVES = env_int("REDDIT_HOBBY_POLLS_SEARCH_HALVES", 4)
SEARCH_ALL = {"mechanicalkeyboards", "Sneakers", "kpopthoughts"}
MAX_MONTHS = env_int("REDDIT_HOBBY_POLLS_MAX_MONTHS", 30)  # ... or after this many months (half of 2020-2024)
SALT = "reddit_hobby_polls-20260926"
YEARS = range(2020, 2025)

# reddit_polls, loaded as a private copy (its module globals MIN_VOTES / VOCAB are set for this source below).
_spec = importlib.util.spec_from_file_location("reddit_hobby_polls_rp",
                                               Path(__file__).parents[1] / "reddit_polls" / "adapter.py")
RP = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(RP)
RP.MIN_VOTES = MIN_VOTES
LICENSE = RP.LICENSE
KEEP = RP.KEEP
FUNNEL: Counter = RP.FUNNEL

_W, _S = "world", "self"
TV, ANIME, MUSIC, GAMES = "world.arts.television.tv_series", "world.arts.television.cartoons_anime", \
    "world.arts.music.musicians_bands", "world.sports.video_games"
TABLETOP = "world.sports.board_card_games"
HOBBY_SELF = "self.lifestyle.leisure_hobbies"
# sub -> (fetch mode, world node, self node)
SUBS: dict[str, tuple[str, str, str]] = {
    # scan: dense polls
    "BokuNoHeroAcademia": ("scan", ANIME, HOBBY_SELF),
    "OnePunchMan": ("scan", ANIME, HOBBY_SELF),
    "Bleach": ("scan", ANIME, HOBBY_SELF),
    "JuJutsuKaisen": ("scan", ANIME, HOBBY_SELF),
    "DemonSlayerAnime": ("scan", ANIME, HOBBY_SELF),
    "Naruto": ("scan", "world.arts.television.cartoons_anime.naruto", HOBBY_SELF),
    "Gundam": ("scan", ANIME, HOBBY_SELF),
    "Berserk": ("scan", "world.arts.visual_art.comics", HOBBY_SELF),
    "DCcomics": ("scan", "world.arts.visual_art.comics", HOBBY_SELF),
    "transformers": ("scan", "world.sports.board_card_games.toy", HOBBY_SELF),
    "Eminem": ("scan", MUSIC, HOBBY_SELF),
    "Kanye": ("scan", MUSIC, HOBBY_SELF),
    "radiohead": ("scan", MUSIC, HOBBY_SELF),
    "KendrickLamar": ("scan", MUSIC, HOBBY_SELF),
    "Mario": ("scan", GAMES, HOBBY_SELF),
    "Persona5": ("scan", GAMES, HOBBY_SELF),
    "Tekken": ("scan", GAMES, HOBBY_SELF),
    "Undertale": ("scan", GAMES, HOBBY_SELF),
    "Valorant": ("scan", GAMES, HOBBY_SELF),
    "KingdomHearts": ("scan", GAMES, HOBBY_SELF),
    "pokemon": ("scan", GAMES, HOBBY_SELF),
    "dragrace": ("scan", TV, HOBBY_SELF),
    "doctorwho": ("scan", TV, HOBBY_SELF),
    "thebachelor": ("scan", TV, HOBBY_SELF),
    "lotr": ("scan", "world.arts.books.specific_books.lord_of_the_rings", HOBBY_SELF),
    "MMA": ("scan", "world.sports.combat_sports", HOBBY_SELF),
    "bjj": ("scan", "world.sports.combat_sports.martial_arts", HOBBY_SELF),
    "dndnext": ("scan", TABLETOP, HOBBY_SELF),
    "conlangs": ("scan", "world.society.languages", HOBBY_SELF),
    # search: sparse polls in core hobby subs
    "mechanicalkeyboards": ("search", "world.tech.computers_hardware", HOBBY_SELF),
    "Sneakers": ("search", "world.arts.fashion.clothing", "self.lifestyle.style_appearance"),
    "kpopthoughts": ("search", "world.arts.music.pop_music", HOBBY_SELF),
    "rpg": ("search", TABLETOP, HOBBY_SELF),
    "DnD": ("search", TABLETOP, HOBBY_SELF),
    "vinyl": ("search", "world.arts.music.albums_songs", HOBBY_SELF),
}


# The fandom or hobby a poll is about, prefixed to its title ("One Punch Man: Who's the 5th strongest S class
# hero?"): inside the subreddit the topic went without saying, but an outside reader needs it. Skipped when the
# title already names it (any alias, case-insensitive).
TOPIC: dict[str, tuple[str, ...]] = {  # keyed like SUBS
    "BokuNoHeroAcademia": ("My Hero Academia", "MHA", "BNHA", "Boku no Hero"), "OnePunchMan": ("One Punch Man", "OPM"),
    "Bleach": ("Bleach",), "JuJutsuKaisen": ("Jujutsu Kaisen", "JJK"), "DemonSlayerAnime": ("Demon Slayer",),
    "Naruto": ("Naruto",), "Gundam": ("Gundam",), "Berserk": ("Berserk",), "DCcomics": ("DC Comics", "DC"),
    "transformers": ("Transformers",), "Eminem": ("Eminem",), "Kanye": ("Kanye West", "Kanye", "Ye"),
    "radiohead": ("Radiohead",), "KendrickLamar": ("Kendrick Lamar", "Kendrick"), "Mario": ("Super Mario", "Mario"),
    "Persona5": ("Persona 5", "Persona"), "Tekken": ("Tekken",), "Undertale": ("Undertale", "Deltarune"),
    "Valorant": ("Valorant",), "KingdomHearts": ("Kingdom Hearts", "KH"), "pokemon": ("Pokemon", "Pokémon"),
    "dragrace": ("RuPaul's Drag Race", "Drag Race"), "doctorwho": ("Doctor Who",), "thebachelor": ("The Bachelor",
    "Bachelor", "Bachelorette"), "lotr": ("The Lord of the Rings", "Lord of the Rings", "LOTR", "Tolkien"),
    "MMA": ("MMA", "UFC"), "bjj": ("Brazilian jiu-jitsu", "BJJ", "jiu jitsu", "jiu-jitsu"),
    "dndnext": ("D&D 5e", "D&D", "DnD", "5e"), "conlangs": ("Constructed languages", "conlang"),
    "mechanicalkeyboards": ("Mechanical keyboards", "keyboard"), "Sneakers": ("Sneakers", "sneaker", "shoe"),
    "kpopthoughts": ("K-pop", "kpop"), "rpg": ("Tabletop RPGs", "RPG", "TTRPG"), "DnD": ("Dungeons & Dragons", "D&D",
    "DnD"), "vinyl": ("Vinyl records", "vinyl"),
}


def _with_topic(sub: str, q: str) -> str:
    names = TOPIC[sub]
    if any(re.search(rf"(?<!\w){re.escape(n)}(?!\w)", q, re.I) for n in names):
        return q
    return f"{names[0]}: {q}"


# --- fetch -----------------------------------------------------------------------------------------------------
_lock = threading.Lock()


def _log(raw_dir: Path, msg: str) -> None:
    with _lock, open(raw_dir / "fetch.log", "a") as f:
        f.write(f"{dt.datetime.now().isoformat(timespec='seconds')} {msg}\n")


def _get(c: httpx.Client, path: str, params: dict, tries: int = 8) -> list[dict] | None:
    """One Arctic Shift call: 20 s timeout, waits out 422/429 ("slow down") using X-RateLimit-Reset. None = gave up."""
    for attempt in range(tries):
        reset = None
        try:
            r = c.get(f"{BASE_URL}/{path}", params=params, timeout=20)
            body = r.json()
            if r.status_code == 200 and body.get("data") is not None:
                time.sleep(0.8)
                return body["data"]
            reset = r.headers.get("x-ratelimit-reset")
        except (httpx.HTTPError, json.JSONDecodeError, ValueError):
            pass
        wait = float(reset) + 1 if reset and reset.replace(".", "", 1).isdigit() else 3 * 2 ** attempt
        time.sleep(min(wait, 90))
    return None


def _write(out: Path, rows: dict) -> None:
    tmp = out.with_suffix(".tmp")
    tmp.write_text("".join(json.dumps(r) + "\n" for r in rows.values()))
    tmp.rename(out)


def _months() -> list[tuple[dt.date, dt.date]]:
    ms = [dt.date(y, m, 1) for y in YEARS for m in range(1, 13)]
    ms = hash_order(ms, lambda d: d.isoformat(), SALT)  # spread a capped sub over the whole period
    return [(d, dt.date(d.year + d.month // 12, d.month % 12 + 1, 1)) for d in ms]


def _ts(d: dt.date) -> int:
    return int(dt.datetime(d.year, d.month, d.day, tzinfo=dt.timezone.utc).timestamp())


def _cached(raw_dir: Path, sub: str) -> int:
    return sum(len(f.read_text().splitlines()) for f in (raw_dir / sub).glob("*.jsonl"))


def _scan_sub(raw_dir: Path, sub: str) -> None:
    (raw_dir / sub).mkdir(parents=True, exist_ok=True)
    with httpx.Client(headers={"User-Agent": "askjev-research/0.1"}) as c:
        for a, b in _months()[:MAX_MONTHS]:
            have = _cached(raw_dir, sub)
            if have >= RAW_CAP:
                break
            out = raw_dir / sub / f"{a:%Y-%m}.jsonl"
            if out.exists():
                continue
            t1, after, ids, ok = _ts(b), _ts(a), [], True
            while True:
                data = _get(c, "search", {"subreddit": sub, "limit": 100, "sort": "asc", "after": after,
                                          "before": t1, "fields": "id,created_utc,selftext,title"})
                if data is None:
                    ok = False
                    break
                ids += [p["id"] for p in data if "reddit.com/poll/" in (p.get("selftext") or "")]
                if len(data) < 100:
                    break
                nxt = data[-1]["created_utc"]
                after = nxt if nxt > after else after + 1
            rows = {}
            for i in range(0, len(ids), 100):
                data = _get(c, "ids", {"ids": ",".join(ids[i:i + 100])}) if ok else None
                if data is None:
                    ok = False
                    break
                rows.update({p["id"]: {k: p.get(k) for k in KEEP} for p in data if p.get("poll_data")})
            if not ok:
                _log(raw_dir, f"FAIL {sub} {a:%Y-%m} (retried next run)")
                continue
            _write(out, rows)
            _log(raw_dir, f"{sub} {a:%Y-%m} polls={len(rows)} total={have + len(rows)}")
    _log(raw_dir, f"DONE {sub} total={_cached(raw_dir, sub)}")


def _halves(sub: str) -> list[tuple[str, dt.date, dt.date]]:
    """The half-years a search sub takes: all ten for the first three, else SEARCH_HALVES in salted-hash order
    (full-text search is slow under the archive's query-time budget)."""
    hs = [(f"{y}-h{h + 1}", a, b) for y in YEARS for h, (a, b) in
          enumerate(((dt.date(y, 1, 1), dt.date(y, 7, 1)), (dt.date(y, 7, 1), dt.date(y + 1, 1, 1))))]
    return hs if sub in SEARCH_ALL else hash_order(hs, lambda x: f"{sub}|{x[0]}", SALT)[:SEARCH_HALVES]


def _search_sub(raw_dir: Path, sub: str) -> None:
    (raw_dir / sub).mkdir(parents=True, exist_ok=True)
    with httpx.Client(headers={"User-Agent": "askjev-research/0.1"}) as c:
        for name, a, b in _halves(sub):
            out = raw_dir / sub / f"{name}.jsonl"
            if out.exists():
                continue
            data = _get(c, "search", {"subreddit": sub, "selftext": "poll", "limit": 100, "sort": "asc",
                                      "after": _ts(a), "before": _ts(b)}, tries=12)
            if data is None:
                _log(raw_dir, f"FAIL {sub} {name} (retried next run)")
                continue
            rows = {p["id"]: {k: p.get(k) for k in KEEP} for p in data if p.get("poll_data")}
            _write(out, rows)
            _log(raw_dir, f"{sub} {name} polls={len(rows)}")
    _log(raw_dir, f"DONE {sub} total={_cached(raw_dir, sub)}")


def fetch(raw_dir: Path) -> None:
    """ASKJEV_REDDIT_HOBBY_POLLS_FETCH=0 skips the network and normalizes the cache as it stands.
    Idempotent: cached files are skipped, failed units are retried on the next run. Eight scan workers plus one
    search worker (full-text search is rate-limited by query time, so it runs alone)."""
    raw_dir.mkdir(parents=True, exist_ok=True)
    if not env_int("REDDIT_HOBBY_POLLS_FETCH", 1):
        return
    scan = [s for s, (m, _, _) in SUBS.items() if m == "scan"]
    search = [s for s, (m, _, _) in SUBS.items() if m == "search"]
    with ThreadPoolExecutor(4) as ex:
        fut = ex.submit(lambda: [_search_sub(raw_dir, s) for s in search])
        with ThreadPoolExecutor(8) as ex2:
            list(ex2.map(lambda s: _scan_sub(raw_dir, s), scan))
        fut.result()


# --- normalize: hobby additions on top of reddit_polls' chain ---------------------------------------------------
PREF_GUARD = RP.PREF_GUARD
# The voter's own gear, collection, rank, habits or history in the hobby (biographical, not an opinion).
_GEAR = (r"collection|setup|set ?up|build|rig|kit|bag|stash|rotation|daily driver|edc|mains?|rank|elo|rating|team|"
         r"deck|army|faction|party|character|class|loadout|library|shelf|backlog|haul|pc|car|ride|record player|"
         r"turntable|keyboards?|pens?|inks?|tank|flock|life list|lifers?|list|streak|score|record|progress|"
         r"playthrough|save|campaign|table|group|gym|belt|handicap|clubs|bag|budget")
HOBBY_FACT = re.compile(
    rf"\byour (current |first |latest |main |own )?({_GEAR})\b|what'?s in your\b|"
    r"\bhow (long|many (years|hours|times))\b.*\b(have|had|did|do) you\b|"
    r"\bhow many\b.*\b(do|did|have) you\b|"
    r"\bhow many of (you|y'?all|us)\b|\bwho (here|else)\b|\bwho (y'?all|you) got\b|"
    r"\bfirst\b.*\byou (ever )?(heard|saw|watched|read|played|listened|bought|got|owned)\b|"
    r"\byou (heard|saw|watched|read|played|bought|got) first\b|"
    r"\bdo (y'?all|you guys|you all|yous) (collect|own|play|use|run|main|have|buy|read|watch)\b|"
    r"^(what|which)\b.*\bdo you (currently |mainly |usually |normally |mostly )?(own|main|play|use|run|drive|"
    r"collect|shoot|ride|have|wear|rock|listen|read|watch|train|solve|do)\b|"
    r"^do you (currently |still |usually |normally |regularly |actually )?(own|main|play|use|run|drive|collect|"
    r"shoot|ride|have|wear|listen|read|watch|train|solve|do|go|buy|compete|follow|attend|keep|make|write|speak)\b|"
    r"^(are|were) you (a |an )?(new|beginner|veteran|member|subscriber|player|dm|gm|forever dm|collector|"
    r"going|planning|gonna|excited|watching|playing|buying|attending|getting|caught up|up to date|still|currently|"
    r"able|ready)\b|"
    r"\bwhat (rank|level|belt|platform|console|region|server|elo)\b|\bwhich (platform|console|region|server)\b|"
    r"\b(when|how|why) did you (start|get into|first|discover|begin|join|find)\b|"
    r"\bwhat (was|is) your first\b|\b(what age|how old) (did|were) you\b|"
    r"^did you\b|^will you\b|^have you\b|^has anyone\b|^anyone\b|\bdid anyone\b|^how do you\b|"
    r"\bdid it take you\b|\bhow (often|much) do you\b|"
    r"\b(you|your) (guys|all)\b", re.I)
# Dated or event-bound (a season, episode, chapter, patch, upcoming release, a result to come).
DATED_HOBBY = re.compile(
    r"\b(season \d+|a?s ?\d+(e\d+)?|szn ?\d+|part (two|three|four|ii|iii|iv|\d)|episode \d+|ep\.? ?\d+|chapter \d+|ch\.? ?\d+|vol(ume)?\.? ?\d+|week \d+|"
    r"round \d+|patch(es)?|update|leaks?|leaked|trailer|teaser|spoilers?|this (season|episode|chapter|week|"
    r"event|patch|update|set|round|card|deck|build|album|song|one|game|fight|match|tournament|draft)|"
    r"next (season|episode|chapter|week|event|patch|album|game|set|fight|match|movie|film)|upcoming|latest|"
    r"new (album|episode|chapter|season|set|patch|update|single|movie|trailer)|ufc \d+|tonight'?s?|last night|"
    r"announced|announcement|release date|so far|anymore|just (released|dropped|finished|came out)|"
    r"leak|rumou?r\w*|drops? (today|tomorrow)|pre-?order\w*|now|still|yet|current|currently|last (chapter|episode|season|week|"
    r"game|fight|event|album|match|night|arc))\b", re.I)
FORECAST = re.compile(r"^will\b|\bthere will be\b|\bwill there be\b|\bwinning\b|\bhow will\b|\bwill (he|she|they|it|we)\b|\bgoing to\b|\bgonna\b|^(who|which|what)( \w+)? will\b|\bwill\b.*\b(win|happen|release|come out|be announced|"
                      r"return|die|make it|get eliminated|go home)\b|\bgoing to win\b|\bpredict\w*\b", re.I)
DEMONSTRATIVE = re.compile(r"\b(this|these|those)\b(?! or\b)", re.I)
# Fragments that lean on the poll options or the thread: "What'll happen with?", "For the final battle?".
FRAGMENT = re.compile(r"^if\b[^,]*\?$|\b(with|for|of|about|between|to|on|in|from|at|vs|versus|and|or)\?$|^(for|at|on|as|between)\b",
                      re.I)


def _hobby_drop(q: str, opt_text: str) -> str | None:
    if HOBBY_FACT.search(q) and not (PREF_GUARD.search(q) and not re.search(r"^(did|have|has|will) you\b", q, re.I)):
        return "6d_hobby_voter_fact"
    if DATED_HOBBY.search(q) or DATED_HOBBY.search(opt_text) or FORECAST.search(q):
        return "6e_hobby_dated_or_forecast"
    if DEMONSTRATIVE.search(q) or FRAGMENT.search(q) or len(q.split()) < 3:
        return "6f_needs_context"
    return None


# Options that point at the thread ("other (explain in comments)") are dropped like "see results" options; polls
# whose options are placeholders for a picture or the body ("A" / "B", "Option 1", "Team 2") are dropped.
COMMENT_OPT = re.compile(r"\bcomments?\b|\bexplain\b|\bbelow\b", re.I)
PLACEHOLDER = re.compile(r"^((option|team|choice|pic|picture|image|photo|number|no|design|version|v)_?)?([a-h]|\d{1,2})$")


# Sexualized polls about characters. Fictional casts in these subs include minors (school-age heroes, teen
# protagonists), so for fiction subs such polls are dropped outright; for real-people subs they are flagged sensitive.
SEXY = re.compile(r"\b(ass|asses|butt|booty|thicc|boobs?|breasts?|tits|thighs|hottest|hotter|sexiest|sexier|"
                  r"sexy|attractive|smash or pass|smashable|fuckable|waifus?|husbandos?|lewd|hentai|fan ?service|simp\w*|"
                  r"horny|seductive|body count|kink\w*|fetish\w*)\b", re.I)
FICTION_SUBS = {"BokuNoHeroAcademia", "OnePunchMan", "Bleach", "JuJutsuKaisen", "DemonSlayerAnime", "Naruto", "Gundam",
                "Berserk", "DCcomics", "transformers", "Mario", "Persona5", "Tekken", "Undertale", "Valorant",
                "KingdomHearts", "pokemon", "doctorwho", "lotr", "dndnext", "rpg", "DnD"}


# reddit_polls' political / sensitive regexes read fandom vocabulary as politics or violence ("Beast Wars", "Which gun
# do you prefer?" in a shooter, Drag Race, a D&D race, Christian Bale; "kill", "death battle", "Pain" in fight
# polls, Dick Grayson). Flags are recomputed with those words masked; sexual, drug, self-harm and profanity terms stay.
FLAG_MASK = re.compile(r"\b(\w+ )?wars?\b|\bguns?\b|\braces?\b|\bchristian\b|"
                       r"\bkill\w*\b(?! (yourself|myself|themselves|himself|herself))|\bdeaths?\b|\bdead\w*|"
                       r"\bdie[sd]?\b|\bdying\b|\bmurder\w*|\bcheat\w*|\bpains?\b|\bcutting\b|\bdick grayson\b|"
                       r"\bbattle\w*|\bfights?\b|\bweapons?\b|\bsword\w*", re.I)


def _flags(it: dict, sub: str) -> list[str]:
    text = f"{it['q']} " + " ".join(v or k.replace("_", " ") for k, v in it["options"].items())
    m = FLAG_MASK.sub(" ", text if sub != "DCcomics" else re.sub(r"\bdick\b", " ", text, flags=re.I))
    flags = []
    if it["flair"] in RP.POLITICAL_FLAIRS or RP.POLITICAL.search(m) or RP.POLITICAL_EXTRA.search(m):
        flags.append("political")
    if RP.SENSITIVE.search(m) or RP.PROFANE.search(m) or SEXY.search(text):
        flags.append("sensitive")
    return flags


# Tabletop rules lookups ("Does Find Familiar's help action grant advantage on initiative?") are rules minutiae,
# not community opinion; "should" questions (house rules, table practice) are kept.
TABLETOP_SUBS = {"dndnext", "DnD", "rpg"}
RULES = re.compile(r"^(does|do|can|is|are|would|will|could|if)\b.*\b(spells?|cantrips?|actions?|bonus action|reactions?|"
                   r"advantage|disadvantage|attacks?|rolls?|saving throws?|saves?|feats?|raw|rai|rules?|damage|ac|"
                   r"hit points|hp|concentration|stack|stacks|proficiency|modifier|multiclass\w*|opportunity|"
                   r"initiative|resistance|immunity|conditions?|grapple\w*|prone|invisible|sneak attack|smite)\b",
                   re.I)


def _fix_options(it: dict) -> dict | None:
    drop = [k for k, v in it["options"].items() if COMMENT_OPT.search(v or k.replace("_", " "))]
    if drop:
        keep = {k: v for k, v in it["options"].items() if k not in drop}
        total = sum(it["dist"][k] for k in keep)
        if len(keep) < 2 or total * it["n"] < MIN_VOTES:
            return None
        it = {**it, "options": keep, "dist": {k: it["dist"][k] / total for k in keep}, "n": round(total * it["n"])}
    if sum(bool(PLACEHOLDER.match(k)) for k in it["options"]) >= 2:
        return None
    return it


def _pool(raw_dir: Path) -> list[dict]:
    # scan subs: only the first MAX_MONTHS months of the fetch order (files past that, from runs with a larger
    # MAX_MONTHS, are ignored so the output does not depend on fetch history)
    months = {f"{a:%Y-%m}.jsonl" for a, _ in _months()[:MAX_MONTHS]}
    lines = {sub: [json.loads(line) for f in sorted((raw_dir / sub).glob("*.jsonl"))
                   if f.name in (months if SUBS[sub][0] == "scan" else {f"{h[0]}.jsonl" for h in _halves(sub)})
                   for line in f.read_text().splitlines()] for sub in SUBS if (raw_dir / sub).exists()}
    # quora_closed's typo check. Hobby titles alone are too few for a word-frequency vocabulary (ordinary words like
    # "tank" or "spectacular" fall under 3), so the vocabulary is quora_closed's 537k questions (its cached raw
    # parquet) plus every fetched hobby poll title (fandom names and jargon).
    RP.VOCAB.clear()
    RP.VOCAB.update(RP.Q._vocab([p.get("title") or "" for ps in lines.values() for p in ps]))
    qf = raw_dir.parent / "quora_closed" / RP.Q.FILE
    if not qf.exists():
        raise FileNotFoundError(f"{qf}: run `askjev source quora_closed` first (its questions are the typo vocabulary)")
    df = pl.read_parquet(qf)
    RP.VOCAB.update(RP.Q._vocab(sorted({q for q in df["sentence1"].to_list() + df["sentence2"].to_list() if q})))
    best: dict[str, dict] = {}
    for sub, ps in lines.items():
        seen = set()
        for p in ps:
            if p["id"] in seen:
                continue
            seen.add(p["id"])
            FUNNEL["0_polls"] += 1
            it = RP._parse(p, sub)
            if not it:
                continue
            if RP._voter_fact(it["q"]):
                FUNNEL["6b_voter_fact"] += 1
                continue
            if RP._crosstab_keys(list(it["options"])):
                FUNNEL["6c_option_crosstab"] += 1
                continue
            it = _fix_options(it)
            if it:
                it["flags"] = _flags(it, sub)
            if not it:
                FUNNEL["6g_placeholder_options"] += 1
                continue
            if SEXY.search(f"{it['q']} {' '.join(it['options']).replace('_', ' ')}"):
                if sub in FICTION_SUBS:
                    FUNNEL["7b_sexualized_fiction"] += 1
                    continue
            if sub in TABLETOP_SUBS and RULES.search(it["q"]) and not re.search(r"\bshould\b", it["q"], re.I):
                FUNNEL["6h_rules_question"] += 1
                continue
            why = _hobby_drop(it["q"], " | ".join(v or k.replace("_", " ") for k, v in it["options"].items()))
            if why:
                FUNNEL[why] += 1
                continue
            key = RP._title_key(it["q"])
            old = best.get(key)
            if old is None or (it["n"], it["id"]) > (old["n"], old["id"]):
                if old is not None:
                    FUNNEL["9_duplicate_titles"] += 1
                best[key] = it
            else:
                FUNNEL["9_duplicate_titles"] += 1
    FUNNEL["10_pool"] = len(best)
    return list(best.values())


def _question(it: dict) -> Question:
    _, world_node, self_node = SUBS[it["sub"]]
    text = _with_topic(it["sub"], it["q"])  # origin "template" when the topic prefix was added
    meta = {"subreddit": it["sub"], "flair": it["flair"], "reddit_title": it["raw_title"], "created": it["created"],
            "closed_when_archived": it["closed_when_archived"]}
    if it["flags"]:
        meta["flags"] = it["flags"]
    return Question(
        text=text, primitive="choice", hemisphere=it["hemisphere"], kind=it["kind"],
        origin="dataset" if text == it["q"] else "template",
        source=NAME, options=it["options"],
        node_hint=world_node if it["hemisphere"] == "world" else self_node,
        source_item_id=f"{it['sub']}:{it['id']}", license=LICENSE,
        human=[HumanDist(population=f"r/{it['sub']} voters", distribution=it["dist"], n=it["n"],
                         source="Reddit native poll vote counts (Arctic Shift archive; 'see results' options "
                                "dropped, shares over the remaining options)")],
        meta=meta,
    )


def normalize(raw_dir: Path) -> Iterator[Question]:
    """Salted-hash order, at most PER_SUB per subreddit, TARGET overall; output sorted by (sub, poll id)."""
    FUNNEL.clear()
    per: Counter = Counter()
    picked = []
    for it in hash_order(_pool(raw_dir), lambda x: x["id"], SALT):
        if len(picked) >= TARGET:
            break
        if per[it["sub"]] >= PER_SUB:
            continue
        per[it["sub"]] += 1
        picked.append(it)
    FUNNEL["11_picked"] = len(picked)
    print("reddit_hobby_polls funnel:", dict(sorted(FUNNEL.items())))
    print("picked by subreddit:", dict(per.most_common()))
    for it in sorted(picked, key=lambda x: (x["sub"], x["id"])):
        yield _question(it)
