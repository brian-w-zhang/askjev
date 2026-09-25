"""Probe how many questions fit in one Jev request through the gateway (docs/01-jev.md §4): sends real screen batches
of increasing size over the neutral state (questions not yet screened, so the answers are usable) and reports the
status and latency per size. Every call is cached and logged like any other.

  uv run python scripts/probe_batch.py 24 48 96 160 250 --reps 3
"""

import argparse
import asyncio
import time

import httpx

from askjev import db
from askjev.answer import NEUTRAL_STATE, screen_questions
from askjev.config import GATEWAY_URL
from askjev.jev import JevClient, Request, canonical, estimate_tokens


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("sizes", nargs="+", type=int)
    ap.add_argument("--reps", type=int, default=3)
    a = ap.parse_args()
    need = max(a.sizes) * a.reps
    with db.connect() as c:
        rows = c.execute(
            """select q.id, q.text, q.options, q.hemisphere from questions q left join question_meta m on m.question_id=q.id
               where m.objective is null and q.state is null limit %s""", (need * 2,)).fetchall()
    items = []
    for q in rows:
        for k, gw in screen_questions(q).items():
            items.append((f"{q['id']}:{k}", gw))
    print(f"{len(rows)} unscreened stateless questions → {len(items)} screen questions available")

    async def go():
        client = JevClient(workers=4, rps=4)
        try:
            off = 0
            for n in a.sizes:
                for rep in range(a.reps):
                    chunk = dict(items[off:off + n])
                    off += n
                    if len(chunk) < n:
                        print(f"size {n}: not enough items"); return
                    req = Request(NEUTRAL_STATE, chunk)
                    t0 = time.monotonic()
                    await client.bucket.take()
                    r = await client.http.post(GATEWAY_URL, content=canonical(req.body))
                    ms = int((time.monotonic() - t0) * 1000)
                    ok = r.status_code == 200
                    got = len((r.json().get("answers") or {})) if ok else 0
                    if ok:
                        resp = r.json()
                        client.log.write({"hash": req.hash, "repeat": 0, "t": time.time(), "latency_ms": ms,
                                          "request": req.body, "response": resp})
                        client._index(req, resp, ms)
                    print(f"size {n:4d} rep {rep}: status {r.status_code} answers {got}/{n} "
                          f"~{estimate_tokens(req.body)} tok  {ms} ms", flush=True)
        finally:
            await client.close()

    asyncio.run(go())


if __name__ == "__main__":
    main()
