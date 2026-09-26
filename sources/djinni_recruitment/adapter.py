"""Djinni recruitment dataset (lang-uk, English subsets): real job postings and real candidate profiles from
Djinni, a Ukrainian IT job board. Every posting and profile carries the category ("Primary Keyword") the
employer or candidate picked from Djinni's fixed list, and postings carry the minimum experience the employer
selected.

Templates:
- "djinni.job_role": Choice "Which role category is the job in `job_description` hiring for?" over 39 Djinni
  categories, truth = the employer's Primary Keyword. Only the description is shown (not the title).
- "djinni.candidate_role": Choice "Which role category is the candidate who wrote `profile` looking for?" over
  the same 39 categories, truth = the candidate's Primary Keyword. The profile is the CV text without the
  headline title.
- "djinni.job_experience": Score "How much professional experience does `job_description` ask for?", five
  levels (no experience, 1, 2, 3, 5+ years), truth = the employer's "Exp Years" selection.
- "djinni.candidate_job_fit": Noul "Is the candidate who wrote `profile` looking for the kind of role
  advertised in `job_description`?" Half pairs share a category (true), half pair categories that are clearly
  different (confusable neighbours such as QA / QA Automation or JavaScript / Node.js are never used as
  negatives).
Rows are kept only when the hidden headline title agrees with the category (TITLE_RE), which removes most
mislabelled rows. "Other" and the job-only categories (Block-chain, Product Owner, React, SAP) are dropped. Each template samples
round-robin across labels (salted hash order), with inputs disjoint across templates.
"""

from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path
from typing import Iterator

import httpx
import polars as pl

from askjev.model import Question
from askjev.sampling import env_int, hash_order

NAME = "djinni_recruitment"
BASE = "https://huggingface.co/api/datasets/lang-uk/recruitment-dataset-{}-english/parquet/default/train/0.parquet"
FILES = {"jobs": "job-descriptions", "candidates": "candidate-profiles"}
LICENSE = "MIT (lang-uk/recruitment-dataset-*-english, Djinni)"
T_JOB_ROLE = env_int("TARGET_DJINNI_JOB_ROLE", 2500)
T_CAND_ROLE = env_int("TARGET_DJINNI_CANDIDATE_ROLE", 2500)
T_JOB_EXP = env_int("TARGET_DJINNI_JOB_EXPERIENCE", 2500)
T_FIT = env_int("TARGET_DJINNI_FIT", 2500)
MAX_CHARS = 1500
MIN_CHARS = 250

ROLES: dict[str, tuple[str, str]] = {
    ".NET": ("dotnet", "C# / .NET development"),
    "Android": ("android", "Native Android app development"),
    "Artist": ("artist", "2D/3D art, animation or illustration (games, media)"),
    "Business Analyst": ("business_analyst", "Gathering and documenting business requirements"),
    "C++": ("cpp", "C or C++ development"),
    "Data Analyst": ("data_analyst", "Reporting, dashboards and business data analysis"),
    "Data Engineer": ("data_engineer", "Data pipelines, warehouses and ETL"),
    "Data Science": ("data_science", "Machine learning, statistics and data modelling"),
    "Design": ("design", "UI/UX, product, web or graphic design"),
    "DevOps": ("devops", "CI/CD, cloud infrastructure and deployment automation"),
    "Flutter": ("flutter", "Cross-platform mobile development with Flutter/Dart"),
    "Golang": ("golang", "Go development"),
    "HR": ("hr", "Human resources, people operations"),
    "iOS": ("ios", "Native iOS app development (Swift, Objective-C)"),
    "Java": ("java", "Java / JVM back-end development"),
    "JavaScript": ("javascript", "JavaScript / TypeScript front-end development (React, Angular, Vue)"),
    "Lead": ("lead", "Senior technical or executive leadership: CTO, architect, head of engineering, C-level"),
    "Lead Generation": ("lead_generation", "Finding and qualifying sales prospects"),
    "Marketing": ("marketing", "Marketing, brand, content, performance or PR"),
    "Node.js": ("nodejs", "Back-end JavaScript / TypeScript on Node.js"),
    "PHP": ("php", "PHP development (Laravel, Symfony, WordPress)"),
    "Product Manager": ("product_manager", "Owning a product's direction and roadmap"),
    "Project Manager": ("project_manager", "Running projects and delivery"),
    "Python": ("python", "Python development"),
    "QA": ("qa_manual", "Manual software testing"),
    "QA Automation": ("qa_automation", "Automated software testing"),
    "Recruiter": ("recruiter", "Recruiting and sourcing candidates"),
    "Ruby": ("ruby", "Ruby / Ruby on Rails development"),
    "Sales": ("sales", "Selling, account management and business development"),
    "Salesforce": ("salesforce", "Salesforce platform development or administration"),
    "Scala": ("scala", "Scala development"),
    "Scrum Master": ("scrum_master", "Scrum master / agile coach"),
    "Security": ("security", "Information security and penetration testing"),
    "SEO": ("seo", "Search engine optimization"),
    "SQL": ("sql", "Database development and administration (SQL, DBA)"),
    "Support": ("support", "Customer or technical support"),
    "Sysadmin": ("sysadmin", "System and network administration"),
    "Technical Writing": ("technical_writing", "Technical writing and documentation"),
    "Unity": ("unity", "Game development with Unity"),
}
ROLE_OPTIONS = {k: d for k, d in ROLES.values()}
# Categories that are close enough that a pair across them is not a clear "different kind of role".
CONFUSABLE = [
    {"QA", "QA Automation"},
    {"JavaScript", "Node.js"},
    {"Data Analyst", "Data Science", "Data Engineer", "SQL"},
    {"Design", "Artist"},
    {"Sales", "Lead Generation", "Salesforce"},
    {"HR", "Recruiter"},
    {"Project Manager", "Product Manager", "Scrum Master", "Business Analyst"},
    {"Marketing", "SEO", "Lead Generation"},
    {"Sysadmin", "DevOps", "Security"},
    {"Android", "Flutter", "iOS"},
    {"Unity", "C++", "Artist"},
    {"Java", "Scala"},
]

# A posting or profile is kept only when its (hidden) headline title agrees with its category, which removes
# most mislabelled rows (e.g. SAP consultant postings filed under Salesforce).
TITLE_RE = {k: re.compile(v, re.I) for k, v in {
    ".NET": r"\.net|c#|asp",
    "Android": r"android",
    "Artist": r"artist|animator|illustrat|\b[23]d\b|concept",
    "Business Analyst": r"business analy|\bba\b|system analy",
    "C++": r"c\+\+|embedded",
    "Data Analyst": r"data analy|\bbi\b|power bi|tableau|analyst",
    "Data Engineer": r"data engineer|etl|big data|data platform|data warehouse",
    "Data Science": r"data scien|machine learning|\bml\b|\bai\b|computer vision|\bnlp\b|deep learning",
    "Design": r"design|\bui\b|\bux\b",
    "DevOps": r"devops|\bsre\b|cloud|infrastructure|platform engineer",
    "Flutter": r"flutter|dart",
    "Golang": r"golang|\bgo\b",
    "HR": r"\bhr\b|human resource|people|talent|hrbp",
    "iOS": r"\bios\b|swift",
    "Java": r"\bjava\b|kotlin|spring",
    "JavaScript": r"javascript|front|react|angular|vue|\bjs\b|typescript",
    "Lead": r"\bcto\b|architect|head of|chief|\bvp\b|director|\blead\b|\bcio\b|\bcfo\b|\bcoo\b|\bceo\b",
    "Lead Generation": r"lead gen|\bsdr\b|business development rep",
    "Marketing": r"market|\bsmm\b|content|\bpr\b|brand|\bppc\b|media buy",
    "Node.js": r"node|nest",
    "PHP": r"php|laravel|symfony|wordpress|magento",
    "Product Manager": r"product",
    "Project Manager": r"project|delivery",
    "Python": r"python|django|flask",
    "QA": r"^(?!.*(automat|aqa|sdet)).*(\bqa\b|test|quality)",
    "QA Automation": r"automat|\baqa\b|sdet",
    "Recruiter": r"recruit|sourc|talent acquisition",
    "Ruby": r"ruby|rails",
    "Sales": r"sales|account|business develop",
    "Salesforce": r"salesforce",
    "Scala": r"scala",
    "Scrum Master": r"scrum|agile",
    "Security": r"secur|pentest|\bsoc\b|cyber",
    "SEO": r"\bseo\b",
    "SQL": r"sql|\bdba\b|database|oracle",
    "Support": r"support|customer|help ?desk",
    "Sysadmin": r"sysadmin|system admin|\badmin|network",
    "Technical Writing": r"writer|technical writ|documentation",
    "Unity": r"unity|game",
}.items()}

EXP_TEXT = "How much professional experience does `job_description` ask for?"
EXP_LEVELS = [
    "The job is open to people with no professional experience yet",
    "The job asks for about one year of professional experience",
    "The job asks for about two years of professional experience",
    "The job asks for about three years of professional experience",
    "The job asks for five or more years of professional experience",
]
EXP_MAP = {"no_exp": 0, "1y": 1, "2y": 2, "3y": 3, "5y": 4}
FIT_TEXT = "Is the candidate who wrote `profile` looking for the kind of role advertised in `job_description`?"
FIT_OPTIONS = {
    "true": "The profile's skills and goals point to the same kind of role the job advertises",
    "false": "The profile points to a clearly different kind of role",
}


def fetch(raw_dir: Path) -> None:
    for slug in FILES.values():
        out = raw_dir / f"recruitment-dataset-{slug}-english.parquet"
        if out.exists():
            continue
        r = httpx.get(BASE.format(slug), follow_redirects=True, timeout=600)
        r.raise_for_status()
        out.write_bytes(r.content)


def _clean(s: str) -> str:
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\n\s*\n+", "\n\n", s).strip()
    if len(s) > MAX_CHARS:
        s = s[:1050].rstrip() + " [...] " + s[-400:].lstrip()
    return s


def _short(s: str, n: int = 1000) -> str:
    return s if len(s) <= n else s[:700].rstrip() + " [...] " + s[-280:].lstrip()


def _round_robin(by_label: dict[str, list], k: int) -> list:
    labels = sorted(by_label)
    out, i = [], 0
    while len(out) < k:
        added = False
        for lab in labels:
            if i < len(by_label[lab]) and len(out) < k:
                out.append(by_label[lab][i])
                added = True
        if not added:
            break
        i += 1
    return out


def _confusable(a: str, b: str) -> bool:
    return any(a in g and b in g for g in CONFUSABLE)


def normalize(raw_dir: Path) -> Iterator[Question]:
    jobs = pl.read_parquet(raw_dir / "recruitment-dataset-job-descriptions-english.parquet")
    cands = pl.read_parquet(raw_dir / "recruitment-dataset-candidate-profiles-english.parquet")

    # Jobs: known role, usable description, dedup by normalized description.
    job_pool: list[dict] = []
    seen: set[str] = set()
    for r in jobs.select(["id", "Position", "Long Description", "Primary Keyword", "Exp Years"]).iter_rows(named=True):
        kw, desc = r["Primary Keyword"], r["Long Description"] or ""
        if kw not in ROLES or len(desc.strip()) < MIN_CHARS or not TITLE_RE[kw].search(r["Position"] or ""):
            continue
        key = re.sub(r"\W+", "", desc.lower())[:400]
        if key in seen:
            continue
        seen.add(key)
        job_pool.append({"id": r["id"], "text": _clean(desc), "kw": kw, "exp": r["Exp Years"]})
    cand_pool: list[dict] = []
    seen = set()
    for r in cands.select(["id", "Position", "CV", "Primary Keyword"]).iter_rows(named=True):
        kw, cv = r["Primary Keyword"], r["CV"] or ""
        if kw not in ROLES or len(cv.strip()) < MIN_CHARS or not TITLE_RE[kw].search(r["Position"] or ""):
            continue
        key = re.sub(r"\W+", "", cv.lower())[:400]
        if key in seen:
            continue
        seen.add(key)
        cand_pool.append({"id": r["id"], "text": _clean(cv), "kw": kw})

    used_jobs: set[str] = set()
    used_cands: set[str] = set()

    def by_label(pool, field, salt, used):
        d: dict = defaultdict(list)
        for x in hash_order(pool, lambda x: x["id"], salt):
            if x["id"] not in used and x[field] is not None:
                d[x[field]].append(x)
        return d

    def q(tid, prim, text, options, shape, node, state, truth, item_id, **meta):
        return Question(
            text=text, primitive=prim, hemisphere="machine", origin="dataset", source=NAME, options=options,
            state=state, shape=shape, node_hint=node, template_id=tid, source_item_id=item_id, license=LICENSE,
            truth=truth, meta=meta,
        )

    # 1. Job role.
    picked = _round_robin(by_label(job_pool, "kw", "djinni.job_role", used_jobs), T_JOB_ROLE)
    used_jobs |= {x["id"] for x in picked}
    for x in picked:
        yield q("djinni.job_role", "choice", "Which role category is the job in `job_description` hiring for?",
                ROLE_OPTIONS, "route", "machine.people.lead_fit", {"job_description": x["text"]},
                ROLES[x["kw"]][0], f"job:{x['id']}", label_raw=x["kw"], exp_years=x["exp"])

    # 2. Candidate role.
    picked = _round_robin(by_label(cand_pool, "kw", "djinni.candidate_role", used_cands), T_CAND_ROLE)
    used_cands |= {x["id"] for x in picked}
    for x in picked:
        yield q("djinni.candidate_role", "choice",
                "Which role category is the candidate who wrote `profile` looking for?", ROLE_OPTIONS, "route",
                "machine.people.resume_match", {"profile": x["text"]}, ROLES[x["kw"]][0], f"candidate:{x['id']}",
                label_raw=x["kw"])

    # 3. Job experience (balanced across the five levels).
    picked = _round_robin(by_label(job_pool, "exp", "djinni.job_experience", used_jobs), T_JOB_EXP)
    used_jobs |= {x["id"] for x in picked}
    for x in picked:
        yield q("djinni.job_experience", "score", EXP_TEXT, EXP_LEVELS, "score", "machine.people.resume_match",
                {"job_description": x["text"]}, EXP_MAP[x["exp"]], f"job:{x['id']}", exp_raw=x["exp"],
                role=x["kw"])

    # 4. Candidate-job fit: half same category, half clearly different category. Lead is excluded (it spans
    # every stack).
    jobs_by = by_label([x for x in job_pool if x["kw"] != "Lead"], "kw", "djinni.fit.jobs", used_jobs)
    cands_by = by_label([x for x in cand_pool if x["kw"] != "Lead"], "kw", "djinni.fit.cands", used_cands)
    labels = sorted(set(jobs_by) & set(cands_by))
    cand_cursor = {lab: 0 for lab in labels}
    job_cursor = {lab: 0 for lab in labels}
    pairs = []
    n = 0
    while len(pairs) < T_FIT:
        progressed = False
        for lab in labels:
            if len(pairs) >= T_FIT:
                break
            if cand_cursor[lab] >= len(cands_by[lab]):
                continue
            cand = cands_by[lab][cand_cursor[lab]]
            cand_cursor[lab] += 1
            same = n % 2 == 0
            n += 1
            if same:
                jlab = lab
            else:
                others = [o for o in labels if o != lab and not _confusable(o, lab)]
                jlab = hash_order(others, lambda o: o, f"djinni.fit|{cand['id']}")[0]
            if job_cursor[jlab] >= len(jobs_by[jlab]):
                continue
            job = jobs_by[jlab][job_cursor[jlab]]
            job_cursor[jlab] += 1
            pairs.append((cand, job, same))
            progressed = True
        if not progressed:
            break
    for cand, job, same in pairs:
        yield q("djinni.candidate_job_fit", "noul", FIT_TEXT, FIT_OPTIONS, "verify", "machine.people.resume_match",
                {"profile": _short(cand["text"]), "job_description": _short(job["text"])}, same,
                f"candidate:{cand['id']}|job:{job['id']}", candidate_role=cand["kw"], job_role=job["kw"])
