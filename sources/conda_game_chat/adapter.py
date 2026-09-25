"""CONDA (Weld et al., ACL 2021): 45K utterances from the chat logs of 1.9K Dota 2 matches, each labelled
with an utterance-level intent: E (explicit toxicity), I (implicit toxicity), A (action request), O (other).

Template "conda.toxic": Noul "Is `chat` toxic toward other players?" Truth = E or I. Rows labelled A are
left out (requests such as "report sf pls" mix with toxicity and are not a clean yes or no). Only the
labelled train and validation files are used (the test file is unannotated). Messages a player sent in a
row are joined by " / " (the dataset's [SEPA] marker). Utterances shorter than three words are dropped
(mostly "gg", "wp", "lol"). Balanced 50/50 in salted hash order.
"""

from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Iterator

import httpx

from askjev.model import Question
from askjev.sampling import env_int, hash_order

NAME = "conda_game_chat"
BASE = "https://raw.githubusercontent.com/usydnlp/CONDA/main/data/"
FILES = ("CONDA_train.csv", "CONDA_valid.csv")
TARGET = env_int("TARGET_CONDA_GAME_CHAT", 2500)
LICENSE = "No license file; public research dataset (usydnlp/CONDA), cite Weld et al. 2021"
TEXT = "Is `chat` toxic toward other players?"
CRITERIA = {
    "true": "The player insults, curses at, taunts, belittles or threatens other players, openly or through "
    "sarcasm and game slang (for example calling someone trash or gloating 'ez')",
    "false": "The chat is ordinary play talk, banter, greetings or strategy with no hostility toward anyone",
}
SEXUAL = re.compile(r"\b(sex\w*|porn\w*|rape\w*|dick|cock|pussy|anus|anal|cum|suck my|masturbat\w*|nude\w*)\b", re.I)
SELF_HARM = re.compile(r"\b(kill (your|ur|urself|yourself)|kys|suicid\w*|hang (your|ur)self)\b", re.I)


def fetch(raw_dir: Path) -> None:
    for f in FILES:
        out = raw_dir / f
        if out.exists():
            continue
        r = httpx.get(BASE + f, follow_redirects=True, timeout=120)
        r.raise_for_status()
        out.write_bytes(r.content)


def _clean(u: str) -> str:
    parts = [" ".join(p.split()) for p in u.split("[SEPA]")]
    return " / ".join(p for p in parts if p)


def normalize(raw_dir: Path) -> Iterator[Question]:
    pools: dict[bool, list[tuple[str, str, str]]] = {True: [], False: []}
    seen: set[str] = set()
    for f in FILES:
        split = f.split("_")[1].removesuffix(".csv")
        with open(raw_dir / f, newline="", encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                label = r["intentClass"].strip()
                if label not in {"E", "I", "O"}:
                    continue
                chat = _clean(r["utterance"])
                words = [w for w in chat.split() if w != "/"]
                if len(words) < 3 or not any(c.isalpha() for c in chat) or chat.lower() in seen:
                    continue
                seen.add(chat.lower())
                pools[label != "O"].append((f"{split}:{r['Id']}", chat, label))

    picked = []
    for label, k in ((True, TARGET // 2), (False, TARGET - TARGET // 2)):
        picked += hash_order(pools[label], lambda x: x[0], f"conda.{label}")[:k]
    picked.sort(key=lambda x: (x[0].split(":")[0], int(x[0].split(":")[1])))

    for sid, chat, label in picked:
        flags = ["sensitive"] if (SEXUAL.search(chat) or SELF_HARM.search(chat)) else []
        yield Question(
            text=TEXT,
            primitive="noul",
            hemisphere="machine",
            origin="dataset",
            source=NAME,
            options=CRITERIA,
            state={"chat": chat[:1500]},
            shape="detect",
            node_hint="machine.trust_safety.game_chat",
            template_id="conda.toxic",
            source_item_id=sid,
            license=LICENSE,
            truth=label != "O",
            meta={"label_raw": label, "game": "Dota 2", **({"flags": flags} if flags else {})},
        )
