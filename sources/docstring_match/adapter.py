"""CodeSearchNet (Husain et al. 2019, GitHub): functions with their documentation comments from
open-source repositories. Test split for Python, JavaScript, Java and Go (HF
code-search-net/code_search_net).

Template "docstring_match.accurate" (Noul, node code.code_review): does the docstring accurately
describe what the code does. Half the pairs are the function's own docstring (truth true); half give the
docstring of a different function from the same repository and language (truth false). Only the
docstring's summary (first paragraph, tag lines such as @param / :param dropped) is shown, and the
docstring is removed from Python bodies. Go comments that open with the function name have that name
removed ("mustWaitPinReady waits..." -> "Waits..."), for mismatched ones too, so the name is not a
giveaway. Functions <= 1,200 chars, summaries 4-60 words, mostly ASCII. Equal share per language.
"""

from __future__ import annotations

import re
import textwrap
from collections import defaultdict
from pathlib import Path
from typing import Iterator

import httpx
import polars as pl

from askjev.model import Question
from askjev.sampling import env_int, hash_order

NAME = "docstring_match"
LANGS = ("python", "javascript", "java", "go")
BASE = "https://huggingface.co/api/datasets/code-search-net/code_search_net/parquet/{lang}/test/0.parquet"
TARGET = env_int("TARGET_DOCSTRING_MATCH", 2500)
LICENSE = "CodeSearchNet: functions from repositories under permissive open-source licenses (each repo's own license)"
TEXT = "Does `docstring` accurately describe what `code` does?"
CRITERIA = {
    "true": "The docstring describes what this function does",
    "false": "The docstring describes something this function does not do",
}
MAX_CODE = 1200
TAG_LINE = re.compile(r"^\s*(@|:param|:type|:return|:rtype|:raises|Args:|Returns:|Parameters|Raises:|Example|>>>)")


def fetch(raw_dir: Path) -> None:
    for lang in LANGS:
        out = raw_dir / f"{lang}_test.parquet"
        if out.exists():
            continue
        r = httpx.get(BASE.format(lang=lang), follow_redirects=True, timeout=300)
        r.raise_for_status()
        out.write_bytes(r.content)


def summary(doc: str, func_name: str, lang: str) -> str:
    doc = re.sub(r'^[rRuUbB]?("""|\'\'\')|("""|\'\'\')\s*$', "", doc.strip())
    lines = [re.sub(r"^\s*(//+|/?\*+/?|#)\s?", "", l).rstrip() for l in doc.split("\n")]
    para: list[str] = []
    for l in lines:
        if TAG_LINE.match(l) or (not l.strip() and para):
            break
        if l.strip():
            para.append(l.strip())
    s = " ".join(" ".join(para).split())
    s = re.sub(r"\{@(?:code|link|linkplain) ([^}]*)\}", r"\1", s)
    if lang == "go":
        short = func_name.split(".")[-1]
        m = re.match(rf"^(?:{re.escape(short)})\s+(\w)", s)
        if m:
            s = m.group(1).upper() + s[m.end():]
    return s


def strip_py_docstring(code: str) -> str | None:
    """Drop the docstring that opens the body (right after the signature). None if unparseable."""
    sig = re.search(r"\)\s*(?:->[^:\n]*)?:[ \t]*(?:#[^\n]*)?\n", code)
    if not sig:
        return None
    m = re.match(r'\s*[rRuUbB]?("""|\'\'\'|"|\')', code[sig.end():])
    if not m:
        return code
    start = sig.end() + m.end()
    end = code.find(m.group(1), start)
    if end < 0:
        return None
    return code[: sig.end()] + code[end + len(m.group(1)):].lstrip(" \t").lstrip("\n")


def reindent(code: str, lang: str) -> str:
    """CodeSearchNet keeps a method's original indentation after the first line; remove it."""
    first, _, rest = code.strip("\n").partition("\n")
    if not rest:
        return first
    rest = textwrap.dedent(rest)
    if lang == "python":
        rest = textwrap.indent(rest, "    ")
    return first + "\n" + rest


def _ok(s: str) -> bool:
    words = s.split()
    return 4 <= len(words) <= 60 and sum(c.isascii() for c in s) >= 0.95 * len(s) and "inheritdoc" not in s.lower()


def normalize(raw_dir: Path) -> Iterator[Question]:
    per_lang = {l: TARGET // len(LANGS) + (1 if i < TARGET % len(LANGS) else 0) for i, l in enumerate(LANGS)}
    for lang in LANGS:
        df = pl.read_parquet(raw_dir / f"{lang}_test.parquet", columns=[
            "repository_name", "func_path_in_repository", "func_name", "func_code_string",
            "func_documentation_string", "func_code_url"]).with_row_index("row")
        items = []
        seen_doc: set[str] = set()
        for r in df.iter_rows(named=True):
            code = r["func_code_string"]
            if lang == "python":
                code = strip_py_docstring(code)
            if not code or len(code) > MAX_CODE:
                continue
            doc = summary(r["func_documentation_string"] or "", r["func_name"], lang)
            if not _ok(doc) or doc.lower() in seen_doc or doc[:40] in code:
                continue
            seen_doc.add(doc.lower())
            items.append({**r, "code": reindent(code, lang), "doc": doc})
        by_repo = defaultdict(list)
        for it in items:
            by_repo[it["repository_name"]].append(it)
        # only repos with at least two usable functions (so a same-repo donor exists)
        pool = [it for it in items if len(by_repo[it["repository_name"]]) >= 2]
        order = hash_order(pool, lambda x: x["row"], f"docmatch.{lang}")
        k_true = per_lang[lang] // 2
        k_false = per_lang[lang] - k_true
        out = [(it, it["doc"], True, None) for it in order[:k_true]]
        for it in order[k_true:]:
            if len(out) >= k_true + k_false:
                break
            donors = [d for d in by_repo[it["repository_name"]]
                      if d["row"] != it["row"] and d["func_name"].split(".")[-1] != it["func_name"].split(".")[-1]
                      and d["doc"].lower()[:30] != it["doc"].lower()[:30]]
            if donors:
                d = hash_order(donors, lambda x: x["row"], f"docmatch.donor.{it['row']}")[0]
                out.append((it, d["doc"], False, d))
        out.sort(key=lambda x: x[0]["row"])
        for it, doc, match, donor in out:
            yield Question(
                text=TEXT,
                primitive="noul",
                hemisphere="machine",
                origin="dataset",
                source=NAME,
                options=CRITERIA,
                state={"docstring": doc, "code": it["code"]},
                shape="verify",
                node_hint="machine.code.code_review",
                template_id="docstring_match.accurate",
                source_item_id=f"{lang}:test:{it['row']}" + (f"|{donor['row']}" if donor else ""),
                license=LICENSE,
                truth=match,
                meta={"language": lang, "repo": it["repository_name"], "func_name": it["func_name"],
                      "url": it["func_code_url"], **({"donor_func": donor["func_name"]} if donor else {})},
            )
