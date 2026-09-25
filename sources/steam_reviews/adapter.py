"""Steam user reviews (English), from the public Hugging Face copy SebastianHops/steam-reviews-english
(reviews pulled from the Steam store API). Each review carries the reviewer's own thumbs-up/down
("voted_up"), so the label is the author's verdict, not an annotator's guess.

Template "steam.recommends": Noul "Does the player who wrote `review` recommend `game`?" Truth = voted_up.
Only the first shard (part.0, ~273k reviews over ~1,000 games) is downloaded. Reviews of 8-250 words with
mostly letters (no ASCII art), Steam BBCode tags stripped, one per author, at most 8 per game and label; balanced 50/50 in salted
hash order.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterator

import httpx
import polars as pl

from askjev.model import Question
from askjev.sampling import env_int, hash_order

NAME = "steam_reviews"
URL = "https://huggingface.co/datasets/SebastianHops/steam-reviews-english/resolve/main/part.0.parquet"
TARGET = env_int("TARGET_STEAM_REVIEWS", 2500)
MAX_PER_GAME = 8
LICENSE = "No license stated on the HF copy; review text from the public Steam store reviews API"
TEXT = "Does the player who wrote `review` recommend `game`?"
CRITERIA = {
    "true": "The player gave the game a thumbs-up: they recommend it to other players",
    "false": "The player gave the game a thumbs-down: they do not recommend it",
}
SEXUAL = re.compile(r"\b(sex\w*|porn\w*|hentai|rape\w*|nude\w*|naked|nsfw|boobs?|tits|dick|cock|pussy|"
                    r"masturbat\w*|suicid\w*|kill (your|ur)self|kys)\b", re.I)


def fetch(raw_dir: Path) -> None:
    out = raw_dir / "part.0.parquet"
    if out.exists():
        return
    r = httpx.get(URL, follow_redirects=True, timeout=600)
    r.raise_for_status()
    out.write_bytes(r.content)


def _ok(text: str) -> bool:
    words = text.split()
    if not 8 <= len(words) <= 250:
        return False
    letters = sum(c.isalpha() for c in text)
    return letters / max(1, len(text.replace(" ", ""))) > 0.75


def normalize(raw_dir: Path) -> Iterator[Question]:
    df = (
        pl.read_parquet(raw_dir / "part.0.parquet",
                        columns=["recommendationid", "appid", "game", "author_steamid", "review", "voted_up"])
        .drop_nulls(["recommendationid", "game", "review", "voted_up"])
        .with_columns(
            pl.col("review")
            .str.replace_all(r"\[/?(h\d|b|i|u|s|strike|spoiler|noparse|hr|list|olist|\*|quote|code|table|tr|td|th|url)(=[^\]]*)?\]", " ")
            .str.replace_all(r"\s+", " ")
            .str.strip_chars()
        )
        .unique("review", keep="first", maintain_order=True)
        .unique("author_steamid", keep="first", maintain_order=True)
    )
    pools: dict[bool, list[tuple[int, str, str]]] = {True: [], False: []}
    for rid, game, review, up in df.select("recommendationid", "game", "review", "voted_up").iter_rows():
        if _ok(review):
            pools[bool(up)].append((int(rid), game.strip(), review))

    picked = []
    for label, k in ((True, TARGET // 2), (False, TARGET - TARGET // 2)):
        per_game: dict[str, int] = {}
        for item in hash_order(pools[label], lambda x: x[0], f"steam.{label}"):
            if len(picked) >= (k if label else TARGET):
                break
            if per_game.get(item[1], 0) >= MAX_PER_GAME:
                continue
            per_game[item[1]] = per_game.get(item[1], 0) + 1
            picked.append((label, item))
    picked.sort(key=lambda x: x[1][0])

    for label, (rid, game, review) in picked:
        yield Question(
            text=TEXT,
            primitive="noul",
            hemisphere="machine",
            origin="dataset",
            source=NAME,
            options=CRITERIA,
            state={"game": game, "review": review[:1500]},
            shape="detect",
            node_hint="machine.commerce.review_insights",
            template_id="steam.recommends",
            source_item_id=f"rec:{rid}",
            license=LICENSE,
            truth=label,
            meta={"voted_up": label, **({"flags": ["sensitive"]} if SEXUAL.search(review) else {})},
        )
