"""LegalBench (Guha et al. 2023, HF `nguha/legalbench`): 162 legal-reasoning tasks built by legal experts
over real legal text. Seven tasks with expert labels and 300+ examples are wrapped as Machine templates
(train + test splits pooled; LegalBench's own task instructions supply each criterion's wording):

- legalbench.privacy_practice (OPP-115, 9 binary tasks): does a privacy-policy segment describe a named
  data practice? The practice definition is in `practice`. -> machine.legal.policy_checks
- legalbench.consumer_contracts_qa: does a Terms of Service excerpt answer a consumer's question with yes?
  -> machine.legal.policy_checks
- legalbench.cuad_provision (CUAD, 38 binary tasks): does a contract clause contain the provision described
  in `provision`? -> machine.legal.clause_detection
- legalbench.legal_area (Learned Hands, 16 binary tasks): does a person's legal-help post (r/legaladvice)
  raise an issue in the area described in `legal_area`? -> machine.legal
- legalbench.overruling: does a sentence from a judicial opinion overrule a previous case? -> machine.legal
- legalbench.definition: does a sentence from a Supreme Court opinion define a term? -> machine.legal
- legalbench.decision_section: which function a paragraph of a court decision serves (7 classes).
  -> machine.legal

Skipped after inspection: privacy_policy_qa (sentence relevance labels look near-random on a sample),
privacy_policy_entailment (segment-level labels often not supported by the segment), supply_chain_disclosure
(statements median 2.7k chars, would need truncation that breaks labels), diversity_* / sara / hearsay /
abercrombie (synthetic or < 300 examples), oral_argument_question_purpose (subjective, small).
"""

from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Iterator

import httpx
import polars as pl

from askjev.model import Question
from askjev.sampling import env_int, hash_order

NAME = "legalbench"
INDEX = "https://huggingface.co/api/datasets/nguha/legalbench/parquet"
META_URL = "https://huggingface.co/datasets/nguha/legalbench/resolve/main/task_metadata.json"
LICENSE_BASE = "LegalBench (CC-BY-4.0 card; per-task source licenses)"
LICENSES = {
    "privacy_practice": "CC-BY-NC (OPP-115 via LegalBench)",
    "consumer_contracts_qa": "CC-BY-NC-4.0 (via LegalBench)",
    "cuad_provision": "CC-BY-4.0 (CUAD via LegalBench)",
    "legal_area": "CC-BY-NC-SA-4.0 (Learned Hands via LegalBench)",
    "overruling": "CC-BY-4.0 (via LegalBench)",
    "definition": "CC-BY-SA-4.0 (via LegalBench)",
    "decision_section": "CC-BY-4.0 (via LegalBench)",
}
TARGETS = {
    "privacy_practice": env_int("TARGET_LEGALBENCH_PRIVACY", 2500),
    "consumer_contracts_qa": env_int("TARGET_LEGALBENCH_CCQA", 400),
    "cuad_provision": env_int("TARGET_LEGALBENCH_CUAD", 2500),
    "legal_area": env_int("TARGET_LEGALBENCH_AREA", 2500),
    "overruling": env_int("TARGET_LEGALBENCH_OVERRULING", 2400),
    "definition": env_int("TARGET_LEGALBENCH_DEFINITION", 1400),
    "decision_section": env_int("TARGET_LEGALBENCH_SECTION", 400),
}
MAX_CHARS = 1500

SENSITIVE = re.compile(
    r"\b(sex|sexual\w*|porn\w*|nude\w*|naked|rape\w*|raped|molest\w*|incest|suicid\w*|kill (my|him|her)self|"
    r"self[- ]harm|overdos\w*|pedo\w*)\b",
    re.I,
)

YES_NO = {"Yes": True, "No": False}

PRACTICE_TEXT = "Does `segment` of a privacy policy describe the data practice defined in `practice`?"
PRACTICE_OPTIONS = {
    "true": "The segment states something about this practice (what the service does, or does not do)",
    "false": "The segment is about something else",
}
CCQA_TEXT = "According to the terms of service in `terms`, is the answer to the consumer's `question` yes?"
CCQA_OPTIONS = {"true": "The terms say yes", "false": "The terms say no"}
CUAD_TEXT = "Does contract clause `clause` contain the kind of provision described in `provision`?"
CUAD_OPTIONS = {"true": "The clause contains this provision", "false": "The clause is a different kind of provision"}
AREA_TEXT = "Does the legal-help request in `post` raise an issue in the area of law described in `legal_area`?"
AREA_OPTIONS = {
    "true": "The situation in the post involves this area",
    "false": "The post is about other areas of law",
}
OVERRULING_TEXT = "Does `sentence` from a court opinion overrule a previous case?"
OVERRULING_OPTIONS = {
    "true": "The court overrules, disapproves or abrogates an earlier decision, in whole or in part",
    "false": "The sentence cites, applies or distinguishes earlier cases without overruling any",
}
DEFINITION_TEXT = "Does `sentence` from a court opinion define a term?"
DEFINITION_OPTIONS = {
    "true": "The sentence states or quotes the meaning of a word or phrase",
    "false": "The sentence uses terms without defining any",
}
SECTION_TEXT = "What function does `paragraph` serve in a court decision?"
SECTION_OPTIONS = {
    "facts": "Describes the factual background that led up to the lawsuit",
    "procedural_history": "Describes the course of litigation that led to the current proceeding",
    "issue": "Describes the legal or factual issue the court must resolve",
    "rule": "States a rule of law relevant to resolving the issue",
    "analysis": "Applies the legal principles to the facts of this dispute",
    "conclusion": "Presents a conclusion of the court",
    "decree": "Resolves the case and sets its outcome (affirmed, reversed, remanded...)",
}

# Learned Hands area names (the definitions come from LegalBench's task instructions).
AREAS = {
    "benefits": "Public benefits",
    "business": "Small business and nonprofits",
    "consumer": "Consumer, money and debt",
    "courts": "Courts and lawyers",
    "crime": "Crime and prisons",
    "divorce": "Divorce and separation",
    "domestic_violence": "Domestic violence",
    "education": "Education",
    "employment": "Work and employment",
    "estates": "Estates, wills and guardianship",
    "family": "Family",
    "health": "Health",
    "housing": "Housing",
    "immigration": "Immigration",
    "torts": "Disputes between people (torts)",
    "traffic": "Traffic and cars",
}
PRACTICES = {
    "data_retention": "Data retention",
    "data_security": "Data security",
    "do_not_track": "Do Not Track",
    "first_party_collection_use": "First-party collection and use",
    "international_and_specific_audiences": "International and specific audiences",
    "policy_change": "Policy change",
    "third_party_sharing_collection": "Third-party sharing and collection",
    "user_access,_edit_and_deletion": "User access, edit and deletion",
    "user_choice_control": "User choice and control",
}


def _tasks(index: dict) -> list[str]:
    keep = ("opp115_", "cuad_", "learned_hands_")
    exact = {"consumer_contracts_qa", "overruling", "definition_classification", "function_of_decision_section"}
    return sorted(t for t in index if t.startswith(keep) or t in exact)


def fetch(raw_dir: Path) -> None:
    idx_path = raw_dir / "index.json"
    if not idx_path.exists():
        r = httpx.get(INDEX, follow_redirects=True, timeout=60)
        r.raise_for_status()
        idx_path.write_bytes(r.content)
    meta = raw_dir / "task_metadata.json"
    if not meta.exists():
        r = httpx.get(META_URL, follow_redirects=True, timeout=60)
        r.raise_for_status()
        meta.write_bytes(r.content)
    index = json.loads(idx_path.read_text())
    with httpx.Client(follow_redirects=True, timeout=120) as client:
        for task in _tasks(index):
            for split, urls in index[task].items():
                out = raw_dir / f"{task}__{split}.parquet"
                if out.exists():
                    continue
                r = client.get(urls[0])
                r.raise_for_status()
                out.write_bytes(r.content)


def _load(raw_dir: Path, task: str) -> list[tuple[str, dict]]:
    rows = []
    for split in ("train", "test"):
        p = raw_dir / f"{task}__{split}.parquet"
        if p.exists():
            rows += [(split, r) for r in pl.read_parquet(p).to_dicts()]
    return rows


def _clean(s: str) -> str:
    return " ".join((s or "").split())


def _criterion(meta: dict, task: str) -> str:
    """The task's yes/no question from LegalBench's instructions (first paragraph)."""
    return meta[task]["instruction"].split("\n\n")[0].strip()


def _balanced(groups: dict[str, dict[bool, list]], target: int, key, salt: str) -> list:
    """Round-robin over groups, alternating yes/no within each, in salted hash order."""
    queues = {(g, lab): hash_order(items, key, f"{salt}|{g}|{lab}") for g, d in groups.items() for lab, items in d.items()}
    cursor = {k: 0 for k in queues}
    out: list = []
    order = sorted(queues)
    while len(out) < target:
        progressed = False
        for k in order:
            if len(out) >= target:
                break
            if cursor[k] < len(queues[k]):
                out.append(queues[k][cursor[k]])
                cursor[k] += 1
                progressed = True
        if not progressed:
            break
    return out


def _flags(*texts: str) -> dict:
    return {"flags": ["sensitive"]} if any(SENSITIVE.search(t or "") for t in texts) else {}


def _q(tid: str, text: str, prim: str, options, state: dict, shape: str, node: str, truth, sid: str, meta: dict) -> Question:
    return Question(
        text=text,
        primitive=prim,
        hemisphere="machine",
        origin="dataset",
        source=NAME,
        options=options,
        state=state,
        shape=shape,
        node_hint=node,
        template_id=f"legalbench.{tid}",
        source_item_id=sid,
        license=LICENSES.get(tid, LICENSE_BASE),
        truth=truth,
        meta=meta,
    )


def _binary_family(raw_dir: Path, meta: dict, prefix: str, max_chars: int = MAX_CHARS):
    """{subtask: {True: [...], False: [...]}} of (subtask, split, idx, text, label) for a family of Yes/No tasks."""
    groups: dict[str, dict[bool, list]] = {}
    for task in sorted(meta):
        if not task.startswith(prefix):
            continue
        sub = task[len(prefix):]
        d: dict[bool, list] = {True: [], False: []}
        seen = set()
        for split, r in _load(raw_dir, task):
            t = _clean(r["text"])
            if not (30 <= len(t) <= max_chars) or t.lower() in seen or r["answer"] not in YES_NO:
                continue
            seen.add(t.lower())
            d[YES_NO[r["answer"]]].append((sub, split, r["index"], t, YES_NO[r["answer"]]))
        groups[sub] = d
    return groups


def normalize(raw_dir: Path) -> Iterator[Question]:
    meta = json.loads((raw_dir / "task_metadata.json").read_text())
    key = lambda x: (x[0], x[1], x[2])  # noqa: E731

    # 1. OPP-115 privacy practices.
    groups = _binary_family(raw_dir, meta, "opp115_")
    for sub, split, idx, seg, truth in sorted(_balanced(groups, TARGETS["privacy_practice"], key, "lb.privacy"), key=key):
        crit = _criterion(meta, f"opp115_{sub}").removeprefix("Does the clause describe ").rstrip("?")
        practice = f"{PRACTICES[sub]}: the policy describes {crit}"
        yield _q("privacy_practice", PRACTICE_TEXT, "noul", PRACTICE_OPTIONS, {"segment": seg, "practice": practice},
                 "verify", "machine.legal.policy_checks", truth, f"opp115_{sub}:{split}:{idx}",
                 {"task": f"opp115_{sub}", "split": split, **_flags(seg)})

    # 2. Consumer contracts QA.
    items = []
    for split, r in _load(raw_dir, "consumer_contracts_qa"):
        c, qn = (r["contract"] or "").strip(), _clean(r["question"])
        if len(c) <= 3000 and qn and r["answer"] in YES_NO:
            items.append((split, r["index"], c, qn, YES_NO[r["answer"]]))
    for split, idx, c, qn, truth in sorted(hash_order(items, lambda x: (x[0], x[1]), "lb.ccqa")[: TARGETS["consumer_contracts_qa"]], key=lambda x: (x[0], x[1])):
        yield _q("consumer_contracts_qa", CCQA_TEXT, "noul", CCQA_OPTIONS, {"terms": c, "question": qn}, "verify",
                 "machine.legal.policy_checks", truth, f"consumer_contracts_qa:{split}:{idx}", {"split": split})

    # 3. CUAD provisions.
    groups = _binary_family(raw_dir, meta, "cuad_")
    for sub, split, idx, clause, truth in sorted(_balanced(groups, TARGETS["cuad_provision"], key, "lb.cuad"), key=key):
        name = sub.replace("_", " ").replace("-", " ").replace("rofr rofo rofn", "ROFR/ROFO/ROFN")
        provision = f"{name[0].upper()}{name[1:]}: {_criterion(meta, 'cuad_' + sub)}"
        yield _q("cuad_provision", CUAD_TEXT, "noul", CUAD_OPTIONS, {"clause": clause, "provision": provision},
                 "detect", "machine.legal.clause_detection", truth, f"cuad_{sub}:{split}:{idx}",
                 {"task": f"cuad_{sub}", "split": split})

    # 4. Learned Hands legal areas.
    groups = _binary_family(raw_dir, meta, "learned_hands_")
    for sub, split, idx, post, truth in sorted(_balanced(groups, TARGETS["legal_area"], key, "lb.area"), key=key):
        crit = _criterion(meta, f"learned_hands_{sub}").removeprefix("Does the post discuss ").rstrip("?")
        area = f"{AREAS[sub]}: {crit[0].upper()}{crit[1:]}"
        yield _q("legal_area", AREA_TEXT, "noul", AREA_OPTIONS, {"post": post, "legal_area": area}, "route",
                 "machine.legal", truth, f"learned_hands_{sub}:{split}:{idx}",
                 {"task": f"learned_hands_{sub}", "split": split, **_flags(post)})

    # 5-6. Overruling and definition sentences (balanced yes/no).
    for tid, task, text, options, target in (
        ("overruling", "overruling", OVERRULING_TEXT, OVERRULING_OPTIONS, TARGETS["overruling"]),
        ("definition", "definition_classification", DEFINITION_TEXT, DEFINITION_OPTIONS, TARGETS["definition"]),
    ):
        d: dict[bool, list] = {True: [], False: []}
        seen = set()
        for split, r in _load(raw_dir, task):
            t = _clean(r["text"])
            if not (15 <= len(t) <= MAX_CHARS) or t.lower() in seen or r["answer"] not in YES_NO:
                continue
            seen.add(t.lower())
            d[YES_NO[r["answer"]]].append((task, split, r["index"], t, YES_NO[r["answer"]]))
        for _, split, idx, sent, truth in sorted(_balanced({task: d}, target, key, f"lb.{tid}"), key=key):
            yield _q(tid, text, "noul", options, {"sentence": sent}, "detect", "machine.legal", truth,
                     f"{task}:{split}:{idx}", {"split": split, **_flags(sent)})

    # 7. Function of a decision section.
    items = []
    seen = set()
    for split, r in _load(raw_dir, "function_of_decision_section"):
        p = _clean(r["Paragraph"])
        lab = r["answer"].lower().replace(" ", "_")
        if not (40 <= len(p) <= MAX_CHARS) or p.lower() in seen or lab not in SECTION_OPTIONS:
            continue
        seen.add(p.lower())
        items.append((split, r["index"], p, lab, r["Citation"]))
    for split, idx, p, lab, cite in sorted(hash_order(items, lambda x: (x[0], x[1]), "lb.section")[: TARGETS["decision_section"]], key=lambda x: (x[0], x[1])):
        yield _q("decision_section", SECTION_TEXT, "choice", SECTION_OPTIONS, {"paragraph": p}, "classify",
                 "machine.legal", lab, f"function_of_decision_section:{split}:{idx}", {"split": split, "citation": cite})
