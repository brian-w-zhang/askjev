"""Yahoo! Answers Topics (Zhang, Zhao & LeCun 2015): community questions (title + details) in 10 top-level
Yahoo! Answers categories.

Template "yahoo_topics.category": one Choice per question over the 10 categories, truth = the dataset label.
State = question title, then the asker's details (truncated). Test split, balanced across categories.
Sexual content involving minors and slurs are dropped; other sexual/self-harm content is flagged sensitive,
contested politics political.
"""

from __future__ import annotations

import html
import re
from collections import defaultdict
from pathlib import Path
from typing import Iterator

import httpx
import polars as pl

from askjev.model import Question
from askjev.sampling import env_int, hash_order

NAME = "yahoo_topics"
URL = (
    "https://huggingface.co/api/datasets/community-datasets/yahoo_answers_topics/parquet/"
    "yahoo_answers_topics/test/0.parquet"
)
LICENSE = "Yahoo! Answers Comprehensive Q&A (Yahoo Webscope L6): non-commercial research use"
TARGET = env_int("TARGET_YAHOO_TOPICS", 2000)
TEXT = "Which topic category does `question` belong to?"
# key -> description, in the dataset's ClassLabel order.
TOPICS: dict[str, str] = {
    "society_culture": "Society and culture: religion, traditions, languages, holidays, cultures, etiquette",
    "science_mathematics": "Science and mathematics: physics, chemistry, biology, astronomy, math problems",
    "health": "Health: illness, symptoms, medicine, fitness, diet, mental health",
    "education_reference": "Education and reference: school, homework help, studying, words and grammar, "
    "general reference",
    "computers_internet": "Computers and the internet: hardware, software, websites, email, programming",
    "sports": "Sports: teams, players, games and competitions, exercise as a sport",
    "business_finance": "Business and finance: jobs and careers, money, investing, taxes, companies",
    "entertainment_music": "Entertainment and music: movies, TV, celebrities, music, books, games, jokes",
    "family_relationships": "Family and relationships: dating, marriage, friends, parenting, family",
    "politics_government": "Politics and government: law, elections, government, military, current affairs",
}
LABELS = list(TOPICS)

SEXUAL = re.compile(
    r"\b(sex\w*|porn\w*|nude\w*|naked|erotic\w*|horny|orgasm\w*|masturbat\w*|penis\w*|vagina\w*|condoms?|"
    r"virginity|oral|blow ?jobs?|boobs?|breasts?|dick|cock|pussy|slut\w*|whore\w*|hooker\w*|prostitut\w*|"
    r"fetish\w*|erection\w*|viagra|intercourse|kinky|stripper\w*)\b",
    re.I,
)
SELF_HARM = re.compile(r"\b(suicid\w*|kill (my|him|her)self|self.harm|cutting myself|overdos\w*)\b", re.I)
GRAPHIC = re.compile(r"\b(rape\w*|molest\w*|incest|abus(e|ed|ing) (me|my|her|him))\b", re.I)
MINOR = re.compile(
    r"\b(i'?m|i am|im|she'?s|he'?s|she is|he is|years?) ?(only )?(1[0-7]|[1-9])\b(?! ?(hours?|days?|weeks?|months?))"
    r"|\b(1[0-7]|[1-9]) ?(yrs?|years?)[ -]?old\b|\b(underage|minors?|teen\w*|child\w*|kids?|boy|girl|daughter|son)\b",
    re.I,
)
SLUR = re.compile(r"\b(nigg\w*|fag\w*|retard\w*|tranny|spic|chink|kike)\b", re.I)
POLITICAL = re.compile(
    r"\b(elections?|electoral|campaign\w*|ballot\w*|vot(e|es|ing|ers?)|republican\w*|democrat\w*|liberal\w*|"
    r"conservative\w*|gop|bush|kerry|cheney|clinton|hillary|obama|trump|putin|chavez|castro|abortion|pro.?life|"
    r"pro.?choice|gun control|second amendment|guns?|immigra\w*|illegal aliens?|same.sex|gay marriage|"
    r"death penalty|capital punishment|iraq war|israel\w*|palestin\w*|terroris\w*|patriot act)\b",
    re.I,
)


def fetch(raw_dir: Path) -> None:
    out = raw_dir / "test.parquet"
    if out.exists():
        return
    r = httpx.get(URL, follow_redirects=True, timeout=180)
    r.raise_for_status()
    out.write_bytes(r.content)


def _clean(t: str) -> str:
    t = html.unescape((t or "").replace("\\n", "\n"))
    t = re.sub(r"<br\s*/?>", "\n", t, flags=re.I)
    lines = [" ".join(line.split()) for line in t.split("\n")]
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()


def normalize(raw_dir: Path) -> Iterator[Question]:
    df = pl.read_parquet(raw_dir / "test.parquet")
    seen: set[str] = set()
    pools: dict[str, list[tuple[int, str, list[str]]]] = defaultdict(list)
    for qid, topic, title, content in df.select("id", "topic", "question_title", "question_content").iter_rows():
        title, content = _clean(title), _clean(content)
        text = f"{title}\n\n{content}" if content else title
        if len(title) < 10 or text.lower() in seen:
            continue
        seen.add(text.lower())
        if SLUR.search(text):
            continue
        sexual = bool(SEXUAL.search(text))
        if sexual and MINOR.search(text):
            continue
        flags = []
        if sexual or SELF_HARM.search(text) or GRAPHIC.search(text):
            flags.append("sensitive")
        if POLITICAL.search(text):
            flags.append("political")
        pools[LABELS[topic]].append((qid, text, flags))

    per = TARGET // len(LABELS)
    picked = []
    for i, lab in enumerate(LABELS):
        k = per + (1 if i < TARGET - per * len(LABELS) else 0)
        picked += [(*x, lab) for x in hash_order(pools[lab], lambda x: x[0], "yahoo_topics.category")[:k]]

    for qid, text, flags, lab in sorted(picked):
        if len(text) > 1500:
            text = text[:1500].rsplit(" ", 1)[0] + " …"
        yield Question(
            text=TEXT,
            primitive="choice",
            hemisphere="machine",
            origin="dataset",
            source=NAME,
            options=TOPICS,
            state={"question": text},
            shape="classify",
            node_hint="machine.documents.taxonomy_classification",
            template_id="yahoo_topics.category",
            source_item_id=f"test:{qid}",
            license=LICENSE,
            truth=lab,
            meta={"split": "test", **({"flags": flags} if flags else {})},
        )
