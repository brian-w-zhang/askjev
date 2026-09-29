"""Portrait step 9 (docs/11-portrait.md): every number on the rendered page must come from the ledger.

Fetches the rendered /portrait page, pulls every number out of its visible text, and checks each against the numbers
in data/analysis/portrait.json (the ledger claims the page uses plus the real rows in its drawers), in every format
the page prints them (percent, count, compact, fixed decimals, signed, ordinal). Prints what does not match, so it can
be read by hand; chapter numbers, axis ticks and years inside titles are expected there.

  uv run python scripts/portrait/verify_page.py [url]            # local dev server by default
  ASKJEV_KEY=... uv run python scripts/portrait/verify_page.py https://<prod>/portrait
  uv run python scripts/portrait/verify_page.py --experiments [base]  # every /portrait/atlas/<id> page against
                                                                      # its own entry in experiments.json
"""

from __future__ import annotations

import html
import http.cookiejar
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

A = Path("data/analysis")


def numbers(x, out: set[float]):
    if isinstance(x, bool):
        return
    if isinstance(x, (int, float)):
        out.add(float(x))
    elif isinstance(x, str):
        for m in re.findall(r"-?\d[\d,]*\.?\d*", x):
            try:
                out.add(float(m.replace(",", "")))
            except ValueError:
                pass
    elif isinstance(x, dict):
        for v in x.values():
            numbers(v, out)
    elif isinstance(x, list):
        for v in x:
            numbers(v, out)


def forms(v: float) -> set[str]:
    f = {f"{v:,.0f}", f"{v:.0f}", f"{v:.1f}", f"{v:.2f}", f"{v:.3f}", f"{abs(v):.1f}", f"{abs(v):.2f}", f"{abs(v):.3f}"}
    if -1.5 <= v <= 1.5:
        f |= {f"{v * 100:.0f}", f"{v * 100:.1f}", format(v, ".0%").rstrip("%"), format(v, ".1%").rstrip("%"),
              f"{100 - v * 100:.0f}", format(1 - v, ".0%").rstrip("%")}
    if v >= 1000:
        f |= {f"{v / 1e6:.1f}M", f"{v / 1e6:.0f}M", f"{round(v / 1e3)}k"}
    if 0 <= v <= 100:
        f |= {f"{100 - v:.0f}"}
    return {s.lstrip("-") for s in f}


def page_text(opener, url: str) -> str:
    raw = opener.open(url).read().decode()
    body = re.sub(r"<script.*?</script>|<style.*?</style>", " ", raw, flags=re.S)
    return html.unescape(re.sub(r"<[^>]+>", " ", body))


def open_site(url: str):
    # production is private: with ASKJEV_KEY set, open the site's key link first so the cookie is set
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    if os.environ.get("ASKJEV_KEY"):
        base = "/".join(url.split("/")[:3])
        opener.open(f"{base}/?key={urllib.parse.quote(os.environ['ASKJEV_KEY'])}").read()
    return opener


def experiments(base: str):
    """Every experiment page: each number it prints must come from that experiment's own entry (result, evidence,
    chart, rows, evaluation), from its rank and the total count, or be a chart axis tick."""
    X = json.loads((A / "experiments.json").read_text())["experiments"]
    opener = open_site(base)
    bad_pages = 0
    for i, e in enumerate(X):
        text = page_text(opener, f"{base}/portrait/atlas/{e['id']}")
        vals: set[float] = {float(i + 1), float(len(X))}
        numbers(e, vals)
        allowed = set().union(*(forms(v) for v in vals))
        # the evidence and prose quote numbers the page prints verbatim; ticks are round numbers on the chart axis
        tokens = re.findall(r"[+−-]?\d[\d,]*(?:\.\d+)?(?:M|k)?", text)
        miss = [t for t in tokens if t.lstrip("+−-") not in allowed and t.lstrip("+−-").replace(",", "") not in allowed
                and not re.fullmatch(r"[+−-]?(\d{1,3}|0\.\d)", t.lstrip("+−-"))]
        if miss:
            bad_pages += 1
            print(f"{e['id']}: {len(miss)} of {len(tokens)} unmatched: {sorted(set(miss))[:8]}")
    print(f"{len(X)} experiment pages checked; {bad_pages} with numbers not in their own entry")


def main():
    if "--experiments" in sys.argv:
        rest = [a for a in sys.argv[1:] if a != "--experiments"]
        return experiments(rest[0] if rest else "http://localhost:4592")
    url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:4592/portrait"
    opener = open_site(url)
    text = page_text(opener, url)
    P = json.loads((A / "portrait.json").read_text())
    allowed: set[str] = set()
    vals: set[float] = set()
    numbers(P["claims"], vals)
    numbers(P["rows"], vals)
    numbers(P["work"], vals)
    st = P.get("story") or {}
    numbers(st, vals)  # the chapters' numbers, copied from the experiments' result files (story.py)
    # derived on the page: 1 minus a share, a ratio of two scales, the top/bottom of a range
    p = st.get("personality") or {}
    for t in p.get("bigfive", []):
        vals.add(1 - t["pct"] / 100)
    for h in p.get("honesty", []):
        vals.add(round(h["jev"] / h["people"], 1))
    for v in vals:
        allowed |= forms(v)
    # sums the page prints: totals of claim n across a figure's claims, shown minus hidden, derived chart parts
    for group in ("knowledge_", "crowd_", "favorites_", "stable_", "fragile_", "bigfive_", "task_", "beyond_", "humor_", "mm_"):
        s = sum(c["n"] for k, c in P["claims"].items() if k.startswith(group))
        allowed |= forms(float(s))
    C = P["claims"]
    allowed |= forms(float(C["landscape_families"]["n"] - C["landscape_hidden"]["n"]))
    sc = C["pipeline_screen"]
    allowed |= forms(float(sc["first_hidden"] - sc["released"] - sc["by_rule"]))
    a = C["landscape_anchoring"]["anchoring"]
    allowed |= forms(a["truth"] - a["both"]) | forms(a["humans"] - a["both"])
    for h in ("world", "self", "machine"):
        allowed |= forms(float(sum(x["len"] for x in C["landscape_primitives"]["primitives"] if x["hemisphere"] == h)))
    tokens = re.findall(r"[+−-]?\d[\d,]*(?:\.\d+)?(?:M|k)?", text)
    missing = {}
    for t in tokens:
        s = t.lstrip("+−-")
        if s in allowed or s.replace(",", "") in allowed:
            continue
        missing[t] = missing.get(t, 0) + 1
    print(f"{len(tokens)} numbers on the page; {len(tokens) - sum(missing.values())} match the ledger")
    for t, k in sorted(missing.items(), key=lambda x: -x[1]):
        i = text.find(t)
        print(f"  {t!r} x{k}: …{' '.join(text[max(0, i - 60):i + 40].split())}…")


if __name__ == "__main__":
    main()
