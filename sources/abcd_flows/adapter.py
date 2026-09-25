"""ABCD, Action-Based Conversations Dataset (Chen et al. 2021, ASAPP): 10k customer-service chats between two
crowdworkers, one playing a customer of an online clothing store with a given scenario, the other a trained
agent following the store's guidelines. Each chat is labelled with the scenario's flow (10) and subflow (55).

Templates:
- "abcd_flows.flow": Choice "What does the customer need help with in `conversation`?" over the 10 flows,
  using only the opening of the chat (turns before the agent's first system action). Balanced across flows.
- "abcd_flows.subflow": Choice "Which request does the customer make in `conversation`?" given the `topic` (the
  flow), options = that flow's subflows, using the whole chat (agent system actions removed). Balanced.
Chats are disjoint between the two templates.
"""

from __future__ import annotations

import gzip
import json
from collections import defaultdict
from pathlib import Path
from typing import Iterator

import httpx

from askjev.model import Question
from askjev.sampling import env_int, hash_order

NAME = "abcd_flows"
URL = "https://raw.githubusercontent.com/asappresearch/abcd/master/data/abcd_v1.1.json.gz"
TARGET_FLOW = env_int("TARGET_ABCD_FLOW", 2500)
TARGET_SUB = env_int("TARGET_ABCD_SUBFLOW", 1500)
MAX_CHARS = 1500
LICENSE = "MIT"
FLOW_TEXT = "What does the customer need help with in `conversation`?"
SUB_TEXT = "Which request does the customer make in `conversation` about `topic`?"
FLOWS = {
    "account_access": "Getting into their account: a forgotten username or password, or two-factor authentication",
    "manage_account": "Changing account details or checking a change to the account (address, name, phone, payment method, credits)",
    "order_issue": "An existing order: its status, fees, payment, quantity, or changing or cancelling it",
    "product_defect": "A faulty or unsuitable item they want to return or get refunded, or the status of a refund",
    "purchase_dispute": "A disputed charge or price: a price drop or competitor price, a promo code, out-of-stock items, or billing for an item returned or never bought",
    "shipping_issue": "Shipping: where a package is, changing shipping, a missing package, or shipping cost",
    "single_item_query": "A question about one product (boots, shirts, jeans, jackets)",
    "storewide_query": "A general question about the store: pricing, membership levels, timing or policies",
    "subscription_inquiry": "Their premium subscription: whether it is active, what is due and when, paying, extending or disputing the bill",
    "troubleshoot_site": "A problem using the website: card entry, shopping cart, search results or slow pages",
}
SUBFLOWS = {
    "account_access": {
        "recover_username": "They forgot their username",
        "recover_password": "They forgot their password",
        "reset_2fa": "They need two-factor authentication reset",
    },
    "manage_account": {
        "status_service_added": "Asking about a service that was added to the account",
        "status_service_removed": "Asking about a service that was removed from the account",
        "status_shipping_question": "Asking about shipping settings on the account",
        "status_credit_missing": "A promised store credit is missing from the account",
        "manage_change_address": "Changing the address on the account",
        "manage_change_name": "Changing the name on the account",
        "manage_change_phone": "Changing the phone number on the account",
        "manage_payment_method": "Changing the payment method on the account",
    },
    "order_issue": {
        "status_mystery_fee": "An unexpected fee on the order",
        "status_delivery_time": "When the order will arrive",
        "status_payment_method": "Which payment method was used or a payment problem on the order",
        "status_quantity": "The quantity of an item in the order is wrong",
        "manage_upgrade": "Upgrading the shipping or order",
        "manage_downgrade": "Downgrading the shipping or order",
        "manage_create": "Placing a new order",
        "manage_cancel": "Cancelling the order",
    },
    "product_defect": {
        "refund_initiate": "Starting a refund",
        "refund_update": "Changing a refund already requested",
        "refund_status": "Checking the status of a refund",
        "return_stain": "Returning an item that arrived stained",
        "return_color": "Returning an item in the wrong color",
        "return_size": "Returning an item that is the wrong size",
    },
    "purchase_dispute": {
        "bad_price_competitor": "A competitor sells the item for less",
        "bad_price_yesterday": "The price dropped right after they bought it",
        "out_of_stock_general": "Items in general are out of stock",
        "out_of_stock_one_item": "One specific item is out of stock",
        "promo_code_invalid": "A promo code does not work",
        "promo_code_out_of_date": "A promo code has expired",
        "mistimed_billing_already_returned": "Billed for an item already returned",
        "mistimed_billing_never_bought": "Billed for an item never bought",
    },
    "shipping_issue": {
        "status": "Where the package is or whether it has shipped",
        "manage": "Changing the shipping method or address for the order",
        "missing": "A package or item that never arrived",
        "cost": "How much shipping costs",
    },
    "single_item_query": {
        "boots": "A question about boots",
        "shirt": "A question about a shirt",
        "jeans": "A question about jeans",
        "jacket": "A question about a jacket",
    },
    "storewide_query": {
        "pricing": "How prices work at the store",
        "membership": "Membership levels and their benefits",
        "timing": "How long things take, such as delivery or promo code validity",
        "policy": "Store policies such as returns or exchanges",
    },
    "subscription_inquiry": {
        "status_active": "Whether the subscription is active",
        "status_due_amount": "How much is due on the subscription",
        "status_due_date": "When the subscription payment is due",
        "manage_pay_bill": "Paying the subscription bill",
        "manage_extension": "Getting more time to pay the subscription",
        "manage_dispute_bill": "Disputing a subscription charge",
    },
    "troubleshoot_site": {
        "credit_card": "The site will not accept their credit card",
        "shopping_cart": "A problem with the shopping cart",
        "search_results": "Search results are wrong or missing",
        "slow_speed": "The site is slow",
    },
}


def fetch(raw_dir: Path) -> None:
    out = raw_dir / "abcd_v1.1.json.gz"
    if out.exists():
        return
    r = httpx.get(URL, follow_redirects=True, timeout=300)
    r.raise_for_status()
    out.write_bytes(r.content)


def _render(turns: list[tuple[str, str]]) -> str:
    out = []
    for sp, t in turns:
        out.append(f"{sp}: {' '.join(t.split())}")
    s = "\n".join(out)
    return s if len(s) <= MAX_CHARS else s[:MAX_CHARS].rsplit(" ", 1)[0] + " ..."


def normalize(raw_dir: Path) -> Iterator[Question]:
    data = json.loads(gzip.open(raw_dir / "abcd_v1.1.json.gz").read())
    convs = []
    seen_open: set[str] = set()
    for split in ("train", "dev", "test"):
        for c in data[split]:
            flow, sub = c["scenario"]["flow"], c["scenario"]["subflow"]
            turns = [(sp, t) for sp, t in c["original"]]
            opening = []
            for sp, t in turns:
                if sp == "action":
                    break
                opening.append((sp, t))
            key = _render(opening).lower()
            if not any(sp == "customer" for sp, _ in opening) or key in seen_open:
                continue
            seen_open.add(key)
            full = [(sp, t) for sp, t in turns if sp != "action"]
            convs.append((f"{split}:{c['convo_id']}", flow, sub, opening, full))
    convs = hash_order(convs, lambda x: x[0], "abcd.v1")
    by_flow: dict[str, list] = defaultdict(list)
    for c in convs:
        by_flow[c[1]].append(c)
    per = TARGET_FLOW // len(FLOWS)
    flow_items = [c for f in FLOWS for c in by_flow[f][:per]]
    used = {c[0] for c in flow_items}
    by_sub: dict[tuple[str, str], list] = defaultdict(list)
    for c in convs:
        if c[0] not in used and c[2] in SUBFLOWS.get(c[1], {}):
            by_sub[(c[1], c[2])].append(c)
    # Round-robin over the 55 subflows until TARGET_SUB (near-balanced; small subflows run out first).
    keys = sorted(by_sub)
    sub_items = []
    depth = 0
    while len(sub_items) < TARGET_SUB and any(depth < len(by_sub[k]) for k in keys):
        for k in keys:
            if depth < len(by_sub[k]) and len(sub_items) < TARGET_SUB:
                sub_items.append(by_sub[k][depth])
        depth += 1

    for cid, flow, sub, opening, _full in sorted(flow_items):
        yield Question(
            text=FLOW_TEXT,
            primitive="choice",
            hemisphere="machine",
            origin="dataset",
            source=NAME,
            options=FLOWS,
            state={"conversation": _render(opening)},
            shape="route",
            node_hint="machine.support.intent_topic",
            template_id="abcd_flows.flow",
            source_item_id=cid,
            license=LICENSE,
            truth=flow,
            meta={"subflow": sub},
        )
    for cid, flow, sub, _opening, full in sorted(sub_items):
        yield Question(
            text=SUB_TEXT,
            primitive="choice",
            hemisphere="machine",
            origin="dataset",
            source=NAME,
            options=SUBFLOWS[flow],
            state={"topic": FLOWS[flow], "conversation": _render(full)},
            shape="classify",
            node_hint="machine.support.intent_topic",
            template_id="abcd_flows.subflow",
            source_item_id=cid,
            license=LICENSE,
            truth=sub,
            meta={"flow": flow},
        )
