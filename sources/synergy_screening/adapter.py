"""SYNERGY v1 / ASReview systematic-review datasets (27 reviews; asreview/synergy-dataset index, metadata
CSVs from asreview/systematic-review-datasets `metadata-v1-final`): every record a review's search returned
(title + abstract), labelled by the review authors as included or excluded.

Template "synergy.include": one Noul per record: did the reviewers include this paper in a systematic review
on `review_topic`? Truth = the authors' label: the title/abstract screening label (`label_abstract_screening`)
wherever the CSV has one (the Cohen 2006 drug-class reviews, Appenzeller-Herzog, Nagtegaal...), else
`label_included` (final inclusion, so a few negatives passed abstract screening and were dropped at full text). `review_topic` is a one-line scope written
from each review's published title (the dataset's index names the review; the Cohen reviews are DERP drug
class reviews of comparative efficacy and safety). Balanced: up to 110 included per review, and as many
excluded records of the same review (topical near-misses from the same search).
"""

from __future__ import annotations

import csv
import io
from pathlib import Path
from typing import Iterator

import httpx

from askjev.model import Question
from askjev.sampling import env_int, hash_order

NAME = "synergy_screening"
INDEX = "https://raw.githubusercontent.com/asreview/synergy-dataset/master/index.csv"
TARGET = env_int("TARGET_SYNERGY_SCREENING", 2400)
PER_REVIEW = 110
TEXT = "Did the reviewers include `paper` in their systematic review on `review_topic`?"
OPTIONS = {
    "true": "Included: the study fits the review's question and was kept",
    "false": "Excluded: the search found it, but it does not fit the review's question",
}
_DRUG = "Comparative efficacy and safety of {} (a drug class review of clinical studies)"
TOPICS = {
    "Appenzeller-Herzog_2020": "Comparative effectiveness of common therapies for Wilson disease (controlled studies)",
    "Bannach-Brown_2019": "Animal models of depression (preclinical studies)",
    "Bos_2018": "Cerebral small vessel disease and the risk of dementia (population-based studies)",
    "Cohen_2006_ACEInhibitors": _DRUG.format("ACE inhibitors"),
    "Cohen_2006_ADHD": _DRUG.format("drugs for attention deficit hyperactivity disorder (ADHD)"),
    "Cohen_2006_Antihistamines": _DRUG.format("newer (second-generation) antihistamines"),
    "Cohen_2006_AtypicalAntipsychotics": _DRUG.format("atypical antipsychotics"),
    "Cohen_2006_BetaBlockers": _DRUG.format("beta blockers"),
    "Cohen_2006_CalciumChannelBlockers": _DRUG.format("calcium channel blockers"),
    "Cohen_2006_Estrogens": _DRUG.format("estrogens for menopausal symptoms"),
    "Cohen_2006_NSAIDS": _DRUG.format("nonsteroidal anti-inflammatory drugs (NSAIDs)"),
    "Cohen_2006_Opiods": _DRUG.format("long-acting opioid analgesics for chronic pain"),
    "Cohen_2006_OralHypoglycemics": _DRUG.format("oral hypoglycemic drugs for type 2 diabetes"),
    "Cohen_2006_ProtonPumpInhibitors": _DRUG.format("proton pump inhibitors"),
    "Cohen_2006_SkeletalMuscleRelaxants": _DRUG.format("skeletal muscle relaxants"),
    "Cohen_2006_Statins": _DRUG.format("statins (HMG-CoA reductase inhibitors)"),
    "Cohen_2006_Triptans": _DRUG.format("triptans for migraine"),
    "Cohen_2006_UrinaryIncontinence": _DRUG.format("drugs for overactive bladder and urinary incontinence"),
    "Hall_2012": "Performance of fault prediction models in software engineering",
    "Kitchenham_2010": "Systematic literature reviews in software engineering (a tertiary study)",
    "Kwok_2020": "Virus metagenomics in farm animals",
    "Nagtegaal_2019": "Nudges aimed at healthcare professionals to promote evidence-based medicine",
    "Radjenovic_2013": "Metrics used for software fault prediction",
    "Wahono_2015": "Software defect prediction: research trends, datasets, methods and frameworks",
    "Wolters_2018": "Coronary heart disease, heart failure and the risk of dementia",
    "van_Dis_2020": "Long-term outcomes of cognitive behavioral therapy for anxiety-related disorders",
    "van_de_Schoot_2017": "Latent trajectories of posttraumatic stress symptoms over time (trajectory studies)",
}
LICENSES = {"custom open license": "Cohen 2006 open data (custom open license)"}


def fetch(raw_dir: Path) -> None:
    idx = raw_dir / "index.csv"
    if not idx.exists():
        r = httpx.get(INDEX, follow_redirects=True, timeout=60)
        r.raise_for_status()
        idx.write_bytes(r.content)
    for row in csv.DictReader(open(idx, encoding="utf-8")):
        out = raw_dir / f"{row['dataset_id']}.csv"
        if out.exists():
            continue
        r = httpx.get(row["url"], follow_redirects=True, timeout=120)
        r.raise_for_status()
        out.write_bytes(r.content)


def _paper(title: str, abstract: str) -> str:
    title, abstract = " ".join(title.split()), " ".join(abstract.split())
    s = f"Title: {title}\nAbstract: {abstract}"
    return s if len(s) <= 1500 else s[:1497].rsplit(" ", 1)[0] + "..."


def normalize(raw_dir: Path) -> Iterator[Question]:
    index = list(csv.DictReader(open(raw_dir / "index.csv", encoding="utf-8")))
    assert {r["dataset_id"] for r in index} == set(TOPICS), {r["dataset_id"] for r in index} ^ set(TOPICS)
    per_review = []
    for row in index:
        did = row["dataset_id"]
        text = (raw_dir / f"{did}.csv").read_text(encoding="utf-8", errors="replace")
        recs = list(csv.DictReader(io.StringIO(text)))
        col = "label_abstract_screening" if "label_abstract_screening" in recs[0] else "label_included"
        pos, neg, seen = [], [], set()
        for r in recs:
            t, a = (r.get("title") or "").strip(), (r.get("abstract") or "").strip()
            lab = (r.get(col) or "").strip()
            if lab not in ("0", "1") or len(t) < 10 or len(a) < 200 or t.lower() in seen:
                continue
            seen.add(t.lower())
            (pos if lab == "1" else neg).append((f"{did}:{r['record_id']}", t, a))
        pos = hash_order(pos, lambda x: x[0], NAME)[:PER_REVIEW]
        neg = hash_order(neg, lambda x: x[0], NAME)[: len(pos)]
        lic = row["license"]
        per_review.append((did, lic, pos, neg, col))
    total = sum(2 * len(p) for _, _, p, _, _ in per_review)
    scale = min(1.0, TARGET / total)
    for did, lic, pos, neg, col in per_review:
        k = round(len(pos) * scale)
        for items, lab in ((pos[:k], True), (neg[:k], False)):
            for sid, t, a in items:
                yield Question(
                    text=TEXT,
                    primitive="noul",
                    hemisphere="machine",
                    origin="dataset",
                    source=NAME,
                    options=OPTIONS,
                    state={"review_topic": TOPICS[did], "paper": _paper(t, a)},
                    shape="classify",
                    node_hint="machine.research.paper_screening",
                    template_id="synergy.include",
                    source_item_id=sid,
                    license=LICENSES.get(lic, lic),
                    truth=lab,
                    meta={"review": did, "label_column": col},
                )
