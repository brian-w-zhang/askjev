"""Moral Foundations Questionnaire: MFQ-2 (Atari et al. 2023, 36 items) and MFQ-30 (Graham, Haidt &
Nosek 2008, 30 scored items). Item-level questions only; no norms, and never partisan norm splits."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterator

import httpx

from askjev.model import Question

NAME = "mfq"
LICENSE = "All rights reserved (MFQ authors); used privately for research"
MFQ30_KEY_URL = "https://moralfoundations.org/wp-content/uploads/files/MFQ30.item-key.doc"
MFQ30_FORM_URL = "https://moralfoundations.org/wp-content/uploads/files/MFQ30.doc"
MFQ2_URL = "https://arxiv.org/pdf/2507.10073"  # reproduces the MFQ-2 items and scoring key (Appendix B)

DESCRIBE = [
    "This does not describe me at all",
    "This describes me a little",
    "This describes me moderately well",
    "This describes me well",
    "This describes me very well",
]
RELEVANCE = [
    "I never take this into account when judging right and wrong",
    "I take this into account only in unusual cases",
    "This is a minor factor among many when I judge right and wrong",
    "This is a regular factor in my judgments of right and wrong",
    "This is one of the main factors in my judgments of right and wrong",
    "This is one of the most important factors when I judge right and wrong",
]

# MFQ-2 items in questionnaire order (Atari et al. 2023, JPSP). Foundation = position mod 6:
# care, equality, proportionality, loyalty, authority, purity. Transcribed from the scoring key in
# arXiv:2507.10073 Appendix B, which reproduces the published instrument.
MFQ2 = [
    "Caring for people who have suffered is an important virtue.",
    "The world would be a better place if everyone made the same amount of money.",
    "I think people who are more hardworking should end up with more money.",
    "I think children should be taught to be loyal to their country.",
    "I think it is important for societies to cherish their traditional values.",
    "I think the human body should be treated like a temple, housing something sacred within.",
    "I believe that compassion for those who are suffering is one of the most crucial virtues.",
    "Our society would have fewer problems if people had the same income.",
    "I think people should be rewarded in proportion to what they contribute.",
    "It upsets me when people have no loyalty to their country.",
    "I feel that most traditions serve a valuable function in keeping society orderly.",
    "I believe chastity is an important virtue.",
    "We should all care for people who are in emotional pain.",
    "I believe that everyone should be given the same quantity of resources in life.",
    "The effort a worker puts into a job ought to be reflected in the size of a raise they receive.",
    "Everyone should love their own community.",
    "I think obedience to parents is an important virtue.",
    "It upsets me when people use foul language like it is nothing.",
    "I am empathetic toward those people who have suffered in their lives.",
    "I believe it would be ideal if everyone in society wound up with roughly the same amount of money.",
    "It makes me happy when people are recognized on their merits.",
    "Everyone should defend their country, if called upon.",
    "We all need to learn from our elders.",
    "If I found out that an acquaintance had an unusual but harmless sexual fetish I would feel uneasy about them.",
    "Everyone should try to comfort people who are going through something hard.",
    "When people work together toward a common goal, they should share the rewards equally, even if some worked harder on it.",
    "In a fair society, those who work hard should live with higher standards of living.",
    "Everyone should feel proud when a person in their community wins in an international competition.",
    "I believe that one of the most important values to teach children is to have respect for authority.",
    "People should try to use natural medicines rather than chemically identical human-made ones.",
    "It pains me when I see someone ignoring the needs of another human being.",
    "I get upset when some people have a lot more money than others in my country.",
    "I feel good when I see cheaters get caught and punished.",
    "I believe the strength of a sports team comes from the loyalty of its members to each other.",
    "I think having a strong leader is good for society.",
    "I admire people who keep their virginity until marriage.",
]
MFQ2_FOUNDATIONS = ["care", "equality", "proportionality", "loyalty", "authority", "purity"]

# MFQ-30 foundation headers -> MFQ-2 node names. MFQ-30 "Fairness" mixes equality and
# proportionality, so it goes to the parent node.
MFQ30_NODE = {"Harm": "care", "Fairness": None, "Ingroup": "loyalty", "Authority": "authority", "Purity": "purity"}
NODE = "self.values.moral_foundations"
CATCH = {"MATH", "GOOD"}  # unscored attention-check items
SENSITIVE = re.compile(r"\b(sexual|fetish|virginity|chastity)\b", re.I)


def fetch(raw_dir: Path) -> None:
    headers = {"User-Agent": "Mozilla/5.0 (askjev research)"}
    for url in (MFQ30_KEY_URL, MFQ30_FORM_URL):
        out = raw_dir / Path(url).name
        if not out.exists():
            r = httpx.get(url, headers=headers, follow_redirects=True, timeout=60)
            r.raise_for_status()
            out.write_bytes(r.content)
    out = raw_dir / "arxiv-2507.10073.pdf"  # provenance for the MFQ-2 transcription
    if not out.exists():
        r = httpx.get(MFQ2_URL, headers=headers, follow_redirects=True, timeout=60)
        r.raise_for_status()
        out.write_bytes(r.content)


def _mfq30(raw_dir: Path) -> list[tuple[int, str, str, str]]:
    """(part, foundation, VARNAME, text) from the item-key .doc (its text stream is plain cp1252)."""
    t = (raw_dir / "MFQ30.item-key.doc").read_bytes().decode("cp1252", errors="replace")
    t = t[t.index("PART 1 ITEMS"):]
    out, part, found = [], 0, None
    for ln in re.split(r"[\r\n]+", t):
        ln = ln.strip()
        if ln.startswith("PART 1"):
            part, found = 1, None
        elif ln.startswith("PART 2"):
            part, found = 2, None
        elif ln.rstrip(":") in MFQ30_NODE and ln.endswith(":"):
            found = ln.rstrip(":")
        else:
            m = re.match(r"^([A-Z]{3,}) [-–] (.+)$", ln)
            if m and found and part and m.group(1) not in CATCH:
                text = m.group(2).replace("’", "'").strip()
                out.append((part, found, m.group(1), text))
        if len(out) == 30:
            break
    return out


def normalize(raw_dir: Path) -> Iterator[Question]:
    for i, stmt in enumerate(MFQ2):
        f = MFQ2_FOUNDATIONS[i % 6]
        yield Question(
            text=f'How well does this statement describe you: "{stmt}"',
            primitive="score",
            hemisphere="self",
            kind="values",
            origin="dataset",
            source=NAME,
            options=DESCRIBE,
            node_hint=f"{NODE}.{f}",
            human_text=f'How well would most people say this statement describes them: "{stmt}"',
            source_item_id=f"MFQ-2 item {i + 1}",
            license=LICENSE,
            meta={"instrument": "MFQ-2", "foundation": f, "item": i + 1}
            | ({"flags": ["sensitive"]} if SENSITIVE.search(stmt) else {}),
        )

    for part, found, var, stmt in _mfq30(raw_dir):
        node = MFQ30_NODE[found]
        if part == 1:
            consideration = stmt.rstrip(".")
            text = f'When you decide whether something is right or wrong, how relevant is this consideration: "{consideration}"?'
            human_text = (
                "When most people decide whether something is right or wrong, how relevant is this "
                f'consideration to them: "{consideration}"?'
            )
            options = RELEVANCE
        else:
            text = f'How well does this statement describe you: "{stmt}"'
            human_text = f'How well would most people say this statement describes them: "{stmt}"'
            options = DESCRIBE
        yield Question(
            text=text,
            primitive="score",
            hemisphere="self",
            kind="values",
            origin="dataset",
            source=NAME,
            options=options,
            node_hint=f"{NODE}.{node}" if node else NODE,
            human_text=human_text,
            source_item_id=f"MFQ-30 {var}",
            license=LICENSE,
            meta={
                "instrument": "MFQ-30",
                "part": "relevance" if part == 1 else "agreement",
                "foundation": found.lower(),
                "variable": var,
                "original_scale": "0-5 relevance" if part == 1 else "6-point disagree-agree (asked here as describes-me)",
            }
            | ({"flags": ["sensitive"]} if SENSITIVE.search(stmt) else {}),
        )
