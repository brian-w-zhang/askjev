"""Fetch Wikipedia Vital Articles (Level 3 and Level 4) with section paths, short descriptions, Wikidata
QIDs, sitelink counts and (optionally) 2-month pageviews. Public MediaWiki / Wikidata / Pageviews APIs only.

Writes data/raw/vital/level3.jsonl and level4.jsonl, one article per line:
  {title, section, section_path, shortdesc, qid, sitelinks, pageviews_60d}

Run: uv run python sources/vital4/fetch_vital.py [--pageviews=3,4]
Idempotent: raw wikitext, metadata and pageviews are cached under data/raw/vital/cache/.
"""

from __future__ import annotations

import json
import re
import sys
import threading
import time
from pathlib import Path
from urllib.parse import quote

import httpx

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "raw" / "vital"
CACHE = OUT / "cache"
UA = "askjev/0.1 (github.com/brian-w-zhang/askjev)"
WP_API = "https://en.wikipedia.org/w/api.php"
WD_API = "https://www.wikidata.org/w/api.php"
PV_API = "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/all-access/user/{}/monthly/{}/{}"
PV_START, PV_END = "20260701", "20260831"  # July + August 2026 (last two complete months)
MIN_INTERVAL = 0.5  # seconds between requests (<= 2 req/s overall)

L3_PAGE = "Wikipedia:Vital articles/Level/3"
L4_TOPICS = [
    "People",
    "History",
    "Geography",
    "Arts",
    "Philosophy and religion",
    "Everyday life",
    "Society and social sciences",
    "Biology and health sciences",
    "Physical sciences",
    "Technology",
    "Mathematics",
]
SKIP_HEADINGS = {"Current total", "Level 3 vital articles"}
LINK_RE = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]*)?(?:\|[^\]]*)?\]\]")
HEAD_RE = re.compile(r"^(=+)\s*(.*?)\s*\1\s*$")
BAD_NS = ("wikipedia:", "file:", "image:", "category:", "template:", "help:", "portal:", ":", "wp:", "special:")

_lock = threading.Lock()
_last = [0.0]
client = httpx.Client(headers={"User-Agent": UA}, timeout=60, follow_redirects=True)


def _throttle() -> None:
    with _lock:
        wait = _last[0] + MIN_INTERVAL - time.monotonic()
        if wait > 0:
            time.sleep(wait)
        _last[0] = time.monotonic()


def get(url: str, params: dict | None = None, allow_404: bool = False) -> dict | None:
    delay = 5.0
    for _ in range(8):
        _throttle()
        try:
            r = client.get(url, params=params)
        except httpx.HTTPError as e:
            print(f"  retry ({type(e).__name__}) {url[:60]}", flush=True)
            time.sleep(delay)
            delay *= 2
            continue
        if r.status_code == 404 and allow_404:
            return None
        if r.status_code in (429, 500, 502, 503, 504) or "too many requests" in r.text[:200].lower():
            print(f"  retry (HTTP {r.status_code}) {url[:60]}", flush=True)
            time.sleep(float(r.headers.get("retry-after", delay)))
            delay *= 2
            continue
        r.raise_for_status()
        d = r.json()
        if isinstance(d, dict) and d.get("error", {}).get("code") == "maxlag":
            print(f"  maxlag: {d['error'].get('info', '')[:80]}", flush=True)
            time.sleep(float(r.headers.get("retry-after", 5)))
            continue
        return d
    raise RuntimeError(f"gave up on {url} {params}")


def wikitext(title: str) -> str:
    f = CACHE / ("page_" + re.sub(r"[^A-Za-z0-9]+", "_", title) + ".txt")
    if f.exists():
        return f.read_text()
    d = get(
        WP_API,
        {
            "action": "query",
            "prop": "revisions",
            "rvprop": "content",
            "rvslots": "main",
            "titles": title,
            "redirects": 1,
            "format": "json",
            "formatversion": 2,
            "maxlag": 5,
        },
    )
    text = d["query"]["pages"][0]["revisions"][0]["slots"]["main"]["content"]
    f.write_text(text)
    return text


def parse_list(text: str, prefix: list[str]) -> list[dict]:
    """Walk headings and list items; each item's first article link gets the current heading path."""
    heads: dict[int, str] = {}
    out, seen = [], set()
    for line in text.splitlines():
        m = HEAD_RE.match(line.strip())
        if m:
            lvl, name = len(m.group(1)), re.sub(r"<[^>]+>|'''?|\{\{[^}]*\}\}", "", m.group(2)).strip()
            heads = {k: v for k, v in heads.items() if k < lvl}
            heads[lvl] = name
            continue
        s = line.lstrip()
        if not s or s[0] not in "#*":
            continue
        s = re.sub(r"<!--.*?-->", "", s)
        for lm in LINK_RE.finditer(s):
            t = lm.group(1).strip().replace("_", " ")
            if t.lower().startswith(BAD_NS):
                continue
            path = [h for lvl, h in sorted(heads.items()) if lvl >= 2 and h not in SKIP_HEADINGS]
            if not path and not prefix:
                break
            t = t[0].upper() + t[1:]
            if t not in seen:
                seen.add(t)
                full = prefix + path
                out.append({"title": t, "section_path": full, "section": " > ".join(full)})
            break
    return out


def metadata(titles: list[str]) -> dict[str, dict]:
    """title -> {resolved, shortdesc, qid} via prop=pageprops|description, 50 titles per call."""
    f = CACHE / "meta.json"
    cache = json.loads(f.read_text()) if f.exists() else {}
    todo = [t for t in titles if t not in cache]
    for i in range(0, len(todo), 50):
        batch = todo[i : i + 50]
        d = get(
            WP_API,
            {
                "action": "query",
                "prop": "pageprops|description",
                "ppprop": "wikibase_item|wikibase-shortdesc",
                "titles": "|".join(batch),
                "redirects": 1,
                "format": "json",
                "formatversion": 2,
                "maxlag": 5,
            },
        )
        q = d["query"]
        alias = {t: t for t in batch}
        for n in q.get("normalized", []):
            alias[n["from"]] = n["to"]
        redir = {r["from"]: r["to"] for r in q.get("redirects", [])}
        pages = {p["title"]: p for p in q["pages"]}
        for t in batch:
            r = alias[t]
            r = redir.get(r, r)
            p = pages.get(r, {})
            pp = p.get("pageprops", {})
            cache[t] = {
                "resolved": r,
                "missing": bool(p.get("missing")) or not p,
                "shortdesc": p.get("description") or pp.get("wikibase-shortdesc"),
                "qid": pp.get("wikibase_item"),
            }
        if i // 50 % 20 == 0:
            f.write_text(json.dumps(cache))
            print(f"  meta {i + len(batch)}/{len(todo)}", flush=True)
    f.write_text(json.dumps(cache))
    return cache


def sitelinks(qids: list[str]) -> dict[str, int]:
    f = CACHE / "sitelinks.json"
    cache = json.loads(f.read_text()) if f.exists() else {}
    todo = sorted({q for q in qids if q and q not in cache})
    for i in range(0, len(todo), 50):
        batch = todo[i : i + 50]
        d = get(WD_API, {"action": "wbgetentities", "ids": "|".join(batch), "props": "sitelinks", "format": "json"})
        time.sleep(1.0)  # Wikidata rate-limits large entity responses harder than enwiki
        for qid, e in d.get("entities", {}).items():
            cache[qid] = len(e.get("sitelinks", {}))
        if i // 50 % 20 == 0:
            f.write_text(json.dumps(cache))
            print(f"  sitelinks {i + len(batch)}/{len(todo)}", flush=True)
    f.write_text(json.dumps(cache))
    return cache


def pageviews(titles: list[str]) -> dict[str, int | None]:
    f = CACHE / f"pageviews_{PV_START}_{PV_END}.json"
    cache = json.loads(f.read_text()) if f.exists() else {}
    todo = [t for t in dict.fromkeys(titles) if t not in cache]

    def one(t: str) -> tuple[str, int | None]:
        d = get(PV_API.format(quote(t.replace(" ", "_"), safe=""), PV_START, PV_END), allow_404=True)
        return t, (sum(it["views"] for it in d["items"]) if d else None)

    for k, t in enumerate(todo, 1):
        try:
            cache[t] = one(t)[1]
        except RuntimeError:  # persistent 429s: leave uncached so a rerun retries it
            print(f"  pageviews skipped: {t}", flush=True)
        time.sleep(0.5)  # the Pageviews API 429s bursts from anonymous clients
        if k % 100 == 0:
            f.write_text(json.dumps(cache))
            print(f"  pageviews {k}/{len(todo)}", flush=True)
    f.write_text(json.dumps(cache))
    return cache


def build(level: int, with_pageviews: bool) -> Path:
    if level == 3:
        items = parse_list(wikitext(L3_PAGE), [])
    else:
        items, seen = [], set()
        for topic in L4_TOPICS:
            got = parse_list(wikitext(f"Wikipedia:Vital articles/Level/4/{topic}"), [topic])
            print(f"  L4 {topic}: {len(got)}", flush=True)
            for it in got:
                if it["title"] not in seen:
                    seen.add(it["title"])
                    items.append(it)
    print(f"level {level}: {len(items)} articles", flush=True)
    meta = metadata([it["title"] for it in items])
    sl = sitelinks([meta[it["title"]]["qid"] for it in items])
    pv = pageviews([meta[it["title"]]["resolved"] for it in items]) if with_pageviews else {}
    out = OUT / f"level{level}.jsonl"
    with open(out, "w") as fh:
        for it in items:
            m = meta[it["title"]]
            if m["missing"]:
                print(f"  missing page: {it['title']}", flush=True)
                continue
            rec = {
                "title": m["resolved"],
                "listed_as": it["title"] if it["title"] != m["resolved"] else None,
                "section": it["section"],
                "section_path": it["section_path"],
                "shortdesc": m["shortdesc"],
                "qid": m["qid"],
                "sitelinks": sl.get(m["qid"]) if m["qid"] else None,
                "pageviews_60d": pv.get(m["resolved"]),
            }
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return out


def main(pageviews_levels: tuple[int, ...] = ()) -> None:
    """Pageviews are opt-in (one request per article; the API rate-limits anonymous clients hard)."""
    CACHE.mkdir(parents=True, exist_ok=True)
    build(3, with_pageviews=3 in pageviews_levels)
    build(4, with_pageviews=4 in pageviews_levels)


if __name__ == "__main__":
    # --pageviews=3 or --pageviews=3,4
    arg = next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--pageviews=")), "")
    main(tuple(int(x) for x in arg.split(",") if x))
