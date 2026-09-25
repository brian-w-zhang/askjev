"""Nebius SWE-agent-trajectories: SWE-agent runs on real GitHub issues (SWE-bench-style), each with a
`target` flag = the submitted patch resolved the issue (the hidden tests passed).

Template "swe_trajectories.completed": Noul "Did the agent in `trace` complete the task it was given?"
State `trace` = a compact trace (the issue text, then the agent's last actions and observations),
at most 1,500 chars. Truth = target. Balanced 50/50, at most 2 runs per (issue, outcome).
"""

from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path
from typing import Iterator

import httpx
import polars as pl

from askjev.model import Question
from askjev.sampling import env_int, hash_order

NAME = "swe_trajectories"
BASE = "https://huggingface.co/api/datasets/nebius/SWE-agent-trajectories/parquet/default/train"
FILES = 6  # of 12 (~90 MB each, ~6.7k runs each)
TARGET = env_int("TARGET_SWE_TRAJECTORIES", 1500)
PER_ISSUE = 2
LICENSE = "CC-BY-4.0"
TEXT = "Did the agent in `trace` complete the task it was given?"
CRITERIA = {
    "true": "The agent's final change actually resolves the issue it was asked to fix",
    "false": "The agent gave up, ran out of room, or submitted a change that does not resolve the issue",
}
MAX_TRACE = 1500
MAX_TASK = 450


def fetch(raw_dir: Path) -> None:
    for i in range(FILES):
        out = raw_dir / f"train_{i}.parquet"
        if out.exists():
            continue
        with httpx.stream("GET", f"{BASE}/{i}.parquet", follow_redirects=True, timeout=600) as r:
            r.raise_for_status()
            with open(out.with_suffix(".part"), "wb") as fh:
                for chunk in r.iter_bytes():
                    fh.write(chunk)
        out.with_suffix(".part").rename(out)


def _squash(s: str) -> str:
    return re.sub(r"[ \t]+", " ", re.sub(r"\n\s*\n+", "\n", s)).strip()


def _cut(s: str, n: int) -> str:
    s = _squash(s)
    return s if len(s) <= n else s[: n - 1].rstrip() + "…"


def _task(user_text: str) -> str | None:
    m = re.search(r"ISSUE:\s*(.*?)\s*INSTRUCTIONS:", user_text, re.S)
    return _cut(m.group(1), MAX_TASK) if m else None


def _action(ai_text: str) -> str:
    """The agent's command (the fenced block) plus the first sentence of its reasoning."""
    blocks = re.findall(r"```\w*\n?(.*?)```", ai_text, re.S)
    thought = re.split(r"```", ai_text)[0]
    first = re.split(r"(?<=[.!?])\s", _squash(thought), maxsplit=1)[0]
    cmd = blocks[-1].strip() if blocks else ""
    out = _cut(first, 160)
    if cmd:
        out += "\n$ " + _cut(cmd, 140)
    return out


def _observation(user_text: str) -> str:
    # Drop the SWE-agent prompt footer ("(Open file: ...)(Current directory: ...)bash-$").
    t = re.split(r"\(Open file:", user_text)[0]
    return _cut(t, 160) or "(no output)"


def _compact(traj: list[dict]) -> str | None:
    turns = [(m["role"], m["text"] or "") for m in traj if m["role"] in ("user", "ai")]
    if len(turns) < 3 or turns[0][0] != "user":
        return None
    task = _task(turns[0][1])
    if not task:
        return None
    head = f"TASK (GitHub issue to fix):\n{task}\n\nLAST STEPS OF THE RUN:"
    steps: list[str] = []
    budget = MAX_TRACE - len(head) - 30
    rest = turns[1:]
    i = len(rest) - 1
    while i >= 0:
        role, text = rest[i]
        piece = ("AGENT: " + _action(text)) if role == "ai" else ("OUTPUT: " + _observation(text))
        if len(piece) + 1 > budget:
            break
        steps.append(piece)
        budget -= len(piece) + 1
        i -= 1
    if len(steps) < 2:
        return None
    steps.reverse()
    earlier = f"[{i + 1} earlier steps omitted]\n" if i >= 0 else ""
    return head + "\n" + earlier + "\n".join(steps)


def normalize(raw_dir: Path) -> Iterator[Question]:
    files = sorted(raw_dir.glob("train_*.parquet"))
    pools: dict[bool, list[tuple[str, str, int, int, str, str]]] = {True: [], False: []}
    for fi, f in enumerate(files):
        df = pl.read_parquet(f, columns=["instance_id", "model_name", "target", "exit_status"])
        fidx = f.stem.split("_")[1]
        for row, (iid, model, target, exit_status) in enumerate(df.iter_rows()):
            pools[bool(target)].append((f"train{fidx}:{row}", iid, fi, row, model, exit_status))

    trajs: dict[int, pl.Series] = {}

    def traj(fi: int, row: int) -> list[dict]:
        if fi not in trajs:
            trajs[fi] = pl.read_parquet(files[fi], columns=["trajectory"])["trajectory"]
        return trajs[fi][row].to_list()

    half = {True: TARGET // 2, False: TARGET - TARGET // 2}
    picked: list[tuple[str, str, bool, str, dict]] = []
    for label in (True, False):
        per_issue: dict[str, int] = defaultdict(int)
        seen: set[str] = set()
        n = 0
        for sid, iid, fi, row, model, exit_status in hash_order(pools[label], lambda x: x[0], f"swe.{label}"):
            if n >= half[label]:
                break
            if per_issue[iid] >= PER_ISSUE:
                continue
            trace = _compact(traj(fi, row))
            if not trace or trace in seen:
                continue
            seen.add(trace)
            per_issue[iid] += 1
            picked.append((sid, iid, label, trace, {"model": model, "exit_status": exit_status}))
            n += 1

    picked.sort(key=lambda x: x[0])
    for sid, iid, label, trace, info in picked:
        yield Question(
            text=TEXT,
            primitive="noul",
            hemisphere="machine",
            origin="dataset",
            source=NAME,
            options=CRITERIA,
            state={"trace": trace},
            shape="verify",
            node_hint="machine.ai_systems.trace_classification",
            template_id="swe_trajectories.completed",
            source_item_id=sid,
            license=LICENSE,
            truth=label,
            meta={"instance_id": iid, "model": info["model"], "exit_status": info["exit_status"]},
        )
