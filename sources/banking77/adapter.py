"""BANKING77 (PolyAI): online-banking customer queries labelled with one of 77 intents.

Template "banking77.intent": one Choice per query over the 77 intents, truth = the dataset label.
Source file: the test split CSV from PolyAI's GitHub repo (the HF dataset is script-based and has no
parquet export).
"""

from __future__ import annotations

import csv
import random
from collections import defaultdict
from pathlib import Path
from typing import Iterator

import httpx

from askjev.model import Question
from askjev.sampling import env_int, hash_order

NAME = "banking77"
URL = "https://raw.githubusercontent.com/PolyAI-LDN/task-specific-datasets/master/banking_data/test.csv"
TARGET = env_int("TARGET_BANKING77", 800)  # Phase 6: 3,000
EXTRA = env_int("EXTRA_BANKING77", 0)  # per secondary template; Phase 6: 1,500
SEED = 77
TEXT = "What is the customer asking the bank about in `message`?"
LICENSE = "CC-BY-4.0"

# Secondary templates over the same messages (no truth: the dataset labels only the intent).
URGENCY_TEXT = "How urgent is `message` for the customer?"
URGENCY_LEVELS = [
    "A general question about how something works that the customer can wait days to have answered",
    "A request or minor problem that is inconvenient but can wait a day or two",
    "A problem that blocks something the customer needs to do today, such as paying or withdrawing cash",
    "Money may be leaving the account or the card or account may be in someone else's hands right now",
]
MONEY_LEFT_TEXT = "Does `message` report a problem with money that already left the account?"
MONEY_LEFT = {
    "true": "The customer describes a payment, transfer, withdrawal or charge that has already been taken "
    "from their account and something is wrong with it",
    "false": "The message is a question, a request, or a problem with money coming in or not yet sent",
}

# key (Jev sees it) -> short description. Keys are the dataset labels, lowercased, with the stray
# "?" dropped from reverted_card_payment?.
INTENTS: dict[str, str] = {
    "activate_my_card": "How to activate a card they have received",
    "age_limit": "The minimum age to open or use an account",
    "apple_pay_or_google_pay": "Using the card with Apple Pay or Google Pay",
    "atm_support": "Which ATMs the card works at",
    "automatic_top_up": "Setting up or using automatic top-ups",
    "balance_not_updated_after_bank_transfer": "A bank transfer in that has not shown up in the balance",
    "balance_not_updated_after_cheque_or_cash_deposit": "A cheque or cash deposit that has not shown up in the balance",
    "beneficiary_not_allowed": "Being unable to add or pay a beneficiary",
    "cancel_transfer": "Cancelling a transfer they made",
    "card_about_to_expire": "A card that is about to expire and its replacement",
    "card_acceptance": "Where the card is accepted",
    "card_arrival": "A new card that has not arrived yet",
    "card_delivery_estimate": "How long card delivery takes",
    "card_linking": "Linking an existing card to the account or app",
    "card_not_working": "A card that is not working",
    "card_payment_fee_charged": "A fee charged on a card payment",
    "card_payment_not_recognised": "A card payment they do not recognise",
    "card_payment_wrong_exchange_rate": "A card payment converted at the wrong exchange rate",
    "card_swallowed": "An ATM that kept (swallowed) the card",
    "cash_withdrawal_charge": "A fee charged on a cash withdrawal",
    "cash_withdrawal_not_recognised": "A cash withdrawal they do not recognise",
    "change_pin": "Changing the card PIN",
    "compromised_card": "A card that may have been compromised or used fraudulently",
    "contactless_not_working": "Contactless payments not working",
    "country_support": "Which countries the service is available in",
    "declined_card_payment": "A card payment that was declined",
    "declined_cash_withdrawal": "A cash withdrawal that was declined",
    "declined_transfer": "A transfer that was declined",
    "direct_debit_payment_not_recognised": "A direct debit they do not recognise",
    "disposable_card_limits": "Limits on disposable virtual cards",
    "edit_personal_details": "Changing personal details on the account",
    "exchange_charge": "Fees for exchanging currency",
    "exchange_rate": "What exchange rate is used",
    "exchange_via_app": "Exchanging currency in the app",
    "extra_charge_on_statement": "An unexpected extra charge on the statement",
    "failed_transfer": "A transfer that failed",
    "fiat_currency_support": "Which currencies can be held or exchanged",
    "get_disposable_virtual_card": "Getting a disposable virtual card",
    "get_physical_card": "Getting a physical card",
    "getting_spare_card": "Getting an extra or spare card",
    "getting_virtual_card": "Getting a virtual card",
    "lost_or_stolen_card": "A lost or stolen card",
    "lost_or_stolen_phone": "A lost or stolen phone with the app on it",
    "order_physical_card": "Ordering a physical card",
    "passcode_forgotten": "A forgotten app passcode",
    "pending_card_payment": "A card payment that is still pending",
    "pending_cash_withdrawal": "A cash withdrawal that is still pending",
    "pending_top_up": "A top-up that is still pending",
    "pending_transfer": "A transfer that is still pending",
    "pin_blocked": "A PIN that has been blocked",
    "receiving_money": "How to receive money into the account",
    "refund_not_showing_up": "A refund from a merchant that has not appeared",
    "request_refund": "Asking for a refund",
    "reverted_card_payment": "A card payment that was reverted",
    "supported_cards_and_currencies": "Which cards and currencies are supported",
    "terminate_account": "Closing the account",
    "top_up_by_bank_transfer_charge": "Fees for topping up by bank transfer",
    "top_up_by_card_charge": "Fees for topping up by card",
    "top_up_by_cash_or_cheque": "Topping up with cash or a cheque",
    "top_up_failed": "A top-up that failed",
    "top_up_limits": "Limits on top-ups",
    "top_up_reverted": "A top-up that was reverted",
    "topping_up_by_card": "How to top up with a card",
    "transaction_charged_twice": "A transaction charged twice",
    "transfer_fee_charged": "A fee charged on a transfer",
    "transfer_into_account": "How to transfer money into the account",
    "transfer_not_received_by_recipient": "A transfer the recipient has not received",
    "transfer_timing": "How long a transfer takes",
    "unable_to_verify_identity": "Being unable to complete identity verification",
    "verify_my_identity": "How to verify their identity",
    "verify_source_of_funds": "Verifying the source of their funds",
    "verify_top_up": "Verifying a top-up",
    "virtual_card_not_working": "A virtual card that is not working",
    "visa_or_mastercard": "Whether the card is Visa or Mastercard",
    "why_verify_identity": "Why identity verification is needed",
    "wrong_amount_of_cash_received": "An ATM that dispensed the wrong amount of cash",
    "wrong_exchange_rate_for_cash_withdrawal": "A cash withdrawal converted at the wrong exchange rate",
}


def _key(label: str) -> str:
    return label.lower().rstrip("?")


def fetch(raw_dir: Path) -> None:
    out = raw_dir / "test.csv"
    if out.exists():
        return
    r = httpx.get(URL, follow_redirects=True, timeout=60)
    r.raise_for_status()
    out.write_bytes(r.content)


def normalize(raw_dir: Path) -> Iterator[Question]:
    rows = list(csv.DictReader(open(raw_dir / "test.csv", newline="", encoding="utf-8")))
    by_label: dict[str, list[tuple[int, str]]] = defaultdict(list)
    for i, r in enumerate(rows):
        by_label[_key(r["category"])].append((i, r["text"].strip()))
    assert set(by_label) == set(INTENTS), set(by_label) ^ set(INTENTS)

    rng = random.Random(SEED)
    labels = sorted(by_label)
    for lab in labels:
        rng.shuffle(by_label[lab])
    # Stratified: round-robin across intents until TARGET (≈10 per intent, first 30 intents get 11).
    picked: list[tuple[str, int, str]] = []
    seen_text: set[str] = set()
    cursor = {lab: 0 for lab in labels}
    while len(picked) < TARGET:
        progressed = False
        for lab in labels:
            if len(picked) >= TARGET:
                break
            pool = by_label[lab]
            while cursor[lab] < len(pool):
                i, text = pool[cursor[lab]]
                cursor[lab] += 1
                if text.lower() not in seen_text:
                    seen_text.add(text.lower())
                    picked.append((lab, i, text))
                    progressed = True
                    break
        if not progressed:
            break

    for lab, i, text in picked:
        yield Question(
            text=TEXT,
            primitive="choice",
            hemisphere="machine",
            origin="dataset",
            source=NAME,
            options=INTENTS,
            state={"message": text[:1500]},
            shape="route",
            node_hint="machine.support.intent_topic",
            template_id="banking77.intent",
            source_item_id=f"test:{i}",
            license=LICENSE,
            truth=lab,
            meta={"split": "test", "label_raw": rows[i]["category"]},
        )

    # Secondary templates: the first EXTRA picked messages in a per-template hash order.
    for tid, prim, text, options, shape, node in (
        ("banking77.urgency", "score", URGENCY_TEXT, URGENCY_LEVELS, "score", "machine.support.urgency_frustration"),
        ("banking77.money_left", "noul", MONEY_LEFT_TEXT, MONEY_LEFT, "detect", "machine.support.churn_refund"),
    ):
        sub = sorted(hash_order(picked, lambda x: x[1], tid)[:EXTRA], key=lambda x: x[1])
        for lab, i, msg in sub:
            yield Question(
                text=text,
                primitive=prim,
                hemisphere="machine",
                origin="dataset",
                source=NAME,
                options=options,
                state={"message": msg[:1500]},
                shape=shape,
                node_hint=node,
                template_id=tid,
                source_item_id=f"test:{i}",
                license=LICENSE,
                truth=None,
                meta={"split": "test", "intent": lab},
            )
