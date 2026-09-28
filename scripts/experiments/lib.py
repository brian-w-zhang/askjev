"""Shared pieces for experiments (docs/16-experiments-plan.md).

An experiment is a `Spec` (the six steps written down: question, sourcing, collection, scoring, chart, limits) plus a
function that computes its `Result` from the corpus. `save` writes the private result file
(`data/analysis/experiments/<id>.json`, including the card the evaluator reads) and renders the public method doc
(`docs/experiments/<id>.md`); numbers stay out of the repo, the doc says where they live.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import asdict, dataclass, field
from functools import lru_cache
from pathlib import Path

import numpy as np
import polars as pl

A = Path("data/analysis")
OUT = A / "experiments"
DOCS = Path("docs/experiments")
RNG = np.random.default_rng(16)


@dataclass
class Spec:
    id: str
    family: str
    title: str
    question: str               # step 1: the question, in one sentence
    why: str                    # what would make the answer interesting
    sourcing: str               # step 2: which questions answer it (the query), and whether they're enough
    scoring: str                # step 4: the method, intervals, robustness
    chart: str                  # step 5: the chart and why that one
    compared_with: str          # what Jev is compared with
    collection: str = "Existing questions only; no new Jev calls."   # step 3
    limits: str = ""            # fine print
    new_questions: int = 0
    sources: list[str] = field(default_factory=list)


@dataclass
class Result:
    result: str                 # the headline sentence, with numbers
    evidence: str               # n, intervals
    numbers: dict               # everything the page or chart needs
    chart: dict                 # {"type": ..., ...data}
    examples: list[str] = field(default_factory=list)   # question ids for the rows drawer
    robustness: str = ""
    n: int = 0


# ---- data ----------------------------------------------------------------------------------------------------------
@lru_cache(maxsize=1)
def table() -> pl.DataFrame:
    q = pl.read_parquet(A / "questions.parquet")
    return q.filter(pl.col("display_ok") & ~pl.col("harmful") & pl.col("jev_dist").is_not_null())


def source(*names: str) -> pl.DataFrame:
    return table().filter(pl.col("source").is_in(list(names)))


def js(x: str | None):
    return json.loads(x) if isinstance(x, str) and x else None


def humans(h: str | None) -> list[dict]:
    return js(h) or []


def biggest(h: str | None) -> dict | None:
    hs = humans(h)
    return max(hs, key=lambda x: x.get("n") or 0) if hs else None


def norm(d: dict) -> dict:
    t = sum(v for v in d.values() if v) or 1.0
    return {k: (v or 0) / t for k, v in d.items()}


def jsd(p: dict, q: dict) -> float:
    """Jensen-Shannon distance (0 identical, 1 disjoint) between two distributions over the same options."""
    keys = set(p) | set(q)
    p, q = norm({k: p.get(k, 0) for k in keys}), norm({k: q.get(k, 0) for k in keys})
    m = {k: (p[k] + q[k]) / 2 for k in keys}
    kl = lambda a: sum(a[k] * math.log2(a[k] / m[k]) for k in keys if a[k] > 0)
    return math.sqrt(max(0.0, (kl(p) + kl(q)) / 2))


def top(d: dict) -> str | None:
    return max(d, key=d.get) if d else None


def level(d: dict) -> float | None:
    """Expected level of a Score distribution keyed '0'..'k-1'."""
    if not d:
        return None
    t = sum(d.values()) or 1
    return sum(int(k) * v for k, v in d.items() if str(k).isdigit()) / t


def boot(values, stat=np.mean, b: int = 1000) -> list[float]:
    v = np.asarray(values, dtype=float)
    if len(v) < 2:
        return [float(stat(v)), float(stat(v))] if len(v) else [float("nan")] * 2
    bs = [stat(v[RNG.integers(0, len(v), len(v))]) for _ in range(b)]
    return [round(float(np.percentile(bs, 5)), 4), round(float(np.percentile(bs, 95)), 4)]


def seeded(ids, key: str, k: int = 3) -> list[str]:
    return sorted(ids, key=lambda i: hashlib.md5(f"{key}|{i}".encode()).hexdigest())[:k]


def ordinal(x: float) -> str:
    n = round(x)
    return f"{n}{'th' if 11 <= n % 100 <= 13 else {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')}"


def agree_word(rho: float) -> str:
    """Rank correlation in words."""
    return "closely" if rho >= 0.7 else "moderately" if rho >= 0.45 else "only loosely" if rho >= 0.2 else "barely"


def pct(x: float, d: int = 0) -> str:
    return f"{x * 100:.{d}f}%"


# ---- output ----------------------------------------------------------------------------------------------------------
def card(spec: Spec, res: Result) -> dict:
    return {"id": spec.id, "title": spec.title, "question": spec.question, "result": res.result, "evidence": res.evidence,
            "compared_with": spec.compared_with, "sourcing": spec.sourcing.split(". ")[0], "chart": spec.chart.split(". ")[0]}


def save(spec: Spec, res: Result) -> dict:
    OUT.mkdir(parents=True, exist_ok=True)
    DOCS.mkdir(parents=True, exist_ok=True)
    p = OUT / f"{spec.id}.json"
    old = json.loads(p.read_text()) if p.exists() else {}
    d = {"spec": asdict(spec), "result": asdict(res), "card": card(spec, res),
         "evaluation": old.get("evaluation"), "evaluations": old.get("evaluations", [])}
    if old.get("card") and old["card"] != d["card"]:
        d["evaluation"] = None  # the card changed; evaluate again
    p.write_text(json.dumps(d, indent=1, default=str))
    (DOCS / f"{spec.id}.md").write_text(render(spec, d.get("evaluation")))
    return d


def render(spec: Spec, ev: dict | None = None) -> str:
    """The method doc for one experiment. Numbers live in the private result file; the doc says how they're made."""
    # the heading is the id, not the title: titles state the finding, and findings stay in the private result file
    lines = [f"# {spec.id}", "", f"family: {spec.family}" + (f" · new questions: {spec.new_questions}" if spec.new_questions else ""), "",
             "## 1. Question", spec.question, "", spec.why, "",
             "## 2. Sourcing", spec.sourcing, ""]
    if spec.sources:
        lines += ["Sources: " + ", ".join(f"`{s}`" for s in spec.sources), ""]
    lines += ["## 3. Collection", spec.collection, "",
              "## 4. Scoring", spec.scoring, "",
              "## 5. Visualization", spec.chart, "",
              "## 6. Evaluation", ("Jev's verdict (evaluator " + ev.get("version", "") + f"): **{ev.get('outcome')}**, head-to-head strength "
                                   f"{ev.get('strength')}, top verdict `{ev.get('top')}`.") if ev else
              "Run `scripts/experiments/evaluate.py new`; the verdict is stored with the result.", "",
              "## Compared with", spec.compared_with, ""]
    if spec.limits:
        lines += ["## Limits", spec.limits, ""]
    lines += ["Results: `data/analysis/experiments/" + spec.id + ".json` (private). Code: `scripts/experiments/`."]
    return "\n".join(lines) + "\n"


def clip(text: str, n: int = 100) -> str:
    """Shorten at a word boundary, marking the cut with an ellipsis."""
    text = " ".join(text.split())
    return text if len(text) <= n else text[:n].rsplit(" ", 1)[0].rstrip(",;:") + "…"


def and_list(xs: list[str]) -> str:
    return xs[0] if len(xs) == 1 else ", ".join(xs[:-1]) + " and " + xs[-1]


@lru_cache(maxsize=64)
def full_meta(name: str) -> dict:
    """id -> the full meta of one source's questions, from its normalized file (the table keeps only a subset)."""
    out = {}
    path = Path("data/normalized") / f"{name}.jsonl"
    for line in path.open():
        r = json.loads(line)
        out[r["id"]] = r.get("meta") or {}
    return out


def with_meta(name: str) -> list[dict]:
    """A source's shown questions as dicts, each with its full meta under 'm'."""
    M = full_meta(name)
    return [{**r, "m": M.get(r["id"], {})} for r in source(name).iter_rows(named=True)]
