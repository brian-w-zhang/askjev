"""Quora closed questions: real yes/no and "which is better, A or B?" questions people asked on Quora.

Source: the Quora Question Pairs corpus as republished in sentence-transformers/quora-duplicates (pair-class:
sentence1, sentence2, label=duplicate). Every unique question string is a candidate; only single, standalone,
closed judgments survive a strict filter chain (see FUNNEL below). Yes/no questions become Noul; "Which is better,
A or B?" / "Who would win: A, B or C?" and "Would you rather A or B?" become Choice with A/B as the option keys.
No truth. Duplicate pairs (label=1) are merged with union-find and one question is kept per cluster.
"""

from __future__ import annotations

import hashlib
import re
import shutil
from collections import Counter
from pathlib import Path
from typing import Iterator

import httpx
import polars as pl

from askjev.model import Question
from askjev.sampling import env_int, hash_order

NAME = "quora_closed"
URL = ("https://huggingface.co/api/datasets/sentence-transformers/quora-duplicates/parquet/"
       "pair-class/train/0.parquet")
FILE = "pair-class.parquet"
LICENSE = "Quora Question Pairs (research use)"
TARGET = env_int("TARGET_QUORA_CLOSED", 10000)
WORLD_SHARE = env_int("QUORA_CLOSED_WORLD_PCT", 60) / 100  # world is at most this share of the output
SALT = "quora_closed-20260924"
WORLD_EXTRA = env_int("QUORA_CLOSED_WORLD_EXTRA", 0)  # extra world-only items appended after the base sample
MIN_WORD_FREQ = 3  # a lowercase word seen fewer times in the 537k questions is treated as a typo

FUNNEL: Counter = Counter()


def fetch(raw_dir: Path) -> None:
    out = raw_dir / FILE
    if out.exists():
        return
    legacy = raw_dir.parent / "quora" / FILE  # downloaded earlier under data/raw/quora/
    if legacy.exists():
        shutil.copyfile(legacy, out)
        return
    r = httpx.get(URL, follow_redirects=True, timeout=300)
    r.raise_for_status()
    out.write_bytes(r.content)


# --- text cleanup ----------------------------------------------------------------------------------------------
TAIL = re.compile(  # trailing follow-up clauses we may strip when the rest is a clean closed question
    r"\s*(if (so|yes|not|no)[, ]*(why|how|what|which|when|where|who)?( not)?|why( not)?|"
    r"why or why not|how( so)?|explain|please explain|and why|what do you think)\s*\??\s*$",
    re.I,
)
OR_NOT = re.compile(r",? or not\s*\?$", re.I)


def clean(q: str) -> str:
    q = q.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    q = " ".join(q.split()).strip()
    q = re.sub(r"\s+\?", "?", q)
    m = TAIL.search(q)
    if m and q[: m.start()].rstrip().endswith("?"):  # "Is X? Why?" -> "Is X?"
        q = q[: m.start()].rstrip()
    q = OR_NOT.sub("?", q)
    return q[:1].upper() + q[1:]


# --- filters ---------------------------------------------------------------------------------------------------
START = re.compile(
    r"^(is|are|was|were|do|does|did|can|could|should|will|would|has|have|had|which|who)\b", re.I)
PERSONAL_I = re.compile(r"\bI\b|\bi\b|\bI'|\bi'")
PERSONAL_W = re.compile(r"\b(me|my|mine|myself|im|ive)\b", re.I)
REQUEST = re.compile(
    r"^(can|could|would|will) (you|someone|somebody|anyone|anybody|u) (please |kindly )?"
    r"(help|suggest|tell|recommend|explain|give|name|share|list|provide|send|guide|refer|elaborate|describe|"
    r"answer|clarify|advise|let|show|point|write|post|check|review|rate|find|make|translate|identify|solve|"
    r"summarize|predict|draw|teach|buy|sell|lend|get|do)\b|"
    r"^(does|has|did|is|was|can|could|will|would|do) (anyone|anybody|someone|somebody|any one|any body)\b|"
    r"^(have|did|were|had) you\b|^(do|would) you (have|know|recommend|suggest|mind)\b|"
    r"^(is|are) (there|their) (any|some)\b(?! (evidence|proof|scientific|truth|chance|difference|link|"
    r"connection|possibility|limit|god|life|afterlife|such thing))|"
    r"^is there (a|an)\b(?! (god|afterlife|heaven|hell|limit|difference|link|connection|chance|scientific|"
    r"such thing|life|cure|conspiracy|correlation|relationship|free will))|"
    r"^(which|who) (are|is|was) (the )?(best|top|good|some|most|worst)\b(?!.*[,:] .+ or )",
    re.I,
)
QUORA = re.compile(r"\b(quora\w*|upvot\w*|downvot\w*|answer(ed|ing|s)? (this|my)|this question|a2a)\b", re.I)
HOMEWORK = re.compile(
    r"\b(prove|solve|equation|integral|integrate|derivative|differentiat\w+|divided by|divisible|factori[sz]\w*|"
    r"simplify|calculate|evaluate the|log ?\d|sin ?\d|cos ?\d|x ?\^|square root of \d|remainder|probability that)\b|"
    r"\d\s*[-+*/x×=^<>]\s*\d|[=^]",
    re.I,
)
CONTEXT = re.compile(  # needs something the reader can't see, or is pinned to a moment that has passed
    r"\b(this|these|those|above|below|following|attached|here|pic|picture|photo|image|screenshot|video|link|"
    r"today|tonight|tomorrow|yesterday|right now|at the moment|this year|next year|last year|upcoming|"
    r"recently|recent|latest|this week|next week|last week|this month|next month|this season)\b",
    re.I,
)
PRONOUN = re.compile(r"\b(he|she|him|her|his|hers)\b", re.I)
MULTI = re.compile(  # a second question hidden after a comma or "and"
    r"(,|;| and| but| also| if so| or)\s+(how|why|what|which|when|where|who|whom|whose|is it|are they|do they|"
    r"does it|can it|should|if)\b|\. [A-Z]|^should [^,]+, (would|will|can|could|is|are|do|does|what|how)\b",
    re.I,
)
ELECTION = re.compile(r"\b(win|wins|elect\w*|vote\w*|voting|nominee|nomination|candidate|primar(y|ies)|campaign|"
                      r"poll\w*|impeach\w*|re-?elected|next (us )?president|next prime minister|next pm)\b", re.I)
CANDIDATES = re.compile(r"\b(trump|clinton|hillary|sanders|bernie|cruz|rubio|kasich|gary johnson|jill stein|pence|kaine|"
                        r"romney|jeb|carson)\b", re.I)
YEAR = re.compile(r"\b20[0-2]\d\b")  # recent years date the question (hiring cycles, "by 2020", phone models)
MOSTLY = re.compile(r"[A-Za-z ]")
SLURS = re.compile(r"\b(fag\w*|nigg\w*|retard\w*|tranny|dyke|spics?|chinks?|kikes?|gooks?|paki)\b", re.I)
MINORS_SEX = re.compile(
    r"(?=.*\b(child|children|kids?|minors?|underage|teen\w*|\d{1,2} ?(year|yr)s? ?old|boys?|girls?)\b)"
    r"(?=.*\b(sex\w*|porn\w*|nude|naked|penis|vagina|masturbat\w*|erotic|molest\w*|rape\w*)\b)",
    re.I,
)

POLITICAL = re.compile(
    r"\b(trump\w*|clinton\w*|hillary|obama\w*|bernie|sanders|pence|biden|putin|modi\w*|namo|bjp|rss|"
    r"congress|rahul gandhi|gandhi|kejriwal|aap|jayalalitha\w*|yogi|owaisi|pm|prime minister|president\w*|"
    r"election\w*|elect\w*|vot\w+|ballot|campaign|democrat\w*|republican\w*|gop|liberal\w*|conservative\w*|"
    r"leftist\w*|left[- ]wing|right[- ]wing|alt[- ]right|libertarian\w*|socialis\w*|communis\w*|marx\w*|"
    r"fascis\w*|nazi\w*|hitler|feminis\w*|patriarch\w*|abortion\w*|pro[- ]life|pro[- ]choice|guns?|nra|"
    r"firearm\w*|bear arms|second amendment|2nd amendment|immigra\w*|refugee\w*|illegal alien\w*|deport\w*|border wall|"
    r"brexit|kashmir\w*|pakistan\w*|israel\w*|palestin\w*|zionis\w*|isis|terroris\w*|jihad\w*|islam\w*|muslim\w*|"
    r"hindu\w*|hindutva|christian\w*|jew\w*|judaism|sikh\w*|atheis\w*|religio\w*|caste|brahmin\w*|dalit\w*|reservation\w*|"
    r"racis\w*|racial|race|white people|black people|blm|black lives|lgbt\w*|gays?|lesbians?|homosexual\w*|queer|bisexual\w*|gay marriage|same[- ]sex|"
    r"transgender|demoneti[sz]ation|gst|note ban|black money|government|govt|policy|policies|politic\w*|"
    r"sanction\w*|war|(?<!star )wars|nuclear|north korea|china|chinese|taiwan|tibet|hong kong|russia\w*|ukrain\w*|"
    r"crimea|syria\w*|iran\w*|iraq\w*|saudi\w*|nationalis\w*|patriot\w*|anti-national|jnu|sedition|"
    r"capital punishment|death penalty|welfare|minimum wage|tax\w*|obamacare|healthcare|socialism|"
    r"climate change|global warming|vaccin\w*|censorship|free speech|affirmative action|police)\b",
    re.I,
)
SENSITIVE = re.compile(
    r"\b(sex\w*|porn\w*|nude|naked|penis\w*|vagina\w*|boob\w*|breasts?|dicks?|cocks?|pussy|tits|masturbat\w*|orgasm\w*|(?<!extra )virgin\w*|"
    r"erect\w*|ejaculat\w*|sperm|semen|condom\w*|horny|erotic\w*|fetish\w*|kinky|anal|oral|blow ?jobs?|blown|hook ?up|"
    r"prostitut\w*|escort\w*|stripper\w*|affair|cheat\w*|rape\w*|molest\w*|incest|"
    r"suicid\w*|self[- ]harm|kill (myself|yourself|themselves)|cutting|depress\w*|anxiety|bipolar|"
    r"schizo\w*|adhd|autis\w*|mental illness|eating disorder|anorexi\w*|bulimi\w*|"
    r"weed|marijuana|cannabis|pot|cocaine|heroin|meth\w*|lsd|mdma|ecstasy|shrooms|psilocybin|dmt|opioid\w*|"
    r"xanax|adderall|drugs?|alcohol\w*|drunk|smok\w*|cigarette\w*|vap\w*|"
    r"pain\w*|cancer\w*|tumou?r\w*|disease\w*|symptom\w*|pregnan\w*|period|periods|menstrua\w*|std|stds|hiv|"
    r"aids|herpes|infection\w*|diabet\w*|blood|bleed\w*|headache\w*|fever|virus|pills?|medication\w*|"
    r"dose|overdose|surgery|abortion\w*|miscarriage|fertility|infertil\w*|acne|rash|itch\w*|swollen|lump|"
    r"death|die|dying|dead|kill\w*|murder\w*|gore|violence)\b",
    re.I,
)

# --- choice parsing ---------------------------------------------------------------------------------------------
CHOICE = re.compile(  # the stem must compare: "Which is better", "Who would win", "Which is more dangerous"
    r"^(?P<stem>(which|who)( one)? (is|are|was|were|would be|would win|will win|will be)"
    r"(?=[^,:?]*\b(better|best|worse|worst|more|most|less|least|win|superior|\w{3,}er|\w{3,}est)\b)( [\w'-]+){0,6}?)"
    r"\s*[,:\-–]\s*(?P<opts>[^,:?]+(, [^,:?]+)*,? or [^,:?]+)\?$",
    re.I,
)
WYR = re.compile(r"^would you rather (?P<opts>[^,:?]+(, [^,:?]+)*,? or [^,:?]+)\?$", re.I)
OPT_BAD = re.compile(r"\b(for|to|in|with|as|when|if|while|because|than|which|who|that|and then)\b", re.I)


NON_OPTIONS = {"other", "others", "neither", "both", "none", "something else", "all", "all of them", "none of them",
               "any other", "anything else", "someone else", "else"}


def split_opts(s: str) -> list[str] | None:
    parts = re.split(r",? or |, ", s)
    parts = [p.strip(" .'\"").strip() for p in parts]
    if not 2 <= len(parts) <= 5:
        return None
    for p in parts:
        if not p or ";" in p or len(p) > 40 or len(p.split()) > 5 or OPT_BAD.search(p) or p.lower() in NON_OPTIONS:
            return None
    others = parts[:-1]
    last = parts[-1].split()
    if len(last) > max(len(p.split()) for p in others) and last[-1].islower() and \
            not any(last[-1] in p.split() for p in others):
        return None  # a shared tail noun ("Google or Yahoo maps", "fried or steamed dumplings")
    if len({p.lower() for p in parts}) != len(parts):
        return None
    return parts


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")[:40]


# --- tagging -----------------------------------------------------------------------------------------------------
VALUES = re.compile(
    r"\b(wrong|immoral|unethical|ethical|moral|morally|justified|justifiable|selfish|evil|a sin|sinful|cruel|"
    r"hypocritical|disrespectful|irresponsible|unfair)\b|^is it (ever )?(right|fair|just) to\b",
    re.I,
)
SOCIAL_JUDGE = re.compile(
    r"^(is|are|was) (it|this) (rude|weird|creepy|awkward|appropriate|inappropriate|polite|impolite|"
    r"embarrassing|attractive|unattractive|a red flag|a turn[- ]off|cheating)\b|"
    r"^is it (ever )?(ok|okay|acceptable|fine|alright|all right) for (a |an )?(\w+ )?(man|men|woman|women|guy|guys|"
    r"girl|girls|boy|boys|person|people|parents?|husband|wife|couple|teacher|friend|boss)\b|"
    r"^(is|are) (it|a|an|the)? ?\w* ?(\w+ )?(rude|creepy|awkward|polite|impolite|attractive|unattractive)\b",
    re.I,
)
SOCIAL = re.compile(
    r"\b(girlfriend|boyfriend|crush|dating|date|dates|friends?|friendship|marriage|married|marry|wife|husband|"
    r"relationships?|breakup|break up|flirt\w*|in love|parents?|siblings?|coworkers?|colleagues?|roommates?|"
    r"guys?|girls?|men|women|boss|people)\b",
    re.I,
)
TASTE = re.compile(
    r"^would you rather\b|^(do|would) you (like|love|enjoy|prefer|hate|dislike|listen|watch|read|play|wear)\b|"
    r"^(is|are|was|were) [^?]+ (beautiful|ugly|cute|sexy|delicious|tasty|attractive|pretty|handsome)\?$",
    re.I,
)
# "you" meaning the answerer (their opinion or choice), as opposed to the generic "you" of "Can you freeze sour cream?"
SELF_YOU = re.compile(
    r"^do you (think|believe|feel that|agree|consider|support|trust|like|prefer|enjoy|love|hate|dislike|"
    r"care about|find)\b|"
    r"^would you (?!(know|have|recommend|suggest|mind|help|please|be able|be interested|use|pay|buy|stay|download|"
    r"subscribe|install|sign up|register|visit|invest|hire|consider (using|buying|investing)|like to (use|try|buy|"
    r"join|invest))\b)\w+|"
    r"^are you (afraid|scared|happy|religious|superstitious|proud|satisfied|interested in|into|a fan of|an? "
    r"(introvert|extrovert|ambivert|morning|night|atheist|optimist|pessimist|feminist|vegetarian|vegan|cat|dog))\b",
    re.I,
)
GENERIC_YOU_OK = re.compile(  # generic-you factual questions ("Do you need a visa to ...")
    r"^do you (need|have to|get|gain|lose|require|pay|qualify|burn|still|really need)\b", re.I)
FORECAST = re.compile(
    r"^(will|is .* going to|are .* going to)\b|^would .* ever\b|\b(in the future|ever (be|become|happen|replace|"
    r"win|end|die|return|come back|go))\b",
    re.I,
)
EVAL = re.compile(
    r"\b(overrated|underrated|over-rated|worth\w*|a good idea|a bad idea|good idea|bad idea|better|worse|best|worst|"
    r"good|bad|useful|useless|necessary|beneficial|effective|ineffective|waste|smart|stupid|genius|great|"
    r"successful|failure|harmful|dangerous|safe|healthy|unhealthy|important|valuable|fake|scam|legit|reliable|"
    r"pointless|meaningful|superior|inferior|easy|hard|difficult|boring|interesting|fun|cool|impressive|"
    r"hype\w*|deserve\w*|fair|okay|ok|funny|talented|overhyped|advantage|boon|comparable)\b",
    re.I,
)


def tag(q: str, choice: bool) -> tuple[str, str]:
    """(hemisphere, kind): self = the answerer's own taste, values, social judgment or opinion; world otherwise."""
    if TASTE.search(q):
        return "self", "taste"
    if re.match(r"^should (you|one|we)\b", q, re.I) and not (VALUES.search(q) or POLITICAL.search(q)):
        return "world", "evaluative"  # practical advice ("Should you wash your hair every day?")
    if re.match(r"^should (you|one|we|people|men|women|guys|girls|parents|kids|children|students|everyone)\b", q, re.I):
        return "self", ("values" if VALUES.search(q) or POLITICAL.search(q) else "social")
    if re.match(r"^should (?!(it|this|there|a|an)\b)", q, re.I):  # policy / what-ought-to-happen judgments
        return "self", "values"
    if SELF_YOU.search(q):
        return "self", ("values" if VALUES.search(q) else "social" if SOCIAL.search(q) else
                        "forecast" if FORECAST.search(q) else "evaluative")
    if re.match(r"^(is|are|was|would) (it|this)\b", q, re.I) and VALUES.search(q):
        return "self", "values"
    if VALUES.search(q) and re.search(r"\b(wrong|immoral|unethical|ethical|moral|morally|evil|a sin|sinful)\b", q, re.I):
        return "self", "values"
    if SOCIAL_JUDGE.search(q):
        return "self", "social"
    if FORECAST.search(q):
        return "world", "forecast"
    if choice or EVAL.search(q):
        return "world", ("social" if SOCIAL.search(q) and not choice else "evaluative")
    if SOCIAL.search(q):
        return "world", "social"
    return "world", "factual"


# --- pool --------------------------------------------------------------------------------------------------------
def _vocab(texts: list[str]) -> Counter:
    c: Counter = Counter()
    for t in texts:
        c.update(set(re.findall(r"[a-z][a-z']*", t.lower())))
    return c


def _typo(q: str, vocab: Counter) -> bool:
    for w in re.findall(r"\b[a-z][a-z']*\b", q.split(" ", 1)[-1]):  # lowercase words after the first; names skipped
        if vocab[w.strip("'")] < MIN_WORD_FREQ:
            return True
    return False


def _keep(raw: str, vocab: Counter) -> dict | None:
    f = FUNNEL
    if not START.match(raw.strip()):
        return None
    f["1_closed_start"] += 1
    q = clean(raw)
    if not q.endswith("?") or q.count("?") != 1 or not 25 <= len(q) <= 160:
        return None
    f["2_single_question_len"] += 1
    if not q.isascii() or len(MOSTLY.findall(q)) / len(q) < 0.9 or re.search(r"([!.,-])\1|[\[\]{}<>|@#*_\\]", q):
        return None
    if _typo(q, vocab) or re.search(r"\b(u|ur|r|plz|pls|abt|wat|coz|bcoz|n)\b", q):
        return None
    f["3_clean_text"] += 1
    if PERSONAL_I.search(q) or PERSONAL_W.search(q):
        return None
    f["4_not_personal"] += 1
    if REQUEST.search(q) or QUORA.search(q):
        return None
    if re.match(r"^(do|are|would|will|could|can|should) you\b", q, re.I) and not (
            SELF_YOU.search(q) or GENERIC_YOU_OK.search(q) or re.match(r"^(can|could|should|will) you\b", q, re.I)):
        return None  # the answerer's habits or body ("Do you fart in the shower?")
    if re.match(r"^do you (like|love|hate|enjoy) (to|your)\b", q, re.I):
        return None  # the answerer's own life ("Do you like your in-laws?") or a sales pitch
    f["5_not_request_or_quora"] += 1
    if HOMEWORK.search(q):
        return None
    f["6_not_homework"] += 1
    if CONTEXT.search(q) or (PRONOUN.search(q) and not re.search(r"\s[A-Z]", q)):
        return None
    if YEAR.search(q) or ((FORECAST.search(q) or re.search(r"\b(will|going to)\b", q, re.I)) and ELECTION.search(q)) \
            or (re.search(r"^(should|will)\b|\b(will|going to)\b", q, re.I) and CANDIDATES.search(q)):
        return None  # pinned to a date or an election that has passed
    f["7_standalone_timeless"] += 1
    if SLURS.search(q) or MINORS_SEX.search(q):
        return None
    f["8_not_slur_or_minor_sexual"] += 1

    m = CHOICE.match(q) or WYR.match(q)
    if m:
        opts = split_opts(m.group("opts"))
        if not opts:
            return None
        if m.re is WYR and len(opts) == 2:  # "rather have a brother or a sister" -> "a brother" / "a sister"
            v = opts[0].split()[0].lower()
            if v in {"be", "have", "get", "own", "live", "eat", "date", "marry", "meet"} and \
                    opts[1].split()[0].lower() != v and len(opts[0].split()) > 1:
                opts[0] = opts[0].split(" ", 1)[1]
        f["9_shape_ok"] += 1
        return {"q": q, "primitive": "choice", "opts": opts}
    if re.match(r"^(which|who)\b", q, re.I):
        return None  # open wh-question that didn't parse as A-or-B
    if MULTI.search(q) or re.search(r"\bor\b", q, re.I):
        return None  # hidden second question, or an either/or asked as yes/no
    if re.match(r"^(do|does|did|can|could|will|would|should|are|were|have|had) (they|them)\b|"
                r"^(is|are) (best|better|good|worth|necessary|possible)\b", q, re.I):
        return None  # subject is an unseen antecedent
    f["9_shape_ok"] += 1
    return {"q": q, "primitive": "noul", "opts": None}


def _norm_key(q: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", q.lower()).strip()


def _pool(raw_dir: Path) -> list[dict]:
    df = pl.read_parquet(raw_dir / FILE)
    s1, s2, lab = df["sentence1"].to_list(), df["sentence2"].to_list(), df["label"].to_list()
    uniq = sorted({q for q in s1 + s2 if q})
    FUNNEL["0_unique_questions"] = len(uniq)
    vocab = _vocab(uniq)

    parent: dict[str, str] = {}

    def find(x: str) -> str:
        while parent.get(x, x) != x:
            parent[x] = parent.get(parent[x], parent[x])
            x = parent[x]
        return x

    for a, b, l in zip(s1, s2, lab):
        if l == 1 and a and b:
            ra, rb = find(a), find(b)
            if ra != rb:
                parent[max(ra, rb)] = min(ra, rb)

    kept: dict[str, dict] = {}  # one per duplicate cluster and per normalized text; first in hash order wins
    for raw in hash_order(uniq, lambda x: x, SALT + "-dedupe"):
        it = _keep(raw, vocab)
        if not it:
            continue
        cluster, nk = find(raw), _norm_key(it["q"])
        if cluster in kept or nk in kept:
            FUNNEL["10_duplicates_dropped"] += 1
            continue
        it["raw"] = raw
        kept[cluster] = kept[nk] = it
    pool = list({id(v): v for v in kept.values()}.values())
    FUNNEL["11_after_dedupe"] = len(pool)
    return pool


def normalize(raw_dir: Path) -> Iterator[Question]:
    pool = _pool(raw_dir)
    for it in pool:
        it["hemisphere"], it["kind"] = tag(it["q"], it["primitive"] == "choice")
    self_pool = [x for x in pool if x["hemisphere"] == "self"]
    world_pool = [x for x in pool if x["hemisphere"] == "world"]
    n_world = min(len(world_pool), int(TARGET * WORLD_SHARE))
    n_self = min(len(self_pool), TARGET - n_world)
    if n_self < TARGET - n_world:  # self runs short: shrink world so it stays at most WORLD_SHARE of the total
        n_world = min(n_world, int(n_self * WORLD_SHARE / (1 - WORLD_SHARE)))
    world_order = hash_order(world_pool, lambda x: x["raw"], SALT)
    picked = hash_order(self_pool, lambda x: x["raw"], SALT)[:n_self] + world_order[:n_world]
    extra = world_order[n_world:n_world + WORLD_EXTRA]  # appended after the base rows so their order is untouched
    FUNNEL.update({"12_pool_self": len(self_pool), "12_pool_world": len(world_pool),
                   "13_picked_self": n_self, "13_picked_world": n_world, "14_world_extra": len(extra)})

    for it in sorted(picked, key=lambda x: x["raw"]) + sorted(extra, key=lambda x: x["raw"]):
        q = it["q"]
        flags = []
        if POLITICAL.search(q):
            flags.append("political")
        if SENSITIVE.search(q):
            flags.append("sensitive")
        meta = {"quora_text": it["raw"]}
        if flags:
            meta["flags"] = flags
        options = None
        if it["primitive"] == "choice":
            options = {slug(o): o for o in it["opts"]}
            if len(options) != len(it["opts"]):
                continue
        yield Question(
            text=q,
            primitive=it["primitive"],
            hemisphere=it["hemisphere"],
            kind=it["kind"],
            origin="dataset",
            source=NAME,
            options=options,
            source_item_id=hashlib.sha1(it["raw"].encode()).hexdigest()[:16],
            license=LICENSE,
            meta=meta,
        )
    print("quora_closed funnel:", dict(sorted(FUNNEL.items())))
