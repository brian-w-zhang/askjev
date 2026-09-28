"""How positive is a tweet with this emoji? (research pass 2, idea 7.)

Human data: the Emoji Sentiment Ranking (Kralj Novak, Smailović, Sluban & Mozetič 2015, "Sentiment of Emojis",
PLoS ONE; CLARIN.SI handle 11356/1048, CC BY-SA 4.0). 83 annotators labeled 1.6 million tweets in 13 European
languages as negative, neutral or positive; for each emoji the file counts the labels of the tweets that contain
it. The question asks Jev the same thing about a tweet it can't see: given only that the emoji is in it. The 300
emojis found in at least 50 labeled tweets.
"""

from __future__ import annotations

import csv
import urllib.request
from pathlib import Path
from typing import Iterator

from askjev.model import HumanDist, Question

NAME = "emoji_sentiment"
NODE = "world.society.languages.word.emoji_sentiment"
LICENSE = "CC BY-SA 4.0 (Emoji Sentiment Ranking v1.0, Kralj Novak et al. 2015, CLARIN.SI 11356/1048)"
URL = "https://www.clarin.si/repository/xmlui/bitstream/handle/11356/1048/Emoji_Sentiment_Data_v1.0.csv"
FILE = "Emoji_Sentiment_Data_v1.0.csv"
MIN_TWEETS = 50
OPTIONS = {"negative": "The tweet is negative", "neutral": "The tweet is neutral", "positive": "The tweet is positive"}


def fetch(raw_dir: Path) -> None:
    if not (raw_dir / FILE).exists():
        urllib.request.urlretrieve(URL, raw_dir / FILE)


def normalize(raw_dir: Path) -> Iterator[Question]:
    for r in csv.DictReader(open(raw_dir / FILE, encoding="utf-8")):
        n = int(r["Occurrences"])
        if n < MIN_TWEETS:
            continue
        counts = {"negative": int(r["Negative"]), "neutral": int(r["Neutral"]), "positive": int(r["Positive"])}
        tot = sum(counts.values()) or 1
        yield Question(
            text=f"A tweet contains the emoji {r['Emoji']}. Knowing only that, is the tweet more likely negative, "
                 "neutral or positive?",
            primitive="choice", hemisphere="world", kind="perception", origin="dataset", source=NAME, options=OPTIONS,
            node_hint=NODE, license=LICENSE, source_item_id=r["Unicode codepoint"],
            human=[HumanDist(population="Tweets labeled by 83 annotators (Kralj Novak et al. 2015)",
                             distribution={k: v / tot for k, v in counts.items()}, n=tot,
                             source="Emoji Sentiment Ranking v1.0: label counts of the tweets containing the emoji")],
            meta={"experiment": "emoji_sentiment", "emoji": r["Emoji"], "name": r["Unicode name"].lower(),
                  "block": r["Unicode block"], "tweets": n, "position": float(r["Position"])})
