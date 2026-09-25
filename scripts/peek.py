"""Print n random normalized items per source for review: uv run python scripts/peek.py <n> <source...>"""
import json, random, sys
from pathlib import Path
n = int(sys.argv[1])
for s in sys.argv[2:]:
    lines = Path(f"data/normalized/{s}.jsonl").read_text().splitlines()
    for l in random.Random(7).sample(lines, min(n, len(lines))):
        d = json.loads(l); o = d["options"]
        ko = list(o.keys()) if isinstance(o, dict) else (o or [])
        st = json.dumps(d["state"], ensure_ascii=False)[:160] if d["state"] else ""
        print(f"{s} | {d['primitive']} | {d['text'][:110]} | {st} | opts={str(ko)[:120]} | truth={d['truth']} | {d['node_hint']} | {d['meta'].get('flags','')}")
