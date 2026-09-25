"""Ingest agent-authored content (authored/): G5 synthetic banks (round-trip filtered) and G2 menu templates.

authored/g5_*.jsonl lines: {"text", "primitive", "options", "node", "kind", "truth"?, "human_text"?}
authored/menus_*.yaml:    {node_id: {"noun": "album", "plural": "albums", "items": ["...", ...]}}

Round-trip filter (docs/03-questions.md §5): Jev must place the synthetic question back at the node it was
written for (or a descendant); otherwise it is rejected to authored/rejected/.
"""

from __future__ import annotations

import asyncio
import re
from pathlib import Path

import orjson
import yaml

from . import db
from .config import AUTHORED
from .ingest import ingest_questions
from .model import Question
from .place import place_many

G2_TEMPLATES = [
    ("favorite", "taste", "Which of these {plural} is your favorite?", "Which of these {plural} would most people pick as their favorite?"),
    ("greatest", "evaluative", "Which of these {plural} is the greatest?", None),
    ("overrated", "evaluative", "Which of these {plural} is the most overrated?", None),
    ("underrated", "evaluative", "Which of these {plural} is the most underrated?", None),
]


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")[:40] or "x"


def g2_from_menus(paths: list[Path]) -> list[Question]:
    out = []
    for p in paths:
        menus = yaml.safe_load(p.read_text()) or {}
        for node, m in menus.items():
            items = [i for i in (m.get("items") or []) if i][:12]
            if len(items) < 3:
                continue
            opts = {}
            for it in items:
                k = slug(it)
                while k in opts:
                    k += "_"
                opts[k] = it
            hem = node.split(".")[0]
            for tid, kind, tmpl, human in G2_TEMPLATES:
                if tid in (m.get("skip") or []):
                    continue
                out.append(Question(
                    text=tmpl.format(plural=m.get("plural") or m.get("noun", "options") + "s"),
                    primitive="choice", hemisphere=hem, origin="template", source="g2_menus",
                    options=opts, kind=kind, node_hint=node, template_id=f"g2.{tid}",
                    human_text=human.format(plural=m.get("plural") or "options") if human else None,
                    meta={"menu_node": node},
                ))
    return out


def load_g5(paths: list[Path]) -> list[tuple[Question, str]]:
    out = []
    for p in paths:
        for line in p.read_bytes().splitlines():
            if not line.strip():
                continue
            d = orjson.loads(line)
            node = d["node"]
            hem = node.split(".")[0]
            q = Question(
                text=d["text"], primitive=d["primitive"], hemisphere=hem, origin="synthetic", source=p.stem,
                options=d.get("options"), kind=d.get("kind"), shape=d.get("shape"), node_hint=node,
                truth=d.get("truth"), human_text=d.get("human_text"), license="authored (askjev)",
                meta={"authored_file": p.name},
            )
            if not q.validate():
                out.append((q, node))
    return out


def round_trip_ok(intended: str, placed: str) -> bool:
    if placed == intended or placed.startswith(intended + "."):
        return True
    # a deep intended node placed at its parent counts (the parent is still the right branch)
    return intended.startswith(placed + ".") and intended.count(".") >= 3


def ingest_authored(paths: list[str] | None = None, round_trip: bool = True) -> str:
    files = [Path(p) for p in paths] if paths else sorted(AUTHORED.glob("g5_*.jsonl")) + sorted(AUTHORED.glob("menus_*.yaml"))
    g5 = load_g5([f for f in files if f.name.startswith("g5_")])
    menus = g2_from_menus([f for f in files if f.name.startswith("menus_")])
    with db.connect() as conn:
        have = {r["id"] for r in conn.execute("select id from questions")}
    g5 = [(q, n) for q, n in g5 if q.id not in have]
    kept, rejected = [], []
    if round_trip and g5:
        # the walk starts at the intended hemisphere (the author already fixed it; the root step only spends a call):
        # still blind to the intended branch below it
        starts = {q.id: node.split(".")[0] for q, node in g5}
        res = asyncio.run(place_many([{"id": q.id, "text": q.text, "options": q.options, "state": q.state} for q, _ in g5],
                                     starts=starts))
        for q, node in g5:
            r = res.get(q.id, {})
            placed = r.get("node", "root")
            if "error" not in r and round_trip_ok(node, placed):
                q.meta["round_trip"] = {"placed": placed, "confidence": r.get("confidence")}
                kept.append(q)
            else:
                rejected.append({"text": q.text, "intended": node, "placed": placed, "file": q.meta["authored_file"]})
    else:
        kept = [q for q, _ in g5]
    rej_dir = AUTHORED / "rejected"
    rej_dir.mkdir(exist_ok=True)
    if rejected:
        with open(rej_dir / "round_trip_rejects.jsonl", "ab") as fh:
            for r in rejected:
                fh.write(orjson.dumps(r) + b"\n")
    n_g5 = ingest_questions(kept)
    n_g2 = ingest_questions(menus)
    rate = len(kept) / max(len(g5), 1)
    return f"G5: {n_g5} ingested, {len(rejected)} rejected by round trip (accept rate {rate:.0%}); G2: {n_g2} ingested"
