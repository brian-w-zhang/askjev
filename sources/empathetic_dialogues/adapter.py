"""EmpatheticDialogues (Rashkin et al. 2019, Facebook AI, CC BY-NC 4.0): crowdworkers were each given one of 32
emotion words and wrote a short situation from their own life in which they felt it. Asked as a 32-way Choice
("which emotion was this person feeling?") with the situation in state and the assigned emotion as truth."""

from __future__ import annotations

import io
import re
import tarfile
from pathlib import Path
from typing import Iterator

import httpx

from askjev.model import Question
from askjev.sampling import env_int, hash_order

NAME = "empathetic_dialogues"
URL = "https://dl.fbaipublicfiles.com/parlai/empatheticdialogues/empatheticdialogues.tar.gz"
LICENSE = "CC BY-NC 4.0 (facebookresearch/EmpatheticDialogues)"
TARGET = env_int("TARGET_EMPATHETIC_DIALOGUES", 5000)
SALT = "empathetic_dialogues-v1"
SPLITS = ("train", "valid", "test")
TEXT = "Someone wrote `situation` about a time in their own life. Which emotion were they feeling?"
NODE = "self.mind.reading_people.reading_feelings"

EMOTIONS = [
    "afraid", "angry", "annoyed", "anticipating", "anxious", "apprehensive", "ashamed", "caring", "confident",
    "content", "devastated", "disappointed", "disgusted", "embarrassed", "excited", "faithful", "furious",
    "grateful", "guilty", "hopeful", "impressed", "jealous", "joyful", "lonely", "nostalgic", "prepared", "proud",
    "sad", "sentimental", "surprised", "terrified", "trusting",
]
# label stems: a situation naming any label word (or a near form) is dropped
GIVEAWAY = {
    "afraid": r"afraid", "angry": r"angr|anger", "annoyed": r"annoy", "anticipating": r"anticipat",
    "anxious": r"anxi", "apprehensive": r"apprehens", "ashamed": r"asham|shame", "caring": r"caring",
    "confident": r"confiden", "content": r"content", "devastated": r"devastat", "disappointed": r"disappoint",
    "disgusted": r"disgust", "embarrassed": r"embarras", "excited": r"excit", "faithful": r"faith",
    "furious": r"furious|fury", "grateful": r"grateful|gratitude|thankful", "guilty": r"guilt",
    "hopeful": r"hope|hoping", "impressed": r"impress", "jealous": r"jealous|envy|envious", "joyful": r"joy",
    "lonely": r"lonel", "nostalgic": r"nostalg", "prepared": r"prepar", "proud": r"proud|pride",
    "sad": r"sad", "sentimental": r"sentiment", "surprised": r"surpris", "terrified": r"terrif",
    "trusting": r"trust",
}
ANY_LABEL = re.compile(r"\b(" + "|".join(GIVEAWAY.values()) + ")", re.I)

SEXUAL = re.compile(r"\b(sex\w*|porn\w*|nudes?|naked|orgasm\w*|erotic\w*|condoms?|horny|one night stand|"
                    r"hook(ed)? up|slept with|spent the night together)\b", re.I)
SELF_HARM = re.compile(r"\b(suicid\w*|kill(ed|ing)? (my|him|her|them)sel(f|ves)|self[- ]harm\w*|overdos\w*|cutting myself)\b", re.I)
VIOLENT = re.compile(r"\b(murder\w*|rap(e|es|ed|ing|ists?)|shooting\w*|stab\w*|molest\w*|assault\w*|abus(e|ed|ive))\b", re.I)
DEATH = re.compile(r"\b(died|dead|death|passed away|funeral|cancer|killed)\b", re.I)
SLUR = re.compile(r"\b(n[i1]gg\w*|fag\w*|retard\w*|tranny|spic|chink|kike)\b", re.I)
POLITICAL = re.compile(r"\b(trump|obama|clinton|biden|hillary|republican\w*|democrat\w*|election|elected|"
                       r"abortion|immigra\w*|gun control|nra|liberal\w*|conservative\w*|politic\w*)\b", re.I)


def fetch(raw_dir: Path) -> None:
    if all((raw_dir / "empatheticdialogues" / f"{s}.csv").exists() for s in SPLITS):
        return
    r = httpx.get(URL, follow_redirects=True, timeout=600)
    r.raise_for_status()
    with tarfile.open(fileobj=io.BytesIO(r.content), mode="r:gz") as tf:
        tf.extractall(raw_dir, filter="data")


def _clean(s: str) -> str:
    s = s.replace("_comma_", ",")
    s = re.sub(r"\s+", " ", s).strip()
    s = re.sub(r"\s+([,.!?])", r"\1", s)
    s = re.sub(r"\bi\b", "I", s)
    return s[:1].upper() + s[1:]


def _situations(raw_dir: Path) -> list[dict]:
    out, seen = [], set()
    for split in SPLITS:
        convs = {}
        with open(raw_dir / "empatheticdialogues" / f"{split}.csv", encoding="utf-8") as fh:
            next(fh)
            for line in fh:
                p = line.rstrip("\n").split(",")
                if len(p) < 8 or p[0] in convs:
                    continue
                convs[p[0]] = (p[2], p[3])
        for conv_id, (emo, prompt) in convs.items():
            sit = _clean(prompt)
            key = sit.lower()
            if emo not in EMOTIONS or key in seen:
                continue
            seen.add(key)
            out.append({"id": f"{split}:{conv_id}", "split": split, "emotion": emo, "situation": sit})
    return out


def normalize(raw_dir: Path) -> Iterator[Question]:
    pool = []
    for d in _situations(raw_dir):
        s = d["situation"]
        words = len(s.split())
        if words < 6 or len(s) > 600 or SLUR.search(s):
            continue
        if ANY_LABEL.search(s):  # names its own label (a giveaway) or another label (a misleading cue)
            continue
        pool.append(d)
    # balanced over the 32 emotions: round-robin through each label's salted-hash order
    by = {e: hash_order([d for d in pool if d["emotion"] == e], key=lambda d: d["id"], salt=SALT) for e in EMOTIONS}
    picked, i = [], 0
    while len(picked) < TARGET and any(i < len(v) for v in by.values()):
        for e in EMOTIONS:
            if i < len(by[e]) and len(picked) < TARGET:
                picked.append(by[e][i])
        i += 1
    for d in picked:
        s = d["situation"]
        flags = []
        if SEXUAL.search(s) or SELF_HARM.search(s) or VIOLENT.search(s):
            flags.append("sensitive")
        if POLITICAL.search(s):
            flags.append("political")
        meta = {"split": d["split"]}
        if DEATH.search(s):
            meta["mentions_death"] = True
        if flags:
            meta["flags"] = flags
        yield Question(
            text=TEXT,
            primitive="choice",
            hemisphere="self",
            kind="social",
            origin="template",
            source=NAME,
            options={e: None for e in EMOTIONS},
            state={"situation": s},
            node_hint=NODE,
            source_item_id=d["id"],
            license=LICENSE,
            truth=d["emotion"],
            template_id=f"{NAME}.emotion",
            meta=meta,
        )
