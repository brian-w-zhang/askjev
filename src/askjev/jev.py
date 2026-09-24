"""Jev client over Vercel AI Gateway (`POST /v1/evaluate`, model `typesafe-ai/jev`).

Every request is content-hashed. A request whose hash is already in `calls` is never re-sent;
the cached response is returned instead. Every sent request is appended to the on-disk log
(`data/calls/<date>/<pid>.jsonl`), which is the source of truth, and indexed in Postgres.

Gateway shape (verified 2026-09-24, see docs/01-jev.md §1):
  request   {model, state, questions: {id: {type: boolean|choice|score, instructions, criteria}}}
  response  {model, answers: {id: {type, probability | choice+probabilities+confidence |
             score+probabilities+confidence}}, usage: {inputTokens, outputTokens},
             providerMetadata: {gateway: {generationId, cost, ...}}}
Noul is called "boolean" on the gateway.
"""

from __future__ import annotations

import asyncio
import hashlib
import math
import os
import random
import time
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

import httpx
import orjson

from . import db
from .config import (
    CALLS,
    GATEWAY_KEY,
    GATEWAY_URL,
    JEV_MODEL,
    MAX_WORKERS,
    REQUEST_TOKEN_BUDGET,
    REQUESTS_PER_SECOND,
)

PRIMITIVE_TO_GATEWAY = {"noul": "boolean", "choice": "choice", "score": "score"}


def canonical(obj: Any) -> bytes:
    return orjson.dumps(obj, option=orjson.OPT_SORT_KEYS)


def sha(obj: Any) -> str:
    return hashlib.sha256(canonical(obj)).hexdigest()


def estimate_tokens(obj: Any) -> int:
    return len(canonical(obj)) // 4 + 8


def gateway_question(primitive: str, instructions: Any, criteria: Any = None) -> dict:
    q: dict[str, Any] = {"type": PRIMITIVE_TO_GATEWAY[primitive], "instructions": instructions}
    if criteria is not None:
        q["criteria"] = criteria
    return q


@dataclass
class Answer:
    type: str  # noul | choice | score
    dist: dict[str, float]  # option -> p ; noul: {"true": p, "false": 1-p}
    confidence: float | None = None
    score: float | None = None

    @property
    def p_yes(self) -> float:
        return self.dist.get("true", 0.0)


def parse_answer(raw: dict) -> Answer:
    t = raw.get("type")
    if t == "boolean":
        p = float(raw["probability"])
        return Answer("noul", {"true": p, "false": round(1 - p, 6)})
    if t == "choice":
        return Answer("choice", {k: float(v) for k, v in raw["probabilities"].items()}, raw.get("confidence"))
    if t == "score":
        return Answer(
            "score",
            {str(k): float(v) for k, v in raw["probabilities"].items()},
            raw.get("confidence"),
            raw.get("score"),
        )
    raise ValueError(f"unknown answer type {t!r}")


@dataclass
class Request:
    state: Any
    questions: dict[str, dict]  # id -> gateway question
    repeat_idx: int = 0  # >0 only for deliberate noise-floor repeats
    body: dict = field(init=False)
    hash: str = field(init=False)

    def __post_init__(self):
        self.body = {"model": JEV_MODEL, "state": self.state, "questions": self.questions}
        self.hash = sha({"body": self.body, "repeat": self.repeat_idx})

    @property
    def tokens(self) -> int:
        return estimate_tokens(self.body)


class TokenBucket:
    def __init__(self, rate: float):
        self.rate = rate
        self.tokens = rate
        self.last = time.monotonic()
        self.lock = asyncio.Lock()

    async def take(self):
        async with self.lock:
            while True:
                now = time.monotonic()
                self.tokens = min(self.rate, self.tokens + (now - self.last) * self.rate)
                self.last = now
                if self.tokens >= 1:
                    self.tokens -= 1
                    return
                await asyncio.sleep((1 - self.tokens) / self.rate)


class CallLog:
    """Append-only JSONL log of every sent request/response (source of truth)."""

    def __init__(self):
        d = CALLS / date.today().isoformat()
        d.mkdir(parents=True, exist_ok=True)
        self.path = d / f"{os.getpid()}.jsonl"
        self.fh = open(self.path, "ab")

    def write(self, rec: dict):
        self.fh.write(orjson.dumps(rec) + b"\n")
        self.fh.flush()
        os.fsync(self.fh.fileno())

    def rel(self) -> str:
        return str(self.path.relative_to(CALLS.parent.parent))


class JevClient:
    def __init__(self, workers: int = MAX_WORKERS, rps: float = REQUESTS_PER_SECOND):
        if not GATEWAY_KEY:
            raise RuntimeError("AI_GATEWAY_API_KEY missing from .env")
        self.sem = asyncio.Semaphore(workers)
        self.bucket = TokenBucket(rps)
        self.http = httpx.AsyncClient(
            timeout=httpx.Timeout(60.0),
            headers={"Authorization": f"Bearer {GATEWAY_KEY}", "Content-Type": "application/json"},
            limits=httpx.Limits(max_connections=workers * 2),
        )
        self.log = CallLog()
        self.stats = {"sent": 0, "cached": 0, "retries": 0, "errors": 0, "input_tokens": 0}

    async def close(self):
        await self.http.aclose()

    # -- cache ---------------------------------------------------------------------
    @staticmethod
    def cached(hashes: list[str]) -> dict[str, dict]:
        if not hashes:
            return {}
        with db.connect() as conn:
            rows = conn.execute(
                "select request_hash, response from calls where request_hash = any(%s) and response is not null",
                (hashes,),
            ).fetchall()
        return {r["request_hash"]: r["response"] for r in rows}

    def _index(self, req: Request, resp: dict, latency_ms: int):
        meta = resp.get("providerMetadata", {}).get("gateway", {})
        slim = {"model": resp.get("model"), "answers": resp.get("answers"), "usage": resp.get("usage")}
        with db.connect() as conn:
            conn.execute(
                """insert into calls (request_hash, kind, model_served, generation_id, log_file,
                                      latency_ms, input_tokens, response)
                   values (%s,'jev',%s,%s,%s,%s,%s,%s) on conflict (request_hash) do nothing""",
                (
                    req.hash,
                    served_version(resp),
                    meta.get("generationId"),
                    self.log.rel(),
                    latency_ms,
                    (resp.get("usage") or {}).get("inputTokens"),
                    db.Jsonb(slim),
                ),
            )
            conn.commit()

    # -- sending ---------------------------------------------------------------
    async def _send(self, req: Request) -> dict:
        delay = 1.0
        for attempt in range(8):
            await self.bucket.take()
            async with self.sem:
                t0 = time.monotonic()
                try:
                    r = await self.http.post(GATEWAY_URL, content=canonical(req.body))
                except (httpx.TransportError, httpx.TimeoutException):
                    r = None
                latency = int((time.monotonic() - t0) * 1000)
            if r is not None and r.status_code == 200:
                resp = r.json()
                self.log.write(
                    {"hash": req.hash, "repeat": req.repeat_idx, "t": time.time(), "latency_ms": latency,
                     "request": req.body, "response": resp}
                )
                self._index(req, resp, latency)
                self.stats["sent"] += 1
                self.stats["input_tokens"] += (resp.get("usage") or {}).get("inputTokens") or 0
                return resp
            code = None if r is None else r.status_code
            if code is not None and code < 500 and code not in (408, 429):
                self.stats["errors"] += 1
                raise JevError(code, r.text[:500], req)
            self.stats["retries"] += 1
            retry_after = None
            if r is not None and r.headers.get("retry-after"):
                try:
                    retry_after = float(r.headers["retry-after"])
                except ValueError:
                    pass
            await asyncio.sleep(retry_after or delay * (1 + random.random() * 0.25))
            delay = min(delay * 2, 30)
        self.stats["errors"] += 1
        raise JevError(code, "retries exhausted", req)

    async def run(self, reqs: list[Request]) -> dict[str, dict]:
        """Returns {request_hash: response} for every request, using the cache where possible."""
        out = self.cached([r.hash for r in reqs])
        self.stats["cached"] += len(out)
        todo = [r for r in reqs if r.hash not in out]

        async def one(r: Request):
            try:
                out[r.hash] = await self._send(r)
            except JevError as e:
                out[r.hash] = {"error": str(e)}

        await asyncio.gather(*(one(r) for r in todo))
        return out


class JevError(Exception):
    def __init__(self, code, text, req: Request):
        super().__init__(f"jev {code}: {text}")
        self.code, self.text, self.req = code, text, req


def served_version(resp: dict) -> str:
    """The gateway does not expose Jev's version number; record model id + date as the best proxy."""
    return f"{resp.get('model', JEV_MODEL)}@{date.today().isoformat()}"


def answers(resp: dict) -> dict[str, Answer]:
    return {k: parse_answer(v) for k, v in (resp.get("answers") or {}).items()}


def pack(state: Any, questions: dict[str, dict], budget: int = REQUEST_TOKEN_BUDGET) -> list[Request]:
    """Split questions over one state into as few requests as fit the token budget."""
    base = estimate_tokens({"state": state})
    reqs, cur, size = [], {}, base
    for qid, q in questions.items():
        t = estimate_tokens(q) + 4
        if cur and size + t > budget:
            reqs.append(Request(state, cur))
            cur, size = {}, base
        cur[qid] = q
        size += t
    if cur:
        reqs.append(Request(state, cur))
    return reqs


def entropy(dist: dict[str, float]) -> float:
    return -sum(p * math.log2(p) for p in dist.values() if p > 0)


def run_sync(reqs: list[Request], **kw) -> dict[str, dict]:
    async def go():
        c = JevClient(**kw)
        try:
            return await c.run(reqs)
        finally:
            await c.close()

    return asyncio.run(go())
