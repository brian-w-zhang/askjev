"""Stack Overflow Developer Survey: pairwise "which would you rather work with over the next year" Choices between
two technologies of one category, with the human split from respondents who have used both and want exactly one."""

from __future__ import annotations

import itertools
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterator

import httpx
import polars as pl

from askjev.model import HumanDist, Question
from askjev.sampling import env_int, hash_order

NAME = "so_survey_pairs"
URL = "https://github.com/StackExchange/Survey/raw/refs/heads/main/packages/archive/{year}/results.csv"
YEARS = (2024, 2025, 2023)  # HumanDist order: 2024 is the primary wave
LICENSE = "Stack Overflow Developer Survey results: ODbL 1.0 (database), DbCL 1.0 (contents)"
TARGET = env_int("TARGET_SO_SURVEY_PAIRS", 5000)
SALT = "so_survey_pairs.v1"
MIN_N_BEST = 50  # a pair needs >= 50 deciders in at least one year
MIN_N_WAVE = 30  # any year with >= 30 deciders adds a HumanDist
MAX_PER_ITEM = 45  # appearances of one technology within its category

TAIL = " would you rather work with over the next year: {a} or {b}?"
# category -> (question stem, node, survey column prefix per year)
CATS: dict[str, dict] = {
    "language": {"stem": "Which programming language", "node": "world.tech.software_programming",
                 "cols": {2023: "Language", 2024: "Language", 2025: "Language"}},
    "database": {"stem": "Which database", "node": "world.tech.software_programming",
                 "cols": {2023: "Database", 2024: "Database", 2025: "Database"}},
    "platform": {"stem": "Which cloud platform", "node": "world.tech.internet_web",
                 "cols": {2023: "Platform", 2024: "Platform", 2025: "Platform"}},
    "webframe": {"stem": "Which web framework or web technology", "node": "world.tech.software_programming",
                 "cols": {2023: "Webframe", 2024: "Webframe", 2025: "Webframe"}},
    "misc": {"stem": "Which software framework or library", "node": "world.tech.software_programming",
             "cols": {2023: "MiscTech", 2024: "MiscTech"}},
    "tools": {"stem": "Which developer tool", "node": "world.tech.software_programming",
              "cols": {2023: "ToolsTech", 2024: "ToolsTech", 2025: "Platform"}},
    "ide": {"stem": "Which code editor or development environment", "node": "world.tech.software_programming",
            "cols": {2023: "NEWCollabTools", 2024: "NEWCollabTools", 2025: "DevEnvs"}},
    "async": {"stem": "Which project collaboration or documentation tool", "node": "world.tech.internet_web",
              "cols": {2023: "OfficeStackAsync", 2024: "OfficeStackAsync", 2025: "OfficeStackAsync"}},
    "sync": {"stem": "Which chat or meeting tool", "node": "world.tech.internet_web",
             "cols": {2023: "OfficeStackSync", 2024: "OfficeStackSync"}},
    "ai": {"stem": "Which AI search or coding assistant", "node": "world.tech.ai",
           "cols": {2023: "AISearch", 2024: "AISearchDev"}},
    "ai_models": {"stem": "Which family of AI models", "node": "world.tech.ai", "cols": {2025: "AIModels"},
                  "tail": " would you rather use over the next year: {a} or {b}?"},
    "community": {"stem": "Which online platform for developer content and community",
                  "node": "world.tech.social_media", "cols": {2025: "CommPlatform"},
                  "tail": " would you rather use over the next year: {a} or {b}?"},
}

# 2025 folded cloud platforms and dev tools into one "Platform" list; these items are cloud platforms, the rest tools.
CLOUD_2025 = {"Amazon Web Services (AWS)", "Cloudflare", "Digital Ocean", "Firebase", "Google Cloud", "Heroku",
              "IBM Cloud", "Microsoft Azure", "Netlify", "Railway", "Supabase", "Vercel", "Yandex Cloud"}
DROP = {"NA", "Colocation", "Managed Hosting"}  # no answer; not a product
RENAME = {
    "Bash/Shell (all shells)": "Bash/Shell", "Cobol": "COBOL", "Dynamodb": "DynamoDB", "Cockroachdb": "CockroachDB",
    "Clickhouse": "ClickHouse", "Neo4J": "Neo4j", "Couch DB": "CouchDB", "Linode, now Akamai": "Linode (Akamai)",
    "IBM Cloud Or Watson": "IBM Cloud", "ASP.NET CORE": "ASP.NET Core", "Htmx": "htmx", "Solid.js": "SolidJS",
    ".NET (5+) ": ".NET (5+)", "Opencv": "OpenCV", "Pip": "pip", "Whatsapp": "WhatsApp", "Clickup": "ClickUp",
    "Rocketchat": "Rocket.Chat", "Ringcentral": "RingCentral", "Markdown File": "Markdown files",
    "Azure Devops": "Azure DevOps", "Lucid (includes Lucidchart)": "Lucid", "Digital Ocean": "DigitalOcean",
    "Dingtalk (Teambition)": "DingTalk (Teambition)", "Planview Projectplace Or Clarizen": "Planview Projectplace or Clarizen",
    "GitHub (public projects, not private repos)": "GitHub", "Slack (public channels, not work)": "Slack",
    "X": "X (Twitter)", "Rasberry Pi": "Raspberry Pi", "openAI GPT (chatbot models)": "OpenAI GPT chat models",
    "openAI Reasoning models": "OpenAI reasoning models", "openAI Image generating models": "OpenAI image models",
    "Anthropic: Claude Sonnet": "Anthropic Claude Sonnet", "Cohere: Command A": "Cohere Command A",
    "Reka (Flash 3 or other Reka models)": "Reka models", "Visual Studio Intellicode": "Visual Studio IntelliCode",
    "Torch/PyTorch": "PyTorch", "Scikit-Learn": "scikit-learn", "Jupyter Notebook/JupyterLab": "Jupyter",
}


def fetch(raw_dir: Path) -> None:
    for y in YEARS:
        out = raw_dir / f"results_{y}.csv"
        if out.exists():
            continue
        with httpx.stream("GET", URL.format(year=y), timeout=900, follow_redirects=True) as r:
            r.raise_for_status()
            with open(out, "wb") as fh:
                for chunk in r.iter_bytes(1 << 20):
                    fh.write(chunk)


def _name(raw: str) -> str:
    return RENAME.get(raw, RENAME.get(raw.strip(), raw.strip()))


def _slug(name: str) -> str:
    s = name.replace("C++", "C plus plus").replace("C#", "C sharp").replace("F#", "F sharp")
    s = s.replace(".NET", " dotnet").replace("++", " plus plus").replace("#", " sharp")
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    s = re.sub(r"[^a-z0-9]+", "_", s).strip("_")
    return s[:40].rstrip("_")


def _in_cat(cat: str, year: int, item: str) -> bool:
    if year == 2025 and cat == "platform":
        return item in CLOUD_2025
    if year == 2025 and cat == "tools":
        return item not in CLOUD_2025
    return True


def _counts(raw_dir: Path) -> dict[tuple[str, int], dict[tuple[str, str], Counter]]:
    """(cat, year) -> {(a, b) sorted names: Counter{name: wanters}} over respondents who used both, wanting one."""
    out: dict[tuple[str, int], dict] = {}
    for y in YEARS:
        cols = {c["cols"][y] for c in CATS.values() if y in c["cols"]}
        need = [f"{p}{s}" for p in sorted(cols) for s in ("HaveWorkedWith", "WantToWorkWith")]
        df = pl.read_csv(raw_dir / f"results_{y}.csv", infer_schema_length=0, columns=need)
        for cat, c in CATS.items():
            if y not in c["cols"]:
                continue
            p = c["cols"][y]
            pairs: dict[tuple[str, str], Counter] = defaultdict(Counter)
            for have, want in zip(df[f"{p}HaveWorkedWith"].to_list(), df[f"{p}WantToWorkWith"].to_list()):
                if not have:
                    continue
                H = {_name(x) for x in have.split(";") if x.strip() not in DROP}
                H = {x for x in H if _in_cat(cat, y, x)}
                W = {_name(x) for x in want.split(";")} if want else set()
                for a, b in itertools.combinations(sorted(H, key=str.lower), 2):
                    if (a in W) != (b in W):
                        pairs[(a, b)][a if a in W else b] += 1
            out[(cat, y)] = pairs
    return out


def normalize(raw_dir: Path) -> Iterator[Question]:
    counts = _counts(raw_dir)
    pool = []
    for cat, c in CATS.items():
        keys = set()
        for y in c["cols"]:
            keys |= set(counts[(cat, y)])
        for pair in keys:
            waves = [(y, counts[(cat, y)].get(pair)) for y in YEARS if y in c["cols"]]
            waves = [(y, ct) for y, ct in waves if ct and sum(ct.values()) >= MIN_N_WAVE]
            if waves and max(sum(ct.values()) for _, ct in waves) >= MIN_N_BEST:
                pool.append((cat, pair, waves))
    used: Counter = Counter()
    taken = []
    for cat, (a, b), waves in hash_order(pool, lambda x: f"{x[0]}|{x[1][0]}|{x[1][1]}", SALT):
        if used[(cat, a)] >= MAX_PER_ITEM or used[(cat, b)] >= MAX_PER_ITEM:
            continue
        used[(cat, a)] += 1
        used[(cat, b)] += 1
        taken.append((cat, (a, b), waves))
        if len(taken) >= TARGET:
            break
    for cat, (a, b), waves in taken:
        c = CATS[cat]
        ka, kb = _slug(a), _slug(b)
        if ka == kb:
            continue
        human = []
        for y, ct in waves:
            n = sum(ct.values())
            human.append(HumanDist(
                population=f"Stack Overflow Developer Survey {y} respondents who had used both and wanted to keep using exactly one",
                distribution={ka: ct[a] / n, kb: ct[b] / n}, n=n,
                source=f"Stack Overflow Developer Survey {y} (HaveWorkedWith x WantToWorkWith)", wave=str(y)))
        yield Question(
            text=c["stem"] + c.get("tail", TAIL).format(a=a, b=b),
            primitive="choice", hemisphere="self", origin="dataset", source=NAME, kind="taste",
            options={ka: a, kb: b}, node_hint="self.lifestyle.work_study_life", source_item_id=f"{cat}:{a}|{b}", license=LICENSE,
            template_id=f"{NAME}.{cat}", human=human,
            meta={"category": cat, "years": [y for y, _ in waves]},
        )
