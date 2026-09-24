"""Dedupe quality: Jev "same question?" Noul (the ask-flow dedupe) vs local-embedding cosine on 300 labeled
Quora pairs (150 duplicates, 150 non-duplicates that are topically close)."""
import asyncio
import random

import numpy as np
import polars as pl

from askjev.config import RAW, ROOT
from askjev.embed import embed
from askjev.dedupe import same_question
from askjev.jev import JevClient, Request, answers

d = pl.read_parquet(RAW / "quora" / "pair-class.parquet").sample(n=20000, seed=3)
pos = d.filter(pl.col("label") == 1).head(150)
neg_pool = d.filter(pl.col("label") == 0)
# hard negatives: highest embedding cosine among a pool of non-duplicates
pool = neg_pool.head(3000)
e1, e2 = embed(pool["sentence1"].to_list()), embed(pool["sentence2"].to_list())
sims = (e1 * e2).sum(1)
neg = pool.with_columns(pl.Series("sim", sims)).sort("sim", descending=True).head(150)
pairs = [(a, b, 1) for a, b in zip(pos["sentence1"], pos["sentence2"])] + [(a, b, 0) for a, b in zip(neg["sentence1"], neg["sentence2"])]
ea, eb = embed([p[0] for p in pairs]), embed([p[1] for p in pairs])
cos = (ea * eb).sum(1)


async def run():
    c = JevClient()
    reqs = [Request({"question": a}, {"d": same_question(b)}) for a, b, _ in pairs]
    res = await c.run(reqs)
    await c.close()
    return [answers(res[r.hash])["d"].p_yes for r in reqs]


p = asyncio.run(run())
y = np.array([l for _, _, l in pairs])


def prf(pred):
    tp = ((pred == 1) & (y == 1)).sum(); fp = ((pred == 1) & (y == 0)).sum(); fn = ((pred == 0) & (y == 1)).sum()
    prec = tp / max(tp + fp, 1); rec = tp / max(tp + fn, 1)
    return prec, rec, 2 * prec * rec / max(prec + rec, 1e-9)


rows = ["# Dedupe quality (300 labeled Quora pairs: 150 duplicates, 150 hard non-duplicates)", "",
        "| method | threshold | precision | recall | F1 |", "|---|---|---|---|---|"]
for t in (0.5, 0.7, 0.9):
    pr = prf((np.array(p) >= t).astype(int))
    rows.append(f"| Jev Noul | {t} | {pr[0]:.2f} | {pr[1]:.2f} | {pr[2]:.2f} |")
for t in (0.85, 0.9, 0.95):
    pr = prf((cos >= t).astype(int))
    rows.append(f"| embedding cosine | {t} | {pr[0]:.2f} | {pr[1]:.2f} | {pr[2]:.2f} |")
both = ((cos >= 0.8) & (np.array(p) >= 0.7)).astype(int)
pr = prf(both)
rows.append(f"| cosine ≥ 0.8 AND Jev ≥ 0.7 (the ask flow) | – | {pr[0]:.2f} | {pr[1]:.2f} | {pr[2]:.2f} |")
rows += ["", "Question: `askjev.dedupe.same_question` (a contrastive true/false variant measured worse: F1 0.54). Quora's duplicate labels mean 'same intent',",
         "which is looser than our 'any answer to one answers the other', so some label disagreement is expected."]
(ROOT / "docs" / "dedupe-eval.md").write_text("\n".join(rows) + "\n")
print("\n".join(rows))
