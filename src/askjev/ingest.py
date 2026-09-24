"""Stage 1-2: run a source adapter (fetch + normalize) and ingest normalized questions into Postgres."""

from __future__ import annotations

import importlib.util
from pathlib import Path

from . import db
from .config import DATA, RAW, SOURCES
from .embed import embed, to_pg
from .model import Question, read_jsonl, write_jsonl

NORMALIZED = DATA / "normalized"
NORMALIZED.mkdir(parents=True, exist_ok=True)


def load_adapter(name: str):
    path = SOURCES / name / "adapter.py"
    spec = importlib.util.spec_from_file_location(f"sources.{name}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def run_source(name: str) -> tuple[int, int]:
    mod = load_adapter(name)
    raw = RAW / name
    raw.mkdir(parents=True, exist_ok=True)
    mod.fetch(raw)
    return write_jsonl(NORMALIZED / f"{name}.jsonl", mod.normalize(raw))


def existing_nodes() -> set[str]:
    with db.connect() as conn:
        return {r["id"] for r in conn.execute("select id from nodes where status='active'")}


def resolve_hint(hint: str | None, nodes: set[str]) -> str | None:
    """Deepest existing ancestor of the hint (or the hint itself)."""
    if not hint:
        return None
    parts = hint.split(".")
    for i in range(len(parts), 0, -1):
        cand = ".".join(parts[:i])
        if cand in nodes:
            return cand
    return None


def ingest_questions(qs: list[Question], batch: int = 500) -> int:
    """Upsert questions (+ human dists, embeddings). Hinted questions get a deterministic placement
    only when the hint resolves exactly; partial matches are left for the Jev placement stage."""
    nodes = existing_nodes()
    n = 0
    with db.connect() as conn:
        for i in range(0, len(qs), batch):
            chunk = qs[i : i + batch]
            vecs = embed([q.text if not q.state else f"{q.text}\n{str(q.state)[:400]}" for q in chunk])
            for q, v in zip(chunk, vecs):
                node = q.node_hint if q.node_hint in nodes else None
                flags = list(q.meta.get("flags", []))
                meta = {k: v2 for k, v2 in q.meta.items() if k != "flags"}
                if q.node_hint:
                    meta["node_hint"] = q.node_hint
                if q.human_text:
                    meta["human_text"] = q.human_text
                cur = conn.execute(
                    """insert into questions (id, node_id, path, hemisphere, kind, shape, primitive, text, options,
                         state, template_id, origin, source, source_item_id, license, truth, flags, display_ok, meta, embedding)
                       values (%s,%s,(select path from nodes where id=%s),%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                       on conflict (id) do nothing""",
                    (
                        q.id, node, node, q.hemisphere, q.kind, q.shape, q.primitive, q.text,
                        db.Jsonb(q.options), db.Jsonb(q.state), q.template_id, q.origin, q.source,
                        q.source_item_id, q.license, db.Jsonb(q.truth), flags,
                        not any(f in ("political", "sensitive") for f in flags),
                        db.Jsonb(meta), to_pg(v),
                    ),
                )
                if cur.rowcount:
                    n += 1
                    if node:
                        conn.execute(
                            "insert into placements (question_id, node_id, node_version, method, confidence) values (%s,%s,1,'deterministic',1.0)",
                            (q.id, node),
                        )
                for h in q.human:
                    conn.execute(
                        """insert into human_dists (question_id, population, n, distribution, source, wave)
                           values (%s,%s,%s,%s,%s,%s) on conflict do nothing""",
                        (q.id, h.population, h.n, db.Jsonb(h.distribution), h.source, h.wave),
                    )
            conn.commit()
    return n


def ingest_file(path: Path) -> int:
    return ingest_questions(list(read_jsonl(path)))


def ingest_source(name: str) -> int:
    return ingest_file(NORMALIZED / f"{name}.jsonl")
