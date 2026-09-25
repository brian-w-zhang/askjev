"""SNIPS NLU benchmark (Coucke et al. 2018): crowd-written commands to a voice assistant, each labelled with one
of 7 intents. Source: the benayas/snips HF copy (train 13,084 + test 1,400 utterances, text + intent).

Template "snips_intents.intent": one Choice per command over the 7 intents, truth = the dataset intent. This is
a finer, different split of the assistant space than MASSIVE's scenario template (e.g. adding to a playlist vs.
playing music, searching a movie showtime vs. a creative work). Case-insensitive dedup; stratified evenly
across intents in salted-hash order.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterator

import httpx
import polars as pl

from askjev.model import Question
from askjev.sampling import env_int, hash_order

NAME = "snips_intents"
BASE = "https://huggingface.co/api/datasets/benayas/snips/parquet/default"
SPLITS = ("train", "test")
LICENSE = "CC0-1.0"
NODE = "machine.support.commands"
TARGET = env_int("TARGET_SNIPS_INTENTS", 1500)
TEXT = "What does the user want the voice assistant to do in `command`?"
INTENTS = {
    "AddToPlaylist": ("add_to_playlist", "Add a song, artist or album to one of their playlists"),
    "BookRestaurant": ("book_restaurant", "Reserve a table at a restaurant"),
    "GetWeather": ("get_weather", "Get the weather forecast for a place or time"),
    "PlayMusic": ("play_music", "Play a song, artist, album, genre or playlist"),
    "RateBook": ("rate_book", "Give a rating to a book or other written work"),
    "SearchCreativeWork": ("search_creative_work", "Find a creative work such as a song, film, TV show, book or game"),
    "SearchScreeningEvent": ("search_screening_event", "Find movie showtimes or which cinemas are showing a film"),
}
OPTIONS = {k: d for k, d in INTENTS.values()}


def fetch(raw_dir: Path) -> None:
    for s in SPLITS:
        out = raw_dir / f"{s}.parquet"
        if out.exists():
            continue
        r = httpx.get(f"{BASE}/{s}/0.parquet", follow_redirects=True, timeout=120)
        r.raise_for_status()
        out.write_bytes(r.content)


def normalize(raw_dir: Path) -> Iterator[Question]:
    seen: set[str] = set()
    pools: dict[str, list] = {k: [] for k, _ in INTENTS.values()}
    for s in SPLITS:
        df = pl.read_parquet(raw_dir / f"{s}.parquet").with_row_index("row")
        for row, text, cat in df.select("row", "text", "category").iter_rows():
            t = " ".join((text or "").split())
            if len(t) < 5 or t.lower() in seen or cat not in INTENTS:
                continue
            seen.add(t.lower())
            pools[INTENTS[cat][0]].append((f"{s}:{row}", t, cat))
    n = len(pools)
    picked = []
    for i, (k, pool) in enumerate(sorted(pools.items())):
        picked += [(k, x) for x in hash_order(pool, lambda x: x[0], f"snips.{k}")[: TARGET // n + (i < TARGET % n)]]
    for k, (item, t, cat) in sorted(picked, key=lambda z: z[1][0]):
        yield Question(
            text=TEXT,
            primitive="choice",
            hemisphere="machine",
            origin="dataset",
            source=NAME,
            options=OPTIONS,
            state={"command": t},
            shape="route",
            node_hint=NODE,
            template_id="snips_intents.intent",
            source_item_id=item,
            license=LICENSE,
            truth=k,
            meta={"label_raw": cat},
        )
