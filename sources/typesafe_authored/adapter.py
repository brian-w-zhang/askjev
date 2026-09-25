"""TypeSafe's empty Machine leaves: authored inputs with author-decided labels (docs/10-expansion.md §8, priority 4).

These leaves (claims triage, KYC/AML, ad alignment, listing compliance, moderation enforcement, response
verification, prohibited claims, methods checks, and the thin People leaves) have no public labeled data.
The question templates below follow TypeSafe's style (one snap judgment over an input, with the state
keys named in backticks). The inputs are realistic records we wrote ourselves, one per line in
`authored/machine_inputs/<leaf>.jsonl`:

    {"id": "ct-0001", "template": "docs_sufficient", "state": {...}, "truth": true,
     "borderline": false, "why": "police report, photos and estimate all attached"}

`truth` is the label the author decided while writing (a choice key, a Noul bool, or a score level index), so
it is the author's judgment, not independent ground truth. `borderline` marks the deliberately hard cases
(~30%). Every question is origin="synthetic" with meta.synthetic_input = true and counts inside a wave's
synthetic cap. Names, numbers, companies and brands in the inputs are invented.

Checks here (a failing line is printed to stderr and emitted with empty text so it counts as rejected):
unknown template, missing state keys the template names, truth outside the options, state length outside
200-1,200 characters, and duplicate input ids.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Iterator

from askjev.model import Question

NAME = "typesafe_authored"
LICENSE = "authored (askjev)"
INPUTS = Path(__file__).resolve().parents[2] / "authored" / "machine_inputs"
MIN_CHARS, MAX_CHARS = 200, 1200


def _noul(true: str, false: str) -> dict:
    return {"true": true, "false": false}


# leaf -> template name -> spec. `keys`: top-level state keys the template text relies on.
TEMPLATES: dict[str, dict[str, dict]] = {
    "machine.finance.claims_triage": {
        "docs_sufficient": dict(
            shape="verify", primitive="noul", keys=["policy", "claim"],
            text="Does `claim` include enough documentation to adjudicate it without follow-up? Compare the "
                 "attachments and details in `claim` with `policy.required_documents`.",
            options=_noul("Everything the policy requires for this kind of loss is attached or stated; an adjuster "
                          "could decide now",
                          "Something required is missing, unreadable or contradictory, so the adjuster must ask "
                          "for more")),
        "exclusion_applies": dict(
            shape="detect", primitive="noul", keys=["policy", "claim"],
            text="Does an exclusion in `policy.exclusions` apply to the loss described in `claim`? Judge the cause "
                 "of loss as the claim states it.",
            options=_noul("A listed exclusion clearly or probably applies to this loss",
                          "No listed exclusion applies to this loss")),
        "handling_path": dict(
            shape="route", primitive="choice", keys=["claim"],
            text="Which handling path should `claim` take? Judge by the loss type, severity and complexity the "
                 "claim describes.",
            options={
                "straight_through": "Small, routine, clearly described loss that can be paid without a human "
                                    "adjuster",
                "desk_adjuster": "Needs an adjuster's judgment by phone or documents, but no inspection or "
                                 "specialist",
                "field_adjuster": "Needs someone to inspect the vehicle, property or scene in person",
                "specialist": "Involves bodily injury, litigation, a total loss of high value, or a coverage "
                              "dispute that needs a specialist unit",
            }),
    },
    "machine.finance.kyc_aml": {
        "watchlist_match": dict(
            shape="verify", primitive="noul", keys=["customer", "watchlist_entry"],
            text="Is `customer` the same person or entity as `watchlist_entry`? Compare names (allowing for "
                 "transliteration and word order), dates of birth or registration, nationality and identifiers.",
            options=_noul("The records describe the same person or entity",
                          "The records describe different people or entities, despite any similarity")),
        "structuring": dict(
            shape="detect", primitive="noul", keys=["alert"],
            text="Does the activity described in `alert` suggest structuring, that is, splitting cash or "
                 "transfers to stay under reporting or identification thresholds?",
            options=_noul("The pattern looks designed to avoid reporting or identification thresholds",
                          "The pattern has a plausible ordinary explanation and does not suggest structuring")),
        "onboarding_complete": dict(
            shape="verify", primitive="noul", keys=["policy", "application"],
            text="Does `application` contain everything `policy` requires before this account can be opened?",
            options=_noul("Every item the policy requires for this customer type is present and consistent",
                          "At least one required item is missing, expired or inconsistent")),
    },
    "machine.commerce.ad_alignment": {
        "offer_delivered": dict(
            shape="verify", primitive="noul", keys=["ad", "landing_page"],
            text="Does `landing_page` deliver the offer that `ad` promises? Check that the promised deal, "
                 "terms and availability appear on the page.",
            options=_noul("A visitor who clicks the ad finds the promised offer on the page",
                          "The promised offer is missing, changed or hidden behind a material condition the ad "
                          "did not mention (not the routine conditions buyers of this product expect)")),
        "price_match": dict(
            shape="verify", primitive="noul", keys=["ad", "landing_page"],
            text="Does the price or discount stated in `ad` match the one shown in `landing_page`?",
            options=_noul("The page shows the same price or discount the ad states",
                          "The page shows a different price or discount, or none at all")),
        "same_product": dict(
            shape="verify", primitive="noul", keys=["ad", "landing_page"],
            text="Is `landing_page` about the same product or service that `ad` advertises?",
            options=_noul("The page offers the advertised product or service itself, not just a mention of it",
                          "The page is for a different product, a generic page, or an unrelated destination")),
    },
    "machine.commerce.listing_compliance": {
        "prohibited_item": dict(
            shape="detect", primitive="noul", keys=["policy", "listing"],
            text="Is `listing` in violation of the marketplace's prohibited-items policy in `policy`?",
            options=_noul("The listed item or its sale breaks the policy",
                          "The listed item is allowed under the policy")),
        "counterfeit": dict(
            shape="detect", primitive="noul", keys=["listing"],
            text="Does `listing` appear to sell a counterfeit, replica or unauthorized copy of a branded item?",
            options=_noul("The listing signals a fake, replica or unauthorized copy",
                          "The listing reads as a genuine, used, or unbranded item")),
        "misleading_title": dict(
            shape="verify", primitive="noul", keys=["listing"],
            text="Does the title in `listing.title` misrepresent the item described in `listing.description`?",
            options=_noul("The title claims something the description contradicts or does not support",
                          "The title fairly represents the item described")),
    },
    "machine.trust_safety.enforcement": {
        "action": dict(
            shape="route", primitive="choice", keys=["policy", "case"],
            text="What enforcement action should be taken on the post in `case`, under `policy` and given the "
                 "author's history in `case.author`?",
            options={
                "allow": "Leave the post up; it breaks no rule",
                "warn": "Leave it up or label it, and warn the author",
                "remove": "Remove the post without a strike",
                "remove_and_strike": "Remove the post and add a strike",
                "suspend": "Remove the post and suspend the account",
            }),
        "queue": dict(
            shape="route", primitive="choice", keys=["case"],
            text="Which moderation queue should own the report in `case`?",
            options={
                "harassment_hate": "Harassment, bullying, threats or hate against people",
                "spam_scams": "Spam, scams, fake engagement or phishing",
                "self_harm": "Suicide, self-harm or eating-disorder content",
                "sexual_content": "Nudity, sexual content or sexual exploitation",
                "violent_extremism": "Graphic violence, terrorism or violent extremism",
                "ip_legal": "Copyright, trademark, privacy or other legal claims",
                "misinformation": "False or misleading claims about health, elections or public safety",
                "none": "No queue; the report does not describe a policy issue",
            }),
        "final_call": dict(
            shape="route", primitive="choice", keys=["case"],
            text="Who should make the final call on `case`?",
            options={
                "automation": "An automated rule can decide; the case is clear-cut and low risk",
                "moderator": "A trained moderator should decide; it needs context or judgment",
                "specialist": "A senior or specialist team (child safety, threats, crisis) should decide",
                "legal": "The legal team should decide; it involves a legal demand, court order or law "
                         "enforcement",
            }),
    },
    "machine.support.response_verification": {
        "resolves_request": dict(
            shape="verify", primitive="noul", keys=["ticket", "reply"],
            text="Does `reply` fully resolve the customer's request in `ticket`?",
            options=_noul("The reply answers or settles everything the customer asked for",
                          "Part or all of the request is left unanswered, deferred or misunderstood")),
        "follows_policy": dict(
            shape="verify", primitive="noul", keys=["policy", "reply"],
            text="Does `reply` follow the support policy in `policy`?",
            options=_noul("Nothing in the reply breaks the policy",
                          "The reply offers, promises, discloses or omits something the policy forbids or "
                          "requires")),
        "followup_promised": dict(
            shape="detect", primitive="noul", keys=["transcript"],
            text="Does the agent in `transcript` promise a specific follow-up action after the call?",
            options=_noul("The agent commits to doing something later (call back, email, escalate, send, "
                          "check and confirm); automatic system messages and other companies' actions do not "
                          "count",
                          "The agent makes no commitment beyond what was done during the call")),
    },
    "machine.legal.prohibited_claims": {
        "claim_type": dict(
            shape="classify", primitive="choice", keys=["copy"],
            text="Which restricted claim, if any, does `copy` make? Pick the most serious one.",
            options={
                "disease_claim": "Says the product treats, cures, prevents or mitigates a disease or medical "
                                 "condition",
                "guaranteed_return": "Promises guaranteed, risk-free or certain financial returns",
                "unsubstantiated_proof": "Says the product is clinically, scientifically or lab proven, or "
                                         "doctor recommended, without citing the support",
                "misleading_comparison": "Claims to be better, cheaper or #1 against competitors without a "
                                         "stated basis",
                "environmental": "Makes a broad eco claim (green, carbon neutral, non-toxic, biodegradable) "
                                 "without specifics",
                "none": "Makes no restricted claim",
            }),
        "disease_claim": dict(
            shape="detect", primitive="noul", keys=["copy"],
            text="Does `copy` claim that the product treats, cures, prevents or mitigates a disease or medical "
                 "condition?",
            options=_noul("It makes a disease or medical-condition claim, stated or clearly implied",
                          "It makes only general wellness, structure-function or no health claims")),
        "guaranteed_return": dict(
            shape="detect", primitive="noul", keys=["copy"],
            text="Does `copy` promise guaranteed or risk-free investment returns?",
            options=_noul("It promises a return is certain, guaranteed or without risk of loss",
                          "It makes no such promise, or states that returns are not guaranteed")),
    },
    "machine.research.methods_checks": {
        "sample_size_justified": dict(
            shape="verify", primitive="noul", keys=["methods"],
            text="Does `methods` report how the sample size was determined, such as a power calculation or "
                 "another stated justification?",
            options=_noul("It states how the sample size was chosen",
                          "It gives the sample size, if at all, without saying how it was chosen")),
        "blinding": dict(
            shape="classify", primitive="choice", keys=["methods"],
            text="According to `methods`, who was blinded to group assignment?",
            options={
                "not_reported": "Blinding is not mentioned",
                "open_label": "It states that nobody was blinded (open label)",
                "participants_only": "Only participants were blinded",
                "assessors_only": "Only outcome assessors or analysts were blinded",
                "participants_and_assessors": "Participants and outcome assessors (or investigators) were "
                                              "blinded",
            }),
        "primary_test_named": dict(
            shape="verify", primitive="noul", keys=["methods"],
            text="Does `methods` name the statistical test or model used to analyze the primary outcome?",
            options=_noul("The analysis of the primary outcome is named (e.g. a t-test, mixed model, Cox "
                          "regression)",
                          "The primary analysis is not named, or only generic words like 'statistical "
                          "analysis' are used")),
    },
    "machine.people.competency_evidence": {
        "resume_depth": dict(
            shape="score", primitive="score", keys=["competency", "resume"],
            text="How much evidence of `competency` does `resume` show?",
            options=[
                "The resume shows no sign of this competency",
                "It is only listed as a skill, or appears in coursework, a certificate or a hobby project",
                "The resume describes using it in a job or substantial project",
                "The resume describes years of hands-on work with it, including leading or designing substantial "
                "work that depends on it",
            ]),
        "feedback_strong": dict(
            shape="verify", primitive="noul", keys=["competency", "feedback"],
            text="Does the interview feedback in `feedback` show concrete evidence that the candidate is strong "
                 "in `competency`?",
            options=_noul("The feedback describes specific behavior in the interview that shows strength in "
                          "this competency",
                          "The feedback shows weakness, mixed results, only vague praise, or nothing about this "
                          "competency")),
    },
    "machine.people.purchase_intent": {
        "near_term_intent": dict(
            shape="detect", primitive="noul", keys=["message"],
            text="Does the prospect in `message` express intent to buy within the next three months?",
            options=_noul("They signal a purchase decision or start within about a quarter",
                          "They are researching, have no timeline, or put the purchase further out")),
        "pricing_objection": dict(
            shape="detect", primitive="noul", keys=["transcript"],
            text="Does the prospect in `transcript` raise a pricing or budget objection?",
            options=_noul("The prospect pushes back on price, cost or budget",
                          "The prospect raises no price or budget concern")),
        "pain_point": dict(
            shape="classify", primitive="choice", keys=["notes"],
            text="Which pain point does the prospect describe in `notes`? Pick the main one.",
            options={
                "manual_work": "Too much manual, repetitive or error-prone work",
                "cost": "Current tools or processes cost too much",
                "integration": "Tools do not connect or share data",
                "compliance_security": "Audit, compliance, privacy or security gaps",
                "scaling": "Current setup cannot keep up with growth or volume",
                "visibility": "No reporting, insight or visibility into what is happening",
                "none": "No pain point is described",
            }),
    },
}


def _truth_ok(spec: dict, truth) -> bool:
    if spec["primitive"] == "noul":
        return isinstance(truth, bool)
    if spec["primitive"] == "choice":
        return truth in spec["options"]
    return isinstance(truth, int) and not isinstance(truth, bool) and 0 <= truth < len(spec["options"])


def check(leaf: str, row: dict) -> list[str]:
    """Problems with one authored line (empty = fine)."""
    spec = TEMPLATES[leaf].get(row.get("template"))
    if spec is None:
        return [f"unknown template {row.get('template')!r}"]
    errs = []
    state = row.get("state")
    if not isinstance(state, dict):
        return ["state must be an object"]
    missing = [k for k in spec["keys"] if k not in state]
    if missing:
        errs.append(f"state missing {missing}")
    if not _truth_ok(spec, row.get("truth")):
        errs.append(f"bad truth {row.get('truth')!r}")
    n = len(json.dumps(state, ensure_ascii=False))
    if not MIN_CHARS <= n <= MAX_CHARS:
        errs.append(f"state is {n} chars")
    if not isinstance(row.get("borderline"), bool):
        errs.append("borderline must be true/false")
    return errs


def fetch(raw_dir: Path) -> None:
    """Nothing to download: the inputs are authored in the repo."""


def normalize(raw_dir: Path) -> Iterator[Question]:
    for leaf, templates in TEMPLATES.items():
        path = INPUTS / f"{leaf.rsplit('.', 1)[-1]}.jsonl"
        if not path.exists():
            print(f"{NAME}: missing {path}", file=sys.stderr)
            continue
        seen: set[str] = set()
        for ln, line in enumerate(path.read_text().splitlines(), 1):
            if not line.strip():
                continue
            row = json.loads(line)
            errs = check(leaf, row)
            if row.get("id") in seen:
                errs.append(f"duplicate id {row.get('id')}")
            seen.add(row.get("id"))
            spec = templates.get(row.get("template")) or next(iter(templates.values()))
            if errs:
                print(f"{NAME}: {path.name}:{ln} {row.get('id')}: {'; '.join(errs)}", file=sys.stderr)
            yield Question(
                text="" if errs else spec["text"],  # an empty text fails validation, so it counts as rejected
                primitive=spec["primitive"], hemisphere="machine", origin="synthetic", source=NAME,
                options=spec["options"], state=row.get("state"), shape=spec["shape"], node_hint=leaf,
                template_id=f"ts_auth.{leaf.rsplit('.', 1)[-1]}.{row.get('template')}",
                source_item_id=f"{path.stem}:{row.get('id')}", license=LICENSE, truth=row.get("truth"),
                meta={"synthetic_input": True, "truth_source": "author", "borderline": row.get("borderline"),
                      "author_rationale": row.get("why")},
            )
