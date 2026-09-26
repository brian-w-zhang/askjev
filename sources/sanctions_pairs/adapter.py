"""OpenSanctions Pairs: candidate record pairs from OpenSanctions' cross-referencing of sanctions, PEP and
corporate-registry lists, each judged by an OpenSanctions analyst as the same real-world entity (positive) or
not (negative). Snapshot 2025-12-09 as pinned on HF (sanctions-er-anon/opensanctions_pairs, 755,540 pairs).

Template "sanctions_pairs.same_entity": Noul "Do `record_a` and `record_b` describe the same person or
organization?", truth = the analyst judgement. Candidates were proposed by a matcher, so negatives are hard
(similar names). Each record is rendered compactly: type, up to five names (Latin script first), and for people
birth date/place, nationality, gender, positions and list topics; for organisations country/jurisdiction,
incorporation date, legal form, sector and registration numbers. Personal document numbers, addresses, source
ids, dataset names and URLs are left out. Only Person-Person and organisation-organisation pairs
(Company / Organization / LegalEntity). Sample: 50% positive, ~60% person pairs, salted hash order.
Pairs involving politically exposed persons or government bodies are flagged "political" and capped at ~15%.
"""

from __future__ import annotations

import gzip
import hashlib
import re
from pathlib import Path
from typing import Iterator

import httpx
import orjson

from askjev.model import Question
from askjev.sampling import env_int

NAME = "sanctions_pairs"
URL = "https://huggingface.co/datasets/sanctions-er-anon/opensanctions_pairs/resolve/main/pairs.json.gz"
LICENSE = "CC-BY-NC-4.0 (OpenSanctions data; HF snapshot sanctions-er-anon/opensanctions_pairs)"
TARGET = env_int("TARGET_SANCTIONS_PAIRS", 2500)
TEXT = "Do `record_a` and `record_b` describe the same person or organization?"
OPTIONS = {
    "true": "Both records refer to the same real-world person or organization",
    "false": "The records refer to different people or organizations",
}
ORG = {"Company", "Organization", "LegalEntity"}
LATIN = re.compile(r"^[\x00-\x7fÀ-ɏḀ-ỿ'’.\-, ()]+$")
PERSON_FIELDS = [
    ("birthDate", "birth_date", 2),
    ("birthPlace", "birth_place", 1),
    ("nationality", "nationality", 3),
    ("citizenship", "citizenship", 3),
    ("country", "country", 3),
    ("gender", "gender", 1),
    ("position", "positions", 2),
    ("topics", "topics", 4),
]
ORG_FIELDS = [
    ("country", "country", 3),
    ("jurisdiction", "jurisdiction", 2),
    ("incorporationDate", "incorporation_date", 1),
    ("legalForm", "legal_form", 1),
    ("sector", "sector", 2),
    ("registrationNumber", "registration_number", 2),
    ("innCode", "inn_code", 1),
    ("ogrnCode", "ogrn_code", 1),
    ("taxNumber", "tax_number", 1),
    ("leiCode", "lei_code", 1),
    ("topics", "topics", 4),
]


def fetch(raw_dir: Path) -> None:
    out = raw_dir / "pairs.json.gz"
    if out.exists():
        return
    with httpx.stream("GET", URL, follow_redirects=True, timeout=600) as r:
        r.raise_for_status()
        with open(out, "wb") as fh:
            for chunk in r.iter_bytes():
                fh.write(chunk)


def _names(p: dict) -> list[str]:
    seen, out = set(), []
    raw = (p.get("name") or []) + (p.get("alias") or []) + (p.get("weakAlias") or [])
    raw = sorted(raw, key=lambda x: 0 if LATIN.match(x) else 1)  # stable: Latin script first
    for n in raw:
        n = " ".join(n.split())
        if n and n.lower() not in seen:
            seen.add(n.lower())
            out.append(n[:120])
        if len(out) == 5:
            break
    return out


def _render(ent: dict) -> dict:
    p = ent.get("properties") or {}
    out: dict = {"type": ent["schema"].lower().replace("legalentity", "legal entity"), "names": _names(p)}
    for src, dst, k in PERSON_FIELDS if ent["schema"] == "Person" else ORG_FIELDS:
        vals = []
        for v in p.get(src) or []:
            v = " ".join(str(v).split())[:160]
            if v and v not in vals:
                vals.append(v)
        if vals:
            out[dst] = vals[:k] if k > 1 else vals[0]
    return out


def _political(ent: dict) -> bool:
    topics = (ent.get("properties") or {}).get("topics") or []
    return any(t.startswith(("role.pep", "role.rca", "gov")) for t in topics)


def normalize(raw_dir: Path) -> Iterator[Question]:
    # Salted hash of the raw line decides the order; only the first ~6% of hash space is parsed.
    cands: list[tuple[str, dict]] = []
    with gzip.open(raw_dir / "pairs.json.gz", "rb") as f:
        for line in f:
            h = hashlib.sha256(b"sanctions_pairs|" + line.strip()).hexdigest()
            if h[:2] > "0f":
                continue
            d = orjson.loads(line)
            if d.get("judgement") not in ("positive", "negative"):
                continue
            ls, rs = d["left"]["schema"], d["right"]["schema"]
            if not ((ls == rs == "Person") or (ls in ORG and rs in ORG)):
                continue
            cands.append((h, d))
    cands.sort(key=lambda x: x[0])

    quota = {
        ("positive", True): TARGET * 3 // 10,
        ("negative", True): TARGET * 3 // 10,
        ("positive", False): TARGET // 5,
        ("negative", False): TARGET // 5,
    }
    # Flagged (political) pairs are hidden from the map, so they are capped at ~15% of each quota.
    pol_quota = {k: v * 15 // 100 for k, v in quota.items()}
    seen: set = set()
    for h, d in cands:
        person = d["left"]["schema"] == "Person"
        key = (d["judgement"], person)
        if quota[key] <= 0:
            continue
        a, b = _render(d["left"]), _render(d["right"])
        if not a["names"] or not b["names"] or a == b:
            continue
        pid = tuple(sorted((d["left"]["id"], d["right"]["id"])))
        skey = orjson.dumps([a, b], option=orjson.OPT_SORT_KEYS)
        if pid in seen or skey in seen:
            continue
        flags = ["political"] if _political(d["left"]) or _political(d["right"]) else []
        if flags:
            if pol_quota[key] <= 0:
                continue
            pol_quota[key] -= 1
        seen.add(pid)
        seen.add(skey)
        quota[key] -= 1
        yield Question(
            text=TEXT,
            primitive="noul",
            hemisphere="machine",
            origin="dataset",
            source=NAME,
            options=OPTIONS,
            state={"record_a": a, "record_b": b},
            shape="verify",
            node_hint="machine.finance.kyc_aml",
            template_id="sanctions_pairs.same_entity",
            source_item_id=f"{pid[0]}|{pid[1]}",
            license=LICENSE,
            truth=d["judgement"] == "positive",
            meta={"flags": flags, "schemas": [d["left"]["schema"], d["right"]["schema"]]} if flags
            else {"schemas": [d["left"]["schema"], d["right"]["schema"]]},
        )
