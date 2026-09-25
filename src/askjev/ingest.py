"""Stage 1-2: run a source adapter (fetch + normalize) and ingest normalized questions into Postgres."""

from __future__ import annotations

import importlib.util
from pathlib import Path

from . import db
from .config import DATA, RAW, SOURCES
from .embed import embed, question_text, to_pg
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


def _clean(v):
    """Postgres text/jsonb can't hold NUL characters; drop them wherever they hide."""
    if isinstance(v, str):
        return v.replace("\x00", "")
    if isinstance(v, dict):
        return {_clean(k): _clean(x) for k, x in v.items()}
    if isinstance(v, list):
        return [_clean(x) for x in v]
    return v


def ingest_questions(qs: list[Question], batch: int = 500) -> int:
    """Upsert questions (+ human dists, embeddings). Hinted questions get a deterministic placement
    only when the hint resolves exactly; partial matches are left for the Jev placement stage."""
    nodes = existing_nodes()
    for q in qs:
        q.text, q.options, q.state = _clean(q.text), _clean(q.options), _clean(q.state)
    n = 0
    with db.connect() as conn:
        have = {r["id"] for r in conn.execute("select id from questions where id = any(%s)", ([q.id for q in qs],))}
        # skip rows already stored (no re-embedding), and embed in length order: similar lengths pad less (~2x faster)
        qs = sorted((q for q in qs if q.id not in have), key=lambda q: len(question_text(q.text, q.options, q.state)))
        for i in range(0, len(qs), batch):
            chunk = qs[i : i + batch]
            vecs = embed([question_text(q.text, q.options, q.state) for q in chunk], batch_size=32)
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
                        db.Jsonb(q.options) if q.options is not None else None, db.Jsonb(q.state) if q.state is not None else None, q.template_id, q.origin, q.source,
                        q.source_item_id, q.license, db.Jsonb(q.truth) if q.truth is not None else None, flags,
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


def ingest_file(path: Path, cap: int | None = None) -> int:
    qs = list(read_jsonl(path))
    if cap and len(qs) > cap:
        qs = sorted(qs, key=lambda q: q.id)[:cap]  # ids are hashes → deterministic pseudo-random sample
    return ingest_questions(qs)


def ingest_source(name: str, cap: int | None = None) -> int:
    return ingest_file(NORMALIZED / f"{name}.jsonl", cap)
