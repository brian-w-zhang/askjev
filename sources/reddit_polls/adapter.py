"""Reddit polls: real r/polls and r/WouldYouRather native polls with their vote counts.

Source: the Arctic Shift public archive API (https://arctic-shift.photon-reddit.com, no login), which serves
Pushshift-style submission JSON including `poll_data` (options + per-option vote counts as archived). fetch()
takes whole UTC days (the 1st, 8th, 15th and 22nd of every month, 2020-01 .. 2024-12) from each subreddit and
keeps only the fields used here.

normalize(): a poll becomes a Choice over its options (2-6 real options after dropping "see results" options),
HumanDist = vote shares among those options (population "r/<sub> voters", n = their total votes, n >= 100).
Title must be one standalone closed question; demographic / personal-fact polls ("How old are you?", "Have you
ever been arrested?") are dropped since they ask about the voter, not an opinion; NSFW-marked, removed and
Relationships/NSFW-flaired posts are dropped. Political and sensitive content is flagged. No node_hint, no truth.
"""

from __future__ import annotations

import datetime as dt
import html
import importlib.util
import json
import re
import time
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Iterator

import httpx

from askjev.model import HumanDist, Question
from askjev.sampling import env_int, hash_order

NAME = "reddit_polls"
API = "https://arctic-shift.photon-reddit.com/api/posts/search"
LICENSE = "Reddit user content via the Arctic Shift public archive (research use; Reddit User Agreement)"
TARGET = env_int("TARGET_REDDIT_POLLS", 15000)
MIN_VOTES = env_int("REDDIT_POLLS_MIN_VOTES", 100)
SALT = "reddit_polls-20260925"
SUBS = ("polls", "WouldYouRather")
DAYS = (1, 8, 15, 22)
YEARS = range(2020, 2025)
KEEP = ("id", "title", "selftext", "over_18", "removed_by_category", "link_flair_text", "created_utc",
        "retrieved_on", "score", "num_comments", "poll_data", "subreddit", "spoiler")
FUNNEL: Counter = Counter()

# quora_closed's political / sensitive / slur / minors regexes, loaded as a private copy with the `elect\w*` fix
# (it also matched electricity) used by stackexchange_closed and wildchat_closed.
_spec = importlib.util.spec_from_file_location("reddit_polls_quora_filters",
                                               Path(__file__).parents[1] / "quora_closed" / "adapter.py")
Q = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(Q)
_ELECT_FIX = r"elect(s|ed|ing|or\w*|oral|ion\w*)?"
Q.POLITICAL = re.compile(Q.POLITICAL.pattern.replace(r"elect\w*", _ELECT_FIX), re.I)
# quora_closed's SENSITIVE also hits "method", "painting" and "erected"; narrow those three stems here.
Q.SENSITIVE = re.compile(Q.SENSITIVE.pattern.replace(r"meth\w*", "meth|methamphetamine")
                         .replace(r"pain\w*", "pain|pains|painful").replace(r"erect\w*", r"erection\w*"), re.I)
POLITICAL, SENSITIVE, SLURS, MINORS_SEX = Q.POLITICAL, Q.SENSITIVE, Q.SLURS, Q.MINORS_SEX
# Gender-identity topics quora_closed's regex misses.
POLITICAL_EXTRA = re.compile(r"\b(non.?binary|enby|trans (people|person|women|woman|men|man|rights|kids)|trans|"
                             r"pronouns?|gender identit\w*|genders|cis|cisgender)\b", re.I)


def _days() -> list[dt.date]:
    return [dt.date(y, m, d) for y in YEARS for m in range(1, 13) for d in DAYS]


def _get(c: httpx.Client, params: dict) -> list[dict]:
    for attempt in range(8):
        try:
            r = c.get(API, params=params)
            if r.status_code == 200:
                body = r.json()
                if body.get("data") is not None:
                    return body["data"]
        except (httpx.HTTPError, json.JSONDecodeError):
            pass
        time.sleep(2 + 3 * attempt)
    raise RuntimeError(f"Arctic Shift request failed: {params}")


def fetch(raw_dir: Path) -> None:
    with httpx.Client(timeout=120, headers={"User-Agent": "askjev-research/0.1"}) as c:
        for sub in SUBS:
            (raw_dir / sub).mkdir(parents=True, exist_ok=True)
            for day in _days():
                out = raw_dir / sub / f"{day.isoformat()}.jsonl"
                if out.exists():
                    continue
                t0 = int(dt.datetime(day.year, day.month, day.day, tzinfo=dt.timezone.utc).timestamp())
                t1, after, rows = t0 + 86400, t0, {}
                while True:
                    data = _get(c, {"subreddit": sub, "limit": 100, "sort": "asc", "after": after, "before": t1})
                    for p in data:
                        if p.get("poll_data"):
                            rows[p["id"]] = {k: p.get(k) for k in KEEP}
                    if len(data) < 100:
                        break
                    nxt = data[-1]["created_utc"]
                    after = nxt if nxt > after else after + 1
                    time.sleep(0.3)
                tmp = out.with_suffix(".tmp")
                tmp.write_text("".join(json.dumps(r) + "\n" for r in rows.values()))
                tmp.rename(out)


# --- normalize -------------------------------------------------------------------------------------------------
# Flairs whose polls ask about the voter's facts, the subreddit itself, trivia without an answer key, news of the
# day, the asker's own decision, or NSFW. Politics flairs are kept and flagged.
DROP_FLAIRS = {"demographics", "reddit", "trivia", "current events", "decide for me", "nsfw", "meta", "mod post",
               "announcement", "mod announcement"}
POLITICAL_FLAIRS = {"politics", "politics and law"}
RESULTS = re.compile(r"\bresults?\b|\bsee (the )?(votes|answers|poll)\b|\bjust (here|looking|curious|want to see)\b|"
                     r"^(view|show|check)\b|\bno opinion\b", re.I)
EMOJI = re.compile("[\U0001F000-\U0001FAFF☀-➿️‍⬀-⯿\U0001F1E6-\U0001F1FF]")
STRIP_PREFIX = re.compile(
    r"^\s*((\[[^\]]*\]|\([^)]*\))\s*|(quick |a |another |serious |honest |random |genuine |simple |hypothetical )?"
    r"(poll|question|q)\s*[:\-]\s*|(hypothetical|serious|poll|question|survey)\s*[:\-]\s*|"
    r"(hey |hi |ok |okay |so )?(reddit(ors)?|r/polls|people|everyone|everybody|folks|y'?all)\s*[,:!\-]\s*|"
    r"(hey|hi|ok|okay|so|genuine question|honest question)\s*[,:!\-]?\s+)", re.I)
TARGETED = re.compile(r"^[\w' ]{2,30}( of reddit| on reddit| here)?\s*[,:]\s+(?=\w)", re.I)  # "Americans, do you..."
WYR_ABBR = re.compile(r"^(wyr|wyrather|would u rather)\b[:,]?\s*", re.I)
OPENER = re.compile(r"^(would|do|does|did|is|are|was|were|which|what|who|whom|how|should|can|could|will|have|has|if|"
                    r"when|where|why|in|at|on|for|a|an|the|as|between|given|assuming|imagine|pick|choose|rate|"
                    r"favou?rite|best|worst|better)\b", re.I)
# Needs something the reader can't see (the post body, a picture, comments) or is about the asker.
CONTEXT = re.compile(
    r"\b(description|desc|body|below|above|explained|details?|context|comments?|this (post|poll|sub|subreddit|picture|"
    r"pic|image|photo|video|song|guy|girl|person|one|thing|meme|situation|scenario|case)|these|op|pictured|"
    r"shown|link|edit|update|part \d|round \d|day \d|pt\.? ?\d|sequel|continued|follow.?up|last poll|previous poll|"
    r"my|me|mine|myself|i|i'm|im|i've|ive|i'd|i'll|we|our|us|did you|you've|you have (ever|been|had|seen|watched|"
    r"done|played|read))\b|\b(this|that|these|those|it|them)\s*\?$", re.I)
REDDIT = re.compile(r"\b(reddit\w*|subreddit|r/\w+|upvot\w*|downvot\w*|karma|mods?|moderators?|u/\w+|poll(s|ing)?|"
                    r"vote\w*|voters?|option\w*|sub)\b", re.I)
DATED = re.compile(r"\b(covid\w*|corona\w*|pandemic|quarantin\w*|lockdown\w*|vaccin\w*|booster|this (year|week|month|"
                   r"weekend|summer|winter|fall|spring|season)|today|tonight|tomorrow|yesterday|right now|currently|"
                   r"lately|recently|new year'?s?|20[12]\d|election|elections)\b", re.I)
# Facts about the voter (age, gender, location, experiences), not an opinion or preference.
PERSONAL_FACT = re.compile(
    r"\b(how old are you|what('s| is) your (age|gender|sex|height|weight|birthday|birth month|zodiac|star sign|"
    r"ethnicity|race|nationality|religion|sexuality|orientation|income|salary|job|occupation|major|degree|name|iq|"
    r"blood type|eye colou?r|hair colou?r|shoe size|country|state|city|location|grade)|"
    r"what (gender|age|generation|country|state|continent|race|ethnicity|religion|grade|year) are you|"
    r"are you (male|female|a (man|woman|boy|girl|guy|student|parent|virgin|teen\w*)|married|single|"
    r"religious|an? (atheist|christian|muslim|jew)|straight|gay|bi|trans|older|younger|over|under)|"
    r"where (are you from|do you live|were you born)|have you ever|had you ever|did you (ever|go|have|get|use)|"
    r"were you (ever|born)|how many [\w' ]{1,20}do you (have|own)|do you (have|own) (a|an|any|kids|children|"
    r"siblings|pets?)\b|when were you born|how (tall|old|much do you weigh)|what time did you|"
    r"what('s| is) your (bmi|gpa|sat|act)|do you know (what|who|how|where|about|the|of|any)|"
    r"have you heard (of|about)|can you (name|guess|spell|read|solve|see|hear|wink|whistle|roll|snap|touch|do|lift|"
    r"run|swim|drive|speak|curl|move|raise|cross|bend|hold)|how many [\w' ]{1,30}can you|handed(ness)?|"
    r"live with (your )?(parents|family|mom|dad)|living with (your )?(parents|family)|how (much|many hours of) "
    r"(sleep|money)|how much do you (make|earn|weigh|sleep))", re.I)
# Options that split the vote by the voter's age or gender (a crosstab, not an answer).
CROSSTAB = re.compile(r"^(male|female|man|woman|men|women|guy|guys|girl|girls|boy|boys|m|f|nb|non-binary|age|under|"
                      r"over)\b|\b(i am|i'm|im) (a )?(man|woman|male|female|guy|girl|boy)\b|\b(age|aged)\s*\d|"
                      r"\d+\s*(yo|y/o|years old|or (older|younger))\b|\b(teen|teenager|adult)\b|"
                      r"\((male|female|m|f|men|women|guys?|girls?|us|uk|eu|non-?us|american|european|british|"
                      r"native|non-?native)\)|\b(male|female)$|\bnon-?(us|american|native|british)\b", re.I)
WOULD_SELF = re.compile(
    r"\b(would you|wyr|do you (prefer|like|enjoy|love|hate|dislike|want|use|eat|drink|play|watch|listen|read|"
    r"wear|sleep|shower|brush|cook|buy|call|say|pronounce|put|keep|go|feel|care|consider|identify|believe|trust|"
    r"usually|always|ever|still|often|rather|choose|pick)|which do you|what do you (prefer|like|use|eat|drink|call|"
    r"do|say|want|choose|pick|usually)|your (favou?rite|preferred|go-to|ideal|dream|choice|pick)|you prefer|"
    r"are you (a|an|more|team|into|for|pro|anti|in favou?r)|how do you|how often do you|when do you|where do you|"
    r"which (one )?would|who would you|what would you|if you (could|had|were)|could you|can you|will you|"
    r"have you|favou?rite|you rather)\b", re.I)
VALUES = re.compile(
    r"\b(should|moral\w*|immoral|ethic\w*|okay to|ok to|acceptable|right or wrong|wrong|justif\w*|fair|unfair|"
    r"deserve\w*|forgiv\w*|allowed|legal|illegal|ban|banned|punish\w*|steal|steals|stealing|stole|lie|lying|cheat\w*|"
    r"sacrifice|betray\w*|honest\w*|trolley|guilty|innocent|responsib\w*|obligat\w*|duty|rights?)\b", re.I)
SOCIAL = re.compile(
    r"\b(friends?|friendship|dat(e|es|ing)|partners?|boyfriend|girlfriend|bf|gf|spouse|husband|wife|marri\w*|"
    r"relationship\w*|crush|flirt\w*|family|parents?|siblings?|kids|children|coworker\w*|boss|neighbou?r\w*|"
    r"strangers?|rude|polite|manners|etiquette|tip|tipping|gift\w*|invite\w*|guests?|party|parties|text\w*|"
    r"apologi\w*|compliment\w*|hug\w*|kiss\w*|greet\w*|awkward|social\w*|introvert\w*|extrovert\w*)\b", re.I)
TASTE = re.compile(r"\b(like|likes|prefer\w*|favou?rite|enjoy\w*|love|hate|taste\w*|tasty|delicious|yummy|gross|"
                   r"flavou?r\w*|smell\w*|cute|beautiful|ugly|pretty|attractive|cool|fun|boring)\b", re.I)
BELIEF = re.compile(r"\b(believe|think|agree|disagree|opinion|consider|trust)\b", re.I)
PROFANE = re.compile(r"\b(fuck\w*|shit\w*|piss\w*|bitch\w*|cunt|asshole|dick)\b", re.I)
GARBLED = re.compile(r"\.{3,}|,{2,}|!{2,}|\?.*\?|\b(and|or) why\b|why or why not|\bexplain\b|\bwhy\?$", re.I)
EXPERIENCE = re.compile(
    r"\b(have|has|had) you (ever |already |)(killed|been|done|seen|played|tried|watched|read|eaten|beaten|finished|met|"
    r"visited|had|got|gotten|used|owned|lived|broken|won|lost|taken|heard|gone|made|bought|worn|cried|kissed)\b", re.I)
REPEAT = re.compile(r"\b(\w+) \1\b", re.I)


def _ascii(t: str) -> str:
    return unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode() if not t.isascii() else t


def _key(t: str) -> str:
    """snake_case key cut at a word boundary (<= 32 chars); the full option text goes in the description."""
    words, out = re.sub(r"[^a-z0-9]+", " ", t.lower()).split(), []
    for w in words:
        if out and len("_".join(out + [w])) > 32:
            break
        out.append(w)
    return "_".join(out)[:32].strip("_")


# The voter's own preference, habit or imagined choice -> self; an opinion about the world, even when phrased "do you
# think ...", -> world.
YOU = re.compile(r"\b(you|your|yours|yourself|u|ur)\b", re.I)
OPINION = re.compile(r"^(do|would|did) you (think|believe(?! in)|agree|consider|say|feel like)\b|^in your (opinion|view)\b|"
                     r"\b(do|would) you (think|believe|agree|consider|say)\b(?!.*\byour?\b)", re.I)


def _flair(p: dict) -> str:
    return EMOJI.sub("", re.sub(r":\w+:", "", p.get("link_flair_text") or "")).strip().lower() or "none"


def _clean_title(raw: str) -> str | None:
    t = html.unescape(raw or "")
    t = _ascii(EMOJI.sub("", t))
    t = " ".join(t.replace("’", "'").replace("“", '"').replace("”", '"').split())
    for _ in range(3):
        t2 = STRIP_PREFIX.sub("", t)
        if t2 == t:
            break
        t = t2
    t = WYR_ABBR.sub("Would you rather ", t).strip()
    t = re.sub(r"^would you rather\b", "Would you rather", t, flags=re.I)
    if TARGETED.match(t) and not OPENER.match(t):
        return None
    t = re.sub(r"\s*\((poll|serious|hypothetical|genuine question|just curious|curious)\)\s*$", "", t, flags=re.I)
    t = re.sub(r"[\s.]*\?+[\s!.?]*$", "?", t)
    if "?" not in t:
        if not OPENER.match(t) or re.search(r"[.!;]\s", t):
            return None
        t = t.rstrip(" .!:,") + "?"
    if t.count("?") != 1 or not t.endswith("?"):
        return None
    t = re.sub(r"\bu\b", "you", t)
    t = re.sub(r"\bur\b", "your", t)
    t = t[0].upper() + t[1:]
    if not (15 <= len(t) <= 220) or not t.isascii() or not OPENER.match(t):
        return None
    if sum(c.isupper() for c in t) > 0.5 * sum(c.isalpha() for c in t):
        return None
    words = t.split()
    if len(words) >= 5 and sum(w[:1].isupper() for w in words[1:]) >= 0.6 * (len(words) - 1):
        return None  # Title Case Titles
    return t


def _clean_opt(o: str) -> str:
    o = " ".join(EMOJI.sub("", html.unescape(o or "")).replace("’", "'").split()).strip(" .")
    return o[:1].upper() + o[1:]


def _kind(q: str, opts: str, self_q: bool) -> str:
    """values > social > (self: taste unless it asks for a belief; world: taste only for liking words) > evaluative."""
    if VALUES.search(q):
        return "values"
    if SOCIAL.search(q):
        return "social"
    if self_q:
        return "evaluative" if BELIEF.search(q) and not TASTE.search(q) else "taste"
    return "taste" if TASTE.search(q) else "evaluative"


def _parse(p: dict, sub: str) -> dict | None:
    pd = p.get("poll_data") or {}
    if p.get("over_18") or p.get("removed_by_category") or pd.get("is_prediction"):
        FUNNEL["1_nsfw_removed_or_prediction"] += 1
        return None
    flair = _flair(p)
    if flair in DROP_FLAIRS:
        FUNNEL["2_flair_dropped"] += 1
        return None
    opts = pd.get("options") or []
    if any(o.get("vote_count") is None for o in opts):
        FUNNEL["3_no_vote_counts"] += 1
        return None
    kept = [(_clean_opt(o.get("text")), int(o["vote_count"])) for o in opts
            if not RESULTS.search(o.get("text") or "")]
    kept = [(t, v) for t, v in kept if t]
    n = sum(v for _, v in kept)
    if not (2 <= len(kept) <= 6) or n < MIN_VOTES:
        FUNNEL["4_options_or_votes"] += 1
        return None
    q = _clean_title(p.get("title"))
    if not q:
        FUNNEL["5_title_not_a_question"] += 1
        return None
    opt_text = " | ".join(t for t, _ in kept)
    if CONTEXT.search(q) or REDDIT.search(q) or DATED.search(q) or DATED.search(opt_text) or \
            PERSONAL_FACT.search(q) or EXPERIENCE.search(q) or REPEAT.search(q) or GARBLED.search(q) or \
            any(RESULTS.search(t) or CROSSTAB.search(t) for t, _ in kept) or Q._typo(q, VOCAB):
        FUNNEL["6_context_personal_dated_or_meta"] += 1
        return None
    if SLURS.search(f"{q} {opt_text}") or MINORS_SEX.search(f"{q} {opt_text}"):
        FUNNEL["7_slur_or_minor_sexual"] += 1
        return None
    options: dict[str, str | None] = {}
    for t, _ in kept:
        k = _key(t)
        if not k or k in options:
            FUNNEL["8_bad_option_keys"] += 1
            return None
        options[k] = t if re.sub(r"[^a-z0-9]+", "_", t.lower()).strip("_") != k else None
    self_q = bool(WOULD_SELF.search(q) or YOU.search(q)) and not OPINION.search(q)
    flags = []
    if flair in POLITICAL_FLAIRS or POLITICAL.search(f"{q} {opt_text}") or POLITICAL_EXTRA.search(f"{q} {opt_text}"):
        flags.append("political")
    if SENSITIVE.search(f"{q} {opt_text}") or PROFANE.search(f"{q} {opt_text}"):
        flags.append("sensitive")
    ended = pd.get("voting_end_timestamp")
    return {
        "id": p["id"], "sub": sub, "q": q, "options": options,
        "dist": {k: v / n for k, (_, v) in zip(options, kept)}, "n": n,
        "hemisphere": "self" if self_q else "world", "kind": _kind(q, opt_text, self_q), "flags": flags,
        "flair": flair, "raw_title": p.get("title"),
        "created": dt.datetime.fromtimestamp(p["created_utc"], tz=dt.timezone.utc).strftime("%Y-%m-%d"),
        "closed_when_archived": bool(ended and p.get("retrieved_on") and p["retrieved_on"] * 1000 >= ended),
    }


VOCAB: Counter = Counter()


def _pool(raw_dir: Path) -> list[dict]:
    # typo check (quora_closed's): a lowercase word seen in fewer than 3 poll titles is treated as a misspelling
    VOCAB.clear()
    VOCAB.update(Q._vocab([json.loads(line).get("title") or "" for sub in SUBS
                           for f in sorted((raw_dir / sub).glob("*.jsonl")) for line in f.read_text().splitlines()]))
    best: dict[str, dict] = {}
    for sub in SUBS:
        for f in sorted((raw_dir / sub).glob("*.jsonl")):
            for line in f.read_text().splitlines():
                FUNNEL["0_polls"] += 1
                it = _parse(json.loads(line), sub)
                if not it:
                    continue
                key = re.sub(r"[^a-z0-9]+", " ", it["q"].lower()).strip()
                old = best.get(key)
                if old is None or (it["n"], it["id"]) > (old["n"], old["id"]):
                    if old is not None:
                        FUNNEL["9_duplicate_titles"] += 1
                    best[key] = it
                else:
                    FUNNEL["9_duplicate_titles"] += 1
    FUNNEL["10_pool"] = len(best)
    return list(best.values())


GROUP_CAP_PCT = env_int("REDDIT_POLLS_GROUP_CAP_PCT", 15)  # at most this share of the output from one flair
WYR_CAP_PCT = env_int("REDDIT_POLLS_WYR_CAP_PCT", 25)  # and from r/WouldYouRather


def normalize(raw_dir: Path) -> Iterator[Question]:
    pool = _pool(raw_dir)
    cap, wyr_cap = TARGET * GROUP_CAP_PCT // 100, TARGET * WYR_CAP_PCT // 100
    per: Counter = Counter()
    picked = []
    for it in hash_order(pool, lambda x: x["id"], SALT):
        if len(picked) >= TARGET:
            break
        g = f"{it['sub']}:{it['flair']}"
        if per[g] >= cap or (it["sub"] == "WouldYouRather" and per["wyr"] >= wyr_cap):
            continue
        per[g] += 1
        per["wyr"] += it["sub"] == "WouldYouRather"
        picked.append(it)
    FUNNEL["11_picked"] = len(picked)
    for it in sorted(picked, key=lambda x: x["id"]):
        meta = {"subreddit": it["sub"], "flair": it["flair"], "reddit_title": it["raw_title"], "created": it["created"],
                "closed_when_archived": it["closed_when_archived"]}
        if it["flags"]:
            meta["flags"] = it["flags"]
        yield Question(
            text=it["q"],
            primitive="choice",
            hemisphere=it["hemisphere"],
            kind=it["kind"],
            origin="dataset",
            source=NAME,
            options=it["options"],
            source_item_id=f"{it['sub']}:{it['id']}",
            license=LICENSE,
            human=[HumanDist(population=f"r/{it['sub']} voters", distribution=it["dist"], n=it["n"],
                             source="Reddit native poll vote counts (Arctic Shift archive; 'see results' options "
                                    "dropped, shares over the remaining options)")],
            meta=meta,
        )
    print("reddit_polls funnel:", dict(sorted(FUNNEL.items())))
    print("picked by group:", dict(per.most_common(25)))
