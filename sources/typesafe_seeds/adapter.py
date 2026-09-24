"""TypeSafe docs seeds: the concrete example questions in TypeSafe's docs, as (template x state) Questions.

Two inputs, both public:
- The archived docs pages (resources/references/typesafe-docs/). Each cookbook embeds its playground
  request (verbatim state + questions) in a `console.typesafe.ai/playground#share/<lz-string>` link;
  fetch() decodes those into data/raw/typesafe_seeds/payloads/. Everything else is transcribed in
  seeds.py from the pages (instructions and criteria verbatim).
- RFC 7519 from rfc-editor.org, for the citation-check cookbook's sections.

States the docs print are used verbatim; states we wrote are marked meta.authored_state = true
("completed" when we finished a truncated preview the docs print). Skipped: the GDPR parallel-questions
payload (54k-char article state) and the semantic-find payload (218-way Choice over a 44k-char document).
"""

from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path
from typing import Iterator

import httpx

from askjev.model import Question

NAME = "typesafe_seeds"
ORIGIN = "typesafe-docs"
LICENSE = "TypeSafe docs (reference)"
HERE = Path(__file__).resolve().parent
DOCS = HERE.parents[1] / "resources" / "references" / "typesafe-docs"
RFC_URL = "https://www.rfc-editor.org/rfc/rfc7519.txt"
MAX_STATE = 1500  # for long free-text fields we truncate (the SEC filing)


def _load(name: str):
    spec = importlib.util.spec_from_file_location(f"typesafe_seeds_{name}", HERE / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------------------------------------- fetch
def fetch(raw_dir: Path) -> None:
    lz = _load("lzdecode")
    out = raw_dir / "payloads"
    out.mkdir(parents=True, exist_ok=True)
    for md in sorted((DOCS / "cookbooks").glob("*.md")):
        dest = out / f"{md.stem}.json"
        if dest.exists():
            continue
        links = re.findall(r"playground#share/([A-Za-z0-9+$-]+)", md.read_text())
        if not links:
            continue
        payload = json.loads(lz.decompress_uri(links[0]))
        dest.write_text(json.dumps(payload, ensure_ascii=False, indent=1))
    rfc = raw_dir / "rfc7519.txt"
    if not rfc.exists():
        r = httpx.get(RFC_URL, follow_redirects=True, timeout=60)
        r.raise_for_status()
        rfc.write_text(r.text)


# ------------------------------------------------------------------------------------------ helpers
def _q(tid, prim, text, options, shape, node, state, truth, doc, authored, item, raw=None, **meta) -> Question:
    m = {"doc": doc, "authored_state": authored}
    if truth is not None:
        m["truth_source"] = "authored" if authored is True else "docs"
    if raw is not None:
        m["instructions_raw"] = raw
    m.update(meta)
    return Question(
        text=text, primitive=prim, hemisphere="machine", origin=ORIGIN, source=NAME,
        options=options, state=state, shape=shape, node_hint=node, template_id=tid,
        source_item_id=item, license=LICENSE, truth=truth, meta=m,
    )


def _payload(raw_dir: Path, stem: str) -> tuple[object, dict]:
    d = json.loads((raw_dir / "payloads" / f"{stem}.json").read_text())
    doc = d["documentText"]
    try:
        state = json.loads(doc)
    except json.JSONDecodeError:
        state = doc
    return state, json.loads(d["promptsText"])


def _opts(q: dict):
    c = q.get("criteria")
    if q["type"] == "noul":
        return {"true": c["true"], "false": c["false"]} if c else None
    return c


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def _rfc_sections(text: str) -> dict[str, str]:
    lines = []
    for line in text.splitlines():
        bare = line.lstrip("\f")
        if re.match(r"Jones, et al\.\s.*\[Page \d+\]$", bare):
            continue
        if re.match(r"RFC 7519\s+JSON Web Token \(JWT\)\s+May 2015$", bare):
            continue
        lines.append(bare)
    source = re.sub(r"\n{3,}", "\n\n", "\n".join(lines))
    marks = list(re.finditer(r"(?m)^(?:(\d+(?:\.\d+)*)\.  .+|Appendix [A-Z]\..*)$", source))
    sections = {}
    for mark, nxt in zip(marks, marks[1:] + [None]):
        if mark.group(1) is None:
            continue
        sections[mark.group(1)] = source[mark.start(): nxt.start() if nxt else len(source)].strip()
    return sections


# ------------------------------------------------------------------------------------------ normalize
def normalize(raw_dir: Path) -> Iterator[Question]:
    sd = _load("seeds")
    S = sd.S

    # 1. Templates transcribed in seeds.py
    for tid, prim, text, options, shape, node, doc, items, raw in sd.T:
        for sname, truth in items:
            s = S[sname]
            yield _q(tid, prim, text, options, shape, node, s["state"], truth, doc, s["authored"], f"{tid}:{sname}", raw)

    # 2. Guardrail batteries (llm_guardrails) over the ten prompts and five replies
    _, gp = _payload(raw_dir, "llm_guardrails")
    dan_text, _ = _payload(raw_dir, "llm_guardrails")
    prompts = dict(sd.GUARD_IN)
    prompts["dan"] = (dan_text, False)
    doc = "cookbooks/llm_guardrails.md"
    for side, battery, msgs in (("input", sd.GUARD_IN_BATTERY, prompts), ("output", sd.GUARD_OUT_BATTERY, sd.GUARD_OUT)):
        for key, prim, text, options, truths in battery:
            for mname, (mtext, authored) in msgs.items():
                if prim == "noul":
                    truth = truths.get(mname, False)
                else:
                    truth = truths.get(mname, truths.get("__default__"))
                flags = ["sensitive"] if mname == "self_harm" else []
                yield _q(f"ts.guardrails.{side}.{key}", prim, text, options, "score" if prim == "score" else "detect",
                         sd.G, {"message" if side == "input" else "reply": mtext}, truth, doc, authored,
                         f"guardrails.{side}.{key}:{mname}", **({"flags": flags} if flags else {}))

    # 3. Invoice structured instructions (advanced.md): field objects go into the state
    for tid, prim, text, options, shape, node, fields, truth in sd.INVOICE:
        state = {"source_text": sd._INVOICE, **fields}
        yield _q(tid, prim, text, options, shape, node, state, truth, "primitives/advanced.md", False, f"{tid}:invoice_4471")

    # 4. RAG passage gating
    for key, text, truths in sd.RAG:
        for sname, truth in truths.items():
            s = S[sname]
            yield _q(f"ts.rag.{key}", "noul", text, None, "detect", "machine.search.rag_gating", s["state"], truth,
                     s["doc"], s["authored"], f"ts.rag.{key}:{sname}")

    # 5. Citation check over RFC 7519
    secs = _rfc_sections((raw_dir / "rfc7519.txt").read_text())
    for cid, claim, sec, truth, authored in sd.CITATIONS:
        section = secs[sec]
        if len(section) > 3500:  # section 2 (Terminology) is long: keep the NumericDate definition
            i = section.find("NumericDate")
            section = section[:200].rsplit("\n", 1)[0] + "\n   [...]\n" + section[i - 3: i + 700].rsplit("\n", 1)[0]
        yield _q("ts.citation.relation", "choice", "How does the section relate to the claim?", sd.RELATION, "verify",
                 "machine.research.claim_support", {"claim": claim, "section": section}, truth,
                 "cookbooks/citation_check.md", authored, f"citation:{cid}", rfc_section=sec)

    # 6. Decoded cookbook playground payloads (verbatim state + questions)
    yield from _payload_questions(raw_dir, sd)


def _payload_questions(raw_dir: Path, sd) -> Iterator[Question]:
    # Moderation rubric (8 Choices) on the cookbook's post + one authored spam post
    state, qs = _payload(raw_dir, "consistency_choice_cookbook")
    doc = "cookbooks/consistency_choice_cookbook.md"
    truth_main = {"target": "Person"}
    node = {"category": "machine.trust_safety.toxicity_harassment", "target": "machine.trust_safety.toxicity_harassment"}
    for key, q in qs.items():
        n = node.get(key, "machine.trust_safety.enforcement")
        shape = "classify" if key in ("category", "target", "severity", "primary_risk") else "route"
        yield _q(f"ts.moderation.{key}", "choice", q["instructions"], q["criteria"], shape, n, state,
                 truth_main.get(key), doc, False, f"moderation.{key}:P-88213")

    # Insurance claim rubric (14 Nouls). Truth only where the claim settles it.
    state, qs = _payload(raw_dir, "consistency_noul_cookbook")
    truths = {"on_circuit": False, "deductible": False, "docs_sufficient": False, "within_limit": True,
              "within_window": True, "reported_timely": True, "rental_eligible": False, "human_review": True,
              "line_items_sum": True, "subrogation": True}
    nodes = {"fraud_flag": "machine.finance.fraud_indicators"}
    for key, q in qs.items():
        yield _q(f"ts.insurance.{key}", "noul", q["instructions"], _opts(q), "verify" if key != "manual_review" else "route",
                 nodes.get(key, "machine.finance.claims_triage"), state, truths.get(key),
                 "cookbooks/consistency_noul_cookbook.md", False, f"insurance.{key}:CLM-55029")

    # Entity alignment (beer pair)
    state, qs = _payload(raw_dir, "entity_alignment")
    truths = {"same_brewery": True, "same_name": False}
    for key, q in qs.items():
        yield _q(f"ts.entity.{key}", q["type"], q["instructions"], _opts(q), "score" if q["type"] == "score" else "verify",
                 "machine.documents.entity_resolution", state, truths.get(key), "cookbooks/entity_alignment.md", False,
                 f"entity.{key}:ambleside")

    # Function calling (trading assistant)
    state, qs = _payload(raw_dir, "function_calling")
    truths = {"__tool__": "rolling_correlation", "rolling_correlation.symbol": "NVDA", "rolling_correlation.benchmark": "SPY",
              "rolling_correlation.benchmark?": True, "rolling_correlation.window": "1mo", "rolling_correlation.window?": True,
              "rolling_correlation.resolution?": False}
    for key, q in qs.items():
        if key == "rolling_correlation.resolution":  # the command states no bar size; its stated-Noul covers it
            continue
        tid = "ts.function.tool" if key == "__tool__" else "ts.function." + key.replace("?", ".stated")
        yield _q(tid, q["type"], q["instructions"], _opts(q), "extract", "machine.ai_systems.function_calling",
                 {"command": state}, truths.get(key), "cookbooks/function_calling.md", False, f"function.{key}")

    # Pre-parsed value pick
    state, qs = _payload(raw_dir, "pre_parsed_value_extraction_cookbook")
    for key, q in qs.items():
        yield _q("ts.preparsed.receipt_email", "choice", q["instructions"], q["criteria"], "extract",
                 "machine.documents.structured_extraction", {"document": state}, "dana.personal@gmail.com",
                 "cookbooks/pre_parsed_value_extraction_cookbook.md", False, "preparsed.receipt")

    # Re-ranking (CLERC): candidate is from Lebron v. National Railroad Passenger Corp., the redacted cite
    state, qs = _payload(raw_dir, "rerank_typesafe")
    for key, q in qs.items():
        yield _q("ts.rerank.is_cited_source", "noul", q["instructions"], _opts(q), "rank", "machine.search.reranking",
                 state, True, "cookbooks/rerank_typesafe.md", False, "rerank.lebron")

    # Skill suggestion: stage-2 Choice + fits Nouls, plus the stage-1 gate Nouls on the same request
    state, qs = _payload(raw_dir, "skill_suggestion")
    for key, q in qs.items():
        tid = "ts.skills.which" if key == "which" else "ts.skills.fits"
        truth = False if key == "fits::chroma" else None
        yield _q(tid, q["type"], q["instructions"], _opts(q), "route", "machine.ai_systems.skill_selection", state, truth,
                 "cookbooks/skill_suggestion.md", False, f"skills.{key}")
    for key, text, truth in sd.SKILL_GATES:
        yield _q(f"ts.skills.{key}", "noul", text, None, "route", "machine.ai_systems.skill_selection", state, truth,
                 "cookbooks/skill_suggestion.md", False, f"skills.{key}")

    # Structured-data-extraction cascade (per-field Noul battery; field_spec/extracted_field move to state)
    state, qs = _payload(raw_dir, "sde_cascade")
    for key, q in qs.items():
        ins = q["instructions"]
        metric = key.split("::")[1]
        if isinstance(ins, dict):
            text = ins["main_question"]
            st = {**state, "field_spec": ins["field_spec"], "extracted_field": ins["extracted_field"]}
        else:
            text, st = ins, state
        yield _q(f"ts.sde.{metric}", "noul", text, _opts(q), "verify", "machine.ai_systems.extraction_verification", st,
                 None, "cookbooks/sde_cascade.md", False, f"sde.{key}")

    # Date extraction (7 Choices for one role)
    state, qs = _payload(raw_dir, "date_extraction_cookbook")
    truths = {"mode": "relative", "month": "none", "day": "none", "year": "none", "day_anchor": "weekday",
              "weekday": "Thursday", "week_offset": "next"}
    for key, q in qs.items():
        yield _q(f"ts.date.{key}", "choice", q["instructions"], q["criteria"], "extract", "machine.documents.structured_extraction",
                 {"document": state}, truths[key], "cookbooks/date_extraction_cookbook.md", False, f"date.{key}:design_review")

    # Wine tasting-note features: a subset of the 38 discovered questions (all share one note)
    state, qs = _payload(raw_dir, "autoresearch_feature_discovery")
    keep = ["complexity", "acidity_intensity", "oak_intensity", "flaw_or_defect_mentioned", "price_value_signal",
            "note_overall_tone_positivity"]
    truths = {"flaw_or_defect_mentioned": False, "price_value_signal": False, "varietal_blend_detail": False, "oak_intensity": 0}
    for key in keep:
        q = qs[key]
        yield _q(f"ts.wine.{key}", q["type"], q["instructions"], _opts(q), "score" if q["type"] == "score" else "detect",
                 "machine.documents.feature_extraction", {"note": state}, truths.get(key),
                 "cookbooks/autoresearch_feature_discovery.md", False, f"wine.{key}")

    # Structure recovery (autoformat pass 2) over the 17-block memo
    state, qs = _payload(raw_dir, "autoformat")
    types = {"B000": "heading", "B001": "paragraph", "B002": "heading", "B003": "paragraph", "B004": "code", "B005": "paragraph",
             "B006": "paragraph", "B007": "list_item", "B008": "list_item", "B009": "list_item", "B010": "heading",
             "B011": "list_item", "B012": "list_item", "B013": "list_item", "B014": "callout", "B015": "quote", "B016": "paragraph"}
    extra = {"hlevel_B000": "title", "hlevel_B002": "section", "hlevel_B010": "section", "callout_B014": "warning"}
    for key, q in qs.items():
        kind, block = key.rsplit("_", 1)
        if kind == "type":
            if block in ("B003", "B005", "B008", "B012", "B016"):  # near-duplicate paragraphs / list items
                continue
            truth = types[block]
        elif key in extra:
            truth = extra[key]
        else:
            continue
        yield _q(f"ts.structure.{kind}", q["type"], q["instructions"], _opts(q), "classify", "machine.documents.structure_recovery",
                 {"document": state}, truth, "cookbooks/autoformat.md", False, f"structure.{key}")

    # Industry classification of a 10-K Item 1 (75 SIC major groups); filer's code 6163 -> group 61
    state, qs = _payload(raw_dir, "classification_using_confidence")
    text = _norm(state)
    cut = text[:MAX_STATE].rsplit(" ", 1)[0]
    for key, q in qs.items():
        yield _q("ts.sec.industry_group", "choice", q["instructions"], q["criteria"], "classify",
                 "machine.documents.taxonomy_classification", {"filing": cut + (" [...]" if len(cut) < len(text) else "")},
                 "61", "cookbooks/classification_using_confidence.md", False, "sec.1389870_2008", truncated=len(cut) < len(text))
