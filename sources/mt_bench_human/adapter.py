"""MT-Bench human judgments (LMSYS, Zheng et al. 2023): experts' pairwise votes on model answers to the
80 MT-Bench questions (two turns each).

Template "mt_bench.better_reply": Choice, which of two assistants gives the better reply to the user's
last message. Votes are pooled per (question, unordered model pair, turn); items whose majority is a tie
(or no majority) are dropped. Truth = the majority winner; HumanDist = the judges' votes (a tie vote counts
half to each side). Which model is shown as `conversation_a` is decided by a salted hash, so truth is
balanced. For turn-2 judgments each transcript holds both turns of that model's conversation.
"""

from __future__ import annotations

import hashlib
from collections import defaultdict
from pathlib import Path
from typing import Iterator

import httpx
import polars as pl

from askjev.model import HumanDist, Question
from askjev.sampling import env_int, hash_order

NAME = "mt_bench_human"
URL = "https://huggingface.co/api/datasets/lmsys/mt_bench_human_judgments/parquet/default/human/0.parquet"
TARGET = env_int("TARGET_MT_BENCH_HUMAN", 3000)
SALT = "mt_bench.better_reply"
LICENSE = "CC-BY-4.0"
MAX_CONV = 5000
TEXT = (
    "Which AI assistant gives the better reply to the user's last message: the one in `conversation_a` "
    "or the one in `conversation_b`?"
)
OPTIONS = {
    "conversation_a": "The assistant in the first conversation gives the better final reply",
    "conversation_b": "The assistant in the second conversation gives the better final reply",
}


def fetch(raw_dir: Path) -> None:
    out = raw_dir / "human.parquet"
    if out.exists():
        return
    r = httpx.get(URL, follow_redirects=True, timeout=300)
    r.raise_for_status()
    out.write_bytes(r.content)


def _render(conv: list[dict], turn: int) -> str:
    msgs = conv[: 2 * turn]
    return "\n\n".join(f"{'User' if m['role'] == 'user' else 'Assistant'}: {m['content'].strip()}" for m in msgs)


def normalize(raw_dir: Path) -> Iterator[Question]:
    df = pl.read_parquet(raw_dir / "human.parquet")
    groups: dict[tuple, dict] = defaultdict(lambda: {"votes": [], "judges": [], "conv": {}})
    for r in df.iter_rows(named=True):
        m1, m2 = sorted([r["model_a"], r["model_b"]])
        g = groups[(r["question_id"], m1, m2, r["turn"])]
        g["conv"][r["model_a"]] = r["conversation_a"]
        g["conv"][r["model_b"]] = r["conversation_b"]
        w = r["winner"]
        g["votes"].append(r["model_a"] if w == "model_a" else r["model_b"] if w == "model_b" else "tie")
        g["judges"].append(r["judge"])

    items = []
    for (qid, m1, m2, turn), g in groups.items():
        s1 = sum(1.0 if v == m1 else 0.5 if v == "tie" else 0.0 for v in g["votes"]) / len(g["votes"])
        if s1 == 0.5:
            continue
        winner = m1 if s1 > 0.5 else m2
        # a strict majority of votes must name the winner (ties don't count toward it)
        if sum(v == winner for v in g["votes"]) * 2 <= len(g["votes"]):
            continue
        c1, c2 = _render(g["conv"][m1], turn), _render(g["conv"][m2], turn)
        if len(c1) > MAX_CONV or len(c2) > MAX_CONV or c1 == c2:
            continue
        key = f"{qid}|{m1}|{m2}|{turn}"
        flip = int(hashlib.sha256(f"{SALT}|{key}".encode()).hexdigest(), 16) % 2 == 1
        a, b = (m2, m1) if flip else (m1, m2)
        ca, cb = (c2, c1) if flip else (c1, c2)
        share_a = s1 if a == m1 else 1 - s1
        items.append({
            "key": key, "qid": qid, "turn": turn, "a": a, "b": b, "ca": ca, "cb": cb,
            "truth": "conversation_a" if winner == a else "conversation_b", "share_a": share_a,
            "votes": g["votes"], "judges": g["judges"],
        })
    seen: set[tuple[str, str]] = set()
    uniq = []
    for x in sorted(items, key=lambda x: x["key"]):
        pair = tuple(sorted([x["ca"], x["cb"]]))
        if pair not in seen:
            seen.add(pair)
            uniq.append(x)
    items = sorted(hash_order(uniq, lambda x: x["key"], SALT)[:TARGET], key=lambda x: x["key"])
    for x in items:
        yield Question(
            text=TEXT, primitive="choice", hemisphere="machine", origin="dataset", source=NAME,
            options=OPTIONS, state={"conversation_a": x["ca"], "conversation_b": x["cb"]},
            shape="rank", node_hint="machine.ai_systems.hallucination_citation",
            template_id="mt_bench.better_reply", source_item_id=x["key"], license=LICENSE,
            truth=x["truth"],
            human=[HumanDist(population="MT-Bench expert and author judges",
                             distribution={"conversation_a": round(x["share_a"], 4),
                                           "conversation_b": round(1 - x["share_a"], 4)},
                             n=len(x["votes"]), source="lmsys/mt_bench_human_judgments (human split)")],
            meta={"question_id": x["qid"], "turn": x["turn"], "model_a": x["a"], "model_b": x["b"],
                  "judges": x["judges"]},
        )
