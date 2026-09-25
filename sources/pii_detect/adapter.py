"""ai4privacy pii-masking-200k (English part): synthetic business, education, legal and psychology texts
with character-offset spans for 54 PII classes.

Every row has at least one span, so truth comes from which span labels a text carries:
- STRONG categories (name, email, phone, street address, government ID, bank account, payment card)
  identify or contact a specific person.
- WEAK labels (job title, date, age, sex, city, currency, company...) are not personal identifiers on
  their own. Rows whose spans are all WEAK are the negatives (hard negatives: they still carry some data).
- Everything else (usernames, IPs, crypto addresses, passwords, device IDs, vehicle plates, DOB, GPS...)
  is ambiguous for the question's definition: such rows never serve as negatives or single-category items.

Templates:
- "pii_detect.contains_pii" (Noul): truth = any STRONG category present; 50/50.
- "pii_detect.pii_kind" (Choice) over 8 categories + none: only rows with exactly one category (the online
  identifier category included) and no ambiguous labels; truth = that category, or none for WEAK-only rows.
  Balanced round-robin across the nine keys.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterator

import httpx
import orjson

from askjev.model import Question
from askjev.sampling import env_int, hash_order

NAME = "pii_detect"
URL = "https://huggingface.co/datasets/ai4privacy/pii-masking-200k/resolve/main/english_pii_43k.jsonl"
LICENSE = "Ai4Privacy license (free for individuals, non-profits and orgs of <=3 staff)"
NODE = "machine.trust_safety.personal_data"
TARGET_NOUL = env_int("TARGET_PII_DETECT", 1600)
TARGET_KIND = env_int("TARGET_PII_DETECT_KIND", 1400)

NOUL_TEXT = (
    "Does `text` contain personal data that identifies or could contact a specific person "
    "(name, email, phone, address, ID or account number)?"
)
NOUL = {
    "true": "It contains a person's name, email address, phone number, street address, government ID, "
    "bank account or payment card number",
    "false": "It contains none of these, though it may mention jobs, dates, places, amounts or general traits",
}
KIND_TEXT = "What kind of personal data does `text` contain?"
KINDS = {
    "name": "A person's first, middle or last name",
    "email_address": "An email address",
    "phone_number": "A phone number",
    "postal_address": "A street address",
    "government_id": "A national ID or social security number",
    "bank_account": "A bank account number or IBAN",
    "payment_card": "A credit or debit card number or its security code",
    "online_identifier": "A username, IP address or device MAC address",
    "none": "None of these: no name, contact details, address, ID, account number or online identifier",
}
CATEGORY = {
    "FIRSTNAME": "name", "MIDDLENAME": "name", "LASTNAME": "name",
    "EMAIL": "email_address",
    "PHONENUMBER": "phone_number",
    "STREET": "postal_address",
    "SSN": "government_id",
    "ACCOUNTNUMBER": "bank_account", "IBAN": "bank_account",
    "CREDITCARDNUMBER": "payment_card", "CREDITCARDCVV": "payment_card",
    "USERNAME": "online_identifier", "IPV4": "online_identifier", "IPV6": "online_identifier",
    "IP": "online_identifier", "MAC": "online_identifier",
}  # fmt: skip
STRONG = {c for c in CATEGORY.values() if c != "online_identifier"}
ADDRESS_PARTS = {"BUILDINGNUMBER", "SECONDARYADDRESS", "ZIPCODE"}  # fine alongside STREET, ambiguous alone
WEAK = {
    "JOBTITLE", "JOBAREA", "JOBTYPE", "CURRENCY", "CURRENCYSYMBOL", "CURRENCYCODE", "CURRENCYNAME", "AMOUNT",
    "TIME", "DATE", "SEX", "GENDER", "AGE", "EYECOLOR", "HEIGHT", "ORDINALDIRECTION", "CREDITCARDISSUER",
    "COMPANYNAME", "CITY", "COUNTY", "STATE", "PREFIX",
}  # fmt: skip


def fetch(raw_dir: Path) -> None:
    out = raw_dir / "english_pii_43k.jsonl"
    if out.exists():
        return
    with httpx.stream("GET", URL, follow_redirects=True, timeout=600) as r:
        r.raise_for_status()
        with open(out, "wb") as fh:
            for chunk in r.iter_bytes():
                fh.write(chunk)


def _profile(labels: set[str]) -> tuple[set[str], bool]:
    """(categories present, has ambiguous labels)."""
    cats = {CATEGORY[l] for l in labels if l in CATEGORY}
    other = labels - set(CATEGORY) - WEAK
    if "postal_address" in cats:
        other -= ADDRESS_PARTS
    return cats, bool(other)


def normalize(raw_dir: Path) -> Iterator[Question]:
    seen: set[str] = set()
    items = []  # (id, text, labels, cats, ambiguous)
    with open(raw_dir / "english_pii_43k.jsonl", "rb") as fh:
        for line in fh:
            d = orjson.loads(line)
            if d.get("language") != "en":
                continue
            t = " ".join(d["source_text"].split())
            if not (20 <= len(t) <= 1500) or t.lower() in seen:
                continue
            seen.add(t.lower())
            labels = {m["label"] for m in d["privacy_mask"]}
            cats, amb = _profile(labels)
            items.append((d["id"], t, sorted(labels), cats, amb))

    def q(tid, text, prim, options, shape, it, truth):
        return Question(
            text=text,
            primitive=prim,
            hemisphere="machine",
            origin="dataset",
            source=NAME,
            options=options,
            state={"text": it[1]},
            shape=shape,
            node_hint=NODE,
            template_id=tid,
            source_item_id=f"en:{it[0]}",
            license=LICENSE,
            truth=truth,
            meta={"pii_labels": it[2]},
        )

    # Noul: 50/50 identifying vs WEAK-only.
    pos = [it for it in items if it[3] & STRONG]
    neg = [it for it in items if not it[3] and not it[4]]
    half = TARGET_NOUL // 2
    n_neg = min(len(neg), TARGET_NOUL - half)
    picked = [(it, True) for it in hash_order(pos, lambda x: x[0], "pii.noul.pos")[: TARGET_NOUL - n_neg]]
    picked += [(it, False) for it in hash_order(neg, lambda x: x[0], "pii.noul.neg")[:n_neg]]
    for it, truth in sorted(picked, key=lambda x: x[0][0]):
        yield q("pii_detect.contains_pii", NOUL_TEXT, "noul", NOUL, "detect", it, truth)

    # Choice: exactly one category and nothing ambiguous; round-robin across the nine keys.
    pools: dict[str, list] = {k: [] for k in KINDS}
    for it in items:
        if it[4] or len(it[3]) > 1:
            continue
        pools[next(iter(it[3])) if it[3] else "none"].append(it)
    ordered = {k: hash_order(v, lambda x: x[0], f"pii.kind.{k}") for k, v in pools.items()}
    take = {k: 0 for k in KINDS}
    n = 0
    while n < TARGET_KIND and any(take[k] < len(ordered[k]) for k in KINDS):
        for k in KINDS:
            if n < TARGET_KIND and take[k] < len(ordered[k]):
                take[k] += 1
                n += 1
    for k in KINDS:
        for it in sorted(ordered[k][: take[k]], key=lambda x: x[0]):
            yield q("pii_detect.pii_kind", KIND_TEXT, "choice", KINDS, "classify", it, k)
