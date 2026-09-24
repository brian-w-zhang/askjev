"""Open Trivia DB multiple-choice trivia, cached per category page, digit-free items only."""

from __future__ import annotations

import hashlib
import html
import json
import random
import re
import time
from pathlib import Path
from typing import Iterator

import httpx

from askjev.model import Question

NAME = "opentdb"
API = "https://opentdb.com/api.php"
TOKEN_API = "https://opentdb.com/api_token.php"
LICENSE = "CC BY-SA 4.0"
TARGET = 500
PAGES = 2  # 2 x 50 questions per category
PER_CATEGORY_CAP = 40
SEED = 20260924
DELAY = 5.5

# category id -> (name, node_hint); 19 Mathematics skipped (numbers).
CATEGORIES = {
    9: ("General Knowledge", "world"),
    10: ("Books", "world.arts.books"),
    11: ("Film", "world.arts.film"),
    12: ("Music", "world.arts.music"),
    13: ("Musicals & Theatres", "world.arts.theatre_dance"),
    14: ("Television", "world.arts.television"),
    15: ("Video Games", "world.sports.video_games"),
    16: ("Board Games", "world.sports.board_card_games"),
    17: ("Science & Nature", "world.science"),
    18: ("Computers", "world.tech.computers_hardware"),
    20: ("Mythology", "world.society.mythology_folklore"),
    21: ("Sports", "world.sports"),
    22: ("Geography", "world.places"),
    23: ("History", "world.history"),
    24: ("Politics", "world.society"),
    25: ("Art", "world.arts.visual_art"),
    26: ("Celebrities", "world.arts.celebrities"),
    27: ("Animals", "world.nature"),
    28: ("Vehicles", "world.tech.vehicles"),
    29: ("Comics", "world.arts"),
    30: ("Gadgets", "world.tech.gadgets"),
    31: ("Anime & Manga", "world.arts.television"),
    32: ("Cartoon & Animations", "world.arts.television"),
}
DIGIT = re.compile(r"\d")


def _get(client: httpx.Client, url: str, params: dict) -> dict:
    for attempt in range(6):
        time.sleep(DELAY)
        r = client.get(url, params=params, timeout=60)
        if r.status_code == 429:
            time.sleep(DELAY * (attempt + 2))
            continue
        r.raise_for_status()
        data = r.json()
        if data.get("response_code") == 5:  # rate limited
            time.sleep(DELAY * (attempt + 2))
            continue
        return data
    raise RuntimeError(f"opentdb: rate limited on {params}")


def fetch(raw_dir: Path) -> None:
    todo = [(c, p) for c in CATEGORIES for p in range(PAGES) if not (raw_dir / f"cat{c}_p{p}.json").exists()]
    if not todo:
        return
    with httpx.Client(headers={"User-Agent": "askjev/0.1 (github.com/brian-w-zhang/askjev)"}) as client:
        token = _get(client, TOKEN_API, {"command": "request"})["token"]
        for c, p in todo:
            if p > 0 and not (raw_dir / f"cat{c}_p{p - 1}.json").exists():
                continue
            for amount in (50, 25, 10):  # codes 1/4: fewer than `amount` questions left for this token
                data = _get(client, API, {"amount": amount, "category": c, "type": "multiple", "token": token})
                if data.get("response_code") == 0:
                    break
            if data.get("response_code") in (1, 4) or not data.get("results"):
                # Category exhausted: record an empty page so reruns don't re-request it.
                data = {"response_code": data.get("response_code"), "results": []}
            (raw_dir / f"cat{c}_p{p}.json").write_text(json.dumps(data, ensure_ascii=False, indent=0))


def _items(raw_dir: Path) -> list[dict]:
    items, seen = [], set()
    for c in CATEGORIES:
        for p in range(PAGES):
            f = raw_dir / f"cat{c}_p{p}.json"
            if not f.exists():
                continue
            for r in json.loads(f.read_text())["results"]:
                q = html.unescape(r["question"]).strip()
                right = html.unescape(r["correct_answer"]).strip()
                wrong = [html.unescape(w).strip() for w in r["incorrect_answers"]]
                if q.lower() in seen or len(wrong) != 3:
                    continue
                if DIGIT.search(q) or any(DIGIT.search(a) for a in [right, *wrong]):
                    continue
                if len({a.lower() for a in [right, *wrong]}) != 4:
                    continue
                seen.add(q.lower())
                items.append({"cat": c, "q": q, "right": right, "wrong": wrong, "difficulty": r["difficulty"]})
    return items


def normalize(raw_dir: Path) -> Iterator[Question]:
    rng = random.Random(SEED)
    by_cat: dict[int, list[dict]] = {}
    for it in _items(raw_dir):
        by_cat.setdefault(it["cat"], []).append(it)
    picked = []
    for c in sorted(by_cat):
        pool = by_cat[c]
        picked += rng.sample(pool, min(PER_CATEGORY_CAP, len(pool)))
    if len(picked) > TARGET:
        picked = rng.sample(picked, TARGET)
    for it in sorted(picked, key=lambda x: (x["cat"], x["q"])):
        answers = [(it["right"], True)] + [(w, False) for w in it["wrong"]]
        r2 = random.Random(int(hashlib.sha256(f"{SEED}:{it['q']}".encode()).hexdigest()[:16], 16))
        r2.shuffle(answers)
        keys = "abcd"
        name, node = CATEGORIES[it["cat"]]
        meta = {"category": name, "difficulty": it["difficulty"]}
        if it["cat"] == 24:
            meta["flags"] = ["political"]
        yield Question(
            text=it["q"],
            primitive="choice",
            hemisphere="world",
            kind="factual",
            origin="dataset",
            source=NAME,
            options={k: a for k, (a, _) in zip(keys, answers)},
            truth=next(k for k, (_, ok) in zip(keys, answers) if ok),
            node_hint=node,
            source_item_id=hashlib.sha1(it["q"].encode()).hexdigest()[:12],
            license=LICENSE,
            meta=meta,
        )
