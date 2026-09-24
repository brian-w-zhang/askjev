"""GlobalOpinionQA (Anthropic/llm_global_opinions): Pew GAS + WVS items with per-country shares."""

from __future__ import annotations

import ast
import csv
import random
import re
from pathlib import Path
from typing import Iterator

import httpx

from askjev.model import HumanDist, Question

NAME = "globalopinionqa"
URL = "https://huggingface.co/datasets/Anthropic/llm_global_opinions/resolve/main/data/global_opinions.csv"
LICENSE = "CC BY-NC-SA 4.0"
POLITICAL_CAP = 170
SEED = 20260924
HUMAN_TEXT = "What would most people answer to this survey question?"

MISSING = re.compile(r"^(no answer|missing|other missing|inap|not asked|total\b|refused$)", re.I)
DK = re.compile(r"^(dk|don.?t know|dk/refused|don.?t know/refused|hard to say)\b", re.I)
NUMERIC = re.compile(r"^\d+(\.\d+)?$")
BAD_OPTION = re.compile(r"^statement #\d", re.I)
POLITICAL = re.compile(
    r"(\belect\w*|\bvot(e|es|ed|ing|ers?)\b|\bpart(y|ies)\b|government|\bpresident|prime minister|chancellor|"
    r"\bleaders?\b|democra\w*|immigra\w*|refugee|asylum|military|\bwars?\b|troops|\barmy\b|\bnato\b|"
    r"united nations|\bthe UN\b|european union|\bEU\b|terror\w*|abortion|homosexual\w*|\bgays?\b|lesbian|"
    r"same-sex|transgender|opposite sex|death penalty|politic\w*|parliament|congress|sanction|nuclear|islam\w*|"
    r"muslim|\bjews?\b|jewish|christians?\b|israel\w*|palestin\w*|putin|obama|trump|bush|merkel|modi|mubarak|"
    r"xi jinping|iran|taliban|\bisis\b|al qaeda|drone|protest\w*|capitalis\w*|communis\w*|socialis\w*|"
    r"free market|\btrade\b|tariff|\bborders?\b|entry into our country|minorit\w*|\brac(e|es|ial)\b|ethnic\w*|"
    r"crimea|ukrain\w*|syria\w*|iraq\w*|afghan\w*|brexit|superpower|\ballies\b|\bally\b|enemy|censor\w*|"
    r"\bguns?\b|climate change|global warming|opinion of|world affairs|foreign|\bpartner of|\bcorrupt\w*|"
    r"unification|independen\w*|constitution|referendum|\bveil\b|sharia|\barabs?\b|religious leaders|"
    r"\bpolice\b|\bcourts?\b|the press|civil service|\bstate\b|dictator\w*|human rights|tax\w*|welfare|"
    r"in power|since 19\d\d|\bprogram\b|influence in the world|\bu\.s\.|united states|americans?\b|china|"
    r"chinese|russia\w*|german\w*|japan\w*|india\b|pakistan\w*|europe\w*|groups of people in your country)",
    re.I,
)
SENSITIVE = re.compile(r"\b(sex|sexual\w*|menstruat\w*|suicide)\b", re.I)
VALUES = re.compile(
    r"(moral\w*|justif\w*|\bshould\b|\bduty\b|acceptable|\bright\b|\bwrong\b|qualities that children|"
    r"important in (your )?life|agree|believe in)",
    re.I,
)
TOPICS = [
    (r"(health|disease|flu|hospital|doctor|medic\w*|hiv|aids)", "world.health"),
    (r"(god|heaven|hell|religio\w*|pray\w*|church|mosque|spirit\w*)", "world.society.world_religions"),
    (r"(school|educat\w*|universit\w*|teacher)", "world.society.education"),
    (r"(news|newspaper|television|radio|internet|social media)", "world.society.media_news"),
    (r"(crime|violence|violent|police|safety|security|stolen|robber\w*)", "world.society.crime_law"),
    (r"(robot|computer|technolog\w*|smartphone|cell phone|mobile phone|landline)", "world.tech"),
    (r"(pollution|environment\w*|air|water|earthquake|tsunami|hurricane)", "world.nature.ecosystems_conservation"),
    (r"(job|employment|work|econom\w*|income|poor|rich|wealth|price|money|bank|business|compan\w*|standard of living)", "world.money.economics"),
    (r"(science|scientif\w*)", "world.science"),
    (r"(sport|olympic|world cup)", "world.sports"),
]


def fetch(raw_dir: Path) -> None:
    out = raw_dir / "global_opinions.csv"
    if out.exists():
        return
    r = httpx.get(URL, follow_redirects=True, timeout=300)
    r.raise_for_status()
    out.write_bytes(r.content)


def _question_text(q: str | None) -> str | None:
    q = (q or "").strip()
    if not q:
        return None
    if re.search(r"_{3,}", q):
        m = re.search(r"\s[a-z]\.\s*\.?(.+)$", q)
        if not m:
            return None
        item = m.group(1).strip().rstrip(".?")
        q = re.sub(r"_{3,}", item, q[: m.start()]).strip()
    q = re.sub(r"\s+", " ", q).strip()
    if re.match(r"^do you think this is\b", q, re.I):
        return None
    return q


def _option_text(o: str) -> str:
    o = re.sub(r"\((vol|do not read|volunteered)\.?\)", "", o, flags=re.I)
    o = o.replace("(survey country)", "this country")
    return re.sub(r"\s+", " ", o).strip()


def _slug(text: str, words: int) -> str:
    toks = re.findall(r"[a-z0-9]+", text.lower().replace("’", "'").replace("'", ""))
    return "_".join(toks[:words]) or "option"


def _keys(opts: list[str]) -> list[str]:
    """Short readable keys: 'dont_know' for DK, else the shortest distinct word-prefix slug (max 5 words)."""
    for words in (3, 4, 5, 8, 50):
        keys = ["dont_know" if DK.match(o) else _slug(o, words) for o in opts]
        if len(set(keys)) == len(keys):
            return keys
    return [f"{k}_{i}" for i, k in enumerate(keys)]


def _population(country: str, taken: set[str]) -> str:
    c = re.sub(r"\s*\((current|old|new)[^)]*\)", "", country, flags=re.I).strip()
    return country.strip() if c in taken else c


def _node(text: str) -> str:
    for pat, node in TOPICS:
        if re.search(r"\b" + pat + r"\b", text, re.I):
            return node
    return "world.society"


def _parse(raw_dir: Path) -> list[tuple[bool, Question]]:
    out = []
    with open(raw_dir / "global_opinions.csv", newline="", encoding="utf-8") as fh:
        for i, r in enumerate(csv.DictReader(fh)):
            text = _question_text(r["question"])
            if not text:
                continue
            opts = [str(o) for o in ast.literal_eval(r["options"])]
            sel = ast.literal_eval(r["selections"].removeprefix("defaultdict(<class 'list'>, ").removesuffix(")"))
            if any(len(v) != len(opts) for v in sel.values()):
                continue
            idx = [j for j, o in enumerate(opts) if not MISSING.match(o.strip())]
            if len(idx) < 2 or any(NUMERIC.match(opts[j].strip()) or BAD_OPTION.match(opts[j].strip()) for j in idx):
                continue
            # Garbled rows merge several questions: countries answer disjoint option sets.
            supports = [frozenset(j for j in idx if v[j] > 0 and not DK.match(opts[j])) for v in sel.values()]
            supports = [s for s in supports if s]
            if any(not (a & b) for a in supports for b in supports):
                continue
            used = [j for j in idx if any(v[j] > 0 for v in sel.values())]
            if len(used) < 2:
                continue
            texts = [_option_text(opts[j]) for j in used]
            keys = _keys(texts)
            options = {k: t for k, t in zip(keys, texts)}
            human, taken = [], set()
            for country, v in sel.items():
                tot = sum(v[j] for j in used)
                if tot <= 0:
                    continue
                pop = _population(country, taken)
                taken.add(pop)
                human.append(HumanDist(population=pop, distribution={k: v[j] / tot for k, j in zip(keys, used)},
                                       source=f"{r['source']} via Anthropic/llm_global_opinions"))
            if not human:
                continue
            blob = text + " " + " ".join(texts)
            political = bool(POLITICAL.search(blob))
            flags = (["political"] if political else []) + (["sensitive"] if SENSITIVE.search(blob) else [])
            meta = {"source_survey": r["source"]}
            if flags:
                meta["flags"] = flags
            out.append((political, Question(
                text=text,
                primitive="choice",
                hemisphere="world",
                kind="values" if VALUES.search(text) else "social",
                origin="dataset",
                source=NAME,
                options=options,
                node_hint=_node(text),
                human_text=HUMAN_TEXT,
                source_item_id=f"row{i}",
                license=LICENSE,
                human=human,
                meta=meta,
            )))
    return out


def normalize(raw_dir: Path) -> Iterator[Question]:
    parsed = _parse(raw_dir)
    seen = set()
    nonpol, pol = [], []
    for political, q in parsed:
        if q.id in seen:
            continue
        seen.add(q.id)
        (pol if political else nonpol).append(q)
    rng = random.Random(SEED)
    pol = rng.sample(pol, min(POLITICAL_CAP, len(pol)))
    yield from sorted(nonpol + pol, key=lambda q: int(q.source_item_id[3:]))
