"""Pick the finalists for the taste finals: the top 24 items per domain by Jev's robust rating (fam_taste.rated),
one per distinct name (editions and re-releases count once), written to data/raw/taste_finals/top24.json for sources/taste_finals to turn into
round-robin head-to-heads. Run from the repo root: `uv run python scripts/experiments/taste_finals_pool.py`."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fam_taste import DOMAINS, rated  # noqa: E402

TOP = 24

if __name__ == "__main__":
    pool = {}
    for dom in DOMAINS:
        t = rated(dom)
        seen, items = set(), []
        for r in t.iter_rows(named=True):
            key = re.sub(r"\s*\([^)]*\)", "", r["name"]).lower().strip()  # one edition per game or film
            if key in seen:
                continue
            seen.add(key)
            items.append({"id": r["id"], "name": r["name"], "score": round(r["score"], 4)})
            if len(items) == TOP:
                break
        pool[dom] = {"node": f"self.lifestyle.ratings.{DOMAINS[dom][0]}", "items": items,
                     "cut": items[-1]["score"], "n_rated": t.height}
        print(dom, t.height, [i["name"] for i in items[:6]], "cut", items[-1]["score"])
    Path("data/raw/taste_finals/top24.json").write_text(json.dumps(pool, indent=1))
