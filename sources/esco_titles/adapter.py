"""ESCO occupation labels -> ISCO-08 sub-major group.

ESCO (European Skills, Competences, Qualifications and Occupations, European Commission) lists ~3,000
occupations, each with a preferred label and alternative labels (the job titles people and employers actually
use), and places every occupation under an ISCO-08 unit group. The HF mirror danieldux/ESCO ships the English
occupations with their full ISCO hierarchy.

Template "esco_titles.isco_submajor": Choice "Which ISCO occupation sub-major group does the job title `job_title` belong to?"
over the 42 ISCO-08 sub-major groups that have ESCO occupations (keys and short descriptions written from the
ISCO-08 definitions), truth = the sub-major group of the occupation the title belongs to. Titles that appear
under occupations in two different sub-major groups are dropped. Round-robin across groups in salted-hash order,
so small groups (armed forces, street vendors, food preparation assistants) are fully used and large ones capped.
This is a different taxonomy and title source from people_docs' O*NET -> SOC major group template.
"""

from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Iterator

import httpx

from askjev.model import Question
from askjev.sampling import env_int, hash_order

NAME = "esco_titles"
URL = "https://huggingface.co/datasets/danieldux/ESCO/resolve/main/esco_occupations.jsonl"
LICENSE = "ESCO (c) European Union, reuse under Commission Decision 2011/833/EU (attribution); HF mirror danieldux/ESCO: CC"
TARGET = env_int("TARGET_ESCO_TITLES", 2500)
TEXT = "Which ISCO occupation sub-major group does the job title `job_title` belong to?"

GROUPS: dict[str, tuple[str, str]] = {
    "01": ("armed_forces_officers", "Commissioned officers in the armed forces"),
    "02": ("armed_forces_nco", "Non-commissioned officers in the armed forces (sergeants and similar)"),
    "03": ("armed_forces_other_ranks", "Armed forces members of other ranks (soldiers, sailors, airmen)"),
    "11": ("chief_executives_officials_legislators", "Chief executives, senior government officials and legislators"),
    "12": ("administrative_commercial_managers", "Managers of business services, administration, sales and marketing"),
    "13": ("production_specialized_managers", "Managers of production, construction, logistics, ICT, health, education and other specialised services"),
    "14": ("hospitality_retail_managers", "Managers of hotels, restaurants, shops and other services"),
    "21": ("science_engineering_professionals", "Scientists, engineers, architects and designers"),
    "22": ("health_professionals", "Doctors, nurses, pharmacists, therapists and other health professionals"),
    "23": ("teaching_professionals", "Teachers and educators at any level"),
    "24": ("business_administration_professionals", "Finance, administration, HR, marketing and sales professionals"),
    "25": ("ict_professionals", "Software, web, database and network professionals"),
    "26": ("legal_social_cultural_professionals", "Lawyers, librarians, social scientists, clergy, writers, artists and performers"),
    "31": ("science_engineering_technicians", "Science and engineering technicians, process controllers, ship and aircraft crew and technicians"),
    "32": ("health_associate_professionals", "Medical, pharmaceutical, dental and prosthetic technicians, nursing and midwifery associates, paramedics and other health associates"),
    "33": ("business_administration_associates", "Finance and sales associates, brokers, agents, secretaries and regulatory officers"),
    "34": ("legal_social_cultural_associates", "Legal, social and religious associates, sports, fitness, arts and culinary associates"),
    "35": ("ict_technicians", "ICT operations, user support and telecommunications technicians"),
    "41": ("general_keyboard_clerks", "General office clerks, secretaries and keyboard operators"),
    "42": ("customer_services_clerks", "Tellers, collectors, travel, reception and other customer service clerks"),
    "43": ("numerical_material_recording_clerks", "Accounting, payroll, stock, production and transport clerks"),
    "44": ("other_clerical_workers", "Library, mail, filing, coding and other clerical workers"),
    "51": ("personal_services_workers", "Travel attendants, cooks, waiters, hairdressers, housekeepers and other personal services"),
    "52": ("sales_workers", "Shop salespersons, cashiers, street and market sellers and other sales workers"),
    "53": ("personal_care_workers", "Child care workers, teachers' aides and personal care workers in health services"),
    "54": ("protective_services_workers", "Firefighters, police officers, prison guards, security guards"),
    "61": ("skilled_agricultural_workers", "Skilled crop, animal and mixed farm workers"),
    "62": ("skilled_forestry_fishery_hunting_workers", "Skilled forestry, fishery and hunting workers"),
    "71": ("building_trades_workers", "Builders, carpenters, plumbers, painters and other building trades (not electricians)"),
    "72": ("metal_machinery_trades_workers", "Metal workers, blacksmiths, toolmakers, machinery mechanics and repairers"),
    "73": ("handicraft_printing_workers", "Handicraft workers, jewellers, potters, instrument makers and printing trades"),
    "74": ("electrical_electronics_trades_workers", "Electricians and electronics and telecommunications installers and repairers"),
    "75": ("food_wood_garment_craft_workers", "Food processing, woodworking, garment and upholstery trades, product graders and testers, fumigators and other craft trades"),
    "81": ("stationary_plant_machine_operators", "Operators of stationary plant and machines (mining, processing, manufacturing)"),
    "82": ("assemblers", "Assemblers of products and components"),
    "83": ("drivers_mobile_plant_operators", "Drivers, locomotive engineers, mobile plant operators and ships' deck crews"),
    "91": ("cleaners_helpers", "Domestic, hotel, office and vehicle cleaners and helpers"),
    "92": ("agricultural_forestry_fishery_labourers", "Farm, forestry and fishery labourers"),
    "93": ("mining_construction_manufacturing_transport_labourers", "Labourers in mining, construction, manufacturing and transport"),
    "94": ("food_preparation_assistants", "Fast food preparers and kitchen helpers"),
    "95": ("street_sales_services_workers", "Street vendors and street service workers (not food)"),
    "96": ("refuse_other_elementary_workers", "Refuse workers, messengers, odd-job persons and other elementary workers"),
}
OPTIONS = {k: d for k, d in GROUPS.values()}

# Second template: ISCO-08 skill level (1-4), stated in each sub-major group's ISCO definition ("Competent
# performance ... requires skills at the Nth ISCO skill level"); 25 (ICT professionals) states none and takes its
# major group's level 4. Armed forces are left out (ISCO assigns them levels by rank, not by task).
TARGET_SKILL = env_int("TARGET_ESCO_SKILL_LEVEL", 2000)
SKILL_TEXT = "What level of skill does the job `job_title` typically require?"
SKILL_LEVELS = [
    "Simple, routine physical or manual tasks that can be learned on the job in a short time; primary schooling is enough",
    "Operating machines or equipment, handling information, serving customers or skilled manual work; typically needs "
    "completed secondary education or vocational training",
    "Complex technical and practical tasks that need a large body of specialised knowledge; typically needs one to "
    "three years of study after secondary school",
    "Complex problem-solving, decision-making and creativity based on extensive theoretical knowledge; typically "
    "needs a university degree or higher",
]
SKILL_OF = {"first": 0, "second": 1, "third": 2, "fourth": 3}


def fetch(raw_dir: Path) -> None:
    out = raw_dir / "esco_occupations.jsonl"
    if out.exists():
        return
    r = httpx.get(URL, follow_redirects=True, timeout=300)
    r.raise_for_status()
    out.write_bytes(r.content)


def normalize(raw_dir: Path) -> Iterator[Question]:
    rows = [json.loads(line) for line in open(raw_dir / "esco_occupations.jsonl", encoding="utf-8") if line.strip()]
    title_groups: dict[str, set[str]] = defaultdict(set)
    title_info: dict[str, tuple[str, str, str]] = {}  # lower title -> (shown title, esco code, occupation)
    for r in rows:
        g = r["ISCO_CODE_2"]
        if g not in GROUPS:  # 63 (subsistence workers) has occupations but no English labels
            continue
        labels = [x for x in (r.get("ESCO_LABELS") or []) + [r.get("ESCO_OCCUPATION")] if x and x.strip()]
        for t in labels:
            t = " ".join(t.split())
            k = t.lower()
            title_groups[k].add(g)
            title_info.setdefault(k, (t, r["ESCO_CODE"], r["ESCO_OCCUPATION"]))
    by_group: dict[str, list[str]] = defaultdict(list)
    for k, gs in title_groups.items():
        if len(gs) == 1 and len(k) <= 120:
            by_group[next(iter(gs))].append(k)
    for g in by_group:
        by_group[g] = hash_order(by_group[g], lambda x: x, f"esco_titles|{g}")
    groups = sorted(by_group)
    picked: list[tuple[str, str]] = []
    i = 0
    while len(picked) < TARGET:
        added = False
        for g in groups:
            if i < len(by_group[g]) and len(picked) < TARGET:
                picked.append((g, by_group[g][i]))
                added = True
        if not added:
            break
        i += 1
    yield from _submajor(picked, title_info)

    # Skill level: titles disjoint from the sub-major sample, 500 per level in salted-hash order.
    level_of: dict[str, int] = {}
    for r in rows:
        g = r["ISCO_CODE_2"]
        if g not in GROUPS or g.startswith("0"):
            continue
        m = re.search(r"skills? at the (\w+) ISCO skill level", r["ISCO_DEFINITION_2"] or "")
        level_of[g] = SKILL_OF[m.group(1)] if m else 3
    used = {k for _, k in picked}
    by_level: dict[int, list[tuple[str, str]]] = defaultdict(list)
    for g in groups:
        if g not in level_of:
            continue
        for k in by_group[g]:
            if k not in used:
                by_level[level_of[g]].append((g, k))
    per = TARGET_SKILL // 4
    for lvl in sorted(by_level):
        for g, k in hash_order(by_level[lvl], lambda x: x[1], f"esco_titles.skill|{lvl}")[:per]:
            shown, code, occ = title_info[k]
            yield Question(
                text=SKILL_TEXT, primitive="score", hemisphere="machine", origin="dataset", source=NAME,
                options=SKILL_LEVELS, state={"job_title": shown}, shape="score",
                node_hint="machine.people.resume_match", template_id="esco_titles.skill_level",
                source_item_id=f"esco:{code}:{k}", license=LICENSE, truth=lvl,
                meta={"isco_submajor": g, "esco_code": code, "esco_occupation": occ},
            )


def _submajor(picked, title_info) -> Iterator[Question]:
    for g, k in picked:
        shown, code, occ = title_info[k]
        yield Question(
            text=TEXT,
            primitive="choice",
            hemisphere="machine",
            origin="dataset",
            source=NAME,
            options=OPTIONS,
            state={"job_title": shown},
            shape="classify",
            node_hint="machine.people.lead_fit",
            template_id="esco_titles.isco_submajor",
            source_item_id=f"esco:{code}:{k}",
            license=LICENSE,
            truth=GROUPS[g][0],
            meta={"isco_submajor": g, "esco_code": code, "esco_occupation": occ},
        )
