"""Brysbaert, Warriner & Kuperman (2014) concreteness ratings for 40k English lemmas: "How concrete is the word X?"

Only common words the Glasgow Norms do not already cover (so the two sources never ask about the same word), each
with its rating mean/SD mapped onto 5 concrete levels. Also home of the shared helpers the word-norm adapters use
(lancaster, glasgow_norms): the Brysbaert xlsx reader (stdlib only), the normal-to-levels discretizer, the word
node_hint (boolq's keyword rules, else `world`) and the word content flags.
"""

from __future__ import annotations

import importlib.util
import math
import re
import sys
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Iterator

import httpx

from askjev.model import HumanDist, Question
from askjev.sampling import env_int, hash_order

NAME = "concreteness"
FILE = "Concreteness_ratings_Brysbaert_et_al_BRM.xlsx"
URL = ("https://static-content.springer.com/esm/art%3A10.3758%2Fs13428-013-0403-5/MediaObjects/"
       "13428_2013_403_MOESM1_ESM.xlsx")  # Behavior Research Methods supplementary file
LICENSE = "Research use (Brysbaert, Warriner & Kuperman 2014, Behavior Research Methods, supplementary data)"
TARGET = env_int("TARGET_CONCRETENESS", 3000)
SALT = "concreteness-20260925"
MIN_SUBTLEX = 150  # raw SUBTLEX-US count (51M words): about 3 per million, i.e. common words
MIN_KNOWN = 0.95
MIN_SD = 0.3

TEXT = 'How concrete is the word "{w}": can you directly see, hear, touch, smell, taste or do what it means?'
HUMAN_TEXT = 'How concrete is the word "{w}" to most people: can they directly perceive or do what it means?'
LEVELS = [
    "Purely abstract: its meaning can only be explained with other words, never shown or sensed",
    "Mostly abstract: it has a few sensory associations but is understood mainly through language",
    "In between: it is partly something you can perceive and partly an idea",
    "Mostly concrete: you can usually see, hear, touch or do what it names",
    "Fully concrete: you can point at it or directly see, hear, touch, smell or taste what it names",
]


# --- shared helpers -----------------------------------------------------------------------------------------------
def read_brysbaert(path: Path) -> dict[str, dict]:
    """word -> {conc_m, conc_sd, n, percent_known, subtlex, bigram} from the supplementary xlsx (no Excel library)."""
    ns = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    with zipfile.ZipFile(path) as z:
        strings = ["".join(t.text or "" for t in si.iter(f"{{{ns['m']}}}t"))
                   for si in ET.fromstring(z.read("xl/sharedStrings.xml")).findall("m:si", ns)]
        sheet = ET.fromstring(z.read("xl/worksheets/sheet1.xml"))
    rows = []
    for row in sheet.find("m:sheetData", ns).findall("m:row", ns):
        vals = {}
        for c in row.findall("m:c", ns):
            col = re.match(r"[A-Z]+", c.get("r")).group(0)
            v = c.find("m:v", ns)
            if v is None:
                continue
            vals[col] = strings[int(v.text)] if c.get("t") == "s" else v.text
        rows.append(vals)
    head = {col: name for col, name in rows[0].items()}
    out = {}
    for r in rows[1:]:
        d = {head[c]: v for c, v in r.items() if c in head}
        w = d.get("Word")
        if not w or "Conc.M" not in d:
            continue
        out[str(w)] = {
            "conc_m": float(d["Conc.M"]),
            "conc_sd": float(d["Conc.SD"]),
            "n": int(float(d["Total"])) - int(float(d["Unknown"])),
            "percent_known": float(d["Percent_known"]),
            "subtlex": int(float(d.get("SUBTLEX") or 0)),
            "bigram": int(float(d.get("Bigram") or 0)),
        }
    return out


def fetch_brysbaert(raw_dir: Path) -> None:
    out = raw_dir / FILE
    if out.exists():
        return
    r = httpx.get(URL, follow_redirects=True, timeout=300)
    r.raise_for_status()
    out.write_bytes(r.content)


def _phi(x: float) -> float:
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def discretize(mean: float, sd: float, edges: list[float], min_sd: float = MIN_SD) -> dict[str, float]:
    """Normal(mean, max(sd, min_sd)) cut at `edges` into len(edges)+1 levels (tails folded into the end levels)."""
    sd = max(sd, min_sd)
    cdf = [0.0] + [_phi((e - mean) / sd) for e in edges] + [1.0]
    p = [cdf[i + 1] - cdf[i] for i in range(len(cdf) - 1)]
    s = sum(p)
    return {str(i): v / s for i, v in enumerate(p)}


_boolq = None


def word_node(word: str) -> str:
    """boolq's keyword rules on the bare word (first matching rule), else the root `world` for the beam walk."""
    global _boolq
    if _boolq is None:
        spec = importlib.util.spec_from_file_location("sources.boolq", Path(__file__).parents[1] / "boolq" / "adapter.py")
        _boolq = importlib.util.module_from_spec(spec)
        sys.modules["sources.boolq"] = _boolq
        spec.loader.exec_module(_boolq)
    for rx, node in _boolq.RULES_RE:
        if rx.search(word):
            return node
    return "world"


SLURS = re.compile(r"^(fag\w*|faggot|nigg\w*|retard\w*|tranny|dyke|spic|spics|chink|chinks|kike|kikes|gook|gooks|"
                   r"paki|wop|coon|honky|cunt|twat|whore|slut)$", re.I)
SENSITIVE = re.compile(
    r"^(sex\w*|porn\w*|nude|naked|penis|vagina|clitoris|boobs?|breasts?|nipples?|dick|cock|pussy|tits|testicles?|"
    r"scrotum|masturbat\w*|orgasm\w*|erect\w*|ejaculat\w*|sperm|semen|condoms?|horny|erotic\w*|fetish\w*|kinky|"
    r"anal|anus|orgy|bondage|brothel|prostitut\w*|hooker|stripper|pimp|lust|seduc\w*|rape\w*|rapist|molest\w*|"
    r"incest|pedophil\w*|paedophil\w*|suicid\w*|self-harm|overdose|corpse|gore|mutilat\w*|torture\w*|decapitat\w*|"
    r"slaughter\w*|murder\w*|massacre|genocide|bitch|bastard|shit|fuck\w*|crap|piss|ass|arse|damn)$",
    re.I,
)
POLITICAL = re.compile(
    r"^(abortion|nazi\w*|hitler|fascis\w*|communis\w*|socialis\w*|capitalis\w*|feminis\w*|immigra\w*|refugee\w*|"
    r"democrat\w*|republican\w*|liberal|conservative|terroris\w*|jihad\w*|islam\w*|muslims?|jews?|jewish|judaism|zionis\w*|"
    r"christian\w*|atheis\w*|racis\w*|gay|lesbian|homosexual\w*|transgender|gun|guns|rifle|election|vote|ballot|"
    r"brexit|trump|obama|clinton)$",
    re.I,
)


def word_flags(word: str) -> list[str]:
    w = re.sub(r"\s*\(.*\)$", "", word).strip()
    flags = []
    if POLITICAL.match(w):
        flags.append("political")
    if SENSITIVE.match(w):
        flags.append("sensitive")
    return flags


def glasgow_words(raw_dir: Path) -> set[str]:
    """Lowercased head words of the Glasgow Norms (for non-overlap), read from the glasgow_norms raw folder."""
    p = raw_dir.parent / "glasgow_norms" / "glasgow_norms.csv"
    if not p.exists():
        raise FileNotFoundError(f"{p}: run `askjev source glasgow_norms` first (concreteness avoids its words)")
    out = set()
    for line in p.read_text(encoding="utf-8").splitlines()[2:]:
        w = line.split(",", 1)[0]
        if w:
            out.add(re.sub(r"\s*\(.*\)$", "", w).strip().lower())
    return out


# --- adapter ------------------------------------------------------------------------------------------------------
def fetch(raw_dir: Path) -> None:
    fetch_brysbaert(raw_dir)


def normalize(raw_dir: Path) -> Iterator[Question]:
    rows = read_brysbaert(raw_dir / FILE)
    skip = glasgow_words(raw_dir)
    pool = [w for w, r in rows.items()
            if r["bigram"] == 0 and re.fullmatch(r"[a-z]{3,}", w) and w not in skip
            and r["subtlex"] >= MIN_SUBTLEX and r["percent_known"] >= MIN_KNOWN and not SLURS.match(w)]
    picked = sorted(hash_order(pool, lambda w: w, SALT)[:TARGET])
    print(f"concreteness: {len(rows)} lemmas, {len(pool)} common single words outside Glasgow, {len(picked)} picked")
    for w in picked:
        r = rows[w]
        meta = {"word": w, "mean_1_5": r["conc_m"], "sd": r["conc_sd"], "subtlex_count": r["subtlex"],
                "dist_method": f"normal(mean, max(sd,{MIN_SD})) on the 1-5 scale, cut at 1.5, 2.5, 3.5, 4.5"}
        flags = word_flags(w)
        if flags:
            meta["flags"] = flags
        yield Question(
            text=TEXT.format(w=w),
            primitive="score",
            hemisphere="world",
            kind="perception",
            origin="dataset",
            source=NAME,
            options=LEVELS,
            node_hint=word_node(w),
            human_text=HUMAN_TEXT.format(w=w),
            source_item_id=w,
            license=LICENSE,
            template_id="concreteness.concreteness",
            human=[HumanDist(
                population="Brysbaert et al. 2014 MTurk raters (US)",
                distribution=discretize(r["conc_m"], r["conc_sd"], [1.5, 2.5, 3.5, 4.5]),
                n=r["n"],
                source="Brysbaert, Warriner & Kuperman 2014 concreteness ratings",
            )],
            meta=meta,
        )
