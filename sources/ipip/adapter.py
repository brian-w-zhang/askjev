"""IPIP Big-Five items (public domain) from ipip.ori.org scoring keys, with Open Psychometrics
response distributions for the 50 Big-Five Factor Markers."""

from __future__ import annotations

import html
import io
import random
import re
import zipfile
from pathlib import Path
from typing import Iterator

import httpx
import polars as pl

from askjev.model import HumanDist, Question

NAME = "ipip"
LICENSE = "Public domain (IPIP items)"
NORMS_LICENSE = "Open Psychometrics raw data (no license stated)"
TARGET = 600
SEED = 20260924

BASE = "https://ipip.ori.org/"
PAGES = {
    "markers": "newBigFive5broadKey.htm",  # 50- and 100-item Big-Five Factor Markers
    "neo": "newNEOKey.htm",  # IPIP-NEO 30 facets (300 items)
    "bfas": "BFASKeys.htm",  # Big Five Aspect Scales (100 items)
    "ab5c": "newAB5CKey.htm",  # AB5C 45 facets
    "hexaco": "newHEXACO_PI_key.htm",  # IPIP HEXACO-PI analog (last-resort fill)
}
NORMS_URL = "https://openpsychometrics.org/_rawdata/IPIP-FFM-data-8Nov2018.zip"
NORMS_DIR = "IPIP-FFM-data-8Nov2018"

LEVELS = [
    "This does not describe me at all",
    "This describes me a little",
    "This describes me moderately well",
    "This describes me well",
    "This describes me very well",
]
TRAITS = ["openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"]
ROMAN = {"I": "extraversion", "II": "agreeableness", "III": "conscientiousness", "IV": "neuroticism", "V": "openness"}
NEO_DOMAIN = {"N": "neuroticism", "E": "extraversion", "O": "openness", "A": "agreeableness", "C": "conscientiousness"}
BFAS_DOMAIN = {
    "Neuroticism": "neuroticism",
    "Agreeableness": "agreeableness",
    "Conscientiousness": "conscientiousness",
    "Extraversion": "extraversion",
    "Openness/Intellect": "openness",
}
# Items whose stem is not a verb phrase, so "I " + stem would not be a sentence.
STEM_FIX = {"willing to": "am willing to", "never at a loss": "am never at a loss", "interested in": "am interested in"}
FLIP = {"+": "-", "-": "+"}
HEXACO_TRAIT = {"X": "extraversion", "A": "agreeableness", "C": "conscientiousness", "O": "openness"}


def fetch(raw_dir: Path) -> None:
    headers = {"User-Agent": "Mozilla/5.0 (askjev research)"}
    for page in PAGES.values():
        out = raw_dir / page
        if not out.exists():
            r = httpx.get(BASE + page, headers=headers, follow_redirects=True, timeout=60)
            r.raise_for_status()
            out.write_bytes(r.content)
    if not (raw_dir / NORMS_DIR / "data-final.csv").exists():
        r = httpx.get(NORMS_URL, headers=headers, follow_redirects=True, timeout=600)
        r.raise_for_status()
        (raw_dir / Path(NORMS_URL).name).write_bytes(r.content)
        zipfile.ZipFile(io.BytesIO(r.content)).extractall(raw_dir)


# ---------- parsing ----------

def _lines(path: Path) -> list[str]:
    t = path.read_bytes().decode("cp1252", errors="replace")
    t = re.sub(r"\s+", " ", t)
    t = re.sub(r"(?is)<(script|style).*?</\1>", " ", t)
    t = re.sub(r"(?i)</?(p|td|tr|br|h\d|li|div|table)\b[^>]*>", "\n", t)
    t = html.unescape(re.sub(r"<[^>]+>", " ", t))
    return [ln for ln in (re.sub(r"\s+", " ", x).strip() for x in t.split("\n")) if ln]


def _sign(line: str) -> str | None:
    if re.fullmatch(r"\+ ?keyed", line):
        return "+"
    if re.fullmatch(r"[–—-] ?keyed", line):
        return "-"
    return None


def _is_item(line: str) -> bool:
    return bool(re.fullmatch(r"\[?[A-Z][A-Za-z'’ ,\-\"“”/]*[.!?][\"”]?\]?( [a-d])?", line)) and not line.startswith("Note")


def _parse_markers(path: Path):
    trait = size = sign = None
    for ln in _lines(path):
        m = re.match(r"Factor ([IV]+) ", ln)
        if m:
            trait = ROMAN[m.group(1)]
            continue
        m = re.match(r"(10|20)-item scale", ln)
        if m:
            size = 50 if m.group(1) == "10" else 100
            continue
        if (s := _sign(ln)) is not None:
            sign = s
            continue
        if trait and sign and _is_item(ln):
            # Factor IV is keyed for Emotional Stability; flip to neuroticism.
            k = FLIP[sign] if trait == "neuroticism" else sign
            scale = f"Big-Five Factor Markers ({size}-item)"
            yield ln, trait, k, None, scale


def _parse_neo(path: Path):
    trait = facet = sign = None
    for ln in _lines(path):
        if ln.startswith("5 NEO Domains"):
            break
        m = re.match(r"([NEOAC])(\d): ([A-Z\- ]+?) \(", ln)
        if m:
            trait, facet, sign = NEO_DOMAIN[m.group(1)], f"{m.group(1)}{m.group(2)} {m.group(3).title()}", None
            continue
        if (s := _sign(ln)) is not None:
            sign = s
            continue
        if trait and sign and _is_item(ln):
            yield ln, trait, sign, facet, "IPIP-NEO-300"


def _parse_bfas(path: Path):
    trait = aspect = sign = None
    for ln in _lines(path):
        if ln.startswith("Note."):
            break
        if ln in BFAS_DOMAIN:
            trait, aspect, sign = BFAS_DOMAIN[ln], None, None
            continue
        if re.fullmatch(r"[A-Z][a-z]+", ln) and trait:
            aspect, sign = ln, None
            continue
        if (s := _sign(ln)) is not None:
            sign = s
            continue
        if trait and aspect and sign and _is_item(ln):
            yield ln, trait, sign, aspect, "BFAS"


def _parse_ab5c(path: Path):
    trait = facet = sign = None
    for ln in _lines(path):
        if ln.startswith("Note."):
            break
        m = re.match(r"([IV]+)\+/([IV]+)([+-]) vs .*?\(.*?\)\s*([A-Z][A-Z\- ]+)$", ln)
        if m:
            trait = ROMAN[m.group(1)]
            facet = f"{m.group(1)}+/{m.group(2)}{m.group(3)} {m.group(4).strip().title()}"
            sign = None
            continue
        if (s := _sign(ln)) is not None:
            sign = s
            continue
        # Bracketed items belong to other facets; skip them here.
        if trait and sign and _is_item(ln) and not ln.startswith("["):
            k = FLIP[sign] if trait == "neuroticism" else sign
            yield ln, trait, k, facet, "AB5C"


def _parse_hexaco(path: Path):
    """IPIP HEXACO-PI analog. X/A/C/O map to the Big Five trait of the same name; H and E have no
    Big Five counterpart and get trait None (placed under the Big Five parent)."""
    dom = facet = sign = None
    for ln in _lines(path):
        if ln.startswith("Note"):
            break
        m = re.match(r"(.+?) \(([HEXACO]):\w+\)", ln)
        if m:
            dom, facet, sign = m.group(2), m.group(1).strip(), None
            continue
        if (s := _sign(ln)) is not None:
            sign = s
            continue
        if dom and sign and _is_item(ln):
            yield ln, HEXACO_TRAIT.get(dom), sign, f"{dom}:{facet}", "IPIP-HEXACO"


def _sentence(stem: str) -> str:
    s = re.sub(r" [a-d]$", "", stem.strip()).strip("[]").strip()
    s = s.replace("’", "'").replace("“", "'").replace("”", "'").replace('"', "'")
    s = re.sub(r"\s+", " ", s)
    low = s[:1].lower() + s[1:]
    for k, v in STEM_FIX.items():
        if low.startswith(k):
            low = v + low[len(k):]
    s = "I " + low
    if not s.endswith((".", "!", "?", ".'")):
        s += "."
    return s


def _norm(s: str) -> str:
    return re.sub(r"[^a-z ]", "", s.lower().replace("'", "")).strip()


# ---------- norms ----------

def _norms(raw_dir: Path) -> dict[str, tuple[dict[str, float], int, str]]:
    """Per-item response shares (1-5 -> "0".."4") over respondents with IPC==1 and all 50 answers valid."""
    d = raw_dir / NORMS_DIR
    items = {}
    for ln in (d / "codebook.txt").read_text(encoding="utf-8", errors="replace").splitlines():
        m = re.match(r"^((?:EXT|EST|AGR|CSN|OPN)\d+)\t(.+)$", ln)
        if m:
            items[m.group(1)] = m.group(2).strip()
    cols = list(items)
    df = pl.read_csv(d / "data-final.csv", separator="\t", columns=cols + ["IPC"], infer_schema_length=0)
    df = df.with_columns([pl.col(c).cast(pl.Int64, strict=False) for c in cols + ["IPC"]])
    df = df.filter(pl.col("IPC") == 1)
    df = df.filter(pl.all_horizontal([pl.col(c).is_between(1, 5) for c in cols]))
    n = df.height
    out = {}
    for c in cols:
        vc = dict(df.group_by(c).len().iter_rows())
        out[_norm(items[c])] = ({str(k - 1): vc.get(k, 0) / n for k in range(1, 6)}, n, c)
    return out


# ---------- normalize ----------

def normalize(raw_dir: Path) -> Iterator[Question]:
    parsers = [
        ("markers", _parse_markers),
        ("neo", _parse_neo),
        ("bfas", _parse_bfas),
        ("ab5c", _parse_ab5c),
        ("hexaco", _parse_hexaco),
    ]
    items: dict[str, dict] = {}
    order: list[str] = []
    for key, fn in parsers:
        for stem, trait, keyed, facet, scale in fn(raw_dir / PAGES[key]):
            text = _sentence(stem)
            k = _norm(text)
            if k in items:
                if scale not in items[k]["also_in"] and scale != items[k]["scale"]:
                    items[k]["also_in"].append(scale)
                continue
            items[k] = dict(text=text, trait=trait, keyed=keyed, facet=facet, scale=scale, group=key, also_in=[])
            order.append(k)

    # Markers, IPIP-NEO and BFAS are kept whole. Then fill to TARGET tier by tier (seeded):
    # AB5C, then HEXACO items on Big Five-like domains (X/A/C/O), then HEXACO H/E.
    tiers = [
        [k for k in order if items[k]["group"] in ("markers", "neo", "bfas")],
        [k for k in order if items[k]["group"] == "ab5c"],
        [k for k in order if items[k]["group"] == "hexaco" and items[k]["trait"]],
        [k for k in order if items[k]["group"] == "hexaco" and not items[k]["trait"]],
    ]
    rng = random.Random(SEED)
    chosen: list[str] = []
    for tier in tiers:
        room = TARGET - len(chosen)
        if room <= 0:
            break
        pick = set(tier) if len(tier) <= room else set(rng.sample(tier, room))
        chosen += [k for k in tier if k in pick]

    norms = _norms(raw_dir)
    for k in chosen:
        it = items[k]
        human = []
        meta = {"scale": it["scale"], "keyed": it["keyed"], "facet": it["facet"], "trait": it["trait"]}
        if it["also_in"]:
            meta["also_in"] = it["also_in"]
        if k in norms:
            dist, n, code = norms[k]
            human.append(
                HumanDist(
                    population="OpenPsychometrics web",
                    distribution=dist,
                    n=n,
                    source="Open Psychometrics IPIP-FFM-data-8Nov2018 (1=Disagree..5=Agree mapped to levels 0-4)",
                    wave="2016-2018",
                )
            )
            meta["openpsychometrics_item"] = code
        stmt = it["text"]
        yield Question(
            text=f'How well does this statement describe you: "{stmt}"',
            primitive="score",
            hemisphere="self",
            kind="personality",
            origin="dataset",
            source=NAME,
            options=LEVELS,
            node_hint=f"self.personality.big_five.{it['trait']}" if it["trait"] in TRAITS else "self.personality.big_five",
            human_text=f'How well would most people say this statement describes them: "{stmt}"',
            source_item_id=f"{it['scale']}|{it['facet'] or it['trait']}|{stmt}",
            license=LICENSE if not human else f"{LICENSE}; norms: {NORMS_LICENSE}",
            human=human,
            meta=meta,
        )
