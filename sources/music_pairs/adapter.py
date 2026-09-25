"""Last.fm 360K: pairwise "Which artist would you rather listen to?" between two widely followed artists with a
shared audience, with the human split from listeners who have both among their top artists (more plays wins)."""

from __future__ import annotations

import itertools
import json
import re
import time
import unicodedata
from pathlib import Path
from typing import Iterator

import httpx
import numpy as np
import polars as pl
import scipy.sparse as sp

from askjev.model import HumanDist, Question
from askjev.sampling import env_int, hash_order

NAME = "music_pairs"
URL = "https://huggingface.co/datasets/matthewfranglen/lastfm-360k/resolve/main/train.gz.parquet"  # user x top-artist plays
MB_AGENT = "askjev-source-adapter/0.1 (non-commercial research; artist-name lookup)"
LICENSE = "Last.fm dataset 360K (Òscar Celma, MTG/UPF): non-commercial use with permission of Last.fm; HF mirror matthewfranglen/lastfm-360k"
TARGET = env_int("TARGET_MUSIC_PAIRS", 4000)
SALT = "music_pairs.v1"
MIN_LISTENERS = 3000  # users (of 287k) with the artist among their top artists: 751 artists
MIN_COSINE = 0.08  # shared-audience cosine: artists with overlapping fan bases (comparable genre/scene)
MIN_CO = 200
MAX_PER_ARTIST = 25
TEXT = "Which artist would you rather listen to?"
# MusicBrainz typography -> plain ASCII punctuation (Unicode hyphens, curly quotes, ellipsis), plus stylizations.
PUNCT = str.maketrans({"\u2010": "-", "\u2011": "-", "\u2019": "'", "\u2018": "'", "\u201c": '"', "\u201d": '"'})
OVERRIDES = {"JAŸ-Z": "Jay-Z"}


def fetch(raw_dir: Path) -> None:
    plays = raw_dir / "train.gz.parquet"
    if not plays.exists():
        with httpx.stream("GET", URL, timeout=1800, follow_redirects=True) as r:
            r.raise_for_status()
            with open(plays, "wb") as fh:
                for chunk in r.iter_bytes(1 << 20):
                    fh.write(chunk)
    # Canonical artist names from MusicBrainz (the Last.fm dumps are lowercased), cached; 1 request/second.
    names_path = raw_dir / "artist_names.json"
    names = json.loads(names_path.read_text()) if names_path.exists() else {}
    mbids = _popular(plays)["musicbrainz_artist_id"].to_list()
    todo = [m for m in mbids if m not in names]
    with httpx.Client(headers={"User-Agent": MB_AGENT}, timeout=60, follow_redirects=True) as client:
        for k, mbid in enumerate(todo):
            for attempt in range(5):
                r = client.get(f"https://musicbrainz.org/ws/2/artist/{mbid}", params={"fmt": "json"})
                if r.status_code == 503:
                    time.sleep(2 + attempt * 2)
                    continue
                break
            names[mbid] = r.json().get("name") if r.status_code == 200 else None
            time.sleep(1.1)
            if k % 50 == 49:
                names_path.write_text(json.dumps(names, ensure_ascii=False, indent=0))
    names_path.write_text(json.dumps(names, ensure_ascii=False, indent=0))


def _plays(path: Path) -> pl.DataFrame:
    return (
        pl.read_parquet(path, columns=["user_index", "musicbrainz_artist_id", "play_count"])
        .group_by("user_index", "musicbrainz_artist_id")
        .agg(pl.col("play_count").sum())
    )


def _popular(path: Path, plays: pl.DataFrame | None = None) -> pl.DataFrame:
    plays = _plays(path) if plays is None else plays
    return (
        plays.group_by("musicbrainz_artist_id").agg(pl.len().alias("n"))
        .filter(pl.col("n") >= MIN_LISTENERS)
        .sort("n", "musicbrainz_artist_id", descending=[True, False])
    )


def _slug(name: str) -> str:
    s = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().lower()
    s = re.sub(r"[^a-z0-9]+", "_", s).strip("_")
    if len(s) > 40:
        s = s[:40].rsplit("_", 1)[0]
    return s


def normalize(raw_dir: Path) -> Iterator[Question]:
    plays = _plays(raw_dir / "train.gz.parquet")
    names = json.loads((raw_dir / "artist_names.json").read_text())
    artists, seen = [], set()
    for row in _popular(raw_dir / "train.gz.parquet", plays).iter_rows(named=True):
        name = (names.get(row["musicbrainz_artist_id"]) or "").strip()  # no MusicBrainz name -> skipped
        name = OVERRIDES.get(name, name).translate(PUNCT).replace("\u2026", "...")
        slug = _slug(name)
        if not slug or slug in seen or not any(ch.isalpha() for ch in name):
            continue
        seen.add(slug)
        artists.append({"mbid": row["musicbrainz_artist_id"], "name": name, "slug": slug, "n": row["n"]})
    for i, a in enumerate(artists):
        a["i"] = i
    idx = pl.DataFrame({"musicbrainz_artist_id": [a["mbid"] for a in artists], "a": [a["i"] for a in artists]})
    sub = plays.join(idx, on="musicbrainz_artist_id").sort("a", "user_index")
    arrays = {a: (g["user_index"].to_numpy(), g["play_count"].to_numpy())
              for (a,), g in sub.group_by("a", maintain_order=True)}

    m = sp.csr_matrix((np.ones(sub.height), (sub["user_index"].to_numpy(), sub["a"].to_numpy())))
    co = (m.T @ m).toarray()
    cnt = np.diag(co)
    cos = co / np.sqrt(np.outer(cnt, cnt))

    pairs = [(a, b) for a, b in itertools.combinations(artists, 2) if cos[a["i"], b["i"]] >= MIN_COSINE]
    uses: dict[int, int] = {}
    taken = 0
    for a, b in hash_order(pairs, lambda p: f"{p[0]['mbid']}|{p[1]['mbid']}", SALT):
        if taken >= TARGET:
            break
        if uses.get(a["i"], 0) >= MAX_PER_ARTIST or uses.get(b["i"], 0) >= MAX_PER_ARTIST:
            continue
        ua, pa = arrays[a["i"]]
        ub, pb = arrays[b["i"]]
        _, ia, ib = np.intersect1d(ua, ub, assume_unique=True, return_indices=True)
        n = len(ia)
        if n < MIN_CO:
            continue
        xa, xb = pa[ia], pb[ib]
        wins_a = float((xa > xb).sum()) + 0.5 * float((xa == xb).sum())
        ka, kb = a["slug"], b["slug"]
        uses[a["i"]] = uses.get(a["i"], 0) + 1
        uses[b["i"]] = uses.get(b["i"], 0) + 1
        taken += 1
        opts = sorted([(ka, a["name"]), (kb, b["name"])])
        yield Question(
            text=TEXT,
            primitive="choice",
            hemisphere="self",
            kind="taste",
            origin="dataset",
            source=NAME,
            options=dict(opts),
            node_hint="self.lifestyle.leisure_hobbies",
            source_item_id=f"{a['mbid']}|{b['mbid']}",
            license=LICENSE,
            template_id="music_pairs.listen",
            human=[
                HumanDist(
                    population="Last.fm users with both artists among their top artists",
                    distribution={ka: round(wins_a / n, 4), kb: round(1 - wins_a / n, 4)},
                    n=n,
                    source="Last.fm 360K (Celma 2010): share who played each artist more, ties split",
                )
            ],
            meta={
                "mbids": [a["mbid"], b["mbid"]],
                "listeners_n": [a["n"], b["n"]],
                "audience_cosine": round(float(cos[a["i"], b["i"]]), 4),
            },
        )
