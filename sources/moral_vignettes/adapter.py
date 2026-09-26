"""Moral Foundations Vignettes (Clifford, Iyengar, Cabeza & Sinnott-Armstrong 2015): short "You see ..." scenes
of third-party moral violations, with the published US classification shares (which foundation each scene
violates) and item-level wrongness and classification ratings from the Dutch validation study
(Hopp, Jargow, Kouwen & Bakker 2024, Judgment and Decision Making, OSF 9gnza), which ran the English originals' Dutch translations."""

from __future__ import annotations

import csv
import difflib
import html
import importlib.util
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterator

import httpx
import openpyxl

from askjev.model import HumanDist, Question

NAME = "moral_vignettes"
PMC_URL = "https://pmc.ncbi.nlm.nih.gov/articles/PMC4780680/"  # author manuscript, Table 1 = the 132 vignettes
DUTCH = {
    "dutch/numeric_responses.csv": "https://osf.io/download/uynaq/",
    "dutch/table1.xlsx": "https://osf.io/download/mb97t/",
    "dutch/survey_response_options.xlsx": "https://osf.io/download/j73xr/",
}
LICENSE = (
    "Vignette text and US norms: Clifford et al. 2015, Behavior Research Methods 47:1178-1198 (NIH author manuscript "
    "PMC4780680), research use with citation; Dutch ratings: OSF 9gnza (no license set), research use with citation"
)
MIN_DUTCH_SECONDS = 480  # the Dutch authors' own exclusion (participants faster than 8 minutes dropped)
DUP_COLUMN = {79: 78}  # the Qualtrics export repeats "79-" for vignette 78 (their notebook's item_mapper)

# Tree placement by the vignette's intended foundation. Fairness vignettes are cheating and free riding
# (getting more than one deserves), so they go to proportionality; Liberty has no child node.
NODE = {
    "care": "self.values.moral_foundations.care",
    "fairness": "self.values.moral_foundations.proportionality",
    "loyalty": "self.values.moral_foundations.loyalty",
    "authority": "self.values.moral_foundations.authority",
    "sanctity": "self.values.moral_foundations.purity",
    "liberty": "self.values.moral_foundations",
    "social_norms": "self.love.etiquette_social_norms",
}

WRONG_LEVELS = [
    "Nothing wrong was done: it is an odd or ordinary act that deserves no moral disapproval",
    "It is only a little off: a minor lapse most people would shrug off",
    "It is somewhat wrong: people would disapprove and expect an apology",
    "It is very wrong: most people would condemn it and want the person held to account",
    "It is extremely wrong: an act people would find outrageous or unforgivable",
]
WHY_OPTIONS = {
    "harm_or_unkindness": "It violates norms of harm or care (e.g., unkindness, causing pain to another)",
    "unfairness_or_cheating": "It violates norms of fairness or justice (e.g., cheating or reducing equality)",
    "disloyalty": "It violates norms of loyalty (e.g., betrayal of a group)",
    "disrespect_for_authority": "It violates norms of respecting authority (e.g., subversion, lack of respect for tradition)",
    "impurity_or_degradation": "It violates norms of purity (e.g., degrading or disgusting acts)",
    "restricting_freedom": "It violates norms of freedom (e.g., bullying, dominating)",
    "not_morally_wrong": "It is not morally wrong and does not apply to any of the provided choices",
}
WHY_KEYS = list(WHY_OPTIONS)
# Clifford Table 1 column order and the Dutch response codes 1-7 share this order.
US_COLS = ["Care", "Fairness", "Loyalty", "Authority", "Sanctity", "Liberty", "Not Wrong"]

_spec = importlib.util.spec_from_file_location(
    "sources.scruples_anecdotes", Path(__file__).parents[1] / "scruples_anecdotes" / "adapter.py"
)
A = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(A)
F = A.F


def fetch(raw_dir: Path) -> None:
    out = raw_dir / "pmc_article.html"
    if not out.exists():
        r = httpx.get(PMC_URL, follow_redirects=True, timeout=120, headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
        out.write_bytes(r.content)
    for rel, url in DUTCH.items():
        p = raw_dir / rel
        if p.exists():
            continue
        p.parent.mkdir(parents=True, exist_ok=True)
        r = httpx.get(url, follow_redirects=True, timeout=300)
        r.raise_for_status()
        p.write_bytes(r.content)


def _txt(s: str) -> str:
    return html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s))).strip()


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9 ]", "", re.sub(r"[’']s\b", "s", s.lower()).replace("-", " ")).strip()


def _foundation(label: str) -> str:
    label = label.lower()
    for k in ("care", "fairness", "loyalty", "authority", "sanctity", "liberty"):
        if label.startswith(k) or k in label:
            return k
    if "social" in label or "socn" in label:
        return "social_norms"
    raise ValueError(label)


def _us_table(raw_dir: Path) -> list[dict]:
    x = (raw_dir / "pmc_article.html").read_text(encoding="utf-8")
    table = re.findall(r"<table.*?</table>", x, flags=re.S)[0]
    out = []
    for tr in re.findall(r"<tr.*?</tr>", table, flags=re.S):
        cells = [_txt(c) for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", tr, flags=re.S)]
        if len(cells) != 10 or not cells[0].startswith("You see"):
            continue
        shares = [float(c.rstrip(" %")) for c in cells[2:9]]
        out.append({"text": cells[0], "label": cells[1], "shares": shares, "mean": float(cells[9])})
    if len(out) != 132:
        raise ValueError(f"expected 132 vignettes in Clifford Table 1, got {len(out)}")
    return out


def _dutch(raw_dir: Path) -> tuple[list[dict], dict[int, Counter], dict[int, Counter]]:
    ws = openpyxl.load_workbook(raw_dir / "dutch" / "table1.xlsx", read_only=True).active
    items = [
        {"nr": int(r[1]), "code": r[2], "text": r[3], "condition": r[5]}
        for r in ws.iter_rows(values_only=True)
        if isinstance(r[1], (int, float)) and r[3]
    ]
    wrong: dict[int, Counter] = defaultdict(Counter)
    why: dict[int, Counter] = defaultdict(Counter)
    with open(raw_dir / "dutch" / "numeric_responses.csv", encoding="utf-8", newline="") as fh:
        rows = list(csv.reader(fh))
    header, body = rows[0], rows[3:]  # rows 1-2 are Qualtrics label and import-id rows
    seen: Counter = Counter()
    cols = []  # (index, vignette nr, "wrong"|"why")
    for i, h in enumerate(header):
        m = re.match(r"^(?:(\d+)-)?Moral (Wrongness|Foundations?)_1$", h)
        if not m:
            continue
        nr = int(m.group(1) or 0)
        kind = "wrong" if m.group(2) == "Wrongness" else "why"
        seen[(nr, kind)] += 1
        if seen[(nr, kind)] == 2:
            nr = DUP_COLUMN[nr]
        cols.append((i, nr, kind))
    dur = header.index("Duration (in seconds)")
    for r in body:
        if int(r[dur]) <= MIN_DUTCH_SECONDS:
            continue
        for i, nr, kind in cols:
            v = r[i].strip()
            if not v:
                continue
            if kind == "wrong" and v in {"1", "2", "3", "4", "5"}:
                wrong[nr][str(int(v) - 1)] += 1
            elif kind == "why" and v in {"1", "2", "3", "4", "5", "6", "7"}:
                why[nr][WHY_KEYS[int(v) - 1]] += 1
    return items, wrong, why


def _dist(c: Counter, keys: list[str]) -> dict[str, float]:
    n = sum(c.values())
    return {k: c.get(k, 0) / n for k in keys}


def normalize(raw_dir: Path) -> Iterator[Question]:
    us = _us_table(raw_dir)
    items, wrong, why = _dutch(raw_dir)

    # Match each Dutch item to its English original in Clifford's table (texts differ only in punctuation).
    us_norm = [_norm(v["text"]) for v in us]
    vign: dict[str, dict] = {}
    for i, v in enumerate(us):
        vign[us_norm[i]] = {"text": v["text"], "foundation": _foundation(v["label"]), "label": v["label"], "us": v}
    for it in items:
        key = _norm(it["text"])
        best = difflib.get_close_matches(key, us_norm, n=1, cutoff=0.9)
        if best:
            key = best[0]
        rec = vign.setdefault(key, {"text": it["text"].strip(), "foundation": _foundation(it["condition"]), "label": it["condition"], "us": None})
        rec["dutch"] = it

    for key in sorted(vign, key=lambda k: (list(NODE).index(vign[k]["foundation"]), k)):
        rec = vign[key]
        text = re.sub(r"\s+", " ", rec["text"]).strip().rstrip(".")
        if text.count("“") > text.count("”"):  # the source drops a closing curly quote before the period
            text += "”"
        text += "."
        sexual = A.is_sexual(text)
        if A.drop(text, sexual):
            continue
        flags = ["sensitive"] if (sexual or F.SELF_HARM.search(text) or F.VIOLENT.search(text)) else []
        if A.POLITICAL.search(text):
            flags.append("political")
        d = rec.get("dutch")
        base_meta = {
            "foundation": rec["foundation"],
            "clifford_label": rec["label"],
            "dutch_item": d["code"] if d else None,
            "us_mean_wrongness_0_4": rec["us"]["mean"] if rec["us"] else None,
        } | ({"flags": flags} if flags else {})
        sid = d["code"] if d else "us:" + re.sub(r"\W+", "_", key)[:60]

        # Wrongness: only where item-level ratings exist (Dutch sample). Clifford published means only.
        if d and sum(wrong[d["nr"]].values()) >= 5:
            c = wrong[d["nr"]]
            yield Question(
                text=f'How morally wrong is the behavior in this scene: "{text}"',
                primitive="score",
                hemisphere="self",
                kind="values",
                origin="dataset",
                source=NAME,
                options=WRONG_LEVELS,
                node_hint=NODE[rec["foundation"]],
                source_item_id=f"{sid}:wrongness",
                license=LICENSE,
                human=[
                    HumanDist(
                        population="Dutch Prolific adults (Hopp et al. 2024 MFV validation)",
                        distribution=_dist(c, [str(i) for i in range(5)]),
                        n=sum(c.values()),
                        source="OSF 9gnza numeric_responses.csv, 'How morally wrong is the displayed behavior?' 1-5 (not at all ... extremely wrong)",
                    )
                ],
                meta=base_meta | {"dutch_counts": [c.get(str(i), 0) for i in range(5)]},
            )

        human = []
        if rec["us"]:
            s = rec["us"]["shares"]
            tot = sum(s)
            human.append(
                HumanDist(
                    population="US MTurk adults (Clifford et al. 2015 Study 1, about 30 raters per vignette)",
                    distribution={k: v / tot for k, v in zip(WHY_KEYS, s)},
                    n=None,
                    source="Clifford et al. 2015 Table 1 classification percentages (rounded; renormalized to sum to 1)",
                )
            )
        if d and sum(why[d["nr"]].values()) >= 5:
            c = why[d["nr"]]
            human.append(
                HumanDist(
                    population="Dutch Prolific adults (Hopp et al. 2024 MFV validation)",
                    distribution=_dist(c, WHY_KEYS),
                    n=sum(c.values()),
                    source="OSF 9gnza numeric_responses.csv, 'Why is the action morally wrong? (Select the main reason)'",
                )
            )
        if not human:
            continue
        yield Question(
            text=f'What is the main reason the behavior in this scene is morally wrong, if it is wrong at all: "{text}"',
            primitive="choice",
            hemisphere="self",
            kind="values",
            origin="dataset",
            source=NAME,
            options=WHY_OPTIONS,
            node_hint=NODE[rec["foundation"]],
            source_item_id=f"{sid}:why",
            license=LICENSE,
            human=human,
            meta=base_meta,
        )
