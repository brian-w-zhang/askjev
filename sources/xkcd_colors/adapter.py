"""Which name fits a color given as a hex code? (research pass 2, idea 8; a documented weak spot.)

Human data: the xkcd color survey (Munroe 2010; about 222,500 people named 5 million colors): rgb.txt lists the 949
most common names with the RGB point each one centers on (CC0). Jev sees a hex code and four names: the survey's name
for that color, the nearest other survey color at least 40 RGB units away (a hard distractor), and two random ones.

TypeSafe documents raw numeric and hex/RGB values as a weak spot (docs/01-jev.md §6, item 2), so this measures a
known limit rather than discovering one; it stays small.
"""

from __future__ import annotations

import math
import random
import urllib.request
from pathlib import Path
from typing import Iterator

from askjev.model import Question

NAME = "xkcd_colors"
NODE = "world.science.physics.color.color_names"
LICENSE = "CC0 (xkcd color survey, Munroe 2010)"
URL = "https://xkcd.com/color/rgb.txt"
N = 150


def fetch(raw_dir: Path) -> None:
    if not (raw_dir / "rgb.txt").exists():
        urllib.request.urlretrieve(URL, raw_dir / "rgb.txt")


def _rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _key(name: str) -> str:
    return name.replace("'", "").replace("/", "_").replace(" ", "_")


def normalize(raw_dir: Path) -> Iterator[Question]:
    rows = [line.rstrip("\n").split("\t")[:2] for line in open(raw_dir / "rgb.txt") if not line.startswith("#")]
    cols = [(n.strip(), h.strip()) for n, h in rows]
    rgb = {n: _rgb(h) for n, h in cols}
    rng = random.Random(2010)
    for name, hexc in rng.sample(sorted(cols), N):
        dist = sorted((math.dist(rgb[name], rgb[o]), o) for o, _ in cols if o != name)
        near = next((d, o) for d, o in dist if d >= 40)
        far = rng.sample([o for d, o in dist if d >= 150], 2)
        names = [name, near[1], *far]
        rng.shuffle(names)
        yield Question(
            text=f"Which name fits the color with the hex code {hexc} best?", primitive="choice", hemisphere="world",
            kind="perception", origin="dataset", source=NAME, options={_key(n): n for n in names}, node_hint=NODE,
            license=LICENSE, truth=_key(name), source_item_id=hexc,
            meta={"experiment": "xkcd_colors", "name": name, "hex": hexc, "near": near[1], "near_dist": round(near[0], 1),
                  "known_limit": "01-jev §6 item 2"})
