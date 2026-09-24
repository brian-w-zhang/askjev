"""Known-path taxonomy test (docs/02-tree.md §9): Jev routing on Shopify's product taxonomy, whose correct
paths are known. Items = leaf category names at depth 4 (e.g. "Pet Chairs"); Jev walks from the top level
(beam K=3, one Choice per node over children names) to depth 3; we score the path prefix accuracy by depth."""
import asyncio
import collections
import math
import random

from askjev.config import RAW, ROOT
from askjev.jev import JevClient, Request, answers, gateway_question

lines = [l.split(" : ", 1)[1].strip() for l in (RAW / "shopify" / "categories.txt").read_text().splitlines() if " : " in l]
paths = [l.split(" > ") for l in lines]
kids = collections.defaultdict(set)
for p in paths:
    for i in range(len(p)):
        kids[tuple(p[:i])].add(p[i])
rng = random.Random(7)
items = [p for p in paths if len(p) == 5]
rng.shuffle(items)
items = items[:120]  # target: first 4 levels known, route the leaf name


def crit(prefix):
    return {f"c{i}": {"label": k} for i, k in enumerate(sorted(kids[tuple(prefix)]))}


async def route(client, name, depth=4):
    beam = [((), 0.0)]
    for d in range(depth):
        cand = []
        qs = {}
        for bi, (pre, lp) in enumerate(beam):
            if kids.get(pre):
                qs[f"b{bi}"] = gateway_question("choice", "Which category does the product in `product` belong to?", crit(pre))
        resp = (await client.run([Request({"product": name}, qs)]))
        a = answers(list(resp.values())[0])
        for bi, (pre, lp) in enumerate(beam):
            ans = a.get(f"b{bi}")
            if not ans:
                continue
            opts = sorted(kids[tuple(pre)])
            for k, p in ans.dist.items():
                if p > 0.01:
                    cand.append((pre + (opts[int(k[1:])],), lp + math.log(p)))
        cand.sort(key=lambda c: c[1] / (len(c[0]) or 1), reverse=True)
        beam = cand[:3]
    return beam[0][0] if beam else ()


async def main():
    c = JevClient()
    sem = asyncio.Semaphore(32)
    got = {}

    async def one(p):
        async with sem:
            got[tuple(p)] = await route(c, p[-1])

    await asyncio.gather(*(one(p) for p in items))
    await c.close()
    acc = collections.Counter()
    for p, r in got.items():
        for d in range(1, 5):
            acc[d] += tuple(p[:d]) == tuple(r[:d])
    n = len(got)
    out = [f"# Known-path taxonomy test: Shopify product taxonomy ({n} leaf items)", "",
           "Jev walks Shopify's own tree (beam K=3, children names only as options) from the top, given only the",
           "depth-5 leaf category name. Accuracy of the predicted path prefix at each depth:", ""]
    for d in range(1, 5):
        out.append(f"- depth {d}: {100*acc[d]/n:.1f}%")
    out.append("\nThis validates the placement machinery (beam search, geometric-mean path score) on a tree with known answers.")
    (ROOT / "docs" / "taxonomy-eval.md").write_text("\n".join(out) + "\n")
    print("\n".join(out))

asyncio.run(main())
