"""PubMed study design: MEDLINE abstracts (2016-2022, English) with the publication type NLM indexers
assigned (Randomized Controlled Trial, Observational Study, Case Reports, Systematic Review / Meta-Analysis,
Review), fetched through the public NCBI E-utilities API (no key).

Template "pubmed_design.design": one Choice per abstract over five designs; truth = the indexed publication
type. Only records that carry exactly one of the five designs are kept (Systematic Review and Meta-Analysis
count as one design; "Review" means a review without either tag). Section labels of structured abstracts
("METHODS:") are dropped; the text itself is unchanged. 480 per design.
"""

from __future__ import annotations

import re
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Iterator

import httpx

from askjev.model import Question
from askjev.sampling import env_int, hash_order

NAME = "pubmed_design"
ESEARCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
EFETCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
PER = env_int("TARGET_PUBMED_DESIGN", 2400) // 5
LICENSE = "NLM PubMed/MEDLINE data (public; abstracts copyright their publishers)"
TEXT = "What kind of study is the paper described in `abstract`?"
OPTIONS = {
    "randomized_controlled_trial": "Participants were randomly assigned to interventions and compared",
    "observational_study": "Participants were observed without assigning an intervention (cohort, case-control, "
    "cross-sectional or registry study)",
    "case_report": "Describes one patient or a small number of individual patients",
    "systematic_review": "A systematic review or meta-analysis that searches for and pools published studies",
    "narrative_review": "A review or overview of a topic without a systematic search",
}
QUERIES = {
    "randomized_controlled_trial": '"randomized controlled trial"[pt]',
    "observational_study": '"observational study"[pt]',
    "case_report": '"case reports"[pt]',
    "systematic_review": '("systematic review"[pt] OR "meta-analysis"[pt])',
    "narrative_review": '"review"[pt] NOT "systematic review"[pt] NOT "meta-analysis"[pt]',
}
PT_TO_KEY = {
    "Randomized Controlled Trial": "randomized_controlled_trial",
    "Observational Study": "observational_study",
    "Case Reports": "case_report",
    "Systematic Review": "systematic_review",
    "Meta-Analysis": "systematic_review",
    "Review": "narrative_review",
}
N_IDS = 1600
SENSITIVE = re.compile(
    r"\b(suicid\w*|self[- ]harm\w*|sexual(ly)? (abuse|assault)\w*|rape\w*|incest|child abuse|overdos\w*)\b", re.I
)


def _get(client: httpx.Client, url: str, params: dict) -> httpx.Response:
    for attempt in range(6):
        r = client.get(url, params=params, timeout=120)
        if r.status_code == 200:
            time.sleep(0.4)
            return r
        time.sleep(2 * (attempt + 1))
    r.raise_for_status()
    return r


def fetch(raw_dir: Path) -> None:
    with httpx.Client(follow_redirects=True) as client:
        for key, q in QUERIES.items():
            out = raw_dir / f"{key}.xml"
            if out.exists():
                continue
            term = f"{q} AND hasabstract AND english[la]"
            r = _get(client, ESEARCH, {"db": "pubmed", "term": term, "retmax": 20000, "retmode": "json",
                                       "datetype": "pdat", "mindate": "2016", "maxdate": "2022"})
            ids = r.json()["esearchresult"]["idlist"]
            ids = hash_order(ids, lambda x: x, NAME)[:N_IDS]
            parts = []
            for i in range(0, len(ids), 200):
                rr = _get(client, EFETCH, {"db": "pubmed", "id": ",".join(ids[i : i + 200]), "retmode": "xml"})
                body = rr.text
                s, e = body.find("<PubmedArticleSet>"), body.rfind("</PubmedArticleSet>")
                parts.append(body[s + len("<PubmedArticleSet>") : e])
            out.write_text("<PubmedArticleSet>" + "".join(parts) + "</PubmedArticleSet>", encoding="utf-8")


def _text(el) -> str:
    return " ".join("".join(el.itertext()).split()) if el is not None else ""


def normalize(raw_dir: Path) -> Iterator[Question]:
    seen = set()
    for key in QUERIES:
        root = ET.parse(raw_dir / f"{key}.xml").getroot()
        pool = []
        for art in root.iter("PubmedArticle"):
            pmid = art.findtext(".//MedlineCitation/PMID")
            pts = {_text(p) for p in art.iter("PublicationType")}
            designs = {PT_TO_KEY[p] for p in pts if p in PT_TO_KEY}
            if "systematic_review" in designs:
                designs.discard("narrative_review")
            if designs != {key} or pmid in seen:
                continue
            if pts & {"Retracted Publication", "Clinical Trial Protocol", "Published Erratum", "Comment"}:
                continue
            title = _text(art.find(".//ArticleTitle"))
            abstract = " ".join(_text(a) for a in art.iter("AbstractText"))
            if len(abstract) < 400 or not title:
                continue
            s = f"Title: {title}\nAbstract: {abstract}"
            if len(s) > 1500:
                s = s[:1497].rsplit(" ", 1)[0] + "..."
            pool.append((pmid, s, sorted(pts)))
        for pmid, s, pts in hash_order(pool, lambda x: x[0], NAME)[:PER]:
            seen.add(pmid)
            yield Question(
                text=TEXT,
                primitive="choice",
                hemisphere="machine",
                origin="dataset",
                source=NAME,
                options=OPTIONS,
                state={"abstract": s},
                shape="classify",
                node_hint="machine.research.methods_checks",
                template_id="pubmed_design.design",
                source_item_id=f"pmid:{pmid}",
                license=LICENSE,
                truth=key,
                meta={"publication_types": pts, **({"flags": ["sensitive"]} if SENSITIVE.search(s) else {})},
            )
