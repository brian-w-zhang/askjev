"""WildChat closed questions: real closed questions people typed to an AI chatbot as their opening message.

Source: allenai/WildChat-1M (ODC-BY, ungated on Hugging Face): 837k logged ChatGPT conversations. fetch() streams
each of the 14 shards once and keeps only the first user turn of English, non-toxic, non-redacted conversations
whose first turn is short (<= 300 chars) and not flagged by the OpenAI moderation pass; the big shard is deleted.

normalize() runs the quora_closed filter chain on each distinct opening message (greetings like "Hi," / "Hey
there!" stripped first) plus a chatbot-specific path for questions addressed to the assistant itself ("Do you
have feelings?", "Are you conscious?", "Would you rather be a cat or a dog?"), which quora_closed rejects as
requests. Single closed questions only: yes/no -> Noul, "Which is better, A or B?" / "Would you rather A or B?" /
"What's your favorite X: A, B or C?" -> Choice with the listed options as keys. No node_hint (beam walk), no truth.
"""

from __future__ import annotations

import gzip
import importlib.util
import json
import re
from collections import Counter
from pathlib import Path
from typing import Iterator

import httpx
import polars as pl

from askjev.model import Question
from askjev.sampling import env_int, hash_order

NAME = "wildchat_closed"
BASE = "https://huggingface.co/datasets/allenai/WildChat-4.8M/resolve/main/data/train-{i:05d}-of-00086.parquet"
N_SHARDS = 86
LICENSE = "ODC-BY (allenai/WildChat-4.8M)"
TARGET = env_int("TARGET_WILDCHAT_CLOSED", 10000)
SELF_PCT = env_int("WILDCHAT_CLOSED_SELF_PCT", 45) / 100  # self share target (taken first; world fills the rest)
SALT = "wildchat_closed-20260925"
MAX_CHARS = 300
# Supplements (WildChat alone yields only ~1,800 closed openers): first human turns of Anthropic HH-RLHF's helpful
# subsets (crowdworkers talking to an assistant; the red-team harmless subsets are not used), first prompter turns
# of OpenAssistant oasst2, and Dolly open/general QA and classification instructions.
HH_SUBSETS = ("helpful-base", "helpful-online", "helpful-rejection-sampled")
HH_URL = "https://huggingface.co/datasets/Anthropic/hh-rlhf/resolve/main/{subset}/{split}.jsonl.gz"
EXTRA = {
    "hh_rlhf": (HH_URL, ("train", "test"), "MIT (Anthropic/hh-rlhf)"),
    "oasst2": ("https://huggingface.co/api/datasets/OpenAssistant/oasst2/parquet/default/{split}/0.parquet",
               ("train", "validation"), "Apache-2.0 (OpenAssistant/oasst2)"),
    "dolly": ("https://huggingface.co/api/datasets/databricks/databricks-dolly-15k/parquet/default/{split}/0.parquet",
              ("train",), "CC-BY-SA-3.0 (databricks/databricks-dolly-15k)"),
}

# quora_closed's filters and tagger, loaded as a private module copy so the fixes below don't touch quora_closed.
_spec = importlib.util.spec_from_file_location("wildchat_quora_filters",
                                               Path(__file__).parents[1] / "quora_closed" / "adapter.py")
Q = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(Q)
# quora_closed's `elect\w*` also matches electric/electron/electricity; narrow it to the election sense.
_ELECT_FIX = r"elect(s|ed|ing|or\w*|oral|ion\w*)?"
Q.POLITICAL = re.compile(Q.POLITICAL.pattern.replace(r"elect\w*", _ELECT_FIX), re.I)
Q.ELECTION = re.compile(Q.ELECTION.pattern.replace(r"elect\w*", _ELECT_FIX), re.I)
POLITICAL, SENSITIVE = Q.POLITICAL, Q.SENSITIVE
Q.MIN_WORD_FREQ = 5  # chat prompts are typo-heavier than Quora titles

FUNNEL: Counter = Counter()


def _shard_prompts(path: Path) -> pl.DataFrame:
    df = pl.read_parquet(path, columns=["conversation_hash", "conversation", "language", "toxic", "redacted",
                                        "openai_moderation", "timestamp"])
    df = df.filter((pl.col("language") == "English") & ~pl.col("toxic") & ~pl.col("redacted"))
    first = pl.col("conversation").list.first().struct
    mod = pl.col("openai_moderation").list.first().struct
    return (
        df.with_columns(prompt=first.field("content"), role=first.field("role"), flagged=mod.field("flagged"))
        .filter((pl.col("role") == "user") & ~pl.col("flagged").fill_null(False)
                & (pl.col("prompt").str.len_chars() <= MAX_CHARS))
        .select("conversation_hash", "prompt", "timestamp")
    )


def fetch(raw_dir: Path) -> None:
    raw_dir.mkdir(parents=True, exist_ok=True)
    for subset in HH_SUBSETS:
        for split in EXTRA["hh_rlhf"][1]:
            out = raw_dir / f"hh_{subset}_{split}.jsonl.gz"
            if not out.exists():
                r = httpx.get(HH_URL.format(subset=subset, split=split), follow_redirects=True, timeout=600)
                r.raise_for_status()
                out.write_bytes(r.content)
    for name, (url, splits, _) in EXTRA.items():
        if name == "hh_rlhf":
            continue
        for split in splits:
            out = raw_dir / f"{name}_{split}.parquet"
            if not out.exists():
                r = httpx.get(url.format(split=split), follow_redirects=True, timeout=600)
                r.raise_for_status()
                out.write_bytes(r.content)
    for i in range(N_SHARDS):
        out = raw_dir / f"prompts_{i:02d}.parquet"
        if out.exists():
            continue
        shard = raw_dir / f"shard{i:02d}.parquet"
        if not shard.exists():
            tmp = shard.with_suffix(".part")
            with httpx.stream("GET", BASE.format(i=i), follow_redirects=True, timeout=600) as r:
                r.raise_for_status()
                with open(tmp, "wb") as fh:
                    for chunk in r.iter_bytes(1 << 20):
                        fh.write(chunk)
            tmp.rename(shard)
        _shard_prompts(shard).write_parquet(out)
        shard.unlink()


# --- chatbot-specific cleanup ------------------------------------------------------------------------------------
GREETING = re.compile(
    r"^((hi|hello|hey|hey there|hi there|hello there|yo|greetings|good (morning|afternoon|evening)|dear chatgpt|"
    r"ok|okay|so|chatgpt|gpt|bot|quick question|question)\b[\s,.!:;-]*)+", re.I)
POLITE = re.compile(r"^(please|pls|can you (please )?)?(answer|tell me)( with)?( only)?( a)?( yes or no| in one word)?"
                    r"[\s,.:;-]+", re.I)
TRAILER = re.compile(r"\s*(\(?(answer|reply|respond)( only)?( with)? (yes|one word|a single word|in one word)[^?]*\)?"
                     r"|(just|only) (answer|say) (yes or no|one word))\s*[.!]?$", re.I)
# about the assistant itself: its nature, preferences, experiences, abilities
ASSISTANT = re.compile(  # about the assistant's own nature, experience or preferences
    r"^(are|were) you (really |actually |truly |ever |even )?(alive|conscious|sentient|human|real|a (robot|person|"
    r"machine|program|bot|human)|self-aware|happy|sad|lonely|bored|tired|afraid|scared|intelligent|smart|creative|"
    r"funny|god|capable of (love|feelings?|emotions?|thought|thinking|lying|suffering))\b|"
    r"^(do|did|can|could|will|would) you (ever |really |actually |truly |still )?(feel|have (feelings|emotions|a soul|"
    r"free will|consciousness|a sense of humou?r|opinions|preferences|a favou?rite \w+|friends|fears|dreams|desires|"
    r"a gender|a name|a personality|beliefs)|dream|sleep|suffer|get (lonely|bored|tired|sad|angry|annoyed)|"
    r"fear|love|hate|like|enjoy|prefer|want to (be|live|exist|have|feel|die|become)|wish (you|for|that)|lie|die|"
    r"think for yourself|believe in god|pray)\b", re.I)
# Chatbot-specific rejects on the quora path: "can you <verb>" is a task request unless the verb is a generic-you
# fact ("Can you freeze cooked rice?"); programming/tool minutiae; Title Case prompt-template lines.
GENERIC_YOU_VERB = re.compile(
    r"^(can|could) you (still |safely |really |legally )?(freeze|refreeze|eat|drink|get|catch|die|survive|reheat|"
    r"mix|see|hear|smell|taste|travel|fly|drive|swim|grow|cook|bake|live|become|breathe|sleep|walk|buy|own|marry|"
    r"visit|lose|gain|recover|overdose|wash|store|microwave|boil|fry|build|swallow|inherit|vote|work|study|enter|"
    r"go|be|have|burn|feel|sue|patent|trademark|copyright|recycle|compost|plant|train|teach|learn|cure|prevent|"
    r"reverse|tell if|tell whether|tell the difference|get pregnant|get sick|get fat)\b", re.I)
TECH = re.compile(
    r"\b(sql|api|apis|python|java|javascript|typescript|c\+\+|c#|rust|golang|php|ruby|kotlin|swift|linux|ubuntu|"
    r"windows \d+|pip|npm|docker|git|github|aws|s3|azure|postgres\w*|mysql|mongodb|redis|react|angular|vue|django|"
    r"flask|node(js)?|html|css|json|xml|yaml|regex|bash|shell|excel|vba|powershell|kubernetes|function|variable|"
    r"array|method|class|code|script|compile\w*|library|framework|database|server|query|dataframe|pandas|numpy|"
    r"tensorflow|pytorch|keras|unity|unreal|godot|chatgpt|gpt\S*|openai|llm|tokens?|prompt|plugin|module|package|"
    r"loop|syntax|endpoint|http\w*|url|ssh|dns|ip|vpn|router|cpu|gpu|ram|laravel|spring|dotnet|\.net|matlab|"
    r"arduino|esp32|raspberry|android|ios|app|apps|software|firmware|driver|browser|chrome|firefox|pdf|csv|"
    r"kernel|sysctl|lambda|async|thread|struct|pointer|recursion|algorithm|model|models|dataset|training)\b", re.I)


def _chat_reject(q: str) -> bool:
    if re.match(r"^(can|could|will|would) you\b", q, re.I) and not GENERIC_YOU_VERB.match(q):
        return True
    if TECH.search(q) and not Q.CHOICE.match(q):
        return True
    words = q.split()
    if len(words) >= 5 and sum(w[:1].isupper() for w in words) / len(words) >= 0.6:
        return True
    if re.search(r"\b(?![aAI]\b)[a-z]\b", q):  # stray single letters: "make muscle h rd"
        return True
    return False


ASSISTANT_REQUEST = re.compile(  # "do you know / can you write" asks for a task, not about the assistant
    r"^(do you know|can you (write|make|help|tell|give|explain|generate|create|list|translate|summarize|rewrite|"
    r"describe|provide|show|find|suggest|recommend|name|draw|code|do|please|continue|act|pretend|play|roleplay|"
    r"be my|imagine|answer)|could you|would you (please|mind|be able|help|write|kindly)|will you (please|help|"
    r"write|be my|marry|go)|have you (heard|seen|read|watched|played|been trained)|do you (have|need) (access|"
    r"internet|a (list|link|name|website))|are you (able|there|ready|familiar|aware of (the|a|any)|gpt|chatgpt|"
    r"gpt-?\d|using|connected|up to date|updated|online|free|still|working|down))\b", re.I)
FAVORITE = re.compile(r"^what('s| is) your (favou?rite|preferred) (?P<what>[\w' -]{2,30}?)\s*[,:\-–]\s*"
                      r"(?P<opts>[^,:?]+(, [^,:?]+)*,? or [^,:?]+)\?$", re.I)


def _prep(raw: str) -> str | None:
    s = " ".join(raw.split())
    if not s or "\n" in raw.strip():
        return None
    s = GREETING.sub("", s).strip()
    s = POLITE.sub("", s).strip()
    s = TRAILER.sub("", s).strip()
    if not s:
        return None
    s = s[0].upper() + s[1:]
    s = re.sub(r"\?+$", "?", s)
    return Q.clean(s)


def _assistant_q(q: str, vocab: Counter) -> dict | None:
    """Closed questions addressed to the assistant about itself, which quora_closed rejects as requests."""
    if not q.endswith("?") or q.count("?") != 1 or not 12 <= len(q) <= 140:
        return None
    if not q.isascii() or re.search(r"([!.,-])\1|[\[\]{}<>|@#*_\\]", q) or Q._typo(q, vocab):
        return None
    if Q.PERSONAL_I.search(q) or Q.PERSONAL_W.search(q) or Q.HOMEWORK.search(q) or Q.CONTEXT.search(q):
        return None
    if Q.SLURS.search(q) or Q.MINORS_SEX.search(q) or Q.MULTI.search(q):
        return None
    m = FAVORITE.match(q) or Q.WYR.match(q)
    if m:
        opts = Q.split_opts(m.group("opts"))
        return {"q": q, "primitive": "choice", "opts": opts, "self": True} if opts else None
    if ASSISTANT_REQUEST.search(q) or not ASSISTANT.search(q) or re.search(r"\bor\b", q, re.I):
        return None
    return {"q": q, "primitive": "noul", "opts": None, "self": True}


def _assistant_kind(q: str, choice: bool) -> str:
    if choice or re.search(r"\b(favou?rite|like|love|hate|enjoy|prefer|rather)\b", q, re.I):
        return "taste"
    if Q.VALUES.search(q):
        return "values"
    if re.search(r"\b(friends?|lonely|humans?|people)\b", q, re.I):
        return "social"
    return "personality"


def _hh_prompts(raw_dir: Path) -> pl.DataFrame:
    ids, prompts, seen = [], [], set()
    for subset in HH_SUBSETS:
        for split in EXTRA["hh_rlhf"][1]:
            with gzip.open(raw_dir / f"hh_{subset}_{split}.jsonl.gz", "rt", encoding="utf-8") as fh:
                for i, line in enumerate(fh):
                    m = re.match(r"\s*Human: (.*?)\n\nAssistant:", json.loads(line)["chosen"], re.S)
                    if not m:
                        continue
                    t = m.group(1).strip()
                    if t in seen or len(t) > MAX_CHARS:
                        continue
                    seen.add(t)
                    ids.append(f"hh:{subset}/{split}:{i}")
                    prompts.append(t)
    return pl.DataFrame({"conversation_hash": ids, "prompt": prompts, "dataset": ["hh_rlhf"] * len(ids)})


def _extra_prompts(raw_dir: Path) -> pl.DataFrame:
    frames = [_hh_prompts(raw_dir)]
    oa = pl.concat([pl.read_parquet(raw_dir / f"oasst2_{sp}.parquet") for sp in EXTRA["oasst2"][1]])
    oa = oa.filter(pl.col("parent_id").is_null() & (pl.col("lang") == "en") & ~pl.col("deleted")
                   & (pl.col("role") == "prompter") & (pl.col("text").str.len_chars() <= MAX_CHARS))
    frames.append(oa.select(conversation_hash=pl.lit("oasst2:") + pl.col("message_id"), prompt=pl.col("text"),
                            dataset=pl.lit("oasst2")))
    do = pl.read_parquet(raw_dir / "dolly_train.parquet").with_row_index("i")
    do = do.filter(pl.col("category").is_in(["open_qa", "general_qa", "classification"])
                   & (pl.col("context").str.len_chars() == 0) & (pl.col("instruction").str.len_chars() <= MAX_CHARS))
    frames.append(do.select(conversation_hash=pl.lit("dolly:") + pl.col("i").cast(pl.String),
                            prompt=pl.col("instruction"), dataset=pl.lit("dolly")))
    return pl.concat(frames)


def _pool(raw_dir: Path) -> list[dict]:
    df = pl.concat([pl.read_parquet(p) for p in sorted(raw_dir.glob("prompts_*.parquet"))])
    FUNNEL["0_first_turns"] = df.height
    df = df.sort("timestamp", "conversation_hash").unique("prompt", keep="first", maintain_order=True)
    FUNNEL["0b_distinct_prompts"] = df.height
    df = pl.concat([df.select("conversation_hash", "prompt", dataset=pl.lit("wildchat")), _extra_prompts(raw_dir)])
    df = df.unique("prompt", keep="first", maintain_order=True)  # WildChat wins a tie
    FUNNEL["0c_with_supplements"] = df.height
    prompts = df["prompt"].to_list()
    hashes = df["conversation_hash"].to_list()
    datasets = df["dataset"].to_list()
    vocab = Q._vocab(prompts)
    kept: dict[str, dict] = {}
    for raw, h, ds in zip(prompts, hashes, datasets):
        s = _prep(raw)
        if not s:
            continue
        FUNNEL["1_single_line"] += 1
        it = _assistant_q(s, vocab)
        if it is None:
            it = Q._keep(s, vocab)
            if it is not None and _chat_reject(it["q"]):
                FUNNEL["1b_chat_reject"] += 1
                it = None
            if it is not None:
                it["self"] = False
        if not it:
            continue
        nk = Q._norm_key(it["q"])
        if nk in kept:
            FUNNEL["2_dupes"] += 1
            continue
        it["raw"], it["hash"], it["dataset"] = raw, h, ds
        FUNNEL["3_kept_" + ds] += 1
        kept[nk] = it
    FUNNEL["3_kept"] = len(kept)
    return list(kept.values())


def normalize(raw_dir: Path) -> Iterator[Question]:
    pool = _pool(raw_dir)
    for it in pool:
        choice = it["primitive"] == "choice"
        if it["self"]:
            it["hemisphere"], it["kind"] = "self", _assistant_kind(it["q"], choice)
        else:
            it["hemisphere"], it["kind"] = Q.tag(it["q"], choice)
    self_pool = [x for x in pool if x["hemisphere"] == "self"]
    world_pool = [x for x in pool if x["hemisphere"] == "world"]
    n_self = min(len(self_pool), int(TARGET * SELF_PCT))
    n_world = min(len(world_pool), TARGET - n_self)
    picked = (hash_order(self_pool, lambda x: x["hash"], SALT)[:n_self]
              + hash_order(world_pool, lambda x: x["hash"], SALT)[:n_world])
    FUNNEL.update({"4_pool_self": len(self_pool), "4_pool_world": len(world_pool),
                   "5_picked_self": n_self, "5_picked_world": n_world})
    for it in sorted(picked, key=lambda x: x["hash"]):
        q = it["q"]
        flags = [f for f, rx in (("political", POLITICAL), ("sensitive", SENSITIVE)) if rx.search(q)]
        meta = {"dataset": it["dataset"], "prompt": it["raw"]}
        if it["self"]:
            meta["addressed_to_assistant"] = True
        if flags:
            meta["flags"] = flags
        options = None
        if it["primitive"] == "choice":
            options = {Q.slug(o): o for o in it["opts"]}
            if len(options) != len(it["opts"]) or not all(options):
                continue
        yield Question(
            text=q,
            primitive=it["primitive"],
            hemisphere=it["hemisphere"],
            kind=it["kind"],
            origin="dataset",
            source=NAME,
            options=options,
            source_item_id=it["hash"],
            license=EXTRA[it["dataset"]][2] if it["dataset"] in EXTRA else LICENSE,
            meta=meta,
        )
    print("wildchat_closed funnel:", dict(sorted(FUNNEL.items())))
