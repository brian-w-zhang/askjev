"""AIMS survey (Artificial Intelligence, Morality, and Sentience; Sentience Institute, CC BY 4.0): nationally
representative US surveys (2021, 2023, 2024 waves plus a 2023 supplement) on whether AIs can be sentient, how
they should be treated, trust in AI and AI risk. Item wording from the published codebooks; one HumanDist per
wave from the census-balancing weights."""

from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path
from typing import Iterator

import httpx
import openpyxl

from askjev.model import HumanDist, Question

NAME = "aims_survey"
MENDELEY = "https://data.mendeley.com/public-files/datasets/x5689yhv2n/files/{}/file_downloaded"
FILES = {
    "Codebook_AIMS.xlsx": "977f760f-f338-481f-9823-9eb3b2f8d8be",
    "Codebook_AIMS_Supplement_2023.xlsx": "bd1c1b1f-91f9-4a43-a515-df0a69066378",
    "AIMS_wave1-3.xlsx": "4f2a515f-1d6a-449a-ad88-54d97b6ef5fa",
    "AIMS_Supplement_2023.xlsx": "ea5687bd-6178-4a4b-b78c-db4288480739",
}
LICENSE = "CC BY 4.0 (Sentience Institute, AIMS Survey, Mendeley Data doi:10.17632/x5689yhv2n.3)"
NODE = "self.mind.consciousness_ai"

AGREE7 = [
    "I strongly disagree with this statement",
    "I disagree with this statement",
    "I somewhat disagree with this statement",
    "I have no opinion on this statement, or neither agree nor disagree",
    "I somewhat agree with this statement",
    "I agree with this statement",
    "I strongly agree with this statement",
]
SUPPORT5 = [
    "I strongly oppose humans uploading their minds into computers",
    "I somewhat oppose it",
    "I neither oppose nor support it",
    "I somewhat support it",
    "I strongly support humans uploading their minds into computers",
]
EXTENT5 = ["Not at all", "A little", "A moderate amount", "Quite a lot", "Very much"]
CAPACITY5 = [
    "They have none of this capacity",
    "They have a little of this capacity",
    "They have a moderate amount of this capacity",
    "They have a lot of this capacity",
    "They fully have this capacity",
]
LIKELY5 = [
    "This almost certainly will not happen (0-10% likely)",
    "This probably will not happen (11-35% likely)",
    "This is about as likely as not (36-64% likely)",
    "This probably will happen (65-89% likely)",
    "This almost certainly will happen (90-100% likely)",
]
C7 = {1: 0, 2: 1, 3: 1, 4: 2, 5: 3, 6: 3, 7: 4}  # 1-7 extent / support scale collapsed to 5 levels


def _pct5(v: float, top: float) -> int:
    x = v / top * 100
    return 0 if x <= 10 else 1 if x <= 35 else 2 if x < 65 else 3 if x < 90 else 4


# key -> (format, kind); format decides text frame, levels and value mapping
AGREE_KEYS = (
    [f"PMC{i}" for i in range(1, 14)] + [f"MCE{i}" for i in range(1, 10)] + [f"SI{i}" for i in range(1, 5)]
    + ["MCA1", "MCA2", "MCEn1", "MCEn2", "TA1", "TA2", "Sub1", "Sub2", "chatbottrust", "LLMtrust", "robottrust",
       "gameAItrust", "relativeLLMchatbottrust", "AID4"] + [f"RS{i}" for i in range(1, 10)]
    + ["LLM1", "LLM2", "LLM3", "SF1", "SF2"]
)
TRUST_PARTS = {"trainingdatatrust": "their training data", "algorithmtrust": "the algorithm",
               "outputtrust": "their output", "companytrust": "the companies that build them",
               "engineertrust": "the engineers who build them", "governmenttrust": "the governments that regulate them"}
EMOTIONS = ["admiration", "awe", "pride", "compassion", "excitement", "respect"]
LLM_CAPS = ["MP1", "MP2", "MP3", "MP4", "owngoals", "safegoals", "upholding", "selfaware", "sitaware", "selfcontrol",
            "understanding", "friendliness", "power", "ownmotives"]
CHOICE3 = {"F1", "F11", "chatGPTsentient", "AID1", "AID2", "AID3"}
YNS = {"yes": "Yes", "no": "No", "not_sure": "Not sure"}
PACE = {"too_fast": "It's too fast", "too_slow": "It's too slow", "fine": "It's fine", "not_sure": "Not sure"}

POLITICAL = re.compile(r"\b(government\w*|ban|banning|regulat\w*|legal rights|campaigns?|demonstration|bill of rights)\b", re.I)
VALUES = re.compile(r"^(PMC|MCE|MCA|MCEn|Sub|LLM)\d|^SI1$")
FORECAST = {"F4", "SI2", "SI3", "SI4", "RS1", "RS2", "F11"}


def fetch(raw_dir: Path) -> None:
    for name, fid in FILES.items():
        p = raw_dir / name
        if not p.exists():
            r = httpx.get(MENDELEY.format(fid), follow_redirects=True, timeout=300)
            r.raise_for_status()
            p.write_bytes(r.content)


def _sheet(path: Path) -> list[dict]:
    wb = openpyxl.load_workbook(path, read_only=True)
    ws = wb.worksheets[0]
    ws.reset_dimensions()
    rows = ws.iter_rows(values_only=True)
    head = [str(h).strip() if h is not None else "" for h in next(rows)]
    return [dict(zip(head, r)) for r in rows]


def _codebook(path: Path) -> dict[str, str]:
    out = {}
    for r in _sheet(path):
        k, t = r.get("Key"), r.get("Item Wording")
        if k and t:
            out[str(k).strip()] = re.sub(r"\s+", " ", str(t)).strip()
    return out


def _clean(s: str) -> str:
    s = s.replace("…", "...").replace("“", '"').replace("”", '"').replace("’", "'")
    s = re.sub(r"\s*\.\.\.\.?\s*", "... ", s).strip()
    return s


def _item(key: str, cb: dict[str, str], year: str) -> tuple[str, str, object, callable] | None:
    """(text, primitive, options, value->key/level) for one variable, or None if not used."""
    t = cb.get(key)
    if t and year:  # the main codebook is the 2021 wording; later waves asked about robots/AIs existing that year
        t = t.replace("2021", year)
    if key == "F1":  # "currently exist (i.e., those that exist in <year>)" would clash with the asking date
        t = f"Do you think any of the robots/AIs that existed in {year} were sentient?"
    if key == "AID4":
        t = "Governments have the power to effectively enforce regulations on the development of AI."
    if key in AGREE_KEYS and t:
        s = _clean(t)
        return f'How much do you agree: "{s}"', "score", AGREE7, lambda v: min(6, max(0, round(float(v)) - 1))
    if key in TRUST_PARTS:
        return (f"AI systems include many different parts. How much do you trust this part of them: {TRUST_PARTS[key]}?",
                "score", EXTENT5, lambda v: C7[min(7, max(1, round(float(v))))])
    if key in EMOTIONS:
        return (f"How much {key} do you feel towards robots and AIs?", "score", EXTENT5,
                lambda v: C7[min(7, max(1, round(float(v))))])
    if key in LLM_CAPS and t and "large language models" in t:
        cap = re.search(r"\[(.+?)\]", t).group(1).strip()
        return (f"To what extent did the large language models that existed in 2023, like ChatGPT, have the capacity "
                f"for {cap}?", "score", CAPACITY5, lambda v: _pct5(float(v), 100))
    if key in ("MP1", "MP2", "MP3", "MP4") and t and "robots/AIs" in t:
        cap = t.split(" - ")[-1].strip()
        return (f"To what extent did the robots and AIs that existed in {year} have the capacity for {cap}?", "score",
                CAPACITY5, lambda v: _pct5(float(v), 100))
    if key.startswith("Anth") and t:
        s = _clean(t).rstrip("?")
        return f"{s}?", "score", CAPACITY5, lambda v: _pct5(float(v), 10)
    if key == "F4":
        return ("How likely is it that robots or AIs will be sentient within the next 100 years (asked in "
                f"{year})?"), "score", LIKELY5, lambda v: _pct5(float(v), 100)
    if key in ("upload1", "upload2") and t:
        s = _clean(t)
        if key == "upload1":
            s = s.replace("Where would you place yourself on this scale?", "Where do you stand on mind uploading?")
        else:
            s = "Do you support humans using advanced technology in the future to upload their minds into computers?"
        return s, "score", SUPPORT5, lambda v: C7[min(7, max(1, round(float(v))))]
    if key in CHOICE3 and t:
        s = _clean(t)
        return s, "choice", YNS, lambda v: {"yes": "yes", "no": "no", "not sure": "not_sure"}.get(str(v).strip().lower())
    if key == "AID5":
        return ("What do you think about the pace of AI development?", "choice", PACE,
                lambda v: {"it's too fast.": "too_fast", "it's too slow.": "too_slow", "it's fine.": "fine",
                           "not sure": "not_sure"}.get(str(v).strip().lower().replace("’", "'")))
    return None


def _kind(key: str) -> str:
    if key in FORECAST or key == "F4":
        return "forecast" if key in ("F4", "F11", "RS2") else "evaluative"
    if VALUES.match(key):
        return "values"
    if key in EMOTIONS or key == "SF1":
        return "taste"
    return "evaluative"


def normalize(raw_dir: Path) -> Iterator[Question]:
    cb_main = _codebook(raw_dir / "Codebook_AIMS.xlsx")
    cb_sup = _codebook(raw_dir / "Codebook_AIMS_Supplement_2023.xlsx")
    waves = defaultdict(list)
    for r in _sheet(raw_dir / "AIMS_wave1-3.xlsx"):
        waves[(str(r["year"]), "main")].append(r)
    waves[("2023", "supplement")] = _sheet(raw_dir / "AIMS_Supplement_2023.xlsx")

    questions: dict[str, dict] = {}  # text -> record, so identical wordings across waves share a question
    for (year, part), rows in sorted(waves.items()):
        cb = cb_main if part == "main" else cb_sup
        for key in rows[0].keys():
            it = _item(key, cb, year)
            if not it:
                continue
            text, prim, opts, conv = it
            tot, n = defaultdict(float), 0
            for r in rows:
                v, w = r.get(key), r.get("weight")
                if v is None or v == "" or w is None:
                    continue
                try:
                    k = conv(v)
                except (ValueError, KeyError, TypeError):
                    k = None
                if k is None:
                    continue
                tot[str(k)] += float(w)
                n += 1
            if n < 100:
                continue
            s = sum(tot.values())
            label = f"AIMS {year}" + (" supplement" if part == "supplement" else "")
            hd = HumanDist(population=f"US adults, census-weighted ({label})",
                           distribution={k: round(v / s, 4) for k, v in sorted(tot.items())}, n=n,
                           source="Sentience Institute AIMS survey, Mendeley Data x5689yhv2n v3", wave=year)
            rec = questions.setdefault(text, {"key": key, "prim": prim, "opts": opts, "human": [], "vars": []})
            rec["human"].append(hd)
            rec["vars"].append(f"{label}:{key}")

    for text, rec in questions.items():
        key = rec["key"]
        meta = {"variables": rec["vars"]}
        if POLITICAL.search(text):
            meta["flags"] = ["political"]
        if rec["prim"] == "score" and rec["opts"] is AGREE7:
            meta["scale_raw"] = "1 strongly disagree .. 4 no opinion .. 7 strongly agree"
        elif rec["opts"] in (EXTENT5, SUPPORT5):
            meta["level_map"] = "1-7 scale (sliders rounded) collapsed: 1->0, 2-3->1, 4->2, 5-6->3, 7->4"
        elif rec["opts"] in (CAPACITY5, LIKELY5):
            meta["level_map"] = "0-100 (or 0-10) slider binned at 10 / 35 / 64 / 89 percent"
        yield Question(
            text=text,
            primitive=rec["prim"],
            hemisphere="self",
            kind=_kind(key),
            origin="dataset",
            source=NAME,
            options=rec["opts"],
            node_hint=NODE,
            source_item_id=rec["vars"][0],
            license=LICENSE,
            human=rec["human"],
            meta=meta,
        )
