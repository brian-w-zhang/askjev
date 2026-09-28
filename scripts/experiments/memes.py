"""Memes for the case studies (docs/17 items 8-9).

Templates are downloaded once into data/portrait/memes/tpl-<slug>.webp (private, gitignored, served by the portrait's
meme route and published with it). data/portrait/memes/catalog.json records each template: name, size, and the label
boxes our words go in (percent of the image; reaction formats have none and take a caption above instead). A case
file names its meme in front matter:

  meme:
    template: drake
    texts: ["...", "..."]        # one per label box, in order
    caption: "..."               # optional, above the image
    alt: "..."                   # what the image shows, for screen readers

  uv run python scripts/experiments/memes.py fetch [slugs]   # download templates (imgflip's public list + extra URLs)
  uv run python scripts/experiments/memes.py check           # every case's meme resolves; no template used twice
"""

from __future__ import annotations

import io
import json
import re
import sys
import urllib.request
from collections import Counter
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cases  # noqa: E402

MEMES = Path("data/portrait/memes")
CATALOG = MEMES / "catalog.json"
TOP = MEMES / "tpl" / "_imgflip_top.json"
UA = {"User-Agent": "Mozilla/5.0 (askjev research; private)"}
# politicians' faces and the too-dark or crude: never used (no politics on the site)
SKIP = {"bernie_i_am_once_again_asking_for_your_support", "bernie_sanders_once_again_asking", "george_bush_9_11",
        "trump_bill_signing", "a_train_hitting_a_school_bus", "megamind_no_bitches"}


def slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def catalog() -> dict:
    return json.loads(CATALOG.read_text()) if CATALOG.exists() else {}


def fetch(only: list[str], extra: dict[str, str] | None = None):
    cat = catalog()
    items = [(slug(m["name"]), m["name"], m["url"]) for m in json.loads(TOP.read_text())["data"]["memes"]]
    items += [(s, s.replace("_", " "), u) for s, u in (extra or {}).items()]
    for s, name, url in items:
        if s in SKIP or (only and s not in only) or (s in cat and (MEMES / cat[s]["file"]).exists()):
            continue
        try:
            raw = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30).read()
            im = Image.open(io.BytesIO(raw)).convert("RGB")
            if im.width > 1000:
                im = im.resize((1000, round(im.height * 1000 / im.width)))
            f = f"tpl-{s}.webp"
            im.save(MEMES / f, "WEBP", quality=82)
            cat.setdefault(s, {"name": name, "boxes": []})
            cat[s].update({"file": f, "w": im.width, "h": im.height, "url": url})
            print("fetched", s, im.size)
        except Exception as e:  # a dead link shouldn't stop the rest
            print("failed", s, e)
    CATALOG.write_text(json.dumps(cat, indent=1, sort_keys=True))


def resolve(m: dict) -> dict | None:
    """A case's meme as the site draws it (see web/src/components/experiments/ExMeme.tsx)."""
    t = catalog().get(m.get("template", ""))
    if not t or not (MEMES / t["file"]).exists():
        return None
    return {"name": m["template"], "file": t["file"], "w": t["w"], "h": t["h"], "boxes": t.get("boxes", []),
            "texts": m.get("texts") or [], "caption": m.get("caption"), "alt": m.get("alt") or t["name"]}


def check():
    cat, used, bad = catalog(), Counter(), []
    ids = sorted(p.name[:-8] for p in cases.OUT.glob("*.case.md"))
    for i in ids:
        m = (cases.load(i) or {}).get("meme")
        if not m:
            bad.append(f"{i}: no meme")
            continue
        t = cat.get(m.get("template", ""))
        used[m.get("template")] += 1
        if not t:
            bad.append(f"{i}: unknown template {m.get('template')}")
        elif len(m.get("texts") or []) > len(t.get("boxes", [])):
            bad.append(f"{i}: {len(m['texts'])} texts for {len(t.get('boxes', []))} boxes")
        elif not m.get("alt"):
            bad.append(f"{i}: no alt text")
    for t, n in used.items():
        if n > 1:
            bad.append(f"template {t} used {n} times")
    print("\n".join(bad) or "all memes resolve; no template reused")
    print(f"{len(ids)} cases, {sum(used.values())} memes, {len(used)} templates")


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "fetch":
        fetch(sys.argv[2:])
    elif cmd == "check":
        check()
