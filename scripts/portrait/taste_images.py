"""Pictures for the portrait's taste section: each of Jev's favorites gets the lead image of its Wikipedia article
(a film's poster, an album's cover, a place's photo), downloaded once into data/portrait/memes/taste-<slug>.webp
(private, served by /portrait/memes and published with the memes) and recorded, with its source page, in
data/portrait/memes/taste.json. The Wikipedia titles are picked by hand so each image is the right thing.

  uv run python scripts/portrait/taste_images.py
"""

from __future__ import annotations

import io
import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

from PIL import Image

OUT = Path("data/portrait/memes")
INDEX = OUT / "taste.json"
UA = {"User-Agent": "askjev-portrait/1.0 (private research page)"}

# (experiment item label as the export writes it) -> Wikipedia article title
TITLES = {
    # films: the top four, Letterboxd style
    "The Shawshank Redemption (1994)": "The Shawshank Redemption",
    "The Godfather (1972)": "The Godfather",
    "Spirited Away (2001)": "Spirited Away",
    "The Dark Knight (2008)": "The Dark Knight",
    "Movie 43 (2013)": "Movie 43",
    # books
    "Surely You're Joking, Mr. Feynman!: Adventures of a Curious Character by Richard Feynman": "Surely You're Joking, Mr. Feynman!",
    "And Then There Were None by Agatha Christie": "And Then There Were None",
    "A Wizard of Earthsea by Ursula K. Le Guin": "A Wizard of Earthsea",
    # albums
    "The album “Kind of Blue” by Miles Davis": "Kind of Blue",
    "“The Dark Side of the Moon” by Pink Floyd": "The Dark Side of the Moon",
    "The album “Abbey Road” by The Beatles": "Abbey Road",
    # anime
    "Fullmetal Alchemist: Brotherhood (TV series)": "Fullmetal Alchemist (TV series)",
    "Hunter x Hunter (2011) (TV series)": "Hunter × Hunter (2011 TV series)",
    # board games
    "Codenames (2015)": "Codenames (board game)",
    "Carcassonne (2000)": "Carcassonne (board game)",
    # games
    "Baldur's Gate 3": "Baldur's Gate 3",
    "Spending an evening playing Outer Wilds": "Outer Wilds",
    # food
    "Affogato": "Affogato",
    "A Montreal smoked meat sandwich": "Montreal-style smoked meat",
    # places
    "Bora Bora's lagoon": "Bora Bora",
    "Banff's Lake Louise": "Lake Louise (Alberta)",
    # art
    "The Creation of Adam by Michelangelo": "The Creation of Adam",
    "David by Michelangelo": "David (Michelangelo)",
    # beer
    "Saison Dupont by Brasserie Dupont sprl (Saison / Farmhouse Ale)": "Saison",
    # nature
    "A blue whale": "Blue whale",
    # culture
    "Spending a day at the Yi Peng lantern release in Chiang Mai": "Yi Peng",
}


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")[:48]


def summary(title: str) -> dict:
    url = "https://en.wikipedia.org/api/rest_v1/page/summary/" + urllib.parse.quote(title.replace(" ", "_"), safe="")
    return json.loads(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30).read())


def main():
    idx = json.loads(INDEX.read_text()) if INDEX.exists() else {}
    for label, title in TITLES.items():
        if label in idx and (OUT / idx[label]["file"]).exists():
            continue
        time.sleep(3)  # Wikipedia rate-limits bursts
        try:
            s = summary(title)
            src = (s.get("originalimage") or s.get("thumbnail") or {}).get("source")
            if not src:
                print("no image:", title)
                continue
            # a bounded size: Wikipedia serves scaled thumbnails at /<w>px- in the thumb path
            thumb = (s.get("thumbnail") or {}).get("source") or src  # the size Wikipedia offers; others are refused
            time.sleep(3)
            raw = urllib.request.urlopen(urllib.request.Request(thumb, headers=UA), timeout=60).read()
            im = Image.open(io.BytesIO(raw)).convert("RGB")
            im.thumbnail((640, 640))
            f = f"taste-{slug(title)}.webp"
            im.save(OUT / f, "WEBP", quality=82)
            idx[label] = {"file": f, "w": im.width, "h": im.height, "title": s.get("title", title),
                          "page": (s.get("content_urls") or {}).get("desktop", {}).get("page", "")}
            print("ok", title, im.size)
        except Exception as e:  # noqa: BLE001 — one missing picture shouldn't stop the rest
            print("failed:", title, e)
    INDEX.write_text(json.dumps(idx, indent=1, ensure_ascii=False))
    print(len(idx), "images")


if __name__ == "__main__":
    main()
