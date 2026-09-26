"""Stack Overflow questions with quality outcomes (Moore, "60k Stack Overflow Questions with Quality Rating",
Kaggle 2020; HF mirror NickyNicky/60k-stack-overflow-questions-with-quality-rate, the 45k train split).

Each post (2016-2020) carries the outcome Stack Overflow itself recorded:
  HQ       - score above 30 and never edited
  LQ_EDIT  - negative score and several community edits, but stayed open
  LQ_CLOSE - closed by the community without a single edit

Templates (disjoint posts):
- "so_quality.outcome": Choice over the three outcomes, truth = Y. 800 per outcome.
- "so_quality.language": Choice "Which programming language is the Stack Overflow question in `question` about?"
  over 16 languages. Truth = the post's own language tag; only posts tagged with exactly one of the 16
  (python-2.7/python-3.x count as python), no html/css tag and some code in the body are used, and the tags
  are not shown. HTML comments (snippet and `language: lang-js` hints) are stripped.

The Kaggle release stores HQ/LQ_CLOSE bodies as HTML and LQ_EDIT bodies as Markdown, which would leak the
outcome, so every body is flattened to the same plain text (code blocks kept, tags stripped, entities
unescaped, line endings normalized).
"""

from __future__ import annotations

import html
import re
from pathlib import Path
from typing import Iterator

import httpx
import polars as pl

from askjev.model import Question
from askjev.sampling import env_int, hash_order

NAME = "so_quality"
URL = (
    "https://huggingface.co/api/datasets/NickyNicky/60k-stack-overflow-questions-with-quality-rate"
    "/parquet/default/train/0.parquet"
)
LICENSE = "CC-BY-SA-4.0 (Stack Overflow content; Kaggle dataset by Moore 2020)"
PER_OUTCOME = env_int("PER_OUTCOME_SO_QUALITY", 800)
PER_LANG = env_int("PER_LANG_SO_QUALITY", 150)
MAX_BODY = 1500

OUTCOME_TEXT = "How did the Stack Overflow community receive the question in `question`?"
OUTCOMES = {
    "well_received": "It scored well (more than 30 upvotes net) and never needed an edit",
    "downvoted_and_edited": "It was downvoted and needed several community edits, but stayed open",
    "closed": "It was closed by the community without being edited",
}
Y_TO_KEY = {"HQ": "well_received", "LQ_EDIT": "downvoted_and_edited", "LQ_CLOSE": "closed"}

LANG_TEXT = "Which programming language is the Stack Overflow question in `question` about?"
LANGS = {
    "python": "Python",
    "javascript": "JavaScript",
    "typescript": "TypeScript",
    "java": "Java",
    "kotlin": "Kotlin",
    "csharp": "C#",
    "cpp": "C++",
    "c": "C",
    "php": "PHP",
    "ruby": "Ruby",
    "go": "Go",
    "swift": "Swift",
    "r": "R",
    "sql": "SQL",
    "vba": "VBA",
    "bash": "Bash / shell script",
}
TAG_TO_LANG = {
    "python": "python", "python-3.x": "python", "python-2.7": "python",
    "javascript": "javascript", "typescript": "typescript", "java": "java", "kotlin": "kotlin",
    "c#": "csharp", "c++": "cpp", "c": "c", "php": "php", "ruby": "ruby", "go": "go", "swift": "swift",
    "r": "r", "sql": "sql", "vba": "vba", "bash": "bash",
}
MARKUP_TAGS = {"html", "css", "html5", "css3"}
POLITICAL = re.compile(
    r"\b(trump|biden|obama|clinton|sanders|republican|democrat|election|abortion|gun control|immigra\w*)\b", re.I
)
SENSITIVE = re.compile(r"\b(porn\w*|nsfw|suicid\w*|self-harm)\b", re.I)


def _flags(*texts: str) -> dict:
    t = " ".join(texts)
    f = (["political"] if POLITICAL.search(t) else []) + (["sensitive"] if SENSITIVE.search(t) else [])
    return {"flags": f} if f else {}


def fetch(raw_dir: Path) -> None:
    out = raw_dir / "train.parquet"
    if out.exists():
        return
    r = httpx.get(URL, follow_redirects=True, timeout=180)
    r.raise_for_status()
    out.write_bytes(r.content)


def _plain(body: str) -> str:
    s = body.replace("\r\n", "\n").replace("\r", "\n")
    s = re.sub(r"(<|&lt;)!--.*?--(>|&gt;)", "", s, flags=re.S)  # snippet/language hints
    if "<p>" in s or "<pre" in s:
        s = re.sub(r"<pre[^>]*>\s*<code[^>]*>(.*?)</code>\s*</pre>", lambda m: "\n" + m.group(1).strip("\n") + "\n", s, flags=re.S)
        s = re.sub(r"<br\s*/?>", "\n", s)
        s = re.sub(r"</?(p|li|ul|ol|blockquote|h\d)[^>]*>", "\n", s)
        s = re.sub(r"<[^>]+>", "", s)
        s = html.unescape(s)
    s = re.sub(r"[ \t]+\n", "\n", s)
    s = re.sub(r"\n{3,}", "\n\n", s).strip()
    if len(s) > MAX_BODY:
        s = s[:MAX_BODY].rsplit(" ", 1)[0] + " ..."
    return s


def _has_code(body: str) -> bool:
    return "<code>" in body or bool(re.search(r"^(    |\t)\S", body.replace("\r", ""), flags=re.M))


def _tags(t: str) -> list[str]:
    return [x for x in t.strip("<>").split("><") if x]


def normalize(raw_dir: Path) -> Iterator[Question]:
    df = pl.read_parquet(raw_dir / "train.parquet")
    rows = [r for r in df.iter_rows(named=True) if r["Title"] and r["Body"] and len(_plain(r["Body"])) >= 40]
    seen: set[str] = set()
    uniq = []
    for r in rows:
        k = r["Title"].strip().lower()
        if k not in seen:
            seen.add(k)
            uniq.append(r)

    used: set[int] = set()
    for y, key in Y_TO_KEY.items():
        pool = hash_order([r for r in uniq if r["Y"] == y], lambda r: r["Id"], "so_quality.outcome")[:PER_OUTCOME]
        for r in sorted(pool, key=lambda r: r["Id"]):
            used.add(r["Id"])
            yield Question(
                text=OUTCOME_TEXT,
                primitive="choice",
                hemisphere="machine",
                origin="dataset",
                source=NAME,
                options=OUTCOMES,
                state={"question": {"title": r["Title"].strip(), "body": _plain(r["Body"]), "tags": _tags(r["Tags"])}},
                shape="classify",
                node_hint="machine.code.issue_triage",
                template_id="so_quality.outcome",
                source_item_id=f"so:{r['Id']}",
                license=LICENSE,
                truth=key,
                meta={"label_raw": y, "created": r["CreationDate"], **_flags(r["Title"], r["Body"])},
            )

    by_lang: dict[str, list[dict]] = {k: [] for k in LANGS}
    for r in uniq:
        if r["Id"] in used:
            continue
        tags = _tags(r["Tags"])
        if MARKUP_TAGS & set(tags) or not _has_code(r["Body"]):
            continue
        langs = {TAG_TO_LANG[t] for t in tags if t in TAG_TO_LANG}
        if len(langs) == 1:
            by_lang[langs.pop()].append(r)
    for lang, pool in by_lang.items():
        for r in sorted(hash_order(pool, lambda r: r["Id"], "so_quality.language")[:PER_LANG], key=lambda r: r["Id"]):
            yield Question(
                text=LANG_TEXT,
                primitive="choice",
                hemisphere="machine",
                origin="dataset",
                source=NAME,
                options=LANGS,
                state={"question": {"title": r["Title"].strip(), "body": _plain(r["Body"])}},
                shape="classify",
                node_hint="machine.code.code_review",
                template_id="so_quality.language",
                source_item_id=f"so:{r['Id']}",
                license=LICENSE,
                truth=lang,
                meta={"tags": _tags(r["Tags"]), "quality": r["Y"], **_flags(r["Title"], r["Body"])},
            )
