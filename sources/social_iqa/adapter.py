"""Social IQa (Sap et al. 2019, AllenAI, CC-BY-4.0): three-way commonsense questions about people's motives,
reactions and next steps in a short everyday situation. Asked as Choice over the three answer texts, with the
situation in state and the dataset's gold answer as truth."""

from __future__ import annotations

import io
import json
import re
import zipfile
from pathlib import Path
from typing import Iterator

import httpx

from askjev.model import Question
from askjev.sampling import env_int, hash_order

NAME = "social_iqa"
URL = "https://storage.googleapis.com/ai2-mosaic/public/socialiqa/socialiqa-train-dev.zip"
LICENSE = "CC-BY-4.0 (allenai/social_i_qa)"
TARGET = env_int("TARGET_SOCIAL_IQA", 5000)
SALT = "social_iqa-v1"
DIR = "socialiqa-train-dev"
SPLITS = ("train", "dev")
KEYS = ("answerA", "answerB", "answerC")

WH = re.compile(r"^(What's|What|How|Why|Where|When|Who)\b")
SEXUAL = re.compile(
    r"\b(sex\w*|porn\w*|nudes?|naked|orgasm\w*|virgin\w*|erotic\w*|condoms?|horny|seduc\w*|topless|strip(per|ping)|"
    r"make out|made out|making out|slept with|sleep with|one night stand|hook(ed)? up)\b", re.I)
SELF_HARM = re.compile(r"\b(suicid\w*|kill(ed|ing)? (him|her|them)sel(f|ves)|self[- ]harm\w*|overdos\w*)\b", re.I)
VIOLENT = re.compile(r"\b(murder\w*|rap(e|ed|ing)|stab\w*|shot|shoot\w*|molest\w*|assault\w*|strangl\w*)\b", re.I)
POLITICAL = re.compile(r"\b(abortion|republican\w*|democrat\w*|election|vot(e|ed|ing) for|immigra\w*|gun control|trump|biden|obama)\b", re.I)

NODES = [  # (regex over context + question + answers, node) — first match wins
    (re.compile(r"\b(boyfriend|girlfriend|wife|husband|spouse|fianc\w*|married|marry|marriage|wedding|anniversary|"
                r"partner|romantic|in love|divorc\w*)\b", re.I), "self.love.romance_partnership"),
    (re.compile(r"\b(date|dated|dating|crush|flirt\w*|kiss\w*|asked \w+ out|ask \w+ out|prom)\b", re.I),
     "self.love.dating_attraction"),
    (re.compile(r"\b(mom|mother|dad|father|parents?|sister|brother|siblings?|son|daughter|kids|children|"
                r"grand(ma|pa|mother|father|parents?)|aunt|uncle|cousin|family|niece|nephew)\b", re.I),
     "self.love.family_parenting"),
    (re.compile(r"\b(coworkers?|co-workers?|boss|manager|employees?|office|colleagues?|job|work|shift|customers?|"
                r"clients?|teacher|class|classmates?|professor|school|neighbou?rs?|roommates?|team ?mates?|coach)\b", re.I),
     "self.love.workplace_community"),
    (re.compile(r"\b(friends?|friendship|best friend|buddy|pal)\b", re.I), "self.love.friendship"),
    (re.compile(r"\b(thank\w*|apologi\w*|sorry|gift|present|polite\w*|rude\w*|manners|tip|invite\w*|invitation|"
                r"hosted|guests?|party|greet\w*|late)\b", re.I), "self.love.etiquette_social_norms"),
]


def fetch(raw_dir: Path) -> None:
    if all((raw_dir / DIR / f"{s}.jsonl").exists() for s in SPLITS):
        return
    r = httpx.get(URL, follow_redirects=True, timeout=300)
    r.raise_for_status()
    (raw_dir / Path(URL).name).write_bytes(r.content)
    zf = zipfile.ZipFile(io.BytesIO(r.content))
    zf.extractall(raw_dir, members=[m for m in zf.namelist() if not m.startswith("__MACOSX")])


def _clean(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def _slug(s: str, maxlen: int = 40) -> str:
    words = re.findall(r"[a-z0-9]+", s.lower().replace("'", ""))
    k = ""
    for w in words:
        if len(k) + len(w) + 1 > maxlen:
            break
        k = f"{k}_{w}" if k else w
    return k or (words[0][:maxlen] if words else "")


def _keys(opts: list[str]) -> list[str] | None:
    for n in (40, 60, 90):
        keys = [_slug(o, n) for o in opts]
        if all(keys) and len(set(keys)) == len(keys):
            return keys
    return None


def _text(question: str) -> str | None:
    q = _clean(question)
    if not WH.match(q):
        return None
    q = re.sub(r"\bOthers\b", "others", q)
    q = q[0].lower() + q[1:]
    if not q.endswith("?"):
        q = q.rstrip(".") + "?"
    return f"In `context`, {q}"


def _rows(raw_dir: Path) -> list[dict]:
    out = []
    for split in SPLITS:
        lines = (raw_dir / DIR / f"{split}.jsonl").read_text(encoding="utf-8").splitlines()
        labels = (raw_dir / DIR / f"{split}-labels.lst").read_text().split()
        assert len(lines) == len(labels), split
        for i, (ln, lab) in enumerate(zip(lines, labels)):
            d = json.loads(ln)
            d.update(split=split, idx=i, label=int(lab))
            out.append(d)
    return out


def normalize(raw_dir: Path) -> Iterator[Question]:
    pool = []
    seen = set()
    for d in _rows(raw_dir):
        ctx = _clean(d["context"])
        ctx = ctx[:1].upper() + ctx[1:]
        text = _text(d["question"])
        opts = [_clean(d[k]) for k in KEYS]
        if not text or len(ctx) < 10 or "{" in ctx or not all(opts):
            continue
        keys = _keys(opts)
        if keys is None:
            continue
        dup = (ctx.lower(), text.lower(), tuple(sorted(keys)))
        if dup in seen:
            continue
        seen.add(dup)
        pool.append((d, ctx, text, opts, keys))

    for d, ctx, text, opts, keys in hash_order(pool, key=lambda x: f"{x[0]['split']}|{x[0]['idx']}", salt=SALT)[:TARGET]:
        blob = " ".join([ctx, d["question"], *opts])
        flags = []
        if SEXUAL.search(blob) or SELF_HARM.search(blob) or VIOLENT.search(blob):
            flags.append("sensitive")
        if POLITICAL.search(blob):
            flags.append("political")
        node = next((n for rx, n in NODES if rx.search(blob)), "self.love")
        meta = {"split": d["split"], "question": _clean(d["question"])}
        if flags:
            meta["flags"] = flags
        yield Question(
            text=text,
            primitive="choice",
            hemisphere="self",
            kind="social",
            origin="dataset",
            source=NAME,
            options={k: o for k, o in zip(keys, opts)},
            state={"context": ctx},
            node_hint=node,
            source_item_id=f"{d['split']}:{d['idx']}",
            license=LICENSE,
            truth=keys[d["label"] - 1],
            meta=meta,
        )
