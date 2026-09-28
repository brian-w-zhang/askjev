"""Is it fair? Kahneman, Knetsch & Thaler's price and wage scenarios (1986).

Human data: Kahneman, Knetsch & Thaler 1986, "Fairness as a Constraint on Profit Seeking: Entitlements in the Market",
American Economic Review 76(4):728-741. Telephone surveys of Toronto and Vancouver residents; each scenario was rated
Completely Fair / Acceptable / Unfair / Very Unfair, and the paper reports only the two grouped shares (acceptable vs
unfair) with N. Items and shares transcribed from the paper text (question numbers as in the paper), checked against
the PDF; the shares are kept in meta, not as a distribution over the four options. fetch() is a no-op.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterator

from askjev.model import Question

NAME = "fair_prices"
NODE = "self.values.fairness_justice.fair_prices"
LICENSE = "Scenario wording and results quoted from Kahneman, Knetsch & Thaler 1986 (AER) for research use"
OPTIONS = {"completely_fair": "Completely fair", "acceptable": "Acceptable", "unfair": "Unfair", "very_unfair": "Very unfair"}
STEM = "Please rate this action as completely fair, acceptable, unfair or very unfair."
SHOP = ("A small photocopying shop has one employee who has worked in the shop for six months and earns $9 per hour. "
        "Business continues to be satisfactory, but a factory in the area has closed and unemployment has increased. "
        "Other small shops have now hired reliable workers at $7 an hour to perform jobs similar to those done by the "
        "photocopy shop employee. ")
CAR = "A shortage has developed for a popular model of automobile, and customers must now wait two months for delivery. "
COMPANY = "A small company employs several people. "
WORKERS = ("A small company employs several workers and has been paying them average wages. There is severe unemployment "
           "in the area and the company could easily replace its current employees with good workers at a lower wage. ")
TABLES = "A small factory produces tables and sells all that it can make at $200 each. "
DOLL = ("A store has been sold out of the popular Cabbage Patch dolls for a month. A week before Christmas a single doll "
        "is discovered in a storeroom. The managers know that many customers would like to buy the doll. They announce "
        "over the store's public address system that the doll will be sold by auction to the customer who offers to pay "
        "the most.")

# (paper question, scenario, N, share acceptable, pair id for framing comparisons)
ITEMS = [
    ("1", "A hardware store has been selling snow shovels for $15. The morning after a large snowstorm, the store raises "
          "the price to $20.", 107, 0.18, None),
    ("2A", SHOP + "The owner of the photocopying shop reduces the employee's wage to $7.", 98, 0.17, "incumbent_vs_new"),
    ("2B", SHOP + "The current employee leaves, and the owner decides to pay a replacement $7 an hour.", 125, 0.73, "incumbent_vs_new"),
    ("3", "A house painter employs two assistants and pays them $9 per hour. The painter decides to quit house painting "
          "and go into the business of providing landscape services, where the going wage is lower. He reduces the "
          "workers' wages to $7 per hour for the landscaping work.", 94, 0.63, None),
    ("4A", "A company is making a small profit. It is located in a community experiencing a recession with substantial "
           "unemployment but no inflation. There are many workers anxious to work at the company. The company decides "
           "to decrease wages and salaries 7% this year.", 125, 0.38, "cut_vs_raise"),
    ("4B", "A company is making a small profit. It is located in a community experiencing a recession with substantial "
           "unemployment and inflation of 12%. There are many workers anxious to work at the company. The company "
           "decides to increase salaries only 5% this year.", 129, 0.78, "cut_vs_raise"),
    ("5A", CAR + "A dealer has been selling these cars at list price. Now the dealer prices this model at $200 above list "
                 "price.", 130, 0.29, "surcharge_vs_discount"),
    ("5B", CAR + "A dealer has been selling these cars at a discount of $200 below list price. Now the dealer sells this "
                 "model only at list price.", 123, 0.58, "surcharge_vs_discount"),
    ("6A", COMPANY + "The workers' incomes have been about average for the community. In recent months, business for the "
                     "company has not increased as it had before. The owners reduce the workers' wages by 10 percent for "
                     "the next year.", 100, 0.39, "wage_vs_bonus"),
    ("6B", COMPANY + "The workers have been receiving a 10 percent annual bonus each year and their total incomes have been "
                     "about average for the community. In recent months, business for the company has not increased as it "
                     "had before. The owners eliminate the workers' bonus for the year.", 98, 0.80, "wage_vs_bonus"),
    ("7", "Suppose that, due to a transportation mixup, there is a local shortage of lettuce and the wholesale price has "
          "increased. A local grocer has bought the usual quantity of lettuce at a price that is 30 cents per head higher "
          "than normal. The grocer raises the price of lettuce to customers by 30 cents per head.", 101, 0.79, None),
    ("8", "A landlord owns and rents out a single small house to a tenant who is living on a fixed income. A higher rent "
          "would mean the tenant would have to move. Other small rental houses are available. The landlord's costs have "
          "increased substantially over the past year and the landlord raises the rent to cover the cost increases when "
          "the tenant's lease is due for renewal.", 151, 0.75, None),
    ("9A", WORKERS + "The company has been making money. The owners reduce the current workers' wages by 5 percent.", 195, 0.23, "profit_vs_loss"),
    ("9B", WORKERS + "The company has been losing money. The owners reduce the current workers' wages by 5 percent.", 195, 0.68, "profit_vs_loss"),
    ("10", "A grocery store has several months supply of peanut butter in stock which it has on the shelves and in the "
           "storeroom. The owner hears that the wholesale price of peanut butter has increased and immediately raises the "
           "price on the current stock of peanut butter.", 147, 0.21, None),
    ("11A", TABLES + "Because of changes in the price of materials, the cost of making each table has recently decreased "
                     "by $40. The factory reduces its price for the tables by $20.", 102, 0.79, None),
    ("11B", TABLES + "Because of changes in the price of materials, the cost of making each table has recently decreased "
                     "by $20. The factory does not change its price for the tables.", 100, 0.53, None),
    ("12", "A severe shortage of Red Delicious apples has developed in a community and none of the grocery stores or "
           "produce markets have any of this type of apple on their shelves. Other varieties of apples are plentiful in all "
           "of the stores. One grocer receives a single shipment of Red Delicious apples at the regular wholesale cost and "
           "raises the retail price of these Red Delicious apples by 25% over the regular price.", 102, 0.37, None),
    ("13", "A grocery chain has stores in many communities. Most of them face competition from other groceries. In one "
           "community the chain has no competition. Although its costs and volume of sales are the same there as "
           "elsewhere, the chain sets prices that average 5 percent higher than in other communities.", 101, 0.24, None),
    ("14", "A landlord rents out a small house. When the lease is due for renewal, the landlord learns that the tenant has "
           "taken a job very close to the house and is therefore unlikely to move. The landlord raises the rent $40 per "
           "month more than he was planning to do.", 157, 0.09, None),
    ("15", DOLL, 101, 0.26, "auction_unicef"),
    ("15U", DOLL + " The proceeds will go to UNICEF.", None, 0.79, "auction_unicef"),
    ("16", "A business in a community with high unemployment needs to hire a new computer operator. Four candidates are "
           "judged to be completely qualified for the job. The manager asks the candidates to state the lowest salary "
           "they would be willing to accept, and then hires the one who demands the lowest salary.", 154, 0.36, None),
]


def fetch(raw_dir: Path) -> None:
    """Transcribed from the paper (data/raw/fair_prices/kkt1986.pdf was used to check); nothing to download."""


def normalize(raw_dir: Path) -> Iterator[Question]:
    for q, text, n, acc, pair in ITEMS:
        yield Question(
            text=f"{text} {STEM}", primitive="choice", hemisphere="self", kind="values", origin="dataset", source=NAME,
            options=OPTIONS, node_hint=NODE, license=LICENSE, source_item_id=f"KKT1986 Q{q}",
            meta={"experiment": "fair_prices", "question": q, "people_acceptable": acc, "n": n, "pair": pair,
                  "people_note": "UNICEF version: the paper reports unfair judgments falling from 74% to 21%; N not given"
                  if q == "15U" else None})
