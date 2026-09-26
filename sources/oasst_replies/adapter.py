"""OpenAssistant Conversations 2 (oasst2): human-written assistant replies rated by volunteer labelers.

Template "oasst.fails_task": Noul, does the assistant reply fail to do what the user asked? Each reply was
flagged (or not) for `fails_task` by several labelers; value = share who flagged it, count = labelers.
Kept: English, not deleted, not synthetic, >= 3 labelers, share >= 2/3 (truth true) or <= 1/3 (truth false).
HumanDist = the labelers' true/false shares. Balanced 50/50, salted-hash order. Earlier turns of the
thread (if any) go in `conversation`.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterator

import httpx
import polars as pl

from askjev.model import HumanDist, Question
from askjev.sampling import env_int, hash_order

NAME = "oasst_replies"
URL = "https://huggingface.co/api/datasets/OpenAssistant/oasst2/parquet/default/{split}/0.parquet"
SPLITS = ("train", "validation")
TARGET = env_int("TARGET_OASST_REPLIES", 2500)
SALT = "oasst_replies.v1"
LICENSE = "Apache-2.0"
TEXT = (
    "Does the assistant's `reply` fail to do what the user asked in `prompt` "
    "(read with the earlier `conversation`, if any)?"
)
OPTIONS = {
    "true": "The reply ignores, misreads or does not carry out what the user asked for",
    "false": "The reply takes on the user's actual request and carries it out, whatever its quality",
}
MAX = 1500
HIST_MAX = 1200

SLURS = re.compile(r"\b(n[i1]gg(er|a|ers|as)|fag(got)?s?|kikes?|spics?|chinks?|trann(y|ies))\b", re.I)
POLITICAL = re.compile(
    r"\b(trump|biden|obama|clinton|republican\w*|democrat\w*|abortion|gun control|immigra\w*|election\w*|"
    r"putin|zelensk\w*|brexit|conservative\w*|liberal\w*|left-wing|right-wing|maga)\b",
    re.I,
)
SENSITIVE = re.compile(
    r"\b(sex|sexual\w*|porn\w*|nude\w*|erotic\w*|suicid\w*|self-harm|kill myself|rape\w*)\b", re.I
)


def fetch(raw_dir: Path) -> None:
    for split in SPLITS:
        out = raw_dir / f"{split}.parquet"
        if out.exists():
            continue
        r = httpx.get(URL.format(split=split), follow_redirects=True, timeout=600)
        r.raise_for_status()
        out.write_bytes(r.content)


def _clip(s: str, n: int) -> str:
    s = s.strip()
    return s if len(s) <= n else s[:n].rsplit(" ", 1)[0] + " ..."


def normalize(raw_dir: Path) -> Iterator[Question]:
    df = pl.concat([pl.read_parquet(raw_dir / f"{s}.parquet") for s in SPLITS])
    msgs = {r["message_id"]: r for r in df.select("message_id", "parent_id", "text", "role").iter_rows(named=True)}

    def history(pid: str | None) -> list[tuple[str, str]]:
        out = []
        while pid:
            m = msgs.get(pid)
            if m is None:
                return []
            out.append((m["role"], m["text"]))
            pid = m["parent_id"]
        return out[::-1]

    pools: dict[bool, list[dict]] = {True: [], False: []}
    cand = df.filter(
        (pl.col("role") == "assistant") & (pl.col("lang") == "en") & ~pl.col("deleted")
        & ~pl.col("synthetic") & pl.col("labels").is_not_null()
    )
    for r in cand.iter_rows(named=True):
        L = r["labels"]
        lab = dict(zip(L["name"], zip(L["value"], L["count"])))
        if "fails_task" not in lab:
            continue
        v, k = lab["fails_task"]
        if k < 3 or 1 / 3 < v < 2 / 3:
            continue
        hist = history(r["parent_id"])
        if not hist or hist[-1][0] != "prompter":
            continue
        prompt = hist[-1][1].strip()
        reply = r["text"].strip()
        if len(prompt) > MAX or len(reply) < 2 or SLURS.search(prompt + " " + reply):
            continue
        earlier = hist[:-1]
        turns = [f"{'User' if role == 'prompter' else 'Assistant'}: {t.strip()}" for role, t in earlier]
        conv = "\n\n".join(turns)
        if len(conv) > HIST_MAX:
            # keep the opening user turn and the most recent text, eliding the middle
            head = _clip(turns[0], 400)
            tail = conv[-(HIST_MAX - len(head)):].split(" ", 1)[-1]
            conv = f"{head}\n\n[...]\n\n... {tail}"
        flags = []
        blob = " ".join(t for _, t in hist) + " " + reply
        if SENSITIVE.search(blob) or lab.get("sexual_content", (0, 0))[0] >= 0.5:
            flags.append("sensitive")
        if POLITICAL.search(blob):
            flags.append("political")
        pools[v >= 2 / 3].append({
            "id": r["message_id"], "v": v, "k": k, "prompt": prompt, "reply": _clip(reply, MAX),
            "conv": conv or "(none: this is the first message)", "flags": flags,
            "depth": len(hist), "tree": r["message_tree_id"],
        })

    half = TARGET // 2
    picked = []
    for truth in (True, False):
        picked += [(truth, x) for x in hash_order(pools[truth], lambda x: x["id"], SALT)[:half]]
    picked.sort(key=lambda tx: tx[1]["id"])
    for truth, x in picked:
        meta = {"fails_task_share": round(x["v"], 4), "labelers": x["k"], "thread_depth": x["depth"],
                "message_tree_id": x["tree"]}
        if x["flags"]:
            meta["flags"] = x["flags"]
        yield Question(
            text=TEXT,
            primitive="noul",
            hemisphere="machine",
            origin="dataset",
            source=NAME,
            options=OPTIONS,
            state={"conversation": x["conv"], "prompt": x["prompt"], "reply": x["reply"]},
            shape="verify",
            node_hint="machine.ai_systems.hallucination_citation",
            template_id="oasst.fails_task",
            source_item_id=f"oasst2:{x['id']}",
            license=LICENSE,
            truth=truth,
            human=[HumanDist(
                population="Open Assistant volunteer labelers",
                distribution={"true": round(x["v"], 4), "false": round(1 - x["v"], 4)},
                n=x["k"],
                source="oasst2 labels.fails_task",
            )],
            meta=meta,
        )
