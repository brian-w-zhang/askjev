"""What jobs are like, per the people who do them: O*NET Work Context (research pass 2, idea 22).

Human data: O*NET 29.0 Work Context (US Department of Labor, CC BY 4.0). Incumbent workers in each occupation answer
how often they deal with angry people, work outdoors, face time pressure, and so on; O*NET publishes the share of
workers choosing each of five answers (scale CXP). Jev gets the same five answers as described levels, asked about
the occupation. 12 context items x 46 well-known occupations.
"""

from __future__ import annotations

import csv
import urllib.request
from pathlib import Path
from typing import Iterator

from askjev.model import HumanDist, Question

NAME = "onet_context"
NODE = "world.money.careers.work_context"
LICENSE = "CC BY 4.0 (O*NET 29.0 Database, U.S. Department of Labor, Employment and Training Administration)"
BASE = "https://www.onetcenter.org/dl_files/database/db_29_0_text/"
FILES = {"work_context.txt": "Work%20Context.txt", "wc_categories.txt": "Work%20Context%20Categories.txt",
         "occupations.txt": "Occupation%20Data.txt"}

ITEMS = {  # element id: question template ({a} = "a nurse")
    "4.C.1.d.2": "How often does {a} have to deal with unpleasant or angry people at work?",
    "4.C.1.d.1": "How often does {a} face conflict situations at work?",
    "4.C.2.a.1.c": "How often does {a} work outdoors, exposed to the weather?",
    "4.C.3.d.1": "How often does {a} work under time pressure to meet strict deadlines?",
    "4.C.1.a.2.c": "How often does {a} speak in public as part of the job?",
    "4.C.1.a.2.h": "How often does {a} use email for work?",
    "4.C.2.c.1.b": "How often is {a} exposed to diseases or infections at work?",
    "4.C.2.d.1.a": "How much of the workday does {a} spend sitting?",
    "4.C.3.a.4": "How much freedom does {a} have to make decisions without supervision?",
    "4.C.3.a.1": "If {a} made a mistake at work, how serious would the result usually be?",
    "4.C.3.b.2": "How automated is the work of {a}?",
    "4.C.3.c.1": "How competitive is the work of {a}?",
}
OCCUPATIONS = {  # O*NET-SOC code: "a <singular>"
    "29-1141.00": "a registered nurse", "11-1011.00": "a chief executive", "25-2021.00": "an elementary school teacher",
    "53-3032.00": "a long-haul truck driver", "23-1011.00": "a lawyer", "33-2011.00": "a firefighter",
    "41-2011.00": "a cashier", "35-3031.00": "a waiter or waitress", "37-2011.00": "a janitor",
    "47-2111.00": "an electrician", "29-1021.00": "a dentist", "29-1051.00": "a pharmacist",
    "53-2011.00": "an airline pilot", "35-1011.00": "a chef", "47-2061.00": "a construction laborer",
    "43-4051.00": "a customer service representative", "25-4022.00": "a librarian", "27-2011.00": "an actor",
    "21-1021.00": "a child and family social worker", "47-2152.00": "a plumber", "39-5012.00": "a hairdresser",
    "47-2031.00": "a carpenter", "35-3011.00": "a bartender", "19-3011.00": "an economist", "29-1131.00": "a veterinarian",
    "53-2031.00": "a flight attendant", "41-9022.00": "a real estate agent", "27-1024.00": "a graphic designer",
    "33-9032.00": "a security guard", "27-2042.00": "a musician or singer", "23-1023.00": "a judge",
    "13-2082.00": "a tax preparer", "41-9041.00": "a telemarketer", "47-2181.00": "a roofer",
    "35-3023.00": "a fast food worker", "53-3052.00": "a bus driver", "45-4022.00": "a logging equipment operator",
    "27-2021.00": "a professional athlete", "15-2021.00": "a mathematician", "53-2021.00": "an air traffic controller",
    "33-3012.00": "a correctional officer", "11-9171.00": "a funeral home manager", "29-1292.00": "a dental hygienist",
    "15-1254.00": "a web developer", "25-2012.00": "a kindergarten teacher", "11-9013.00": "a farmer or rancher",
}


def fetch(raw_dir: Path) -> None:
    for f, u in FILES.items():
        if not (raw_dir / f).exists():
            urllib.request.urlretrieve(BASE + u, raw_dir / f)


def normalize(raw_dir: Path) -> Iterator[Question]:
    cats: dict[str, list[str]] = {}
    for r in csv.DictReader(open(raw_dir / "wc_categories.txt"), delimiter="\t"):
        if r["Scale ID"] == "CXP" and r["Element ID"] in ITEMS:
            cats.setdefault(r["Element ID"], []).append(r["Category Description"])
    data: dict[tuple[str, str], dict] = {}
    for r in csv.DictReader(open(raw_dir / "work_context.txt"), delimiter="\t"):
        if r["Scale ID"] != "CXP" or r["Element ID"] not in ITEMS or r["O*NET-SOC Code"] not in OCCUPATIONS:
            continue
        d = data.setdefault((r["O*NET-SOC Code"], r["Element ID"]), {"dist": {}, "n": int(r["N"] or 0), "suppress": False,
                                                                      "name": r["Element Name"], "date": r["Date"]})
        d["dist"][str(int(r["Category"]) - 1)] = float(r["Data Value"]) / 100
        d["suppress"] |= r["Recommend Suppress"] == "Y"
    titles = {r["O*NET-SOC Code"]: r["Title"] for r in csv.DictReader(open(raw_dir / "occupations.txt"), delimiter="\t")}
    for (code, el), d in sorted(data.items()):
        if d["suppress"] or len(d["dist"]) != 5:
            continue
        tot = sum(d["dist"].values()) or 1
        a = OCCUPATIONS[code]
        yield Question(
            text=ITEMS[el].format(a=a), primitive="score", hemisphere="world", kind="factual", origin="dataset",
            source=NAME, options=cats[el], node_hint=NODE, license=LICENSE, source_item_id=f"{code}:{el}",
            human=[HumanDist(population=f"US workers in the occupation ({titles[code]})",
                             distribution={k: v / tot for k, v in sorted(d["dist"].items())}, n=d["n"],
                             source=f"O*NET 29.0 Work Context, {d['name']} (scale CXP), incumbents surveyed {d['date']}")],
            meta={"experiment": "onet_context", "occupation": titles[code], "soc": code, "element": d["name"],
                  "element_id": el})
