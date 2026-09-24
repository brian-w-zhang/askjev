"""Canonical question record produced by every adapter/generator (docs/06-pipeline.md §5, §8)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Iterator

import orjson

from .jev import sha

PRIMITIVES = {"noul", "choice", "score"}
HEMISPHERES = {"world", "self", "machine"}
KINDS = {"personality", "values", "taste", "evaluative", "social", "factual", "forecast", "perception"}
SHAPES = {"classify", "detect", "score", "route", "rank", "verify", "extract"}
ORIGINS = {"dataset", "template", "wikidata-fact", "typesafe-docs", "synthetic", "mined", "asked"}


@dataclass
class HumanDist:
    population: str  # "global", "US", "FR", "OpenPsychometrics web", "MTurk x5" ...
    distribution: dict[str, float]  # option key (or level index as str, or "true"/"false") -> share
    n: int | None = None
    source: str | None = None
    wave: str | None = None


@dataclass
class Question:
    text: str  # self-frame question (Machine: the template's instructions)
    primitive: str  # noul | choice | score
    hemisphere: str  # world | self | machine
    origin: str
    source: str
    options: Any = None  # choice: {key: description|None}; score: [level descriptions low→high]; noul: {"true","false"}|None
    state: Any = None  # context; Machine: the real input
    kind: str | None = None  # world/self
    shape: str | None = None  # machine
    node_hint: str | None = None  # tree id for deterministic placement (e.g. "self.personality.big_five.extraversion")
    human_text: str | None = None  # optional explicit human-frame wording
    source_item_id: str | None = None
    license: str | None = None
    truth: Any = None  # choice: key; noul: bool; score: level index
    template_id: str | None = None
    human: list[HumanDist] = field(default_factory=list)
    meta: dict = field(default_factory=dict)

    @property
    def id(self) -> str:
        return sha({"p": self.primitive, "t": self.text.strip(), "o": self.options, "s": self.state})[:24]

    def validate(self) -> list[str]:
        errs = []
        if self.primitive not in PRIMITIVES:
            errs.append(f"bad primitive {self.primitive}")
        if self.hemisphere not in HEMISPHERES:
            errs.append(f"bad hemisphere {self.hemisphere}")
        if self.origin not in ORIGINS:
            errs.append(f"bad origin {self.origin}")
        if self.hemisphere == "machine":
            if self.shape not in SHAPES:
                errs.append(f"machine question needs shape, got {self.shape}")
        elif self.kind not in KINDS:
            errs.append(f"needs kind, got {self.kind}")
        if self.primitive == "choice":
            if not isinstance(self.options, dict) or not (2 <= len(self.options) <= 255):
                errs.append("choice needs 2-255 options dict")
        if self.primitive == "score":
            if not isinstance(self.options, list) or not (2 <= len(self.options) <= 10):
                errs.append("score needs 2-10 levels list")
        if not self.text or len(self.text) > 4000:
            errs.append("text empty or too long")
        return errs

    def to_json(self) -> bytes:
        d = asdict(self)
        d["id"] = self.id
        return orjson.dumps(d)

    @classmethod
    def from_dict(cls, d: dict) -> "Question":
        d = dict(d)
        d.pop("id", None)
        d["human"] = [HumanDist(**h) for h in d.get("human") or []]
        return cls(**d)


def write_jsonl(path, questions: Iterator[Question]) -> tuple[int, int]:
    ok = bad = 0
    seen = set()
    with open(path, "wb") as fh:
        for q in questions:
            errs = q.validate()
            if errs or q.id in seen:
                bad += 1
                continue
            seen.add(q.id)
            fh.write(q.to_json() + b"\n")
            ok += 1
    return ok, bad


def read_jsonl(path) -> Iterator[Question]:
    with open(path, "rb") as fh:
        for line in fh:
            if line.strip():
                yield Question.from_dict(orjson.loads(line))
