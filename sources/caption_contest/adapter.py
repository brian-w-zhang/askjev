"""New Yorker Cartoon Caption Contest crowd ratings (NEXT / nextml caption-contest-data, Jain et al. 2020): every
submitted caption was rated "unfunny / somewhat funny / funny" by thousands of site visitors. Joined with the
cartoon's written scene description from Hessel et al. 2023 ("Do Androids Laugh at Electric Sheep?", CC BY 4.0),
so the question is text-only.

"How funny is this caption for the cartoon?" as a 3-level Score; state = scene, cartoon description, caption. The
human distribution is the caption's vote shares.
"""

from __future__ import annotations

import io
import re
from pathlib import Path
from typing import Iterator

import httpx
import polars as pl

from askjev.model import HumanDist, Question
from askjev.sampling import env_int, hash_order

NAME = "caption_contest"
TREE = "https://api.github.com/repos/nextml/caption-contest-data/git/trees/gh-pages?recursive=1"
RAW = "https://raw.githubusercontent.com/nextml/caption-contest-data/gh-pages/"
HF = "https://huggingface.co/datasets/jmhessel/newyorker_caption_contest/resolve/main/matching/"
HF_FILES = ["train-00000-of-00002", "train-00001-of-00002", "validation-00000-of-00001", "test-00000-of-00001"]
DESC = "descriptions.parquet"
LICENSE = ("Caption votes: nextml/caption-contest-data (Jain et al. 2020, NEXT), public GitHub release, no explicit "
           "license, research use with citation; cartoon descriptions: jmhessel/newyorker_caption_contest, CC BY 4.0")
TARGET = env_int("TARGET_CAPTION_CONTEST", 3000)
PER_CONTEST = 15  # 5 per funniness tier
MIN_VOTES = 100
SALT = "caption_contest-20260925"
TEXT = "How funny is this caption for the cartoon?"
HUMAN_TEXT = "How funny do most people find this caption for the cartoon?"
LEVELS = [
    "Unfunny: the caption doesn't land for me, no smile",
    "Somewhat funny: I get the joke and smile a little",
    "Funny: it makes me laugh",
]
SLURS = re.compile(r"\b(fag\w*|nigg\w*|retard\w*|tranny|dyke|spic|chink|kike|gook|wetback|towelhead|raghead)\b", re.I)
POLITICAL = re.compile(
    r"\b(trump\w*|donald|melania|ivanka|obama\w*|hillary|clinton\w*|bernie|sanders|biden|pence|putin|mueller|"
    r"comey|pelosi|mcconnell|republican\w*|democrat\w*|gop|election\w*|electoral|vot(e|es|ed|ers?|ing)|ballot\w*|"
    r"impeach\w*|maga|build the wall|border wall|immigra\w*|refugee\w*|deport\w*|abortion\w*|nra|gun control|"
    r"congress\w*|senat\w*|white house|president\w*|brexit|fake news|covfefe|tweet\w*)\b",
    re.I,
)
SENSITIVE = re.compile(
    r"\b(sex\w*|porn\w*|nude\w*|naked|orgasm\w*|viagra|penis\w*|genital\w*|vagina\w*|breasts?|boobs?|erect\w*|"
    r"condoms?|hooker|prostitut\w*|rap(e|ed|ist)|suicid\w*|kill (myself|yourself)|hang (myself|yourself)|"
    r"molest\w*|pedophil\w*|colonoscop\w*|rectal|probe|anal|butt\w*|poop\w*|fart\w*|urin\w*|pee|masturbat\w*|"
    r"dick|cock|balls|testicle\w*|horny|foreplay|threesome|lap dance|stripper\w*)\b",
    re.I,
)


def fetch(raw_dir: Path) -> None:
    raw_dir.mkdir(parents=True, exist_ok=True)
    if not (raw_dir / DESC).exists():
        cols = ["contest_number", "image_location", "image_description", "image_uncanny_description", "instance_id"]
        # Projection pushdown over HTTP range requests: the parquet files also hold the images (600 MB), never read.
        d = pl.concat([pl.scan_parquet(HF + f + ".parquet").select(cols).collect() for f in HF_FILES])
        d.write_parquet(raw_dir / DESC)
    contests = set(pl.read_parquet(raw_dir / DESC)["contest_number"].to_list())
    sdir = raw_dir / "summaries"
    sdir.mkdir(exist_ok=True)
    if any(sdir.iterdir()):
        return
    tree = httpx.get(TREE, timeout=120).json()["tree"]
    for t in tree:
        m = re.fullmatch(r"summaries/((\d+)(_[\w-]+)?\.csv)", t["path"])
        if m and int(m.group(2)) in contests:
            r = httpx.get(RAW + t["path"], timeout=120, follow_redirects=True)
            r.raise_for_status()
            (sdir / m.group(1)).write_bytes(r.content)


def _descriptions(raw_dir: Path) -> dict[int, dict]:
    """One description per contest: the first by instance id (annotations differ in wording, not in content)."""
    d = pl.read_parquet(raw_dir / DESC).sort("contest_number", "instance_id").unique("contest_number", keep="first")
    return {r["contest_number"]: r for r in d.iter_rows(named=True)}


def _summary(raw_dir: Path, contest: int) -> pl.DataFrame | None:
    """The contest's summary file with the most votes (a few contests ran two sampling algorithms)."""
    best = None
    for f in sorted((raw_dir / "summaries").glob(f"{contest}*.csv")):
        if not re.fullmatch(rf"{contest}(_[\w-]+)?\.csv", f.name):
            continue
        df = pl.read_csv(io.BytesIO(f.read_bytes()), infer_schema_length=0)
        need = {"caption", "votes", "not_funny", "somewhat_funny", "funny"}
        if not need <= set(df.columns):
            continue
        df = df.select(
            pl.col("caption"), *[pl.col(c).cast(pl.Int64, strict=False) for c in ("votes", "not_funny", "somewhat_funny", "funny")],
            file=pl.lit(f.name),
        ).drop_nulls()
        if best is None or df["votes"].sum() > best["votes"].sum():
            best = df
    return best


def _clean(s: str) -> str:
    return re.sub(r"\s+", " ", s.replace(" ", " ")).strip()


def normalize(raw_dir: Path) -> Iterator[Question]:
    desc = _descriptions(raw_dir)
    picked = []
    for contest in sorted(desc):
        df = _summary(raw_dir, contest)
        if df is None:
            continue
        rows, seen = [], set()
        for r in df.iter_rows(named=True):
            cap = _clean(r["caption"] or "")
            n = r["not_funny"] + r["somewhat_funny"] + r["funny"]
            # Votes must add up and every level must get some votes (drops seeded/test captions like 923/924 "funny").
            if (len(cap.split()) < 3 or len(cap) > 300 or n < MIN_VOTES or n != r["votes"] or cap.casefold() in seen
                    or SLURS.search(cap) or min(r["not_funny"], r["somewhat_funny"], r["funny"]) == 0):
                continue
            seen.add(cap.casefold())
            rows.append({**r, "caption": cap, "n": n, "contest": contest,
                         "mean": (r["somewhat_funny"] + 2 * r["funny"]) / n})
        if len(rows) < PER_CONTEST * 3:
            continue
        # Funniness tiers by mean rating: top 10%, middle, bottom half; 4 captions from each in salted-hash order.
        rows.sort(key=lambda r: (-r["mean"], r["caption"]))
        k = len(rows)
        tiers = [rows[: max(k // 10, 4)], rows[max(k // 10, 4): k // 2], rows[k // 2:]]
        for tier in tiers:
            picked += hash_order(tier, lambda r: f"{r['contest']}|{r['caption']}", SALT)[: PER_CONTEST // 3]
    picked = hash_order(picked, lambda r: f"{r['contest']}|{r['caption']}", SALT)[:TARGET]
    for r in picked:
        d = desc[r["contest"]]
        n = r["n"]
        flags = [f for f, rx in (("political", POLITICAL), ("sensitive", SENSITIVE)) if rx.search(r["caption"])]
        yield Question(
            text=TEXT,
            primitive="score",
            hemisphere="self",
            kind="taste",
            origin="dataset",
            source=NAME,
            options=LEVELS,
            state={"cartoon_scene": _clean(d["image_location"] or ""),
                   "cartoon": _clean(f"{d['image_description']} {d['image_uncanny_description']}"),
                   "caption": r["caption"]},
            node_hint="self.personality.humor_style.joke_ratings",
            human_text=HUMAN_TEXT,
            source_item_id=f"{r['contest']}|{r['caption']}",
            license=LICENSE,
            template_id="caption_contest.funny",
            human=[HumanDist(
                population="New Yorker Caption Contest voters (newyorker.com, NEXT crowd rating)",
                distribution={"0": round(r["not_funny"] / n, 4), "1": round(r["somewhat_funny"] / n, 4),
                              "2": round(r["funny"] / n, 4)},
                n=n,
                source=f"nextml/caption-contest-data summaries/{r['file']}: unfunny / somewhat funny / funny votes",
            )],
            meta={"contest": r["contest"], "mean_rating": round(r["mean"], 4),
                  "description_instance": d["instance_id"], **({"flags": flags} if flags else {})},
        )
