"""ProtoQA dev (Family Feud survey questions): "Which of these would most people name first?" over the top answers."""

from __future__ import annotations

import json
import random
import re
from pathlib import Path
from typing import Iterator

import httpx

from askjev.model import HumanDist, Question

NAME = "protoqa"
BASE = "https://raw.githubusercontent.com/iesl/protoqa-data/master/data/dev"
FILES = ["dev.scraped.jsonl", "dev.crowdsourced.jsonl"]
LICENSE = "CC BY 4.0 (iesl/protoqa-data); answer clusters scraped from Family Feud fan sites"
TARGET = 150
SEED = "protoqa-20260924"
MIN_OPTIONS, MAX_OPTIONS = 4, 6
MIN_TOTAL = 80  # survey answers covered by the listed clusters (Family Feud surveys ~100 people)

# Questions whose answers are numbers, letters, or counts break §7 (no arithmetic/counting).
NUMERIC_Q = re.compile(
    r"\b(how many|how much|how old|what age|at what age|what year|what time|how long|how far|letters?|"
    r"number|percent|degrees?|minutes?|hours?|dollars?|price)\b",
    re.I,
)
SLURS = re.compile(r"\b(fag\w*|nigg\w*|retard\w*|tranny|dyke|spic|chink|kike|gook)\b", re.I)
SEXUAL = re.compile(
    r"\b(sex\w*|porn\w*|nude|naked|orgasm\w*|virgin\w*|penis\w*|vagina\w*|boobs?|breasts?|condoms?|"
    r"strip\w*|lingerie|erotic\w*|kinky|horny|foreplay|viagra|affair|bedroom activit\w*)\b",
    re.I,
)
SELF_HARM = re.compile(r"\b(suicid\w*|kill (yourself|himself|herself|themselves)|overdose)\b", re.I)

# (pattern, node_hint) first match wins; self hemisphere unless the node starts with "world."
NODES = [
    (r"\b(cartoons?|tv|television|sitcoms?|soap operas?|talk shows?|game shows?)\b", "world.arts.television"),
    (r"\b(movies?|films?|actors?|actress\w*|hollywood|superhero\w*|disney)\b", "world.arts.film"),
    (r"\b(books?|novels?|lord of the rings|harry potter|fairy ?tales?|nursery rhymes?)\b", "world.arts.books"),
    (r"\b(celebrit\w*|famous)\b", "world.arts.celebrities"),
    (r"\b(danc\w*|ballet|ballroom)\b", "world.arts.theatre_dance"),
    (r"\b(knights?|kings?|queens?|castles?|medieval|pirates?|cowboys?|ancient|president\w*)\b", "world.history"),
    (r"\b(police|cops?|crim\w*|jail|prison|law\w*|ticket\w*|violation|court|judge|thief|steal\w*|rob\w*)\b", "world.society.crime_law"),
    (r"\b(church|priest|pastor|bible|god|heaven|pray\w*|relig\w*)\b", "world.society.world_religions"),
    (r"\b(countr\w*|cit(y|ies)|states?|italy|france|paris|mexico|canada|england|new york|las vegas|hawaii|california|texas|florida)\b", "world.places"),
    (r"\b(weather|rain\w*|snow\w*|hot day|summer|winter|storms?)\b", "world.nature.weather_climate"),
    (r"\b(boyfriend|girlfriend|date|dating|kiss\w*|romantic|romance|flirt\w*|crush|valentine)\b", "self.love.dating_attraction"),
    (r"\b(husbands?|wife|wives|spouses?|partners?|couples?|married|marriage|wedding|honeymoon|divorce\w*|in-laws?)\b", "self.love.romance_partnership"),
    (r"\b(friends?|best friend|roommates?|neighbou?rs?)\b", "self.love.friendship"),
    (r"\b(mom|mother|dad|father|parents?|kids?|child\w*|baby|babies|toddlers?|teen\w*|grandm\w*|grandp\w*|family|sibling\w*)\b", "self.love.family_parenting"),
    (r"\b(boss|job|work\w*|office|cowork\w*|employ\w*|school|teacher|student|college|class)\b", "self.lifestyle.work_study_life"),
    (r"\b(polite|rude|manners|etiquette|embarrass\w*|apolog\w*|compliment\w*|gift|guest|host)\b", "self.love.etiquette_social_norms"),
    (r"\b(bed|bedtime|sleep\w*|wake|morning|shower\w*|bath|brush\w*|routine|habit\w*)\b", "self.lifestyle.habits_routines"),
    (r"\b(dogs?|cats?|pets?|puppy|kitten)\b", "self.lifestyle.pets"),
    (r"\b(animals?|birds?|insects?|bugs?|fish|zoo|farm animal\w*|wild)\b", "world.nature"),
    (r"\b(eat\w*|food|fruit\w*|vegetables?|meal|breakfast|lunch|dinner|snack\w*|restaurant|pizza|sandwich\w*|dessert|candy|cook\w*|bake\w*|recipe)\b", "world.food"),
    (r"\b(drinks?|beverages?|beer|wine|coffee|soda|bar|bartender)\b", "world.food"),
    (r"\b(house|home|kitchen|bathroom|garage|yard|furniture|room|closet|attic|basement|clean\w*)\b", "self.lifestyle.home_living"),
    (r"\b(wear\w*|cloth\w*|dress\w*|shoes?|hair\w*|makeup|jewelry|fashion|hat)\b", "self.lifestyle.style_appearance"),
    (r"\b(vacation|travel\w*|trip|airport|airplane|plane|hotel|beach|tourists?|luggage|camping)\b", "self.lifestyle.travel_preferences"),
    (r"\b(money|buy\w*|pay\w*|store|shop\w*|spend\w*|cheap|expensive|bank|wallet|purse)\b", "self.lifestyle.money_habits"),
    (r"\b(phones?|computers?|internet|video games?|radio|email|social media)\b", "self.lifestyle.screens_media"),
    (r"\b(car|drive\w*|driving|traffic|road)\b", "world.tech.vehicles"),
    (r"\b(doctors?|dentists?|sick|hospital|health|medicine|hurt|pain|injur\w*|nurse)\b", "world.health"),
    (r"\b(christmas|halloween|thanksgiving|easter|birthday|holiday\w*|new year)\b", "world.society.holidays_traditions"),
    (r"\b(sports?|football|baseball|basketball|soccer|golf|tennis|hockey|olympic\w*|athlete)\b", "world.sports"),
    (r"\b(music|song|singer|band|instrument)\b", "world.arts.music"),
    (r"\b(hobby|hobbies|weekend|party|parties|fun|game|games|play\w*)\b", "self.lifestyle.leisure_hobbies"),
]
NODES = [(re.compile(p, re.I), n) for p, n in NODES]


def fetch(raw_dir: Path) -> None:
    for f in FILES:
        out = raw_dir / f
        if out.exists():
            continue
        r = httpx.get(f"{BASE}/{f}", follow_redirects=True, timeout=120)
        r.raise_for_status()
        out.write_bytes(r.content)


def _sentence(s: str) -> str:
    s = re.sub(r"\s+", " ", s).strip()
    s = re.sub(r"\bi\b", "I", s)
    s = s[:1].upper() + s[1:]
    return s if s[-1:] in ".?!" else s + "."


def _key(s: str) -> str:
    s = re.sub(r"\s+", " ", s).strip()
    return s[:1].upper() + s[1:]


def _node(q: str) -> str:
    for pat, node in NODES:
        if pat.search(q):
            return node
    return "self.lifestyle"


def normalize(raw_dir: Path) -> Iterator[Question]:
    # Only the scraped dev set: one clean label per cluster from a ~100-person survey. The 51 crowdsourced
    # dev questions have heterogeneous clusters with no label (e.g. "the streets / traffic light / new york
    # city"), so they can't give readable option keys.
    rows = []
    for line in open(raw_dir / "dev.scraped.jsonl", encoding="utf-8"):
        d = json.loads(line)
        q = _sentence(d["question"]["normalized"])
        clusters = sorted(
            ((_key(c["answers"][0]), c["count"]) for c in d["answers"]["clusters"].values() if c["count"] > 0),
            key=lambda kc: -kc[1],
        )[:MAX_OPTIONS]
        keys = [k for k, _ in clusters]
        total = sum(c for _, c in clusters)
        text = q + " " + " ".join(keys)
        if (
            len(clusters) < MIN_OPTIONS
            or total < MIN_TOTAL
            or NUMERIC_Q.search(q)
            or any(re.search(r"\d", k) for k in keys)
            or any(len(k) > 40 for k in keys)
            or len({k.lower() for k in keys}) < len(keys)
            or SLURS.search(text)
        ):
            continue
        rows.append((d["metadata"]["id"], q, clusters, total, d["num"]["answers"], d["metadata"]["source"]))

    rng = random.Random(SEED)
    picked = sorted(rng.sample(rows, min(TARGET, len(rows))), key=lambda r: int(r[0].rsplit("q", 1)[1]))
    for qid, q, clusters, total, all_answers, src in picked:
        node = _node(q)
        text = f'Which of these would most people name first when asked: "{q}"'
        both = q + " " + " ".join(k for k, _ in clusters)
        flags = ["sensitive"] if SEXUAL.search(both) or SELF_HARM.search(both) else []
        yield Question(
            text=text,
            primitive="choice",
            hemisphere="world" if node.startswith("world.") else "self",
            kind="social",
            origin="dataset",
            source=NAME,
            options={k: None for k, _ in clusters},
            node_hint=node,
            human_text=text,
            source_item_id=qid,
            license=LICENSE,
            human=[
                HumanDist(
                    population="ProtoQA crowd",
                    distribution={k: c / total for k, c in clusters},
                    n=total,
                    source="ProtoQA dev.scraped (Family Feud survey answer counts)",
                )
            ],
            meta={
                "question": q,
                "counts": dict(clusters),
                "answers_all_clusters": all_answers,
                "answer_source": src,
                "dist_method": "cluster counts renormalized over the offered (top 4-6) clusters",
                **({"flags": flags} if flags else {}),
            },
        )
