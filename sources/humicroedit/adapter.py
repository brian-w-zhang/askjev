"""Humicroedit (Hossain et al. 2019) + FunLines (Hossain et al. 2020), SemEval-2020 Task 7: real news headlines
with one word swapped to make them funny, each edit graded 0-3 by (usually) five judges.

"How funny is this edited news headline?" as a 4-level Score; state = the original and the edited headline. The
human distribution is the share of judges giving each grade. Headlines are mostly US politics, so the sample
takes headlines that do not match the political keyword list first (salted-hash order) and only then political
ones (flagged).
"""

from __future__ import annotations

import io
import re
import zipfile
from pathlib import Path
from typing import Iterator

import httpx
import polars as pl

from askjev.model import HumanDist, Question
from askjev.sampling import env_int, hash_order

NAME = "humicroedit"
URL = "https://www.cs.rochester.edu/u/nhossain/semeval-2020-task-7-dataset.zip"
ZIP = "semeval-2020-task-7-dataset.zip"
DIR = "semeval-2020-task-7-dataset/subtask-1/"
FILES = {  # file -> (corpus, judge population)
    "train.csv": ("humicroedit", "Humicroedit crowd judges (Amazon Mechanical Turk)"),
    "dev.csv": ("humicroedit", "Humicroedit crowd judges (Amazon Mechanical Turk)"),
    "test.csv": ("humicroedit", "Humicroedit crowd judges (Amazon Mechanical Turk)"),
    "train_funlines.csv": ("funlines", "FunLines players (funlines.co)"),
}
LICENSE = ("SemEval-2020 Task 7 dataset (Humicroedit, Hossain et al. 2019; FunLines, Hossain et al. 2020): "
           "public research release, no explicit license; cite the papers")
TARGET = env_int("TARGET_HUMICROEDIT", 5000)
SALT = "humicroedit-20260925"
TEXT = "How funny is this edited news headline?"
HUMAN_TEXT = "How funny do most people find this edited news headline?"
LEVELS = [
    "Not funny: the swapped word falls flat or just makes the headline confusing",
    "Slightly funny: I see the joke, but it gets a faint smile at most",
    "Moderately funny: it gets a real smile or a chuckle",
    "Funny: it makes me laugh out loud",
]

POLITICAL = re.compile(
    r"\b(trump\w*|donald|obama\w*|clinton\w*|hillary|bernie|sanders|biden|warren|pelosi|schumer|mcconnell|pence|"
    r"kushner|ivanka|bannon|mueller|comey|flynn|manafort|giuliani|cohen|stormy|kavanaugh|tillerson|pompeo|spicer|"
    r"sessions|mccabe|sen|haley|graham|gillibrand|mattis|kelly|dnc|rnc|ukraine|"
    r"scaramucci|huckabee|conway|devos|pruitt|mnuchin|romney|cruz|rubio|paul ryan|moore|"
    r"putin|vladimir|kremlin|erdogan|netanyahu|kim jong|duterte|maduro|bolsonaro|xi jinping|trudeau|modi|macron|merkel|"
    r"theresa may|boris|johnson|corbyn|farage|brexit|election\w*|elect|electoral|vot(e|es|ed|ers?|ing)|ballot\w*|"
    r"polls?|polling|campaign\w*|primar(y|ies)|republican\w*|democrat\w*|gop|dems?|liberal\w*|conservative\w*|"
    r"tories|tory|labour|senat\w*|congress\w*|house intel|white house|impeach\w*|president\w*|administration|"
    r"abortion\w*|pro-life|planned parenthood|guns?|nra|firearms?|immigra\w*|refugee\w*|asylum|deport\w*|daca|"
    r"dreamers|border wall|travel ban|muslim ban|obamacare|healthcare bill|estate tax|tax (bill|cuts?|plan|reform)|"
    r"lawmakers?|legislat\w*|governor\w*|parliament\w*|minister|partisan|alt-right|antifa|far-right|far right|"
    r"neo-nazi\w*|white supremac\w*|confedera\w*|russia probe|collusion|fbi)\b",
    re.I,
)
SENSITIVE = re.compile(
    r"\b(sex\w*|rap(e|ed|es|ist\w*)|porn\w*|nude\w*|naked|molest\w*|pedophil\w*|paedophil\w*|genital\w*|penis\w*|"
    r"vagina\w*|breasts?|orgasm\w*|brothel|prostitut\w*|suicid\w*|self-harm|massacre\w*|behead\w*|genocide|"
    r"murder\w*|mass shooting|shooting|shooter|killed|killing|dead|death\w*|corpses?|bodies|torture\w*|"
    r"terror\w*|bomb\w*|isis|nazi\w*|holocaust|drugs?|cocaine|heroin|weed|marijuana|poop\w*|fart\w*|butt\w*|"
    r"ass|toilet\w*|urin\w*)\b",
    re.I,
)
SLURS = re.compile(r"\b(fag\w*|nigg\w*|retard\w*|tranny|dyke|spic|chink|kike|gook|wetback|towelhead|raghead)\b", re.I)


def fetch(raw_dir: Path) -> None:
    out = raw_dir / ZIP
    if out.exists():
        return
    r = httpx.get(URL, follow_redirects=True, timeout=300)
    r.raise_for_status()
    out.write_bytes(r.content)


def _detok(s: str) -> str:
    """Undo the dataset's tokenization spaces ("Trump 's", "fire , says") without touching the words."""
    s = re.sub(r"\s+", " ", s).strip()
    s = re.sub(r" ([,.?!:;%)\]]|'s\b|’s\b|n't\b|n’t\b|'re\b|'ve\b|'ll\b|'d\b|'m\b)", r"\1", s)
    s = re.sub(r"([(\[$]) ", r"\1", s)
    s = re.sub(r"‘ (.*?) ’", r"‘\1’", s)
    s = re.sub(r"“ (.*?) ”", r"“\1”", s)
    s = re.sub(r"(?<![\w])' (.+?) '(?![\w])", r"'\1'", s)
    s = re.sub(r"(?<![\w])\" ([^\"]*?) \"(?![\w])", r'"\1"', s)
    s = re.sub(r"(\ws) ' (?=\w)", r"\1' ", s)  # unpaired: plural possessive ("states ' rights")
    return s


def _rows(raw_dir: Path) -> list[dict]:
    out, seen = [], set()
    with zipfile.ZipFile(raw_dir / ZIP) as z:
        for fname, (corpus, population) in FILES.items():
            df = pl.read_csv(io.BytesIO(z.read(DIR + fname)), schema_overrides={"grades": pl.Utf8, "id": pl.Utf8})
            for r in df.iter_rows(named=True):
                orig, edit, grades = r["original"], (r["edit"] or "").strip(), (r["grades"] or "").strip()
                m = re.search(r"<([^<>]*?)/>", orig or "")
                if not m or not edit or not re.fullmatch(r"[0-3]+", grades) or len(grades) < 5:
                    continue  # "0" (judge count unknown) and malformed rows
                if abs(sum(map(int, grades)) / len(grades) - float(r["meanGrade"])) > 0.01:
                    continue
                original = _detok(orig.replace(m.group(0), m.group(1)))
                edited = _detok(orig.replace(m.group(0), edit))
                if edited[:1].islower() and original[:1].isupper():
                    edited = edited[0].upper() + edited[1:]  # edit replaced the headline's first word
                if original.casefold() == edited.casefold() or SLURS.search(edited) or SLURS.search(original):
                    continue
                if edited.casefold() in seen:
                    continue
                seen.add(edited.casefold())
                out.append({"id": f"{corpus}:{r['id']}", "corpus": corpus, "population": population, "file": fname,
                            "original": original, "edited": edited, "word": m.group(1), "edit": edit,
                            "grades": grades, "mean": float(r["meanGrade"]),
                            "political": bool(POLITICAL.search(original) or POLITICAL.search(edited)),
                            "sensitive": bool(SENSITIVE.search(original) or SENSITIVE.search(edited))})
    return out


def normalize(raw_dir: Path) -> Iterator[Question]:
    rows = _rows(raw_dir)
    # Non-political headlines first, then political ones; each group in salted-hash order (prefix-stable).
    order = (hash_order([r for r in rows if not r["political"]], lambda r: r["id"], SALT)
             + hash_order([r for r in rows if r["political"]], lambda r: r["id"], SALT))
    for r in order[:TARGET]:
        n = len(r["grades"])
        counts = [r["grades"].count(str(i)) for i in range(4)]
        flags = [f for f in ("political", "sensitive") if r[f]]
        yield Question(
            text=TEXT,
            primitive="score",
            hemisphere="self",
            kind="taste",
            origin="dataset",
            source=NAME,
            options=LEVELS,
            state={"original_headline": r["original"], "edited_headline": r["edited"]},
            node_hint="self.personality.humor_style.joke_ratings",
            human_text=HUMAN_TEXT,
            source_item_id=r["id"],
            license=LICENSE,
            template_id="humicroedit.funny",
            human=[HumanDist(
                population=r["population"],
                distribution={str(i): round(c / n, 4) for i, c in enumerate(counts)},
                n=n,
                source=f"SemEval-2020 Task 7 subtask-1 {r['file']}: share of judges giving each grade 0-3",
            )],
            meta={"corpus": r["corpus"], "replaced_word": r["word"], "edit_word": r["edit"],
                  "mean_grade": r["mean"], **({"flags": flags} if flags else {})},
        )
