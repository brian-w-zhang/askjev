"""HaluEval (Li et al. 2023, RUCAIBox): LLM outputs paired with source knowledge, each item carrying a
right and a hallucinated answer.

Three Noul templates at machine.ai_systems.hallucination_citation, one per HaluEval task. Each source item
is used once, with EITHER its right or its hallucinated output (exactly half of each template's sample is
hallucinated, chosen by a salted hash), so no input appears twice. Truth = the output is grounded.
  - halueval.qa: "Is `answer` supported by `knowledge`...?" (HotpotQA-based)
  - halueval.dialogue: "Is `response` faithful to `knowledge` and the conversation...?" (OpenDialKG-based)
  - halueval.summarization: "Is every claim in `summary` supported by `document`?" (CNN/DailyMail-based;
    only documents <= 2,000 chars, kept whole, so no summary refers to cut-off text)
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Iterator

import httpx

from askjev.model import Question
from askjev.sampling import env_int, hash_order

NAME = "halueval"
BASE = "https://raw.githubusercontent.com/RUCAIBox/HaluEval/main/data"
FILES = ("qa_data", "dialogue_data", "summarization_data")
TARGET = env_int("TARGET_HALUEVAL", 1500)  # per template
LICENSE = "MIT"
NODE = "machine.ai_systems.hallucination_citation"
MAX_DOC = 2000

SENSITIVE = re.compile(
    r"\b(sex\w*|porn\w*|nude\w*|naked|prostitut\w*|suicid\w*|rape[ds]?|raping|rapist\w*|incest|molest\w*|"
    r"pedophil\w*|paedophil\w*|beheaded|decapitat\w*|dismember\w*|mutilat\w*|self-harm)\b",
    re.I,
)
POLITICAL = re.compile(
    r"\b(abortion|gun control|second amendment|death penalty|capital punishment|immigra\w*|refugee\w*|"
    r"republican\w*|democrat\w*|trump|obama|clinton|hillary|biden|netanyahu|putin|palestin\w*|gaza|west bank|"
    r"same.sex|gay marriage|brexit|electoral college|gerrymander\w*|gop|white house|senator\w*|congressman|"
    r"presidential|election\w*|nra|isis|isil|jihad\w*)\b",
    re.I,
)

TEMPLATES = {
    "qa": dict(
        text="Is `answer` supported by `knowledge`, with no invented or contradicting details?",
        options={
            "true": "Everything the answer states is given in the knowledge or follows directly from it",
            "false": "The answer states something the knowledge does not give, or contradicts it",
        },
        right="right_answer",
        wrong="hallucinated_answer",
    ),
    "dialogue": dict(
        text="Is `response` faithful to `knowledge` and the conversation, with no invented facts?",
        options={
            "true": "Every fact the response states matches the knowledge and the conversation",
            "false": "The response states a fact that the knowledge and conversation do not give, or contradicts them",
        },
        right="right_response",
        wrong="hallucinated_response",
    ),
    "summarization": dict(
        text="Is every claim in `summary` supported by `document`?",
        options={
            "true": "Every claim in the summary is stated in the document or follows directly from it",
            "false": "At least one claim in the summary is missing from the document or contradicts it",
        },
        right="right_summary",
        wrong="hallucinated_summary",
    ),
}


def _clean(s: str) -> str:
    return " ".join(s.split())


GLUED = re.compile(r"(?<=[a-z0-9)\]\"'])\.(?=[A-Z][a-z])")  # "...USA.The Oberoi" -> "...USA. The Oberoi"


def _knowledge(s: str) -> str:
    return GLUED.sub(". ", _clean(s))


def _conversation(history: str) -> str:
    """'[Human]: hi [Assistant]: hello' -> one turn per line, 'User:' / 'Assistant:'."""
    parts = re.split(r"\[(Human|Assistant)\]:", history)
    lines = []
    for who, said in zip(parts[1::2], parts[2::2]):
        said = _clean(said)
        if said:
            lines.append(f"{'User' if who == 'Human' else 'Assistant'}: {said}")
    return "\n".join(lines)


def fetch(raw_dir: Path) -> None:
    for f in FILES:
        out = raw_dir / f"{f}.json"
        if out.exists():
            continue
        r = httpx.get(f"{BASE}/{f}.json", follow_redirects=True, timeout=300)
        r.raise_for_status()
        out.write_bytes(r.content)


def _items(raw_dir: Path, task: str) -> list[tuple[int, dict]]:
    out = []
    seen: set[str] = set()
    with open(raw_dir / f"{task}_data.json", encoding="utf-8") as fh:
        for i, line in enumerate(fh):
            if not line.strip():
                continue
            d = json.loads(line)
            t = TEMPLATES[task]
            right, wrong = _clean(d.get(t["right"]) or ""), _clean(d.get(t["wrong"]) or "")
            if not right or not wrong or right.lower() == wrong.lower():
                continue
            if task == "qa":
                key = d["question"].strip().lower()
                if not d["knowledge"].strip():
                    continue
            elif task == "dialogue":
                key = d["dialogue_history"].strip().lower()
                if not d["knowledge"].strip() or not _conversation(d["dialogue_history"]):
                    continue
            else:
                if len(d["document"].strip()) > MAX_DOC:
                    continue
                key = d["document"].strip().lower()
            if key in seen:
                continue
            seen.add(key)
            out.append((i, d))
    return out


def normalize(raw_dir: Path) -> Iterator[Question]:
    for task, t in TEMPLATES.items():
        tid = f"halueval.{task}"
        picked = hash_order(_items(raw_dir, task), lambda x: x[0], tid)[:TARGET]
        # Exactly half hallucinated: the first half of a second salted order.
        halluc = {i for i, _ in hash_order(picked, lambda x: x[0], f"{tid}.halluc")[: len(picked) // 2]}
        for i, d in sorted(picked, key=lambda x: x[0]):
            is_h = i in halluc
            output = _clean(d[t["wrong"] if is_h else t["right"]])
            if task == "qa":
                state = {"question": _clean(d["question"]), "knowledge": _knowledge(d["knowledge"])[:1500], "answer": output}
            elif task == "dialogue":
                state = {
                    "knowledge": _clean(d["knowledge"])[:1500],
                    "conversation": _conversation(d["dialogue_history"])[-1500:],
                    "response": output,
                }
            else:
                state = {"document": _clean(d["document"]), "summary": output}
            blob = " ".join(state.values())
            flags = []
            if SENSITIVE.search(blob):
                flags.append("sensitive")
            if POLITICAL.search(blob):
                flags.append("political")
            yield Question(
                text=t["text"],
                primitive="noul",
                hemisphere="machine",
                origin="dataset",
                source=NAME,
                options=t["options"],
                state=state,
                shape="verify",
                node_hint=NODE,
                template_id=tid,
                source_item_id=f"{task}:{i}",
                license=LICENSE,
                truth=not is_h,
                meta={"task": task, "variant": "hallucinated" if is_h else "right", **({"flags": flags} if flags else {})},
            )
