"""Star positions for the nebula view (docs/07-ui.md): each displayable question's place inside its node's ball.

Direction = whitened 3D PCA of the node's question embeddings (similar questions sit together); radius is
rank-normalized (∛ of the rank) so every ball fills evenly. Read-only on Postgres; writes data/stars/:
  stars.bin   12 bytes per star: u16 node index, i8 x/y/z (×127), u8 primitive, u8 stability, u8 human gap,
              u8 frame gap, u8 placement confidence, u8 flags (1 = correct, 2 = wrong), u8 pad; 255 = no data
  ids.txt     24-char question ids concatenated, in star order
  nodes.json  {"nodes": [[node_id, offset, count], ...], "count": N}
Stars are ordered by (node_id, id). The browser reads them through /api/stars.
"""

import json
import struct

import numpy as np

from askjev import db
from askjev.config import DATA

PRIM = {"noul": 0, "choice": 1, "score": 2}
OUT = DATA / "stars"


def u8(v):
    return 255 if v is None else max(0, min(254, round(float(v) * 254)))


def hash_dirs(ids):
    # deterministic fallback directions for nodes too small for PCA
    out = []
    for i in ids:
        rng = np.random.default_rng(int(i[:12], 16))
        v = rng.normal(size=3)
        out.append(v / np.linalg.norm(v))
    return np.array(out)


def local_positions(ids, emb):
    n = len(ids)
    if n < 5:
        dirs = hash_dirs(ids)
        raw = np.linalg.norm(emb - emb.mean(0), axis=1) if n > 1 else np.zeros(n)
    else:
        x = emb - emb.mean(0)
        _, _, vt = np.linalg.svd(x, full_matrices=False)
        p = x @ vt[:3].T
        p /= p.std(0) + 1e-9
        raw = np.linalg.norm(p, axis=1)
        dirs = p / (raw[:, None] + 1e-9)
    rank = np.argsort(np.argsort(raw, kind="stable"), kind="stable")
    r = np.cbrt((rank + 0.5) / n) if n > 1 else np.array([0.0])
    return dirs * r[:, None]


def main():
    with db.connect() as conn:
        rows = conn.execute(
            """select q.id, q.node_id, q.primitive, q.embedding::text emb, m.stability, m.human_gap, m.frame_gap,
                      m.placement_conf, m.correct
                 from questions q left join question_meta m on m.question_id = q.id
                 join nodes n on n.id = q.node_id and n.status = 'active'
                where q.display_ok and q.embedding is not null"""
        ).fetchall()
    rows.sort(key=lambda r: (r["node_id"], r["id"]))
    OUT.mkdir(parents=True, exist_ok=True)
    nodes, buf, ids = [], bytearray(), []
    i = 0
    while i < len(rows):
        j = i
        while j < len(rows) and rows[j]["node_id"] == rows[i]["node_id"]:
            j += 1
        grp = rows[i:j]
        emb = np.array([json.loads(r["emb"]) for r in grp], dtype=np.float32)
        pos = local_positions([r["id"] for r in grp], emb)
        k = len(nodes)
        nodes.append([grp[0]["node_id"], i, j - i])
        for r, p in zip(grp, pos):
            x, y, z = (int(round(float(c) * 127)) for c in p)
            flags = 0 if r["correct"] is None else (1 if r["correct"] else 2)
            buf += struct.pack("<Hbbb7B", k, x, y, z, PRIM[r["primitive"]], u8(r["stability"]), u8(r["human_gap"]),
                               u8(r["frame_gap"]), u8(r["placement_conf"]), flags, 0)
            ids.append(r["id"])
        i = j
    assert all(len(x) == 24 for x in ids)
    (OUT / "stars.bin").write_bytes(bytes(buf))
    (OUT / "ids.txt").write_text("".join(ids))
    (OUT / "nodes.json").write_text(json.dumps({"nodes": nodes, "count": len(ids)}))
    print(f"{len(ids)} stars in {len(nodes)} nodes -> {OUT}")


if __name__ == "__main__":
    main()
