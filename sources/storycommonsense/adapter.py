"""StoryCommonsense (Rashkin, Bosselut, Sap, Knight & Choi 2018, "Modeling Naive Psychology of Characters in
Simple Commonsense Stories"): five-sentence ROC stories where crowdworkers marked, line by line, each character's
emotions (Plutchik's eight) and motives (Maslow's needs). Two Choice templates with the story so far in state and
the annotators' category shares as the human distribution."""

from __future__ import annotations

import io
import json
import re
import zipfile
from collections import defaultdict
from pathlib import Path
from typing import Iterator

import httpx

from askjev.model import HumanDist, Question
from askjev.sampling import env_int, hash_order

NAME = "storycommonsense"
URL = "https://uwnlp.github.io/storycommonsense/data/storycommonsense_data.zip"
LICENSE = ("StoryCommonsense annotations (Rashkin et al. 2018, UW / AI2), public research release with no explicit "
           "license; stories from ROCStories (Mostafazadeh et al. 2016). Research use with citation.")
TARGET_EMOTION = env_int("TARGET_STORYCOMMONSENSE_EMOTION", 5000)
TARGET_MOTIVE = env_int("TARGET_STORYCOMMONSENSE_MOTIVE", 5000)
SALT = "storycommonsense-v1"
PER_STORY = 2  # at most this many questions per story and template

EMO_TEXT = "Which emotion best describes the feelings of {who} at the end of `story`?"
MOT_TEXT = "Which need best explains the actions or wishes of {who} in the last sentence of `story`?"
EMOTIONS = {
    "joy": "joy or happiness", "trust": "trust or acceptance", "fear": "fear or worry", "surprise": "surprise",
    "sadness": "sadness", "disgust": "disgust", "anger": "anger or annoyance",
    "anticipation": "anticipation, looking forward to something", "no_clear_emotion": "no clear emotion",
}
NEEDS = {
    "physiological": "physical needs: food, rest, health",
    "stability": "stability: safety, order, money, a secure life",
    "love": "love and belonging: family, friends, romance, company",
    "esteem": "esteem: status, approval, winning, respect",
    "spiritual_growth": "growth: curiosity, learning, independence, ideals, creativity",
    "no_clear_need": "no clear need or motive",
}
MASLOW = {"physiological": "physiological", "stability": "stability", "love": "love", "esteem": "esteem",
          "spiritual growth": "spiritual_growth", "none": "no_clear_need"}
NODE_EMO = "self.mind.reading_people.reading_feelings"
NODE_MOT = "self.mind.reading_people.reading_motives"

PRONOUNISH = {"everyone", "everybody", "someone", "somebody", "people", "others", "all", "anyone", "one", "nobody",
              "something", "it", "many", "herself", "himself", "they", "he", "she"}
SEXUAL = re.compile(r"\b(sex\w*|porn\w*|naked|nude|orgasm\w*|erotic\w*|condoms?|horny|strip(per|ping)|"
                    r"one night stand|slept with|hook(ed)? up)\b", re.I)
SELF_HARM = re.compile(r"\b(suicid\w*|kill(ed|ing)? (my|him|her|them)sel(f|ves)|self[- ]harm\w*|overdos\w*)\b", re.I)
VIOLENT = re.compile(r"\b(murder\w*|rap(e|es|ed|ing|ists?)|stab\w*|molest\w*|assault\w*|abus(e|ed|ive)|shooting\w*|"
                     r"shot (him|her|them|me)|kidnap\w*)\b", re.I)
SLUR = re.compile(r"\b(n[i1]gg\w*|fag\w*|retard\w*|spic|chink|kike)\b", re.I)
POLITICAL = re.compile(r"\b(trump|obama|clinton|hillary|republican\w*|democrat\w*|election\w*|abortion|immigra\w*|"
                       r"gun control|politic\w*|vot(e|ed|ing) for|protest\w*)\b", re.I)


def fetch(raw_dir: Path) -> None:
    if (raw_dir / "json_version" / "annotations.json").exists():
        return
    r = httpx.get(URL, follow_redirects=True, timeout=600)
    r.raise_for_status()
    (raw_dir / "storycommonsense_data.zip").write_bytes(r.content)
    with zipfile.ZipFile(io.BytesIO(r.content)) as zf:
        zf.extract("json_version/annotations.json", raw_dir)


def _who(name: str, story: str) -> str | None:
    """How the question refers to the character, or None if it can't be named cleanly."""
    if name == "I (myself)":
        return "the narrator"
    words = name.split()
    low = name.lower()
    if low in PRONOUNISH or not re.fullmatch(r"[A-Za-z][A-Za-z' .-]*", name):
        return None
    if len(words) == 2 and words[0].lower() == "my":
        return f"the narrator's {words[1].lower()}" if re.search(rf"\bmy {re.escape(words[1])}\b", story, re.I) else None
    if len(words) == 2 and words[0].lower() == "the":
        return f"the {words[1].lower()}" if re.search(rf"\b{re.escape(low)}\b", story, re.I) else None
    if len(words) != 1:
        return None
    hits = re.findall(rf"\b{re.escape(name)}\b", story, re.I)
    if not hits:
        return None
    if any(h[0].islower() for h in hits):  # used as a common noun in the story ("my dog", "the friends")
        return f"the {low}"
    return name


def _dist(anns: list[list[str]], mapper) -> dict[str, float] | None:
    """Each annotator's unit split evenly over the categories they ticked. None unless some category was ticked by
    a majority of the annotators (flat three-way splits are too noisy to be a question)."""
    tot, votes = defaultdict(float), defaultdict(int)
    for cats in anns:
        keys = {k for k in (mapper(c) for c in cats) if k}
        if not keys:
            return None
        for k in keys:
            tot[k] += 1 / len(keys)
            votes[k] += 1
    if max(votes.values()) * 2 <= len(anns):
        return None
    n = sum(tot.values())
    return {k: round(v / n, 4) for k, v in sorted(tot.items(), key=lambda kv: -kv[1])}


def _emo_key(c: str) -> str | None:
    return c.split(":")[0] if c.split(":")[0] in EMOTIONS else None


def _items(raw_dir: Path) -> tuple[list[dict], list[dict]]:
    data = json.loads((raw_dir / "json_version" / "annotations.json").read_text(encoding="utf-8"))
    emo, mot = [], []
    for sid, s in data.items():
        if s["partition"] not in ("dev", "test"):  # only dev/test carry the categorical labels
            continue
        lines = [s["lines"][str(i)]["text"].strip() for i in range(1, len(s["lines"]) + 1)]
        for ln in range(1, len(lines) + 1):
            story = " ".join(lines[:ln])
            for name, a in s["lines"][str(ln)]["characters"].items():
                if not a.get("app"):
                    continue
                who = _who(name, story)
                if not who:
                    continue
                base = {"story_id": sid, "line": ln, "char": name, "who": who, "story": story,
                        "partition": s["partition"], "title": s.get("title")}
                e_anns = [x["plutchik"] or ["no_clear_emotion"] for x in a["emotion"].values() if "plutchik" in x]
                if len(e_anns) >= 3:
                    d = _dist(e_anns, lambda c: "no_clear_emotion" if c == "no_clear_emotion" else _emo_key(c))
                    if d:
                        emo.append({**base, "dist": d, "n": len(e_anns), "raw": e_anns})
                m_anns = [x["maslow"] or ["none"] for x in a["motiv"].values() if "maslow" in x]
                if len(m_anns) >= 3:
                    d = _dist(m_anns, lambda c: MASLOW.get(c))
                    if d:
                        mot.append({**base, "dist": d, "n": len(m_anns), "raw": m_anns})
    return emo, mot


def _pick(pool: list[dict], k: int, salt: str) -> list[dict]:
    out, per = [], defaultdict(int)
    for it in hash_order(pool, key=lambda x: f"{x['story_id']}|{x['line']}|{x['char']}", salt=salt):
        if len(out) >= k:
            break
        if per[it["story_id"]] >= PER_STORY:
            continue
        per[it["story_id"]] += 1
        out.append(it)
    return out


def _question(it: dict, text: str, options: dict, node: str, tid: str, what: str) -> Question | None:
    s = it["story"]
    if SLUR.search(s):
        return None
    flags = []
    if SEXUAL.search(s) or SELF_HARM.search(s) or VIOLENT.search(s):
        flags.append("sensitive")
    if POLITICAL.search(s):
        flags.append("political")
    meta = {"partition": it["partition"], "line": it["line"], "character": it["char"], "annotator_labels": it["raw"]}
    if flags:
        meta["flags"] = flags
    return Question(
        text=text.format(who=it["who"]),
        primitive="choice",
        hemisphere="self",
        kind="social",
        origin="template",
        source=NAME,
        options=options,
        state={"story": s},
        node_hint=node,
        source_item_id=f"{it['story_id']}:{it['line']}:{it['char']}:{what}",
        license=LICENSE,
        human=[HumanDist(population="StoryCommonsense MTurk annotators", distribution=it["dist"], n=it["n"],
                         source="Rashkin et al. 2018 dev/test categorical annotations")],
        template_id=tid,
        meta=meta,
    )


def normalize(raw_dir: Path) -> Iterator[Question]:
    emo, mot = _items(raw_dir)
    for it in _pick(emo, TARGET_EMOTION, SALT + "|emotion"):
        q = _question(it, EMO_TEXT, EMOTIONS, NODE_EMO, f"{NAME}.emotion", "emotion")
        if q:
            yield q
    for it in _pick(mot, TARGET_MOTIVE, SALT + "|motive"):
        q = _question(it, MOT_TEXT, NEEDS, NODE_MOT, f"{NAME}.motive", "motive")
        if q:
            yield q
