"""Coverage probe (docs/10-expansion.md §11): questions written by context-free subagents (one file per angle in a folder,
one question per line) are checked against the corpus two ways:
  1. nearest neighbour by local embedding over all questions (free): similarity and the neighbour's text/node;
  2. Jev's beam walk from the root (optional, --walk): where the tree would put it, and whether it reaches a specific node
     (depth ≥ 3) or stops at the root / a hemisphere / an L1 — a sign that a category is missing.
Writes a markdown report. Nothing is ingested.

  uv run python scripts/probe_coverage.py <folder> --walk --out docs/coverage-probe.md
"""

import argparse
import asyncio
from pathlib import Path

from askjev import db
from askjev.embed import embed, to_pg
from askjev.place import place_many

BANDS = [(0.92, "near-duplicate"), (0.85, "close analog"), (0.78, "same topic"), (0.0, "novel")]


def band(sim: float) -> str:
    return next(name for lo, name in BANDS if sim >= lo)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("folder")
    ap.add_argument("--walk", action="store_true")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    rows = []
    for f in sorted(Path(a.folder).glob("*.txt")):
        for line in f.read_text().splitlines():
            t = line.strip().lstrip("-•0123456789. ").strip()
            if len(t) > 8:
                rows.append({"angle": f.stem, "text": t})
    vecs = embed([r["text"] for r in rows])
    with db.connect() as c:
        c.execute("set hnsw.ef_search = 80")
        for r, v in zip(rows, vecs):
            nn = c.execute(
                "select text, node_id, 1 - (embedding <=> %s::vector) sim from questions order by embedding <=> %s::vector limit 1",
                (to_pg(v), to_pg(v))).fetchone()
            r.update(nn_text=nn["text"], nn_node=nn["node_id"], sim=float(nn["sim"]), band=band(float(nn["sim"])))
    if a.walk:
        res = asyncio.run(place_many([{"id": f"p{i}", "text": r["text"], "options": None, "state": None} for i, r in enumerate(rows)]))
        for i, r in enumerate(rows):
            p = res.get(f"p{i}", {})
            r["walk"] = p.get("node", "?")
            r["depth"] = r["walk"].count(".") + (0 if r["walk"] == "root" else 1)
            r["conf"] = p.get("confidence")
    angles = sorted({r["angle"] for r in rows})
    out = ["# Coverage probe", "", f"{len(rows)} context-free questions across {len(angles)} angles.", "",
           "| angle | n | near-dup ≥.92 | close ≥.85 | same topic ≥.78 | novel | mean sim" + (" | walk stuck (depth ≤ 2)" if a.walk else "") + " |",
           "|---|---|---|---|---|---|---" + ("|---" if a.walk else "") + "|"]
    for ang in angles + ["ALL"]:
        rs = [r for r in rows if ang == "ALL" or r["angle"] == ang]
        cnt = {b: sum(r["band"] == b for r in rs) for _, b in BANDS}
        line = (f"| {ang} | {len(rs)} | {cnt['near-duplicate']} | {cnt['close analog']} | {cnt['same topic']} | {cnt['novel']} | "
                f"{sum(r['sim'] for r in rs) / len(rs):.3f}")
        if a.walk:
            line += f" | {sum(r['depth'] <= 2 for r in rs)}"
        out.append(line + " |")
    out += ["", "## Novel questions (no close analog in the corpus), with Jev's placement", ""]
    for r in sorted((r for r in rows if r["band"] == "novel"), key=lambda r: (r["angle"], r["sim"])):
        out.append(f"- [{r['angle']}] {r['text']} — sim {r['sim']:.2f}" + (f" → `{r['walk']}`" if a.walk else "")
                   + f"  (nearest: “{r['nn_text'][:70]}”)")
    if a.walk:
        out += ["", "## Stuck at root / hemisphere / L1 (possible missing category)", ""]
        for r in (r for r in rows if r["depth"] <= 2):
            out.append(f"- [{r['angle']}] {r['text']} → `{r['walk']}`")
    text = "\n".join(out) + "\n"
    if a.out:
        Path(a.out).write_text(text)
    print(text[:6000])


if __name__ == "__main__":
    main()
