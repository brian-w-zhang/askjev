"""Which headline got more clicks? Real A/B tests from Upworthy (research pass 2, idea 35).

Human data: the Upworthy Research Archive (Matias, Munger, Le Quere & Ebersole 2021, Scientific Data 8:195; OSF jd64p,
CC BY 4.0): 32,487 randomized headline tests run on Upworthy's readers in 2013-2015, with impressions and clicks per
version. From the exploratory release, pairs of versions from the same test that share the same image and differ only
in the headline, each shown to 1,000+ readers; one pair per test. The truth is the version with the higher
click-through rate. Pairs are sampled evenly across three bands of the click gap (the ratio of the two rates).

Politics is left out: tests whose headlines mention parties, politicians, elections, legislation or contested issues
are dropped by a keyword list before sampling (Upworthy covered a lot of politics).
"""

from __future__ import annotations

import math
import random
import re
import urllib.request
from pathlib import Path
from typing import Iterator

import polars as pl

from askjev.model import Question

NAME = "upworthy_headlines"
NODE = "world.society.media_news.journalism.headline_tests"
LICENSE = "CC BY 4.0 (Upworthy Research Archive, Matias et al. 2021, OSF jd64p)"
URL = "https://osf.io/download/3vqmp/"
PER_BAND = 200
POLITICS = re.compile(
    r"\b(obama|romney|biden|trump|clinton|hillary|bernie|sanders|mccain|palin|cruz|rand paul|boehner|pelosi|mcconnell|"
    r"bush|cheney|koch|republican|democrat|gop|tea party|congress|congressman|congresswoman|senat\w*|legislat\w*|"
    r"politic\w*|election\w*|vote\w*|voting|voter\w*|ballot|campaign|president\w*|governor|supreme court|"
    r"obamacare|affordable care act|health care law|abortion|pro-life|pro-choice|planned parenthood|gun\w*|nra|"
    r"second amendment|immigra\w*|deport\w*|border|refugee\w*|police|cops?|ferguson|racis\w*|white privilege|"
    r"black lives|gay|lesbian|lgbt\w*|transgender|same-sex|marriage equality|feminis\w*|patriarchy|rape|"
    r"fox news|liberal\w*|conservative\w*|socialis\w*|welfare|food stamps|minimum wage|tax\w*|wall street|"
    r"climate|global warming|fracking|iraq|afghanistan|syria|isis|israel\w*|palestin\w*|gaza|war|military|"
    r"muslim\w*|islam\w*|religio\w*|church|atheis\w*|death penalty|execution|torture|guantanamo|snowden|nsa|"
    r"surveillance|protest\w*|occupy|union\w*|koch|walmart|ceo pay|inequality|1 percent|one percent)\b",
    re.I)


def fetch(raw_dir: Path) -> None:
    if not (raw_dir / "exploratory.csv").exists():
        urllib.request.urlretrieve(URL, raw_dir / "exploratory.csv")


def _clean(h: str) -> str:
    return " ".join(str(h).replace("*", "").split())


def normalize(raw_dir: Path) -> Iterator[Question]:
    d = pl.read_csv(raw_dir / "exploratory.csv", infer_schema_length=10000)
    d = d.filter((pl.col("impressions") >= 1000) & pl.col("headline").is_not_null()).with_columns(
        (pl.col("clicks") / pl.col("impressions")).alias("ctr"))
    rng = random.Random(2021)
    pairs = []
    for (test, _img), g in sorted(d.group_by("clickability_test_id", "eyecatcher_id"), key=lambda x: x[0]):
        g = g.unique(subset="headline", keep="first").sort("headline")
        if g.height < 2 or any(POLITICS.search(str(h)) for h in g["headline"]):
            continue
        a, b = rng.sample(g.to_dicts(), 2)
        if min(a["ctr"], b["ctr"]) <= 0 or a["ctr"] == b["ctr"] or _clean(a["headline"]) == _clean(b["headline"]):
            continue
        pairs.append((test, a, b, abs(math.log(a["ctr"] / b["ctr"]))))
    seen, uniq = set(), []
    for p in pairs:  # one pair per test
        if p[0] not in seen:
            seen.add(p[0])
            uniq.append(p)
    uniq.sort(key=lambda p: p[3])
    third = len(uniq) // 3
    for band, lo in zip(("small", "medium", "large"), (0, third, 2 * third)):
        chunk = uniq[lo:lo + third] if band != "large" else uniq[lo:]
        for test, a, b, gap in rng.sample(chunk, min(PER_BAND, len(chunk))):
            win = a if a["ctr"] > b["ctr"] else b
            opts = {"headline_a": _clean(a["headline"]), "headline_b": _clean(b["headline"])}
            # a two-proportion z-test says whether the gap is more than noise
            p = (a["clicks"] + b["clicks"]) / (a["impressions"] + b["impressions"])
            se = math.sqrt(p * (1 - p) * (1 / a["impressions"] + 1 / b["impressions"])) or 1e-9
            yield Question(
                text="Upworthy tested these two headlines for the same story on its readers, with the same image. "
                     "Which headline got more clicks?",
                primitive="choice", hemisphere="world", kind="perception", origin="dataset", source=NAME,
                options=opts, node_hint=NODE, license=LICENSE, truth="headline_a" if win is a else "headline_b",
                source_item_id=f"{test}:{a['']}:{b['']}",
                meta={"experiment": "upworthy", "test": test, "band": band, "ctr_a": round(a["ctr"], 5),
                      "ctr_b": round(b["ctr"], 5), "impressions_a": a["impressions"], "impressions_b": b["impressions"],
                      "log_ratio": round(gap, 4), "z": round(abs(a["ctr"] - b["ctr"]) / se, 3),
                      "len_a": len(opts["headline_a"]), "len_b": len(opts["headline_b"])})
