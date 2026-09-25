"""FiNER-139 (Loukas et al. 2022): sentences from SEC 10-K/10-Q filings in which the numbers are tagged with the
XBRL (US-GAAP) concept the filing company itself attached to them.

Template "finer_xbrl.concept": Choice "Which XBRL concept does the number `value` in `sentence` report?" over the
30 most frequent concepts (readable keys, US-GAAP element names in meta), truth = the filer's tag. Only numbers
that occur once in their sentence, are tagged with one of the 30 concepts, and whose unit agrees with the concept
(% for rates, $ for amounts, years/months for periods, neither for counts; this drops FiNER's misaligned tags);
balanced across concepts.
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

NAME = "finer_xbrl"
URL = "https://huggingface.co/api/datasets/nlpaueb/finer-139/parquet/finer-139/test/0.parquet"
INFO_URL = "https://datasets-server.huggingface.co/info?dataset=nlpaueb/finer-139"
TARGET = env_int("TARGET_FINER_XBRL", 2500)
LICENSE = "CC-BY-SA-4.0"
TEXT = "Which XBRL concept does the number `value` in `sentence` report?"

# US-GAAP element -> (key, description). The 30 most frequent FiNER-139 concepts in the test split.
CONCEPTS = {
    "DebtInstrumentInterestRateStatedPercentage": ("debt_stated_interest_rate", "The stated (coupon) interest rate of a debt instrument"),
    "LineOfCreditFacilityMaximumBorrowingCapacity": ("credit_facility_max_capacity", "The maximum amount that can be borrowed under a line of credit facility"),
    "DebtInstrumentBasisSpreadOnVariableRate1": ("debt_variable_rate_spread", "The margin added to a reference rate (such as LIBOR or the prime rate) on variable-rate debt"),
    "DebtInstrumentFaceAmount": ("debt_face_amount", "The face (principal) amount of a debt instrument when issued"),
    "AllocatedShareBasedCompensationExpense": ("share_based_comp_expense", "Share-based compensation expense recognized in the period"),
    "AntidilutiveSecuritiesExcludedFromComputationOfEarningsPerShareAmount": ("antidilutive_securities_excluded", "Securities left out of diluted earnings per share because they would be antidilutive"),
    "ConcentrationRiskPercentage1": ("concentration_risk_percentage", "The share of a total (such as revenue or receivables) coming from one customer, supplier or group"),
    "DerivativeNotionalAmount": ("derivative_notional_amount", "The notional amount of a derivative contract such as a swap or forward"),
    "EffectiveIncomeTaxRateContinuingOperations": ("effective_tax_rate", "The effective income tax rate on continuing operations"),
    "AmortizationOfIntangibleAssets": ("intangible_amortization", "Amortization expense of intangible assets"),
    "EquityMethodInvestmentOwnershipPercentage": ("equity_method_ownership_pct", "The ownership percentage in an investee accounted for by the equity method"),
    "IncomeTaxExpenseBenefit": ("income_tax_expense", "Income tax expense or benefit for the period"),
    "EmployeeServiceShareBasedCompensationNonvestedAwardsTotalCompensationCostNotYetRecognizedPeriodForRecognition1": ("unrecognized_comp_cost_period", "The period over which not-yet-recognized share-based compensation cost will be recognized"),
    "LineOfCredit": ("line_of_credit_outstanding", "The amount outstanding (borrowed) under a line of credit"),
    "ShareBasedCompensationArrangementByShareBasedPaymentAwardEquityInstrumentsOtherThanOptionsGrantsInPeriod": ("non_option_awards_granted", "The number of equity awards other than options (such as restricted stock units) granted in the period"),
    "NumberOfReportableSegments": ("reportable_segments_count", "The number of reportable segments"),
    "ShareBasedCompensationArrangementByShareBasedPaymentAwardAwardVestingPeriod1": ("award_vesting_period", "The vesting period of a share-based award"),
    "EmployeeServiceShareBasedCompensationNonvestedAwardsTotalCompensationCostNotYetRecognized": ("unrecognized_comp_cost", "Share-based compensation cost for unvested awards not yet recognized"),
    "DebtInstrumentCarryingAmount": ("debt_carrying_amount", "The carrying amount of a debt instrument on the balance sheet"),
    "Goodwill": ("goodwill", "The amount of goodwill"),
    "LettersOfCreditOutstandingAmount": ("letters_of_credit_outstanding", "The amount of letters of credit outstanding"),
    "LongTermDebt": ("long_term_debt", "Total long-term debt"),
    "RestructuringCharges": ("restructuring_charges", "Restructuring charges recognized"),
    "NumberOfRealEstateProperties": ("real_estate_properties_count", "The number of real estate properties"),
    "LineOfCreditFacilityRemainingBorrowingCapacity": ("credit_facility_remaining_capacity", "The amount still available to borrow under a line of credit facility"),
    "RevenueFromContractWithCustomerExcludingAssessedTax": ("revenue", "Revenue from contracts with customers"),
    "ContractWithCustomerLiabilityRevenueRecognized": ("deferred_revenue_recognized", "Revenue recognized in the period that had been deferred as a contract liability"),
    "DebtInstrumentInterestRateEffectivePercentage": ("debt_effective_interest_rate", "The effective interest rate of a debt instrument"),
    "CashAndCashEquivalentsFairValueDisclosure": ("cash_equivalents_fair_value", "The fair value of cash and cash equivalents"),
    "StockRepurchaseProgramAuthorizedAmount1": ("buyback_authorized_amount", "The amount authorized for a stock repurchase program"),
}
PCT = {"DebtInstrumentInterestRateStatedPercentage", "DebtInstrumentBasisSpreadOnVariableRate1", "ConcentrationRiskPercentage1",
       "EffectiveIncomeTaxRateContinuingOperations", "EquityMethodInvestmentOwnershipPercentage", "DebtInstrumentInterestRateEffectivePercentage"}
DURATION = {"EmployeeServiceShareBasedCompensationNonvestedAwardsTotalCompensationCostNotYetRecognizedPeriodForRecognition1",
            "ShareBasedCompensationArrangementByShareBasedPaymentAwardAwardVestingPeriod1"}
COUNT = {"AntidilutiveSecuritiesExcludedFromComputationOfEarningsPerShareAmount", "NumberOfReportableSegments",
         "ShareBasedCompensationArrangementByShareBasedPaymentAwardEquityInstrumentsOtherThanOptionsGrantsInPeriod",
         "NumberOfRealEstateProperties"}
NUM = re.compile(r"^\d[\d,]*(\.\d+)?$")


def fetch(raw_dir: Path) -> None:
    for name, url in (("test.parquet", URL), ("info.json", INFO_URL)):
        out = raw_dir / name
        if out.exists():
            continue
        r = httpx.get(url, follow_redirects=True, timeout=300)
        r.raise_for_status()
        out.write_bytes(r.content)


def _detok(tokens: list[str]) -> str:
    s = " ".join(tokens)
    s = re.sub(r"\s+([,.;:%)\]])", r"\1", s)
    s = re.sub(r"([($\[])\s+", r"\1", s)
    return re.sub(r"\s*([’'])\s+s\b", r"\1s", s)


def _consistent(concept: str, tokens: list[str], i: int) -> bool:
    """Drop tags whose surface form contradicts the concept's unit (FiNER has some misaligned tags)."""
    prev = tokens[i - 1] if i else ""
    nxt = tokens[i + 1].lower() if i + 1 < len(tokens) else ""
    if concept in PCT:
        return nxt in ("%", "percent")
    if concept in DURATION:
        return nxt.rstrip("s") in ("year", "month", "day") or nxt.startswith(("year", "month"))
    if concept in COUNT:
        return prev != "$" and nxt not in ("%", "percent")
    return prev == "$"  # money amounts


def normalize(raw_dir: Path) -> Iterator[Question]:
    names = json.loads((raw_dir / "info.json").read_text())["dataset_info"]["finer-139"]["features"]["ner_tags"]["feature"]["names"]
    df = pl.read_parquet(raw_dir / "test.parquet")
    by_concept: dict[str, list] = defaultdict(list)
    seen_sent: set[str] = set()
    for sid, tokens, tags in df.select("id", "tokens", "ner_tags").rows():
        sent = _detok(tokens)
        if len(sent) > 1200 or len(tokens) < 8 or sent in seen_sent:
            continue
        seen_sent.add(sent)
        for i, (tok, t) in enumerate(zip(tokens, tags)):
            name = names[t]
            if not name.startswith("B-") or name[2:] not in CONCEPTS or not NUM.match(tok):
                continue
            if sum(1 for x in tokens if x == tok) != 1 or not _consistent(name[2:], tokens, i):
                continue
            by_concept[name[2:]].append((sid, i, tok, sent))
    per = -(-TARGET // len(CONCEPTS))
    picked = []
    for c in CONCEPTS:
        # at most one question per sentence
        used_s: set[int] = set()
        for it in hash_order(by_concept[c], lambda x: (x[0], x[1]), f"finer.{c}"):
            if len([p for p in picked if p[0] == c]) >= per:
                break
            if it[0] in used_s:
                continue
            used_s.add(it[0])
            picked.append((c, *it))
    picked = hash_order(picked, lambda x: (x[1], x[2]), "finer.cap")[:TARGET]
    options = {k: d for k, d in CONCEPTS.values()}
    for c, sid, i, tok, sent in sorted(picked, key=lambda x: (x[1], x[2])):
        yield Question(
            text=TEXT,
            primitive="choice",
            hemisphere="machine",
            origin="dataset",
            source=NAME,
            options=options,
            state={"sentence": sent, "value": tok},
            shape="extract",
            node_hint="machine.finance",
            template_id="finer_xbrl.concept",
            source_item_id=f"test:{sid}:{i}",
            license=LICENSE,
            truth=CONCEPTS[c][0],
            meta={"us_gaap": c},
        )
