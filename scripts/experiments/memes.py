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
import urllib.error
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


PAGES = MEMES / "tpl" / "_imgflip_pages.json"


def _assignments(what: str = "A") -> dict:
    """Which meme each experiment gets (A), and the memes we cut rather than force (CUT):
    data/portrait/memes/assign.py, private because the captions quote results."""
    ns: dict = {}
    exec((MEMES / "assign.py").read_text(), ns)
    return ns.get(what, {})


def fetch_assigned():
    """Download every assigned template at full size, with imgflip's own default text boxes (from its generator page),
    converted to our label boxes: center x, y and width in percent, white outlined or dark text."""
    import html as H
    A = _assignments()
    pages = {H.unescape(v["name"]): (k, v["thumb"]) for k, v in json.loads(PAGES.read_text()).items()}
    cat = catalog()
    for name in sorted({v[0] for v in A.values()}):
        s = slug(name)
        if s in cat and cat[s].get("boxes_src") == "imgflip" and (MEMES / cat[s]["file"]).exists():
            continue
        key, thumb = pages[name]
        url = "https:" + thumb.replace("/4/", "/") if thumb.startswith("//") else thumb.replace("/4/", "/")
        try:
            raw = None
            for u in (url, re.sub(r"\.jpg$", ".png", url)):  # the thumbnail is a jpg; the full image may be a png
                try:
                    raw = urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=30).read()
                    url = u
                    break
                except urllib.error.HTTPError:
                    continue
            if raw is None:
                raise ValueError("no image")
            im = Image.open(io.BytesIO(raw)).convert("RGB")
            try:
                page = urllib.request.urlopen(urllib.request.Request(f"https://imgflip.com/memegenerator/{key}", headers=UA), timeout=30).read().decode("utf-8", "ignore")
            except urllib.error.HTTPError:  # some listing keys 404; the numeric id from imgflip's API works
                tid = next((t["id"] for t in json.loads(TOP.read_text())["data"]["memes"] if t["name"] == name), None)
                page = urllib.request.urlopen(urllib.request.Request(f"https://imgflip.com/memegenerator/{tid}", headers=UA), timeout=30).read().decode("utf-8", "ignore")
        except Exception as e:  # a dead link shouldn't stop the rest
            print("failed", name, e)
            continue
        boxes = []
        for m in re.finditer(r'\{"id":\d+,"uid":\d+,"name":"((?:[^"\\]|\\.)*)","w":(\d+),"h":(\d+).*?"default_settings":"((?:[^"\\]|\\.)*)"', page):
            if H.unescape(json.loads(f'"{m.group(1)}"')) != name:
                continue
            W, Hh = int(m.group(2)), int(m.group(3))
            try:
                settings = json.loads(json.loads(f'"{m.group(4)}"') or "[]")
            except json.JSONDecodeError:
                settings = []
            for b in settings:
                if b.get("type") != "text" or not all(k in b for k in ("x", "y", "w", "h")):
                    continue
                dark = str(b.get("font_color", "#ffffff")).lower() in ("#000000", "#000", "black")
                boxes.append({"x": round((b["x"] + b["w"] / 2) / W * 100, 1), "y": round((b["y"] + b["h"] / 2) / Hh * 100, 1),
                              "w": round(b["w"] / W * 100, 1), **({"style": "ink"} if dark else {})})
            break
        if im.width > 1000:
            im = im.resize((1000, round(im.height * 1000 / im.width)))
        f = f"tpl-{s}.webp"
        im.save(MEMES / f, "WEBP", quality=82)
        cat[s] = {"name": name, "file": f, "w": im.width, "h": im.height, "url": url, "boxes": boxes, "boxes_src": "imgflip"}
        print("fetched", s, im.size, len(boxes), "boxes")
    CATALOG.write_text(json.dumps(cat, indent=1, sort_keys=True))


def apply():
    """Write each assignment into its case file's front matter (meme: template, texts, caption, alt)."""
    import yaml
    A = _assignments()
    cat = catalog()
    for eid, (name, labels, caption) in A.items():
        p = cases.path(eid)
        if not p.exists():
            continue
        text = p.read_text()
        m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
        front = yaml.safe_load(m.group(1)) or {}
        front.pop("meme_idea", None)
        front.pop("meme_cut", None)
        front["meme"] = {"template": slug(name), "texts": labels or [], "caption": caption,
                         "alt": f"{name} meme" + (": " + "; ".join(x for x in (labels or []) if x) if labels else (f": {caption}" if caption else ""))}
        p.write_text("---\n" + yaml.safe_dump(front, sort_keys=False, allow_unicode=True, width=120) + "---\n" + m.group(2))
    for eid, why in _assignments("CUT").items():
        p = cases.path(eid)
        m = re.match(r"^---\n(.*?)\n---\n(.*)$", p.read_text(), re.S)
        front = yaml.safe_load(m.group(1)) or {}
        front.pop("meme", None)
        front["meme_cut"] = why
        p.write_text("---\n" + yaml.safe_dump(front, sort_keys=False, allow_unicode=True, width=120) + "---\n" + m.group(2))
    print(f"{len(A)} memes written into case files, {len(_assignments('CUT'))} cut")


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
        c = cases.load(i) or {}
        m = c.get("meme")
        if not m:
            if not c.get("meme_cut"):
                bad.append(f"{i}: no meme and no reason for cutting it")
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
    cut = [i for i in ids if (cases.load(i) or {}).get("meme_cut")]
    print(f"{len(ids)} cases, {sum(used.values())} memes, {len(used)} templates, {len(cut)} cut: {', '.join(cut)}")


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "fetch":
        fetch(sys.argv[2:])
    elif cmd == "fetch_assigned":
        fetch_assigned()
    elif cmd == "apply":
        apply()
    elif cmd == "check":
        check()
