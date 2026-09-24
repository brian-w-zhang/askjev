"""Open Psychometrics raw data (https://openpsychometrics.org/_rawdata/): item texts from each zip's
codebook plus per-item response distributions from its data.csv, for the instruments other than the
IPIP Big-Five markers (sources/ipip). One Question per distinct item statement; an item that appears in
several instruments gets one HumanDist per instrument."""

# no `from __future__ import annotations`: the CLI loads adapters without registering them in sys.modules,
# which dataclasses need to resolve string annotations.

import html
import io
import re
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator
from urllib.parse import quote

import httpx
import numpy as np
import polars as pl

from askjev.model import HumanDist, Question

NAME = "openpsych"
LICENSE = "Open Psychometrics raw data (no license stated); item texts from the instruments' codebooks"
BASE = "https://openpsychometrics.org/_rawdata/"
KEY_ROWS = 50_000  # first rows (all items of the scale valid) used to estimate data-driven keys

# zip name -> folder it extracts to
ZIPS = {
    "16PF.zip": "16PF",
    "HEXACO.zip": "HEXACO",
    "AMBI_data_Dec2019.zip": "AMBI_data_Nov2019",
    "AS+SC+AD+DO.zip": "AS+SC+AD+DO",
    "CFCS.zip": "CFCS",
    "DASS_data_21.02.19.zip": "DASS_data_21.02.19",
    "ECR-data-1March2018.zip": "ECR-data-1March2018",
    "EQSQ.zip": "EQSQ",
    "FBPS-ValidationData.zip": "FBPS-ValidationData",
    "FTI-data.zip": "FTI-data",
    "GCBS.zip": "data",
    "HSNS+DD.zip": "HSNS+DD",
    "HSQ.zip": "HSQ",
    "KIMS.zip": "KIMS",
    "MACH_data.zip": "MACH_data",
    "MIES_Dev_Data.zip": "MIES_Dev_Data",
    "NIS_data.zip": "NIS_data",
    "NPAS-data-16December2018.zip": "NPAS-data-16December2018",
    "NPI.zip": "NPI",
    "NR-6-data-OSPP2024.zip": "NR-6-data-OSPP2024",
    "OHBDS-data.zip": "HBDS-data",
    "OSRI44_dev_data.zip": "OSRI44_dev_data",
    "PWE_data.zip": "PWE_data",
    "RIASEC_data12Dec2018.zip": "RIASEC_data12Dec2018",
    "duckworth-grit-scale-data.zip": "duckworth-grit-scale-data",
    "RSE.zip": "RSE",
    "SD3.zip": "SD3",
    "Wagner.zip": "Wagner",
}

# ---------- response scales ----------

DESCRIBE5 = [
    "This does not describe me at all",
    "This describes me a little",
    "This describes me moderately well",
    "This describes me well",
    "This describes me very well",
]
DESCRIBE4 = [
    "This does not describe me at all",
    "This describes me a little",
    "This describes me well",
    "This describes me very well",
]
AGREE5 = [
    "I strongly disagree with this statement",
    "I somewhat disagree with this statement",
    "I neither agree nor disagree with this statement",
    "I somewhat agree with this statement",
    "I strongly agree with this statement",
]
AGREE4 = [
    "I strongly disagree with this statement",
    "I disagree with this statement",
    "I agree with this statement",
    "I strongly agree with this statement",
]
FREQ5 = [
    "This is never or very rarely true of me",
    "This is rarely true of me",
    "This is sometimes true of me",
    "This is often true of me",
    "This is very often or always true of me",
]
DASS4 = [
    "This did not apply to me at all in the past week",
    "This applied to me to some degree, or some of the time, in the past week",
    "This applied to me to a considerable degree, or a good part of the time, in the past week",
    "This applied to me very much, or most of the time, in the past week",
]
ENJOY5 = [
    "I would dislike doing this",
    "I would somewhat dislike doing this",
    "I would feel neutral about doing this",
    "I would somewhat enjoy doing this",
    "I would enjoy doing this",
]

ID5 = {1: 0, 2: 1, 3: 2, 4: 3, 5: 4}
ID4 = {1: 0, 2: 1, 3: 2, 4: 3}
C7 = {1: 0, 2: 1, 3: 1, 4: 2, 5: 3, 6: 3, 7: 4}
REV5 = {5: 0, 4: 1, 3: 2, 2: 3, 1: 4}
C7_NOTE = "7-point collapsed to 5 levels: 1->0, 2-3->1, 4->2, 5-6->3, 7->4"

# scale type -> (raw->level map, levels for self-descriptions, levels for other statements, question/human templates)
SCALES = {
    "agree5": (ID5, DESCRIBE5, AGREE5),
    "agree7": (C7, DESCRIBE5, AGREE5),
    "agree4": (ID4, DESCRIBE4, AGREE4),
    "char5": (ID5, DESCRIBE5, AGREE5),
    "freq5": (ID5, FREQ5, FREQ5),
    "dass4": (ID4, DASS4, DASS4),
    "enjoy5": (ID5, ENJOY5, ENJOY5),
    "likeme5": (REV5, DESCRIBE5, AGREE5),  # 1=Very much like me ... 5=Not like me at all
}
FRAMES = {
    "describe": ('How well does this statement describe you: "{s}"',
                 'How well would most people say this statement describes them: "{s}"'),
    "agree": ('How much do you agree: "{s}"', 'How much would most people agree: "{s}"'),
    "freq": ('How often is this statement true of you: "{s}"',
             'How often would most people say this statement is true of them: "{s}"'),
    "dass": ('How much did this statement apply to you over the past week: "{s}"',
             'How much would most people say this statement applied to them over the past week: "{s}"'),
    "enjoy": ('How much would you enjoy this work activity: "{s}"', 'How much would most people enjoy this work activity: "{s}"'),
}

# ---------- flags ----------

POLITICAL = re.compile(r"(?i)\b(liberal political|vote for|one true religion|devoted to religion|God\b|divine power|national anthem|put painlessly to death)")
SENSITIVE = re.compile(r"(?i)(worthless|hopelessness|life (has no|wasn't|was) mean|life wasn't worthwhile|no good at all|"
                       r"attacked someone physically)")
DROP = re.compile(r"(?i)\bsex")  # sexual content is out of scope for the Self hemisphere
FIRST_PERSON = re.compile(r"\bI\b|\bI'(m|ve|d|ll)\b|(?i:\b(me|my|myself|mine)\b)")

# IPIP stems with no verb when "I" is prepended (same fixes as sources/ipip, so identical items get identical ids)
STEM_FIX = {"willing to": "am willing to", "never at a loss": "am never at a loss", "interested in": "am interested in"}
TEXT_FIX = {
    "I when interacting with a group of people, am often bothered by at least one of them.":
        "When interacting with a group of people, I am often bothered by at least one of them.",
    "I don?tend to find social situations confusing.": "I don't tend to find social situations confusing.",
    "Other people often say that I am insensitive, though I don?always see why.":
        "Other people often say that I am insensitive, though I don't always see why.",
    "I am good an entertaining children.": "I am good at entertaining children.",
    "I have periods of such great restlessness that I cannot sit long I a chair.":
        "I have periods of such great restlessness that I cannot sit long in a chair.",
    "I try to be with someone else when Im feeling badly.": "I try to be with someone else when I'm feeling badly.",
    "I have thought about dying my hair.": "I have thought about dyeing my hair.",
    "I don't bother to the read instructions before I start putting something together.":
        "I don't bother to read the instructions before I start putting something together.",
    "I worry that romantic partners wont care about me as much as I care about them.":
        "I worry that romantic partners won't care about me as much as I care about them.",
    "I do not need others praise.": "I do not need others' praise.",
    "I like to play RPGs. (Ex. D&D).": "I like to play RPGs (for example D&D).",
}


def clean(s: str) -> str:
    s = html.unescape(html.unescape(s))
    for a, b in (("â€™", "'"), ("’", "'"), ("‘", "'"), ("“", "'"), ("”", "'"), ('"', "'"), ("—", "-"), ("–", "-")):
        s = s.replace(a, b)
    s = re.sub(r"\s+", " ", s).strip()
    s = re.sub(r"\bi'm\b", "I'm", s)
    s = re.sub(r"\s+\(R\)$", "", s)
    if s and s[-1] not in ".!?":
        s += "."
    return TEXT_FIX.get(s, s)


def ipip_sentence(stem: str) -> str:
    low = stem[:1].lower() + stem[1:]
    for k, v in STEM_FIX.items():
        if low.startswith(k):
            low = v + low[len(k):]
    return clean("I " + low)


def norm(s: str) -> str:
    return re.sub(r"[^a-z ]", "", s.lower().replace("'", "")).strip()


# ---------- instruments ----------


@dataclass
class Item:
    code: str  # item code in the instrument (column stem)
    text: str
    scale: str | None = None  # subscale / facet name (keys are relative to its pole)
    node: str = "self.personality"
    keyed: str | None = None  # "+" / "-" relative to scale pole; None = estimate from data (if scale set)
    kind: str = "personality"
    flags: list[str] = field(default_factory=list)


@dataclass
class Instrument:
    code: str  # short id, e.g. "HEXACO"
    label: str  # population label part
    folder: str
    file: str
    scale: str  # key of SCALES
    scale_raw: str
    items: list[Item]
    col: str = "{c}"  # column name format
    frame: str | None = None  # force frame (freq/dass/enjoy); None = describe/agree by wording
    keys_from: str = "codebook"  # description of where keys come from, for meta
    citation: str = ""
    anchors: dict[str, tuple[str, str]] = field(default_factory=dict)  # scale -> (item whose sign is fixed, sign)


def read_text(p: Path) -> str:
    b = p.read_bytes()
    try:
        return b.decode("utf-8")
    except UnicodeDecodeError:
        return b.decode("cp1252", errors="replace")


def tab_items(text: str, prefix: str) -> dict[str, str]:
    """Lines like 'Q1\\tText' or 'Q1. Text' or 'E1 Text' whose code starts with one of the prefixes."""
    out = {}
    for ln in text.splitlines():
        m = re.match(rf"^\s*((?:{prefix})\d+)[\s.:]+(\S.*?)\s*$", ln)
        if m and m.group(1) not in out:
            out[m.group(1)] = m.group(2)
    return out


def json_items(text: str) -> dict[str, str]:
    out = {}
    for m in re.finditer(r"""['"](Q\d+)['"]\s*:\s*(['"])(.*?)\2\s*,?\s*$""", text, re.M):
        out[m.group(1)] = m.group(3)
    return out


def html_items(text: str) -> dict[str, str]:
    t = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", text))
    return {m.group(1): m.group(2) for m in re.finditer(r'\b([A-Z]\d+) INTEGER "([^"]*)"', t)}


def groups(spec: dict[str, list[int]], prefix: str = "Q") -> dict[str, str]:
    return {f"{prefix}{i}": name for name, ids in spec.items() for i in ids}


PF16 = {  # IPIP analog of Cattell's 16PF: letter -> (factor, Big Five node)
    "A": ("Warmth", "agreeableness"), "B": ("Intellect", "openness"), "C": ("Emotional Stability", "neuroticism"),
    "D": ("Assertiveness", "extraversion"), "E": ("Gregariousness", "extraversion"), "F": ("Dutifulness", "conscientiousness"),
    "G": ("Friendliness", "extraversion"), "H": ("Sensitivity", "openness"), "I": ("Distrust", "agreeableness"),
    "J": ("Imagination", "openness"), "K": ("Reserve", "extraversion"), "L": ("Anxiety", "neuroticism"),
    "M": ("Complexity", "openness"), "N": ("Introversion", "extraversion"), "O": ("Orderliness", "conscientiousness"),
    "P": ("Emotionality", "neuroticism"),
}
HEX_DOMAIN = {"H": ("Honesty-Humility", None), "E": ("Emotionality", "neuroticism"), "X": ("Extraversion", "extraversion"),
              "A": ("Agreeableness", "agreeableness"), "C": ("Conscientiousness", "conscientiousness"),
              "O": ("Openness to Experience", "openness")}
TIPI = {  # item -> (Big Five trait, keyed relative to that trait)
    "TIPI1": ("extraversion", "+"), "TIPI2": ("agreeableness", "-"), "TIPI3": ("conscientiousness", "+"),
    "TIPI4": ("neuroticism", "+"), "TIPI5": ("openness", "+"), "TIPI6": ("extraversion", "-"),
    "TIPI7": ("agreeableness", "+"), "TIPI8": ("conscientiousness", "-"), "TIPI9": ("neuroticism", "-"),
    "TIPI10": ("openness", "-"),
}
BF = "self.personality.big_five."
P = "self.personality."

# Generic Conspiracist Beliefs Scale items (Brotherton, French & Pickering 2013, Frontiers in Psychology 4:279,
# Table A1). The Open Psychometrics codebook only says question numbers match that table.
GCBS = [
    "The government is involved in the murder of innocent citizens and/or well-known public figures, and keeps this a secret",
    "The power held by heads of state is second to that of small unknown groups who really control world politics",
    "Secret organizations communicate with extraterrestrials, but keep this fact from the public",
    "The spread of certain viruses and/or diseases is the result of the deliberate, concealed efforts of some organization",
    "Groups of scientists manipulate, fabricate, or suppress evidence in order to deceive the public",
    "The government permits or perpetrates acts of terrorism on its own soil, disguising its involvement",
    "A small, secret group of people is responsible for making all major world decisions, such as going to war",
    "Evidence of alien contact is being concealed from the public",
    "Technology with mind-control capacities is used on people without their knowledge",
    "New and advanced technology which would harm current industry is being suppressed",
    "The government uses people as patsies to hide its involvement in criminal activity",
    "Certain significant events have been the result of the activity of a small group who secretly manipulate world events",
    "Some UFO sightings and rumors are planned or staged in order to distract the public from real alien contact",
    "Experiments involving new drugs or technologies are routinely carried out on the public without their knowledge or consent",
    "A lot of important information is deliberately concealed from the public out of self-interest",
]
# Grit-12 (Duckworth, Peterson, Matthews & Kelly 2007). The codebook abbreviates each item to its first words
# ("GS2 New ideas..."), which match these full texts in order. Items 2,3,5,7,8,11 (consistency of interests) are reversed.
GRIT = [
    "I have overcome setbacks to conquer an important challenge.",
    "New ideas and projects sometimes distract me from previous ones.",
    "My interests change from year to year.",
    "Setbacks don't discourage me.",
    "I have been obsessed with a certain idea or project for a short time but later lost interest.",
    "I am a hard worker.",
    "I often set a goal but later choose to pursue a different one.",
    "I have difficulty maintaining my focus on projects that take more than a few months to complete.",
    "I finish whatever I begin.",
    "I have achieved a goal that took years of work.",
    "I become interested in new pursuits every few months.",
    "I am diligent.",
]
GCBS_POLITICAL = {1, 2, 6, 7, 11, 12}  # items about governments and control of world politics


def instruments(raw: Path) -> list[Instrument]:
    out: list[Instrument] = []

    def cb(folder: str, name: str = "codebook.txt") -> str:
        return read_text(raw / folder / name)

    # 16PF (IPIP analog). P10 has no text in the codebook.
    t = html_items(cb("16PF", "codebook.html"))
    items = []
    for c, s in t.items():
        fac, trait = PF16[c[0]]
        items.append(Item(c, clean(s), scale=f"{c[0]}: {fac}", node=BF + trait))
    out.append(Instrument("16PF", "IPIP 16PF", "16PF", "data.csv", "agree5",
                          "1=Strongly disagree, 2=Disagree, 3=Neither, 4=Agree, 5=Strongly agree", items,
                          keys_from="data", citation="IPIP scales for Cattell's 16 personality factors"))

    # HEXACO (IPIP HEXACO-PI analog, 240 items, 7-point)
    items = []
    for ln in cb("HEXACO").splitlines():
        m = re.match(r"^([HEXACO])([A-Z][a-z]{2}[A-Za-z])(\d+)\s+(.+)$", ln.strip())
        if m:
            dom, fac = m.group(1), m.group(2)
            trait = HEX_DOMAIN[dom][1]
            items.append(Item(f"{dom}{fac}{m.group(3)}", clean(m.group(4)), scale=f"{HEX_DOMAIN[dom][0]}: {fac}",
                              node=BF + trait if trait else "self.personality.big_five"))
    anchors = {it.scale: (re.sub(r"\d+$", "1", it.code), "+") for it in items}
    out.append(Instrument("HEXACO", "IPIP HEXACO", "HEXACO", "data.csv", "agree7",
                          "1=Strongly disagree ... 4=Neutral ... 7=Strongly agree (codebook mislabels 5 as 'slightly disagree')",
                          items, keys_from="data", anchors=anchors))

    # AMBI (181 IPIP items spanning many inventories; no subscale keys in the codebook)
    t = json_items(cb("AMBI_data_Nov2019"))
    items = [Item(c, clean(s)) for c, s in t.items()]
    out.append(Instrument("AMBI", "AMBI", "AMBI_data_Nov2019", "data.csv", "agree7",
                          "1=Strongly disagree, 2=Disagree, 3=Slightly disagree, 4=Neutral, 5=Slightly agree, 6=Agree, 7=Strongly agree",
                          items, col="{c}A", keys_from="none"))

    # Assertiveness / Social confidence / Adventurousness / Dominance (IPIP, stems without "I")
    t = tab_items(cb("AS+SC+AD+DO"), "AS|SC|AD|DO")
    sc = {"AS": ("Assertiveness", BF + "extraversion"), "SC": ("Social Confidence", BF + "extraversion"),
          "AD": ("Adventurousness", BF + "openness"), "DO": ("Dominance", BF + "agreeableness")}
    items = [Item(c, ipip_sentence(s), scale=sc[c[:2]][0], node=sc[c[:2]][1]) for c, s in t.items()]
    out.append(Instrument("AS+SC+AD+DO", "IPIP AS+SC+AD+DO", "AS+SC+AD+DO", "data.csv", "agree5",
                          "1=Strongly disagree, 2=Disagree, 3=Neither, 4=Agree, 5=Strongly agree", items, keys_from="data"))

    # Consideration of Future Consequences
    t = tab_items(cb("CFCS"), "Q")
    items = [Item(c, clean(s), scale="Consideration of future consequences", node=P + "risk_decision_style") for c, s in t.items()]
    out.append(Instrument("CFCS", "CFCS", "CFCS", "data.csv", "char5",
                          "1=Extremely uncharacteristic, 2=Somewhat uncharacteristic, 3=Uncertain, 4=Somewhat characteristic, 5=Extremely characteristic",
                          items, keys_from="data"))

    # DASS-42 (past-week frequency) + TIPI from its research survey is taken from NIS instead
    dass = {"Depression": [3, 5, 10, 13, 16, 17, 21, 24, 26, 31, 34, 37, 38, 42],
            "Anxiety": [2, 4, 7, 9, 15, 19, 20, 23, 25, 28, 30, 36, 40, 41],
            "Stress": [1, 6, 8, 11, 12, 14, 18, 22, 27, 29, 32, 33, 35, 39]}
    g = groups(dass)
    t = tab_items(cb("DASS_data_21.02.19"), "Q")
    items = [Item(c, clean(s), scale=g[c], node=P + "emotions_stress", keyed="+", flags=["sensitive"]) for c, s in t.items()]
    out.append(Instrument("DASS", "DASS-42", "DASS_data_21.02.19", "data.csv", "dass4",
                          "1=Did not apply to me at all, 2=Applied to some degree, 3=Applied to a considerable degree, 4=Applied very much (past week)",
                          items, col="{c}A", frame="dass"))

    # ECR attachment (odd items avoidance, even items anxiety)
    t = html_items(cb("ECR-data-1March2018", "codebook.html"))
    items = [Item(c, clean(s), scale="Attachment avoidance" if int(c[1:]) % 2 else "Attachment anxiety",
                  node="self.love.romance_partnership") for c, s in t.items()]
    out.append(Instrument("ECR", "ECR", "ECR-data-1March2018", "data.csv", "agree5",
                          "1=Strongly disagree, 2=Disagree, 3=Neither, 4=Agree, 5=Strongly agree", items, keys_from="data"))

    # Empathizing / Systemizing Quotients (4-point, no neutral)
    t = tab_items(cb("EQSQ"), "E|S")
    items = [Item(c, clean(s), scale="Empathizing" if c[0] == "E" else "Systemizing",
                  node=P + "emotions_stress" if c[0] == "E" else BF + "openness") for c, s in t.items()]
    out.append(Instrument("EQSQ", "EQ+SQ", "EQSQ", "data.csv", "agree4",
                          "1=Strongly disagree, 2=Disagree, 3=Agree, 4=Strongly agree", items, keys_from="data"))

    # Fisher Temperament Inventory (4-point)
    fti = {"Curious/Energetic": (range(1, 15), BF + "openness"), "Cautious/Social norm compliant": (range(15, 29), BF + "conscientiousness"),
           "Analytical/Tough-minded": (range(29, 43), P + "type.tf"), "Prosocial/Empathetic": (range(43, 57), P + "type.tf")}
    t = json_items(cb("FTI-data"))
    items = []
    for c, s in t.items():
        name = next(k for k, (r, _) in fti.items() if int(c[1:]) in r)
        items.append(Item(c, clean(s), scale=name, node=fti[name][1]))
    out.append(Instrument("FTI", "Fisher Temperament Inventory", "FTI-data", "data.csv", "agree4",
                          "1=Strongly disagree, 2=Disagree, 3=Agree, 4=Strongly agree", items, col="{c}A", keys_from="data"))

    # GCBS (texts from the source paper; the online version used 1=Disagree, 3=Neutral, 5=Agree)
    items = [Item(f"Q{i}", clean(s), scale="Generic conspiracist beliefs", node="self.mind.epistemics", keyed="+", kind="values",
                  flags=["political"] if i in GCBS_POLITICAL else []) for i, s in enumerate(GCBS, 1)]
    out.append(Instrument("GCBS", "GCBS", "data", "data.csv", "agree5", "1=Disagree, 3=Neutral, 5=Agree", items,
                          citation="Brotherton, French & Pickering (2013) Table A1"))

    # Hypersensitive Narcissism + Dirty Dozen
    t = tab_items(cb("HSNS+DD"), "HSNS|DDM|DDP|DDN")
    dd = {"HSNS": "Hypersensitive narcissism", "DDM": "Machiavellianism", "DDP": "Psychopathy", "DDN": "Narcissism"}
    items = [Item(c, clean(s), scale=dd[re.match(r"[A-Z]+", c).group()], node=P + "dark_side", keyed="+") for c, s in t.items()]
    out.append(Instrument("HSNS+DD", "HSNS + Dirty Dozen", "HSNS+DD", "data.csv", "agree5", "1=Disagree, 3=Neutral, 5=Agree", items))

    # Humor Styles Questionnaire (published keys; reverse items 1,7,9,15,16,17,22,23,25,29,31)
    hsq = {"Affiliative": range(1, 33, 4), "Self-enhancing": range(2, 33, 4), "Aggressive": range(3, 33, 4),
           "Self-defeating": range(4, 33, 4)}
    rev = {1, 7, 9, 15, 16, 17, 22, 23, 25, 29, 31}
    t = tab_items(cb("HSQ"), "Q")
    items = [Item(c, clean(s), scale=next(k for k, r in hsq.items() if int(c[1:]) in r), node=P + "humor_style",
                  keyed="-" if int(c[1:]) in rev else "+") for c, s in t.items()]
    out.append(Instrument("HSQ", "Humor Styles Questionnaire", "HSQ", "data.csv", "freq5",
                          "1=Never or very rarely true, 2=Rarely true, 3=Sometimes true, 4=Often true, 5=Very often or always true",
                          items, frame="freq", citation="Martin et al. (2003)"))

    # KIMS mindfulness (facet membership from the published scale; signs from data)
    kims = {"Observing": [1, 5, 9, 13, 17, 21, 25, 29, 30, 33, 37, 39], "Describing": [2, 6, 10, 14, 18, 22, 26, 34],
            "Acting with awareness": [3, 7, 11, 15, 19, 23, 27, 31, 35, 38],
            "Accepting without judgment": [4, 8, 12, 16, 20, 24, 28, 32, 36]}
    g = groups(kims)
    t = tab_items(cb("KIMS"), "Q")
    items = [Item(c, clean(s), scale=g[c], node=P + "emotions_stress") for c, s in t.items()]
    out.append(Instrument("KIMS", "KIMS", "KIMS", "data.csv", "freq5",
                          "1=Never or very rarely true, 2=Rarely true, 3=Sometimes true, 4=Often true, 5=Very often or always true",
                          items, frame="freq", keys_from="data", anchors={"Accepting without judgment": ("Q4", "-"), "Acting with awareness": ("Q7", "+")}))

    # MACH-IV (published key: items 3,4,6,7,9,10,11,14,16,17 reversed)
    rev = {3, 4, 6, 7, 9, 10, 11, 14, 16, 17}
    t = json_items(cb("MACH_data"))
    items = [Item(c, clean(s), scale="Machiavellianism", node=P + "dark_side", keyed="-" if int(c[1:]) in rev else "+")
             for c, s in t.items()]
    out.append(Instrument("MACH-IV", "MACH-IV", "MACH_data", "data.csv", "agree5",
                          "1=Disagree, 2=Slightly disagree, 3=Neutral, 4=Slightly agree, 5=Agree", items, col="{c}A"))

    # Multidimensional Introversion-Extraversion Scales (development items)
    t = json_items(cb("MIES_Dev_Data"))
    items = [Item(c, clean(s), scale="Introversion", node=BF + "extraversion") for c, s in t.items()]
    out.append(Instrument("MIES", "MIES development", "MIES_Dev_Data", "data.csv", "agree5",
                          "1=Disagree, 2=Slightly disagree, 3=Neutral, 4=Slightly agree, 5=Agree", items, col="{c}A", keys_from="data"))

    # Nonverbal Immediacy Scale (frequency)
    t = tab_items(cb("NIS_data"), "Q")
    items = [Item(c, clean(s), scale="Nonverbal immediacy", node=BF + "extraversion") for c, s in t.items()]
    out.append(Instrument("NIS", "Nonverbal Immediacy Scale", "NIS_data", "data.csv", "freq5",
                          "1=Never, 2=Rarely, 3=Occasionally, 4=Often, 5=Very often", items, frame="freq", keys_from="data"))

    # TIPI (from the NIS research survey, the largest sample carrying it)
    t = tab_items(cb("NIS_data"), "TIPI")
    items = [Item(c, clean("I see myself as " + s[:1].lower() + s[1:]), scale=f"Big Five: {TIPI[c][0]}",
                  node=BF + TIPI[c][0], keyed=TIPI[c][1]) for c, s in t.items()]
    out.append(Instrument("TIPI", "TIPI, NIS survey", "NIS_data", "data.csv", "agree7",
                          "1=Disagree strongly, 2=Disagree moderately, 3=Disagree a little, 4=Neither, 5=Agree a little, 6=Agree moderately, 7=Agree strongly",
                          items, citation="Gosling, Rentfrow & Swann (2003)"))

    # Nerdy Personality Attributes Scale (all items positively keyed)
    t = tab_items(cb("NPAS-data-16December2018"), "Q")
    items = [Item(c, clean(s), scale="Nerdiness", node=P + "self_concept", keyed="+") for c, s in t.items()]
    out.append(Instrument("NPAS", "NPAS", "NPAS-data-16December2018", "data.csv", "agree5", "1=Disagree, 3=Neutral, 5=Agree", items))

    # Nature Relatedness (NR-6)
    t = tab_items(cb("NR-6-data-OSPP2024"), "Q")
    items = [Item(c, clean(s), scale="Nature relatedness", node="self.values.animals_environment", keyed="+", kind="values")
             for c, s in t.items()]
    out.append(Instrument("NR-6", "NR-6", "NR-6-data-OSPP2024", "NR6-data-cleaned-22Feb2024.csv", "agree5",
                          "1=Disagree ... 5=Agree", items, col="{c}A"))

    # Open Hemispheric Brain Dominance Scale
    t = tab_items(cb("HBDS-data"), "Q")
    items = [Item(c, clean(s), scale="Left-brain (logical) vs right-brain", node="self.personality") for c, s in t.items()]
    out.append(Instrument("OHBDS", "OHBDS", "HBDS-data", "data.csv", "agree5", "1=Disagree, 3=Neutral, 5=Agree", items,
                          keys_from="data", anchors={items[0].scale: ("Q2", "+")}))

    # Open Sex Role Inventory development items (Q43 repeats Q27)
    t = tab_items(cb("OSRI44_dev_data"), "Q")
    items = [Item(c, clean(s), scale="Masculine-typed vs feminine-typed", node=P + "self_concept") for c, s in t.items()]
    out.append(Instrument("OSRI", "OSRI development", "OSRI44_dev_data", "data.csv", "agree5", "1=Disagree, 3=Neutral, 5=Agree",
                          items, keys_from="data"))

    # Protestant Work Ethic (published key: 9, 13, 15 reversed)
    t = tab_items(cb("PWE_data"), "Q")
    items = [Item(c, clean(s), scale="Protestant work ethic", node=P + "motivation_ambition", kind="values",
                  keyed="-" if int(c[1:]) in (9, 13, 15) else "+") for c, s in t.items()]
    out.append(Instrument("PWE", "Protestant Work Ethic Scale", "PWE_data", "data.csv", "agree5",
                          "1=Disagree, 2=Slightly disagree, 3=Neutral, 4=Slightly agree, 5=Agree", items, col="{c}A"))

    # RIASEC activities
    riasec = {"R": "Realistic", "I": "Investigative", "A": "Artistic", "S": "Social", "E": "Enterprising", "C": "Conventional"}
    t = tab_items(cb("RIASEC_data12Dec2018"), "R|I|A|S|E|C")
    items = [Item(c, clean(s).rstrip("."), scale=riasec[c[0]], node=P + "interests", keyed="+") for c, s in t.items()]
    out.append(Instrument("RIASEC", "RIASEC", "RIASEC_data12Dec2018", "data.csv", "enjoy5", "1=Dislike, 3=Neutral, 5=Enjoy",
                          items, frame="enjoy"))

    # Rosenberg Self-Esteem (published key: 3,5,8,9,10 reversed)
    t = tab_items(cb("RSE"), "Q")
    items = [Item(c, clean(s), scale="Self-esteem", node=P + "self_concept", keyed="-" if int(c[1:]) in (3, 5, 8, 9, 10) else "+")
             for c, s in t.items()]
    out.append(Instrument("RSE", "Rosenberg Self-Esteem Scale", "RSE", "data.csv", "agree4",
                          "1=Strongly disagree, 2=Disagree, 3=Agree, 4=Strongly agree", items))

    # Short Dark Triad (published key: N2, N6, N8, P2, P7 reversed)
    t = tab_items(cb("SD3"), "M|N|P")
    sd3 = {"M": "Machiavellianism", "N": "Narcissism", "P": "Psychopathy"}
    items = [Item(c, clean(s), scale=sd3[c[0]], node=P + "dark_side", keyed="-" if c in ("N2", "N6", "N8", "P2", "P7") else "+")
             for c, s in t.items()]
    out.append(Instrument("SD3", "Short Dark Triad", "SD3", "data.csv", "agree5", "1=Disagree, 3=Neutral, 5=Agree", items))

    # Grit-12: check the codebook's abbreviations against the full texts before using them
    abbr = tab_items(cb("duckworth-grit-scale-data"), "GS")
    items = []
    for i, full in enumerate(GRIT, 1):
        stem = abbr.get(f"GS{i}", "").rstrip(".").strip()
        if stem and full.startswith(stem):
            items.append(Item(f"GS{i}", clean(full), scale="Grit", node=P + "motivation_ambition",
                              keyed="-" if i in (2, 3, 5, 7, 8, 11) else "+"))
    out.append(Instrument("GRIT", "Grit Scale", "duckworth-grit-scale-data", "data.csv", "likeme5",
                          "1=Very much like me, 2=Mostly like me, 3=Somewhat like me, 4=Not much like me, 5=Not like me at all "
                          "(reversed onto levels: 5->0 ... 1->4)", items, citation="Duckworth et al. (2007) Grit-12"))

    # Firstborn personality research survey (items picked to separate birth orders; no key)
    t = tab_items(cb("FBPS-ValidationData", "FBPS-ValidationData-Codebook.txt").split("HOST SURVEY")[0], "Q")
    items = [Item(c, clean(s)) for c, s in t.items()]
    out.append(Instrument("FBPS", "FBPS research survey", "FBPS-ValidationData", "FBPS-ValidationData.csv", "agree5",
                          "1=Disagree, 3=Neutral, 5=Agree", items, keys_from="none"))
    return out


# ---------- forced-choice instruments ----------

STOP = {"i", "a", "an", "the", "to", "of", "that", "am", "is", "be", "it", "in", "my", "me", "when", "and", "or", "for", "so",
        "would", "will", "can", "do", "just", "much", "very", "not", "no", "are", "if", "because", "as", "on", "with", "at"}


def slug(s: str, other: list[str], maxlen: int = 30) -> str:
    words = re.findall(r"[a-z0-9]+", s.lower().replace("'", ""))
    neg = [w for w in words if w in ("not", "no", "never", "dont", "doesnt", "nothing", "rarely")]
    keep = [w for w in words if w not in STOP] or words
    if neg and neg[0] not in keep:
        keep = [neg[0]] + keep
    k = ""
    for w in keep:
        if len(k) + len(w) + 1 > maxlen:
            break
        k = f"{k}_{w}" if k else w
    return k or "option"


def choice_keys(opts: list[str]) -> list[str]:
    keys = [slug(o, opts) for o in opts]
    if len(set(keys)) < len(keys):
        keys = [slug(o, opts, 60) for o in opts]
    if len(set(keys)) < len(keys):
        keys = [f"{chr(97 + i)}_{k}" for i, k in enumerate(keys)]
    return keys


@dataclass
class ChoiceItem:
    inst: str
    label: str
    code: str
    options: list[str]  # raw value i+1 -> options[i]
    node: str
    keyed: int | None  # raw value of the keyed (high-trait) option
    scale: str | None
    folder: str
    file: str
    col: str
    text: str
    human_text: str
    scale_raw: str


def choice_items(raw: Path) -> list[ChoiceItem]:
    out = []
    # NPI-40: key from the codebook's scoring code
    t = read_text(raw / "NPI" / "codebook.txt")
    key = {m.group(1): int(m.group(2)) for m in re.finditer(r"\['(Q\d+)'\] == (\d)", t)}
    for m in re.finditer(r"^(Q\d+)\. 1=\s*(.+?) 2=\s*(.+?)\s*$", t, re.M):
        c = m.group(1)
        out.append(ChoiceItem("NPI", "NPI-40", c, [clean(m.group(2)), clean(m.group(3))], P + "dark_side", key.get(c),
                              "Narcissism", "NPI", "data.csv", "{c}", "Which statement describes you better?",
                              "Which statement describes most people better?", "forced choice: 1=first statement, 2=second"))
    # FTI forced-choice items
    t = read_text(raw / "FTI-data" / "codebook.txt")
    fnode = {"T1": BF + "openness", "T2": BF + "extraversion", "T3": P + "self_concept", "T4": P + "risk_decision_style",
             "T5": P + "type.sn", "T6": P + "type.tf"}
    for m in re.finditer(r"^(T\d)A\s+1=(.+?) 2=(.+?)\s*$", t, re.M):
        c = m.group(1)
        out.append(ChoiceItem("FTI", "Fisher Temperament Inventory", c, [clean(m.group(2)), clean(m.group(3))], fnode[c], None,
                              None, "FTI-data", "data.csv", "{c}A", "Which statement describes you better?",
                              "Which statement describes most people better?", "forced choice: 1=first statement, 2=second"))
    # Wagner Preference Inventory: pick one of four activities (the codebook labels the 12th item Q11 again)
    t = read_text(raw / "Wagner" / "codebook.txt")
    rows = re.findall(r"^Q\d+\s+1=(.+?), 2=(.+?), 3=(.+?), 4=(.+?)\s*$", t, re.M)
    for i, opts in enumerate(rows, 1):
        out.append(ChoiceItem("WPI-Wagner", "Wagner Preference Inventory", f"Q{i}", [clean(o).rstrip(".") for o in opts],
                              P + "interests", None, None, "Wagner", "data.csv", "{c}",
                              "Which of these activities would you most like to do?",
                              "Which of these activities would most people most like to do?",
                              "1-4 = the four activities in codebook order"))
    return out


# ---------- data ----------

_cache: dict[Path, pl.DataFrame] = {}


def load(path: Path, cols: list[str]) -> pl.DataFrame:
    head = path.open("r", encoding="utf-8", errors="replace").readline()
    sep = "\t" if "\t" in head else ","
    df = pl.read_csv(path, separator=sep, infer_schema_length=0, quote_char='"', columns=cols, encoding="utf8-lossy",
                     truncate_ragged_lines=True)
    return df.with_columns([pl.col(c).cast(pl.Int64, strict=False) for c in cols])


def dist(series: pl.Series, mapping: dict[int, int], k: int) -> tuple[dict[str, float], int]:
    vc = dict(series.drop_nulls().value_counts().iter_rows())
    counts = [0] * k
    for raw, lvl in mapping.items():
        counts[lvl] += vc.get(raw, 0)
    n = sum(counts)
    return ({str(i): round(c / n, 6) for i, c in enumerate(counts)} if n else {}), n


def data_keys(df: pl.DataFrame, cols: list[str], valid: list[int]) -> list[str]:
    """Signs of each item on its scale: iterate item vs rest-score correlations, oriented so the first item is '+'."""
    sub = df.select(cols).filter(pl.all_horizontal([pl.col(c).is_in(valid) for c in cols])).head(KEY_ROWS)
    x = sub.to_numpy().astype(float)
    if len(cols) < 3 or x.shape[0] < 50:
        return ["+"] * len(cols)
    x = (x - x.mean(0)) / (x.std(0) + 1e-9)
    s = np.sign(np.array([np.corrcoef(x[:, i], x[:, 0])[0, 1] for i in range(len(cols))]))
    s[0] = 1
    for _ in range(5):
        tot = x @ s
        new = np.sign([np.corrcoef(x[:, i], tot - s[i] * x[:, i])[0, 1] for i in range(len(cols))])
        new[new == 0] = 1
        if new[0] < 0:
            new = -new
        if (new == s).all():
            break
        s = new
    return ["+" if v > 0 else "-" for v in s]


# ---------- fetch / normalize ----------


def fetch(raw_dir: Path) -> None:
    headers = {"User-Agent": "Mozilla/5.0 (askjev research)"}
    for z, folder in ZIPS.items():
        if (raw_dir / folder).exists():
            continue
        r = httpx.get(BASE + quote(z), headers=headers, follow_redirects=True, timeout=600)
        r.raise_for_status()
        (raw_dir / z).write_bytes(r.content)
        zf = zipfile.ZipFile(io.BytesIO(r.content))
        zf.extractall(raw_dir, members=[m for m in zf.namelist() if "/images/" not in m and "/items/" not in m])


def ipip_markers(raw: Path) -> set[str]:
    """The 50 IPIP Big-Five Factor Markers (ingested with norms by sources/ipip), listed in the FBPS codebook."""
    t = read_text(raw / "FBPS-ValidationData" / "FBPS-ValidationData-Codebook.txt")
    return {norm(clean(s)) for s in tab_items(t, "EXT|EST|AGR|CSN|OPN").values()}


def normalize(raw_dir: Path) -> Iterator[Question]:
    markers = ipip_markers(raw_dir)
    merged: dict[str, dict] = {}  # norm(text)+frame -> record
    order: list[str] = []

    for inst in instruments(raw_dir):
        mapping, lv_self, lv_other = SCALES[inst.scale]
        k = len(lv_self)
        cols = [inst.col.format(c=it.code) for it in inst.items]
        df = load(raw_dir / inst.folder / inst.file, cols)
        valid = sorted(mapping)
        keys: dict[str, str] = {}
        if inst.keys_from == "data":
            by_scale: dict[str, list[Item]] = {}
            for it in inst.items:
                if it.scale and it.keyed is None:
                    by_scale.setdefault(it.scale, []).append(it)
            for sc, its in by_scale.items():
                code, sign = inst.anchors.get(sc, (its[0].code, "+"))
                its = sorted(its, key=lambda i: i.code != code)  # anchor first
                for it, sg in zip(its, data_keys(df, [inst.col.format(c=i.code) for i in its], valid)):
                    keys[it.code] = sg if sign == "+" else {"+": "-", "-": "+"}[sg]
        for it in inst.items:
            if DROP.search(it.text) or norm(it.text) in markers:
                continue
            frame = inst.frame or ("describe" if FIRST_PERSON.search(it.text) else "agree")
            levels = lv_self if frame in ("describe", "freq", "dass", "enjoy") else lv_other
            d, n = dist(df[inst.col.format(c=it.code)], mapping, k)
            if not n:
                continue
            flags = list(it.flags)
            if POLITICAL.search(it.text) and "political" not in flags:
                flags.append("political")
            if SENSITIVE.search(it.text) and "sensitive" not in flags:
                flags.append("sensitive")
            keyed = it.keyed or keys.get(it.code)
            rid = f"{norm(it.text)}|{frame}"
            hd = HumanDist(population=f"OpenPsychometrics web ({inst.label})", distribution=d, n=n,
                           source=f"openpsychometrics.org/_rawdata {inst.folder} item {it.code}; {inst.scale_raw}"
                           + (f"; {C7_NOTE}" if mapping is C7 else ""))
            if rid in merged:
                rec = merged[rid]
                if hd.population not in {h.population for h in rec["human"]}:
                    rec["human"].append(hd)
                    rec["meta"]["also_in"].append({"instrument": inst.code, "item_code": it.code, "scale": it.scale, "keyed": keyed})
                rec["meta"]["flags"] = sorted(set(rec["meta"].get("flags", [])) | set(flags))
                continue
            q_text, h_text = FRAMES[frame]
            meta = {"instrument": inst.code, "item_code": it.code, "scale": it.scale, "keyed": keyed,
                    "keyed_from": None if keyed is None else ("data" if it.code in keys else "published"),
                    "scale_raw": inst.scale_raw, "level_map": {str(a): b for a, b in mapping.items()}, "also_in": []}
            if inst.citation:
                meta["citation"] = inst.citation
            if flags:
                meta["flags"] = sorted(flags)
            merged[rid] = dict(
                text=q_text.format(s=it.text), human_text=h_text.format(s=it.text), options=levels, kind=it.kind,
                node=it.node, sid=f"{inst.code}|{it.code}", human=[hd], meta=meta,
            )
            order.append(rid)

    for rid in order:
        r = merged[rid]
        if not r["meta"]["also_in"]:
            del r["meta"]["also_in"]
        yield Question(
            text=r["text"], primitive="score", hemisphere="self", kind=r["kind"], origin="dataset", source=NAME,
            options=r["options"], node_hint=r["node"], human_text=r["human_text"], source_item_id=r["sid"],
            license=LICENSE, human=r["human"], meta=r["meta"],
        )

    by_file: dict[tuple[str, str], list[ChoiceItem]] = {}
    for ci in choice_items(raw_dir):
        by_file.setdefault((ci.folder, ci.file), []).append(ci)
    for (folder, file), cis in by_file.items():
        df = load(raw_dir / folder / file, [ci.col.format(c=ci.code) for ci in cis])
        for ci in cis:
            if any(DROP.search(o) for o in ci.options):
                continue
            keys = choice_keys(ci.options)
            d, n = dist(df[ci.col.format(c=ci.code)], {i + 1: i for i in range(len(keys))}, len(keys))
            if not n:
                continue
            flags = sorted({"political" for o in ci.options if POLITICAL.search(o)} | {"sensitive" for o in ci.options if SENSITIVE.search(o)})
            meta = {"instrument": ci.inst, "item_code": ci.code, "scale": ci.scale,
                    "keyed": keys[ci.keyed - 1] if ci.keyed else None, "keyed_from": "published" if ci.keyed else None,
                    "scale_raw": ci.scale_raw, "raw_values": {str(i + 1): k for i, k in enumerate(keys)}}
            if flags:
                meta["flags"] = flags
            yield Question(
                text=ci.text, primitive="choice", hemisphere="self", kind="personality", origin="dataset", source=NAME,
                options={k: o for k, o in zip(keys, ci.options)}, node_hint=ci.node, human_text=ci.human_text,
                source_item_id=f"{ci.inst}|{ci.code}", license=LICENSE, meta=meta,
                human=[HumanDist(population=f"OpenPsychometrics web ({ci.label})",
                                 distribution={keys[int(a)]: v for a, v in d.items()}, n=n,
                                 source=f"openpsychometrics.org/_rawdata {folder} item {ci.code}; {ci.scale_raw}")],
            )
