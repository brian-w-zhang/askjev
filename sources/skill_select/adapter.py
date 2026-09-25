"""MetaTool (Huang et al. 2024, ICLR; github.com/HowieHwong/MetaTool): tool-selection prompts built from 199
ChatGPT-plugin-style tools, each with a user query, a 5-15 tool candidate list with descriptions, and the gold tool.

Template skill_select.pick (machine.ai_systems.skill_selection): Choice "Which of these tools, if any, is the right
one for `request`?" over the item's candidate tools (key = tool name, description = the tool's one-line
description) plus `none`. Items come from three MetaTool task files:
  - Task2-Subtask1 (similar-tool selection: the gold tool plus its 9 nearest tools) -> truth = gold tool
  - Task2-Subtask2 (scenario lists, 5/10/15 tools incl. the gold tool)             -> truth = gold tool
  - Task2-Subtask3 (reliability: 10 tools that exclude the gold tool)              -> truth = none
Each query is used once. `none` items are dropped when the list holds a catch-all tool (web search, "access web
pages", app connectors...), since such a tool could serve any query; gold-tool items are dropped when the list
holds a catch-all tool other than the gold one.
"""

from __future__ import annotations

import ast
import json
import re
from pathlib import Path
from typing import Iterator

import httpx

from askjev.model import Question
from askjev.sampling import env_int, hash_order

NAME = "skill_select"
BASE = "https://raw.githubusercontent.com/HowieHwong/MetaTool/master/dataset/tmp_dataset"
FILES = {"similar": "Task2-Subtask1.json", "scenario": "Task2-Subtask2.json", "reliability": "Task2-Subtask3.json"}
TARGET = env_int("TARGET_SKILL_SELECT", 1500)
NONE_SHARE = 1 / 3
LICENSE = "MIT"
TEXT = "Which of these tools, if any, is the right one for `request`?"
NONE_DESC = "None of these tools fits the request"
CATCH_ALL = {
    "MixerBox_WebSearchG_web_search", "internetSearch", "jini", "lsongai", "metaphor_search_api",
    "total_query_meta_search_engine", "web_requests", "universal", "aiAgents", "ai_council", "Zapier",
}
LIST = re.compile(
    r"\[List of Tools with Names and Descriptions Start\]\n(.*?)\[List of Tools with Names and Descriptions End\]", re.S
)
# Queries the generator wrote in the assistant's voice ("Sure, here is...", "Yes, the plugin can..."): not requests.
ASSISTANT_VOICE = re.compile(
    r"^(sure|certainly|of course|absolutely|here is|here are|as an ai|i'd be happy|i would be happy|"
    r"i can (help|assist|definitely|provide|certainly)|yes, (i|it|the|this|that|there|you|users?|we)\b)",
    re.I,
)
LINE = re.compile(r"^\d+\. tool name: (.*?), tool description: (.*)$", re.M)


def _desc(raw: str) -> str:
    raw = raw.strip()
    if raw.startswith("["):
        try:
            parts = ast.literal_eval(raw)
            raw = str(parts[0]) if parts else ""
        except (ValueError, SyntaxError):
            raw = raw.strip("[]'\"")
    return " ".join(raw.split())


def _tools(prompt: str) -> list[tuple[str, str]] | None:
    m = LIST.search(prompt)
    if not m:
        return None
    return [(n.strip(), _desc(d)) for n, d in LINE.findall(m.group(1))]


def fetch(raw_dir: Path) -> None:
    for f in FILES.values():
        out = raw_dir / f
        if out.exists():
            continue
        r = httpx.get(f"{BASE}/{f}", follow_redirects=True, timeout=300)
        r.raise_for_status()
        out.write_bytes(r.content)


def _load(raw_dir: Path) -> list[dict]:
    out = []
    for task, f in FILES.items():
        for i, x in enumerate(json.load(open(raw_dir / f, encoding="utf-8"))):
            tools = _tools(x["action_prompt"])
            query = " ".join(str(x["query"]).split())
            if len(query) < 15 or ASSISTANT_VOICE.search(query):
                continue
            if not tools or len({n.lower() for n, _ in tools}) != len(tools):
                continue
            if "none" in {n.lower() for n, _ in tools} or not all(d for _, d in tools):
                continue
            names = {n for n, _ in tools}
            gold = x["tool"]
            if task == "reliability":
                if gold in names or names & CATCH_ALL:
                    continue
                truth = "none"
            else:
                if gold not in names or (names - {gold}) & CATCH_ALL:
                    continue
                truth = gold
            out.append(dict(id=f"{task}:{i}", task=task, query=query, tools=tools, truth=truth, gold=gold,
                            scenario=x.get("scenario")))
    return out


def normalize(raw_dir: Path) -> Iterator[Question]:
    items = _load(raw_dir)
    n_none = round(TARGET * NONE_SHARE)
    used: set[str] = set()
    picked: list[dict] = []
    for it in hash_order([x for x in items if x["truth"] == "none"], lambda x: x["id"], "skill.none")[:n_none]:
        if it["query"].lower() not in used:
            used.add(it["query"].lower())
            picked.append(it)
    for it in hash_order([x for x in items if x["truth"] != "none"], lambda x: x["id"], "skill.gold"):
        if len(picked) >= TARGET:
            break
        if it["query"].lower() not in used:
            used.add(it["query"].lower())
            picked.append(it)

    for it in sorted(picked, key=lambda x: x["id"]):
        yield Question(
            text=TEXT,
            primitive="choice",
            hemisphere="machine",
            origin="dataset",
            source=NAME,
            options={**{n: d for n, d in it["tools"]}, "none": NONE_DESC},
            state={"request": it["query"][:1500]},
            shape="route",
            node_hint="machine.ai_systems.skill_selection",
            template_id="skill_select.pick",
            source_item_id=it["id"],
            license=LICENSE,
            truth=it["truth"],
            meta={"task": it["task"], "gold_tool": it["gold"], "n_tools": len(it["tools"]),
                  **({"scenario": it["scenario"]} if it["scenario"] else {})},
        )
