"""Measure (per-question core metadata) and rollup (node_stats) stages (docs/03-questions.md §8)."""

from __future__ import annotations

import math
from collections import defaultdict

from . import db


def tvd(p: dict, q: dict) -> float:
    keys = set(p) | set(q)
    return 0.5 * sum(abs(p.get(k, 0.0) - q.get(k, 0.0)) for k in keys)


def top(d: dict) -> tuple[str | None, float, float]:
    if not d:
        return None, 0.0, 0.0
    items = sorted(d.items(), key=lambda kv: kv[1], reverse=True)
    t, p = items[0]
    second = items[1][1] if len(items) > 1 else 0.0
    return t, p, p - second


def entropy(d: dict) -> float:
    return -sum(p * math.log2(p) for p in d.values() if p > 0)


def norm(d: dict) -> dict:
    s = sum(d.values()) or 1.0
    return {k: v / s for k, v in d.items()}


def pooled_human(dists: list[dict]) -> dict | None:
    if not dists:
        return None
    acc: dict[str, float] = defaultdict(float)
    for h in dists:
        for k, v in (h["distribution"] or {}).items():
            acc[str(k)] += float(v)
    return norm(dict(acc))


def brier(dist: dict, truth_key: str) -> float:
    keys = set(dist) | {truth_key}
    return sum((dist.get(k, 0.0) - (1.0 if k == truth_key else 0.0)) ** 2 for k in keys)


def truth_key(primitive: str, truth) -> str | None:
    if truth is None:
        return None
    if primitive == "noul":
        return "true" if truth in (True, "true", 1) else "false"
    return str(truth)


def measure_all(ids: list[str] | None = None) -> str:
    f = " and question_id = any(%s)" if ids else ""
    arg = (ids,) if ids else ()
    with db.connect() as conn:
        qs = conn.execute("select id, primitive, truth from questions" + (" where id = any(%s)" if ids else ""), arg).fetchall()
        probes = conn.execute(
            """select p.question_id, p.frame, p.variant_kind, a.distribution, a.confidence, a.model_served
               from probes p join answers a on a.probe_id = p.id where p.universe_id='base'""" + f, arg
        ).fetchall()
        hum = conn.execute("select question_id, distribution, n from human_dists where true" + f, arg).fetchall()
        plc = conn.execute(
            """select distinct on (question_id) question_id, confidence, separation from placements where true"""
            + f + " order by question_id, created_at desc", arg
        ).fetchall()
    by_q = defaultdict(list)
    for p in probes:
        by_q[p["question_id"]].append(p)
    hum_q = defaultdict(list)
    for h in hum:
        hum_q[h["question_id"]].append(h)
    plc_q = {p["question_id"]: p for p in plc}
    n = 0
    with db.connect() as conn:
        for q in qs:
            ps = by_q.get(q["id"])
            if not ps:
                continue
            base = next((p for p in ps if p["variant_kind"] == "base" and p["frame"] in ("self", "none")), None)
            if not base:
                continue
            d = base["distribution"]
            t, pt, margin = top(d)
            human = next((p for p in ps if p["variant_kind"] == "base" and p["frame"] == "human"), None)
            th, pth, _ = top(human["distribution"]) if human else (None, None, None)
            variants = [p for p in ps if p["variant_kind"] in ("shuffle", "reversed_levels")]
            stability = (sum(1 for v in variants if top(v["distribution"])[0] == t) / len(variants)) if variants else None
            frame_gap = tvd(d, human["distribution"]) if human else None
            hd = pooled_human(hum_q.get(q["id"], []))
            human_gap = tvd(human["distribution"], hd) if (human and hd) else None
            tk = truth_key(q["primitive"], q["truth"])
            correct = (t == tk) if tk is not None else None
            br = brier(d, tk) if tk is not None else None
            pl = plc_q.get(q["id"])
            conn.execute(
                """insert into question_meta (question_id, model_served, top, p_top, margin, entropy, confidence, top_h, p_top_h,
                     stability, frame_gap, human_gap, correct, brier, placement_conf, separation, updated_at)
                   values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,now())
                   on conflict (question_id) do update set model_served=excluded.model_served, top=excluded.top,
                     p_top=excluded.p_top, margin=excluded.margin, entropy=excluded.entropy, confidence=excluded.confidence,
                     top_h=excluded.top_h, p_top_h=excluded.p_top_h, stability=excluded.stability,
                     frame_gap=excluded.frame_gap, human_gap=excluded.human_gap, correct=excluded.correct,
                     brier=excluded.brier, placement_conf=excluded.placement_conf, separation=excluded.separation, updated_at=now()""",
                (q["id"], base["model_served"], t, pt, margin, entropy(d), base["confidence"], th, pth,
                 stability, frame_gap, human_gap, correct, br,
                 pl["confidence"] if pl else None, pl["separation"] if pl else None),
            )
            n += 1
        conn.commit()
    return f"measured {n} questions"


def ece(pairs: list[tuple[float, bool]], bins: int = 10) -> float | None:
    if len(pairs) < 20:
        return None
    buckets = defaultdict(list)
    for p, c in pairs:
        buckets[min(int(p * bins), bins - 1)].append((p, c))
    total = len(pairs)
    return sum(len(b) / total * abs(sum(p for p, _ in b) / len(b) - sum(c for _, c in b) / len(b)) for b in buckets.values())


def rollup() -> str:
    with db.connect() as conn:
        nodes = conn.execute("select id, path::text as path from nodes where status='active'").fetchall()
        rows = conn.execute(
            """select q.path::text as path, q.node_id, q.kind, q.shape, q.origin, q.ask_count,
                      m.stability, m.frame_gap, m.human_gap, m.p_top, m.correct, m.brier, m.placement_conf
               from questions q left join question_meta m on m.question_id=q.id where q.node_id is not null"""
        ).fetchall()
        agg = {}
        for n in nodes:
            agg[(n["id"], "direct")] = []
            agg[(n["id"], "subtree")] = []
        path_to_id = {n["path"]: n["id"] for n in nodes}
        for r in rows:
            if (r["node_id"], "direct") in agg:
                agg[(r["node_id"], "direct")].append(r)
            parts = (r["path"] or "").split(".")
            for i in range(1, len(parts) + 1):
                nid = path_to_id.get(".".join(parts[:i]))
                if nid:
                    agg[(nid, "subtree")].append(r)

        def mean(xs):
            xs = [x for x in xs if x is not None]
            return sum(xs) / len(xs) if xs else None

        conn.execute("delete from node_stats")
        for (nid, scope), rs in agg.items():
            kinds = defaultdict(int)
            for r in rs:
                kinds[r["kind"] or r["shape"] or "unknown"] += 1
            stab = [r["stability"] for r in rs if r["stability"] is not None]
            cal = [(r["p_top"], bool(r["correct"])) for r in rs if r["correct"] is not None and r["p_top"] is not None]
            conn.execute(
                """insert into node_stats (node_id, scope, n_questions, n_asked, kind_counts, stability, frame_gap, human_gap,
                     calibration_ece, brier, placement_conf, fragile_share, updated_at)
                   values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,now())""",
                (nid, scope, len(rs), sum(1 for r in rs if r["origin"] == "asked"), db.Jsonb(dict(kinds)),
                 mean(stab), mean([r["frame_gap"] for r in rs]), mean([r["human_gap"] for r in rs]),
                 ece(cal), mean([r["brier"] for r in rs]), mean([r["placement_conf"] for r in rs]),
                 (sum(1 for s in stab if s < 0.67) / len(stab)) if stab else None),
            )
        conn.commit()
    return f"rolled up {len(nodes)} nodes"
