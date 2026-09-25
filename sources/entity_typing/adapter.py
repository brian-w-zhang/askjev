"""Named-entity typing over two human-annotated NER corpora (tner parquet mirrors):

- CoNLL-2003 English (Tjong Kim Sang & De Meulder 2003; Reuters news, 1996-97): PER / ORG / LOC / MISC.
  Template "entity_typing.conll_type".
- WNUT-17 emerging entities (Derczynski et al. 2017; Twitter, Reddit, YouTube, StackExchange): person,
  location, corporation, product, creative-work, group. Template "entity_typing.wnut_type".

One question per (sentence, entity span): Choice "What type of entity is `span` in `sentence`?", truth =
the gold BIO type of that span. At most one span per sentence (the first span of the sampled type), and
the sample is balanced over types in salted hash order. Tokens are joined with light detokenization.
"""

from __future__ import annotations

import html
import re
from pathlib import Path
from typing import Iterator

import httpx
import polars as pl

from askjev.model import Question
from askjev.sampling import env_int, hash_order

NAME = "entity_typing"
URL = "https://huggingface.co/api/datasets/tner/{name}/parquet/{name}/{split}/0.parquet"
SPLITS = ("train", "validation", "test")
TEXT = "What type of entity is `span` in `sentence`?"
SENSITIVE = re.compile(r"\b(sex\w*|porn\w*|nude\w*|naked|rape\w*|suicid\w*|nsfw|fuck\w*|pussy|dick|cock)\b", re.I)

CORPORA = {
    "conll": {
        "hf": "conll2003",
        "file": "conll",
        "target": env_int("TARGET_ENTITY_CONLL", 2500),
        "license": "Research use (CoNLL-2003 annotations; Reuters RCV1 text)",
        "labels": {"O": 0, "B-ORG": 1, "B-MISC": 2, "B-PER": 3, "I-PER": 4, "B-LOC": 5, "I-ORG": 6, "I-MISC": 7, "I-LOC": 8},
        "map": {"PER": "person", "ORG": "organization", "LOC": "location", "MISC": "other"},
        "options": {
            "person": "A person's name",
            "organization": "A company, team, government body, party, agency or other organization",
            "location": "A country, city, region, body of water or other place",
            "other": "Another kind of name: a nationality, language, event, product, title, or a word derived from a name",
        },
        "min_tokens": 6,
    },
    "wnut": {
        "hf": "wnut2017",
        "file": "wnut",
        "target": env_int("TARGET_ENTITY_WNUT", 2000),
        "license": "CC-BY-4.0",
        "labels": {"B-corporation": 0, "B-creative-work": 1, "B-group": 2, "B-location": 3, "B-person": 4, "B-product": 5,
                   "I-corporation": 6, "I-creative-work": 7, "I-group": 8, "I-location": 9, "I-person": 10, "I-product": 11, "O": 12},
        "map": {"person": "person", "location": "location", "corporation": "corporation", "product": "product",
                "creative-work": "creative_work", "group": "group"},
        "options": {
            "person": "A person's name (real or fictional), including usernames that refer to a person",
            "location": "A place: a country, city, building, landmark or other location",
            "corporation": "A company or other commercial organization",
            "product": "A product: a device, software, car, drug or other made thing",
            "creative_work": "A song, film, book, show, game or other creative work",
            "group": "A band, sports team, political party or other group of people that is not a company",
        },
        "min_tokens": 5,
    },
}


def _detok(tokens: list[str]) -> str:
    s = html.unescape(" ".join(tokens))
    s = re.sub(r" ([,.;:!?)\]%])", r"\1", s)
    s = re.sub(r"([(\[$]) ", r"\1", s)
    s = re.sub(r" (n't|'s|'re|'ll|'ve|'d|'m)\b", r"\1", s)
    return s


def _spans(tags: list[str]) -> list[tuple[int, int, str]]:
    out, start, typ = [], None, None
    for i, t in enumerate(tags + ["O"]):
        if start is not None and not (t.startswith("I-") and t[2:] == typ):
            out.append((start, i, typ))
            start = typ = None
        if t.startswith("B-") or (t.startswith("I-") and start is None):
            start, typ = i, t[2:]
    return out


def fetch(raw_dir: Path) -> None:
    for c in CORPORA.values():
        for split in SPLITS:
            out = raw_dir / f"{c['file']}_{split}.parquet"
            if out.exists():
                continue
            r = httpx.get(URL.format(name=c["hf"], split=split), follow_redirects=True, timeout=120)
            r.raise_for_status()
            out.write_bytes(r.content)


def normalize(raw_dir: Path) -> Iterator[Question]:
    for cname, c in CORPORA.items():
        inv = {v: k for k, v in c["labels"].items()}
        pools: dict[str, list[tuple]] = {k: [] for k in c["options"]}
        seen: set[str] = set()
        for split in SPLITS:
            df = pl.read_parquet(raw_dir / f"{c['file']}_{split}.parquet")
            for row, (tokens, tags) in enumerate(df.select("tokens", "tags").iter_rows()):
                tokens = [t for t in tokens]
                if len(tokens) < c["min_tokens"] or tokens[0].startswith("-DOCSTART-"):
                    continue
                sent = _detok(tokens)
                if sent.lower() in seen or len(sent) > 1000:
                    continue
                seen.add(sent.lower())
                strs = [inv[t] for t in tags]
                spans = _spans(strs)
                # One candidate span per type per sentence (the first); the span text must be unique in the sentence.
                done = set()
                for s, e, typ in spans:
                    key = c["map"].get(typ)
                    span = _detok(tokens[s:e])
                    if key is None or key in done or sent.count(span) != 1 or len(span) < 2:
                        continue
                    done.add(key)
                    pools[key].append((split, row, sent, span, s))
        # Balanced: fill the smallest types first, one span per sentence overall.
        picked: list[tuple] = []
        used: set[tuple] = set()
        order = sorted(pools, key=lambda k: len(pools[k]))
        for n, lab in enumerate(order):
            want = (c["target"] - len(picked)) // (len(order) - n)
            got = 0
            for x in hash_order(pools[lab], lambda x: (x[0], x[1], x[4]), f"entity_typing|{cname}|{lab}"):
                if got >= want:
                    break
                if (x[0], x[1]) in used:
                    continue
                used.add((x[0], x[1]))
                picked.append((lab, *x))
                got += 1
        picked.sort(key=lambda x: (x[1], x[2], x[5]))
        for lab, split, row, sent, span, start in picked:
            yield Question(
                text=TEXT,
                primitive="choice",
                hemisphere="machine",
                origin="dataset",
                source=NAME,
                options=c["options"],
                state={"sentence": sent, "span": span},
                shape="classify",
                node_hint="machine.documents.structured_extraction",
                template_id=f"entity_typing.{cname}_type",
                source_item_id=f"{cname}:{split}:{row}:{start}",
                license=c["license"],
                truth=lab,
                meta={"corpus": c["hf"], "split": split, **({"flags": ["sensitive"]} if SENSITIVE.search(sent) else {})},
            )
