"""How funny Jev finds each case study's meme (a Score, 1-5 on the page).

Jev can't see images, so it reads the meme in words: the template's name, what the image shows and how the format is
used (data/portrait/memes/describe.json, written by hand from the images), the words on it, the caption above it, and
the result the meme is about. Writes data/analysis/experiments/_funny/<id>.json (private). The portrait's own memes
are rated the same way from data/portrait/memes/portrait_memes.json (their words as the page renders them, and the
card they sit on) into _funny/_portrait.json, which export_page.py puts in portrait.json. Jev calls are cached.

  ASKJEV_RPS=16 uv run python scripts/experiments/meme_funny.py [ids]
  ASKJEV_RPS=16 uv run python scripts/experiments/meme_funny.py portrait
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cases  # noqa: E402
import memes  # noqa: E402
from askjev.jev import Request, answers, gateway_question as gq, run_sync  # noqa: E402

OUT = cases.OUT / "_funny"
DESCRIBE = memes.MEMES / "describe.json"
# situations, not degrees (docs/01-jev.md §7); the page shows them as 1-5 with the short name before the colon
LEVELS = ["Not funny: it gets no reaction, the joke doesn't land",
          "Slightly funny: a flicker of a smile at most",
          "Funny: a real smile or a quiet laugh",
          "Very funny: an actual laugh out loud",
          "Hilarious: the kind of meme people send to friends and quote for days"]


def card(c: dict, e: dict, desc: str) -> dict:
    m = c["meme"]
    x = {"meme format": memes.catalog()[m["template"]]["name"], "what the image shows": desc}
    if m.get("texts"):
        x["words on the image, in order"] = [t for t in m["texts"] if t]
    if m.get("caption"):
        x["caption above the image"] = m["caption"]
    x["what the meme is about"] = f"{e['spec']['title']}. {(c.get('result') or e['result']['result']).strip()}"
    return x


def funny(resp: dict) -> dict:
    d = answers(resp)["funny"].dist
    t = sum(d.values()) or 1
    dist = [round(d.get(str(k), 0) / t, 3) for k in range(5)]
    return {"dist": dist, "level": round(sum(k * p for k, p in enumerate(dist)), 2), "labels": [s.split(":")[0] for s in LEVELS]}


Q = {"funny": gq("score", "How funny is this meme?", LEVELS)}


def portrait():
    todo = []
    for m in json.loads((memes.MEMES / "portrait_memes.json").read_text()):
        x = {"meme format": m["alt"].split(" meme")[0], "what the image shows": m["describe"]}
        if m["labels"]:
            x["words on the image, in order"] = m["labels"]
        if m["caption"]:
            x["caption above the image"] = m["caption"]
        x["what the meme is about"] = f"{m['section']} {m['lead']}".strip()
        todo.append((m["name"], Request(x, Q)))
    res = run_sync([r for _, r in todo])
    out = {n: funny(res[r.hash]) for n, r in todo if "answers" in res.get(r.hash, {})}
    OUT.mkdir(exist_ok=True)
    (OUT / "_portrait.json").write_text(json.dumps(out, indent=1))
    print(f"{len(out)} portrait memes rated")


def main(ids: list[str]):
    desc = json.loads(DESCRIBE.read_text())
    q = Q
    todo = []
    for p in sorted(cases.OUT.glob("*.case.md")):
        i = p.name[:-8]
        c = cases.load(i) or {}
        if (ids and i not in ids) or not c.get("meme"):
            continue
        if c["meme"]["template"] not in desc:
            print(f"{i}: no description for {c['meme']['template']}")
            continue
        e = json.loads((cases.OUT / f"{i}.json").read_text())
        todo.append((i, Request(card(c, e, desc[c["meme"]["template"]]), q)))
    res = run_sync([r for _, r in todo])
    OUT.mkdir(exist_ok=True)
    n = 0
    for i, r in todo:
        resp = res.get(r.hash, {})
        if "answers" not in resp:
            print(f"{i}: no answer ({resp.get('error', '?')})")
            continue
        (OUT / f"{i}.json").write_text(json.dumps(funny(resp), indent=1))
        n += 1
    print(f"{n} memes rated")


if __name__ == "__main__":
    if sys.argv[1:] == ["portrait"]:
        portrait()
    else:
        main(sys.argv[1:])
